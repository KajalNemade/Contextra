"""
Indexing pipeline.
Stages: Upload → Sanitize → Filter → Parse → Graph → Embed → Summarize → READY
Each stage updates the job progress and repo status.
Runs in FastAPI BackgroundTasks (V1).
"""
from __future__ import annotations
import os
from datetime import datetime
from typing import Optional
import structlog

from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from models.db import Repo, File, Function, Import, Summary, Job, Event, TokenUsage
from models.db import RepoStatus, JobStatus
from services.scanner import scan_directory, clone_repo, get_commit_hash, check_limits
from services.sanitizer import is_blocked_file, scan_for_secrets
from parser.tree_parser import parse_file
from graph.builder import build_graph_from_files
from embeddings.engine import ensure_collection, embed_text, upsert_chunk, delete_repo_chunks
from services.llm_provider import summarize_code

log = structlog.get_logger()


async def _update_job(
    session: AsyncSession,
    job: Job,
    stage: str,
    progress: int,
    status: JobStatus = JobStatus.RUNNING,
):
    job.stage = stage
    job.progress = progress
    job.status = status
    session.add(job)
    await session.commit()


async def _update_repo_status(session: AsyncSession, repo: Repo, status: RepoStatus, error: str = None):
    repo.status = status
    if error:
        repo.error_message = error
    session.add(repo)
    await session.commit()


async def _emit_event(session: AsyncSession, repo_id: int, event_type: str, data: dict = None):
    event = Event(repo_id=repo_id, event_type=event_type, data=data or {})
    session.add(event)
    await session.commit()


async def run_indexing_pipeline(repo_id: int, session_factory):
    """
    Full indexing pipeline. Called as a background task.
    session_factory: callable returning AsyncSession context manager.
    """
    async with session_factory() as session:
        repo = await session.get(Repo, repo_id)
        if not repo:
            log.error("Repo not found", repo_id=repo_id)
            return

        job = Job(
            repo_id=repo_id,
            job_type="index",
            status=JobStatus.RUNNING,
            stage="starting",
            started_at=datetime.utcnow(),
        )
        session.add(job)
        await session.commit()

        try:
            await _run(repo, job, session)
        except Exception as e:
            log.error("Pipeline failed", repo_id=repo_id, error=str(e))
            await _update_repo_status(session, repo, RepoStatus.FAILED, str(e))
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.ended_at = datetime.utcnow()
            session.add(job)
            await session.commit()
            await _emit_event(session, repo_id, "repo_index_failed", {"error": str(e)})


async def _run(repo: Repo, job: Job, session: AsyncSession):
    repo_id = repo.id

    # ── Stage 1: Clone / locate ──────────────────────────────────────────────
    await _update_repo_status(session, repo, RepoStatus.INDEXING)
    await _update_job(session, job, "cloning", 5)

    if repo.url:
        local_path = clone_repo(repo.url, repo_id)
        repo.local_path = local_path
        repo.commit_hash = get_commit_hash(local_path)
        session.add(repo)
        await session.commit()
    elif repo.local_path:
        local_path = repo.local_path
    else:
        raise ValueError("No URL or local_path for repo")

    await _emit_event(session, repo_id, "repo_cloned", {"path": local_path})

    # ── Stage 2: Scan ────────────────────────────────────────────────────────
    await _update_repo_status(session, repo, RepoStatus.INDEXING)
    await _update_job(session, job, "scanning", 10)

    scan = scan_directory(local_path)
    limit_error = check_limits(scan["file_count"], scan["total_loc"])
    if limit_error:
        raise ValueError(limit_error)

    repo.file_count = scan["file_count"]
    repo.total_loc = scan["total_loc"]
    repo.languages = scan["languages"]
    session.add(repo)
    await session.commit()

    # ── Stage 3: Parse ───────────────────────────────────────────────────────
    await _update_repo_status(session, repo, RepoStatus.PARSING)
    await _update_job(session, job, "parsing", 20)

    file_imports_for_graph = []
    db_files = []

    for i, fi in enumerate(scan["files"]):
        # Secret scan
        try:
            with open(fi["full_path"], "r", errors="ignore") as f:
                raw = f.read()
            secret_warnings = scan_for_secrets(raw)
            if secret_warnings:
                log.warning("Secrets detected", path=fi["path"], warnings=secret_warnings)
        except Exception:
            pass

        # Parse
        parsed = parse_file(fi["full_path"], fi["path"], fi["language"])

        db_file = File(
            repo_id=repo_id,
            path=fi["path"],
            language=fi["language"],
            size_bytes=fi["size_bytes"],
            loc=fi["loc"],
            file_hash=fi["file_hash"],
        )
        session.add(db_file)
        await session.flush()  # get ID

        for fn in parsed.functions:
            db_fn = Function(
                file_id=db_file.id,
                repo_id=repo_id,
                name=fn["name"],
                class_name=fn.get("class_name"),
                start_line=fn["start_line"],
                end_line=fn["end_line"],
                body=fn.get("body"),
                docstring=fn.get("docstring"),
                parameters=fn.get("parameters", []),
                is_async=fn.get("is_async", False),
            )
            session.add(db_fn)

        for imp in parsed.imports:
            db_imp = Import(
                file_id=db_file.id,
                repo_id=repo_id,
                module=imp["module"],
                names=imp.get("names", []),
                is_relative=imp.get("is_relative", False),
            )
            session.add(db_imp)

        file_imports_for_graph.append({
            "path": fi["path"],
            "language": fi["language"],
            "loc": fi["loc"],
            "imports": parsed.imports,
        })
        db_files.append((db_file, parsed))

        if i % 20 == 0:
            await session.commit()
            progress = 20 + int((i / len(scan["files"])) * 20)
            await _update_job(session, job, "parsing", progress)

    await session.commit()
    await _emit_event(session, repo_id, "repo_parsed", {"file_count": len(db_files)})

    # ── Stage 4: Graph ───────────────────────────────────────────────────────
    await _update_repo_status(session, repo, RepoStatus.GRAPHING)
    await _update_job(session, job, "graphing", 45)

    dep_graph = build_graph_from_files(file_imports_for_graph)
    entry_points = dep_graph.get_entry_points()

    # Mark entry point files
    for ep in entry_points:
        for db_file, _ in db_files:
            if db_file.path == ep:
                db_file.is_entry_point = True
                session.add(db_file)

    await session.commit()
    await _emit_event(session, repo_id, "repo_graphed", {"entry_points": entry_points[:5]})

    # ── Stage 5: Embed ───────────────────────────────────────────────────────
    await _update_repo_status(session, repo, RepoStatus.EMBEDDING)
    await _update_job(session, job, "embedding", 55)

    await ensure_collection()
    await delete_repo_chunks(repo_id)

    embed_count = 0
    for db_file, parsed in db_files:
        for fn in parsed.functions:
            body = fn.get("body", "")
            if not body or len(body) < 20:
                continue

            chunk_text = f"File: {db_file.path}\nFunction: {fn['name']}\n\n{body}"
            print("EMBEDDING:", db_file.path, fn["name"],)
            vector = await embed_text(chunk_text)
            if vector:
                await upsert_chunk(
                    chunk_id=f"{repo_id}:{db_file.path}:{fn['name']}",
                    vector=vector,
                    payload={
                        "repo_id": repo_id,
                        "file_path": db_file.path,
                        "function_name": fn["name"],
                        "class_name": fn.get("class_name"),
                        "start_line": fn["start_line"],
                        "body": body,
                        "language": db_file.language,
                    },
                )
                embed_count += 1
                print("UPSERTED:", fn["name"],)

        if embed_count % 50 == 0 and embed_count > 0:
            progress = 55 + int((embed_count / max(1, sum(len(p.functions) for _, p in db_files))) * 20)
            await _update_job(session, job, "embedding", min(75, progress))

    await _emit_event(session, repo_id, "repo_embedded", {"chunk_count": embed_count})

    print("=" * 60)
    print("EMBEDDING FINISHED")
    print("TOTAL CHUNKS:", embed_count)
    print("=" * 60)

    await _update_repo_status(session, repo, RepoStatus.EMBEDDING)
    await _update_job(session, job, "embedding_complete", 90)

    print("=" * 60)
    print("SETTING REPO READY")
    print("REPO ID:", repo_id)
    print("=" * 60)

    await _update_repo_status(session, repo, RepoStatus.READY)

    print("READY SAVED TO DATABASE")

    job.status = JobStatus.DONE
    job.progress = 100
    job.stage = "complete"
    job.ended_at = datetime.utcnow()

    job.status = JobStatus.DONE
    job.progress = 100
    job.stage = "complete"
    job.ended_at = datetime.utcnow()

    session.add(job)
    await session.commit()

    await _emit_event(
        session,
        repo_id,
        "repo_ready",
        {
            "file_count": repo.file_count,
            "total_loc": repo.total_loc,
            "chunks": embed_count,
        },
    )

    log.info(
        "Indexing complete",
        repo_id=repo_id,
        files=repo.file_count,
    )
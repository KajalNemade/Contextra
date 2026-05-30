from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from storage.database import get_db
from models.db import Repo, Summary, File, Function, RepoStatus

router = APIRouter(prefix="/summary", tags=["summary"])


@router.get("/{repo_id}")
async def get_summary(repo_id: int, session: AsyncSession = Depends(get_db)):
    """Return the project-level and top file summaries."""
    repo = await session.get(Repo, repo_id)
    if not repo:
        raise HTTPException(404, "Repo not found")

    summaries_result = await session.execute(
        select(Summary)
        .where(Summary.repo_id == repo_id)
        .order_by(Summary.scope)
    )
    summaries = summaries_result.scalars().all()

    project_summary = next((s.content for s in summaries if s.scope == "project"), None)
    file_summaries = [
        {"path": s.path, "summary": s.content}
        for s in summaries if s.scope == "file"
    ][:20]

    # Structure overview
    files_result = await session.execute(
        select(File)
        .where(File.repo_id == repo_id)
        .order_by(File.loc.desc())
        .limit(20)
    )
    files = files_result.scalars().all()

    fn_result = await session.execute(
        select(Function)
        .where(Function.repo_id == repo_id)
        .limit(5)
    )
    sample_functions = fn_result.scalars().all()

    return {
        "repo_id": repo_id,
        "name": repo.name,
        "status": repo.status,
        "stats": {
            "file_count": repo.file_count,
            "total_loc": repo.total_loc,
            "languages": repo.languages or {},
        },
        "project_summary": project_summary,
        "file_summaries": file_summaries,
        "top_files": [
            {"path": f.path, "language": f.language, "loc": f.loc, "is_entry_point": f.is_entry_point}
            for f in files
        ],
        "onboarding": _generate_onboarding(repo, files, project_summary),
    }


def _generate_onboarding(repo, files, project_summary: str) -> dict:
    """Generate a deterministic onboarding guide from metadata (no AI needed)."""
    entry_points = [f.path for f in files if f.is_entry_point]
    languages = list(set(f.language for f in files if f.language))

    steps = []
    if entry_points:
        steps.append(f"Start at: {entry_points[0]}")
    steps.append(f"Languages: {', '.join(languages)}")
    steps.append(f"Total: {repo.file_count} files, {repo.total_loc:,} lines of code")

    key_dirs = list({"/".join(f.path.split("/")[:-1]) for f in files if "/" in f.path})[:5]
    if key_dirs:
        steps.append(f"Key directories: {', '.join(key_dirs)}")

    return {
        "summary": project_summary or f"Repository '{repo.name}' with {repo.file_count} files.",
        "steps": steps,
        "entry_points": entry_points[:5],
    }
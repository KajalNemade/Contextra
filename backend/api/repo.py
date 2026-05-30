from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, HttpUrl
from typing import Optional
import os
import shutil
import zipfile

from storage.database import get_db, AsyncSessionLocal
from models.db import Repo, RepoStatus
from jobs.indexing import run_indexing_pipeline
from config.settings import settings

router = APIRouter(prefix="/repo", tags=["repository"])


class RepoCreateRequest(BaseModel):
    url: Optional[str] = None
    name: Optional[str] = None


class RepoResponse(BaseModel):
    id: int
    name: str
    status: str
    url: Optional[str]
    commit_hash: Optional[str]
    file_count: int
    total_loc: int
    languages: Optional[dict]
    error_message: Optional[str]

    class Config:
        from_attributes = True


@router.post("", response_model=RepoResponse, status_code=201)
async def create_repo(
    request: RepoCreateRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
):
    """
    Submit a GitHub URL for indexing.
    Returns immediately with repo_id + QUEUED status.
    Indexing happens in background.
    """
    if not request.url:
        raise HTTPException(400, "URL is required")

    name = request.name or request.url.split("/")[-1].replace(".git", "")

    repo = Repo(name=name, url=request.url, status=RepoStatus.QUEUED)
    session.add(repo)
    await session.commit()
    await session.refresh(repo)

    background_tasks.add_task(run_indexing_pipeline, repo.id, AsyncSessionLocal)

    return repo


@router.post("/upload", response_model=RepoResponse, status_code=201)
async def upload_zip(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
):
    """
    Upload a ZIP of a repository.
    """
    if not file.filename.endswith(".zip"):
        raise HTTPException(400, "Only .zip files accepted")

    name = file.filename.replace(".zip", "")
    repo = Repo(name=name, status=RepoStatus.QUEUED)
    session.add(repo)
    await session.commit()
    await session.refresh(repo)

    dest_dir = os.path.join(settings.repos_path, str(repo.id))
    os.makedirs(dest_dir, exist_ok=True)
    zip_path = os.path.join(dest_dir, "upload.zip")

    with open(zip_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            # Check for zip bombs
            total_size = sum(info.file_size for info in z.infolist())
            if total_size > 500 * 1024 * 1024:  # 500 MB uncompressed limit
                raise HTTPException(400, "Archive too large when uncompressed")
            z.extractall(dest_dir)
    except zipfile.BadZipFile:
        raise HTTPException(400, "Invalid ZIP file")

    os.remove(zip_path)

    repo.local_path = dest_dir
    session.add(repo)
    await session.commit()

    background_tasks.add_task(run_indexing_pipeline, repo.id, AsyncSessionLocal)
    return repo


@router.get("", response_model=list[RepoResponse])
async def list_repos(session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Repo).order_by(Repo.created_at.desc()))
    return result.scalars().all()


@router.get("/{repo_id}", response_model=RepoResponse)
async def get_repo(repo_id: int, session: AsyncSession = Depends(get_db)):
    repo = await session.get(Repo, repo_id)
    if not repo:
        raise HTTPException(404, "Repo not found")
    return repo


@router.delete("/{repo_id}", status_code=204)
async def delete_repo(repo_id: int, session: AsyncSession = Depends(get_db)):
    repo = await session.get(Repo, repo_id)
    if not repo:
        raise HTTPException(404, "Repo not found")
    await session.delete(repo)
    await session.commit()

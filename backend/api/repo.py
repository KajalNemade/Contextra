from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
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


# -------------------------------
# CREATE REPO
# -------------------------------
@router.post("", response_model=RepoResponse, status_code=201)
async def create_repo(
    request: RepoCreateRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
):
    """
    Submit GitHub repository for indexing
    """

    if not request.url:
        raise HTTPException(status_code=400, detail="URL is required")

    repo_name = (
        request.name
        or request.url.split("/")[-1].replace(".git", "")
    )

    repo = Repo(
        name=repo_name,
        url=request.url,
        status=RepoStatus.QUEUED,
        commit_hash=None,
        file_count=0,
        total_loc=0,
        languages={},
        error_message=None,
    )

    session.add(repo)

    await session.commit()
    await session.refresh(repo)

    # Background indexing
    background_tasks.add_task(
        run_indexing_pipeline,
        repo.id,
        AsyncSessionLocal,
    )

    return repo


# -------------------------------
# UPLOAD ZIP
# -------------------------------
@router.post("/upload", response_model=RepoResponse, status_code=201)
async def upload_zip(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
):
    """
    Upload ZIP repository
    """

    if not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail="Only .zip files accepted",
        )

    repo_name = file.filename.replace(".zip", "")

    repo = Repo(
        name=repo_name,
        status=RepoStatus.QUEUED,
        file_count=0,
        total_loc=0,
        languages={},
    )

    session.add(repo)

    await session.commit()
    await session.refresh(repo)

    # Create repo directory
    dest_dir = os.path.join(settings.repos_path, str(repo.id))

    os.makedirs(dest_dir, exist_ok=True)

    zip_path = os.path.join(dest_dir, "upload.zip")

    # Save uploaded zip
    with open(zip_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Extract zip
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            total_size = sum(
                info.file_size for info in z.infolist()
            )

            # Prevent zip bombs
            if total_size > 500 * 1024 * 1024:
                raise HTTPException(
                    status_code=400,
                    detail="Archive too large",
                )

            z.extractall(dest_dir)

    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=400,
            detail="Invalid ZIP file",
        )

    os.remove(zip_path)

    repo.local_path = dest_dir

    session.add(repo)

    await session.commit()

    # Background indexing
    background_tasks.add_task(
        run_indexing_pipeline,
        repo.id,
        AsyncSessionLocal,
    )

    return repo


# -------------------------------
# LIST REPOS
# -------------------------------
@router.get("", response_model=list[RepoResponse])
async def list_repos(
    session: AsyncSession = Depends(get_db),
):
    result = await session.execute(
        select(Repo).order_by(Repo.id.desc())
    )

    repos = result.scalars().all()

    return repos


# -------------------------------
# GET SINGLE REPO
# -------------------------------
@router.get("/{repo_id}", response_model=RepoResponse)
async def get_repo(
    repo_id: int,
    session: AsyncSession = Depends(get_db),
):
    repo = await session.get(Repo, repo_id)

    if not repo:
        raise HTTPException(
            status_code=404,
            detail="Repo not found",
        )

    return repo


# -------------------------------
# DELETE REPO
# -------------------------------
@router.delete("/{repo_id}", status_code=204)
async def delete_repo(
    repo_id: int,
    session: AsyncSession = Depends(get_db),
):
    repo = await session.get(Repo, repo_id)

    if not repo:
        raise HTTPException(
            status_code=404,
            detail="Repo not found",
        )

    await session.delete(repo)

    await session.commit()

    return

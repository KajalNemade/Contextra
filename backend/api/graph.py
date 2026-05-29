from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from storage.database import get_db
from models.db import Repo, File, Import, RepoStatus
from graph.builder import build_graph_from_files

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/{repo_id}")
async def get_graph(repo_id: int, session: AsyncSession = Depends(get_db)):
    """
    Return the dependency graph for a repo.
    Used by React Flow for architecture visualization.
    Works completely offline — no AI needed.
    """
    repo = await session.get(Repo, repo_id)
    if not repo:
        raise HTTPException(404, "Repo not found")
    if repo.status not in (RepoStatus.READY, RepoStatus.SUMMARIZING, RepoStatus.EMBEDDING):
        raise HTTPException(409, f"Repo not ready (status: {repo.status})")

    # Load files
    files_result = await session.execute(select(File).where(File.repo_id == repo_id))
    files = files_result.scalars().all()

    file_map = {f.id: f for f in files}

    # Load imports
    imports_result = await session.execute(select(Import).where(Import.repo_id == repo_id))
    imports = imports_result.scalars().all()

    # Group imports by file
    imports_by_file: dict[int, list] = {}
    for imp in imports:
        imports_by_file.setdefault(imp.file_id, []).append({
            "module": imp.module,
            "names": imp.names or [],
            "is_relative": imp.is_relative,
        })

    file_imports = [
        {
            "path": f.path,
            "language": f.language,
            "loc": f.loc,
            "imports": imports_by_file.get(f.id, []),
        }
        for f in files
    ]

    graph = build_graph_from_files(file_imports)
    graph_data = graph.to_dict()
    layers = graph.get_architecture_layers()
    entry_points = graph.get_entry_points()
    circular = graph.detect_circular()

    return {
        "repo_id": repo_id,
        "graph": graph_data,
        "layers": layers,
        "entry_points": entry_points[:10],
        "circular_dependencies": circular[:5],
        "stats": {
            "total_nodes": len(graph_data["nodes"]),
            "total_edges": len(graph_data["edges"]),
        },
    }


@router.get("/{repo_id}/impact/{file_path:path}")
async def get_impact(repo_id: int, file_path: str, session: AsyncSession = Depends(get_db)):
    """Impact analysis: what breaks if this file changes?"""
    repo = await session.get(Repo, repo_id)
    if not repo:
        raise HTTPException(404, "Repo not found")

    files_result = await session.execute(select(File).where(File.repo_id == repo_id))
    files = files_result.scalars().all()
    imports_result = await session.execute(select(Import).where(Import.repo_id == repo_id))
    imports = imports_result.scalars().all()

    imports_by_file: dict[int, list] = {}
    for imp in imports:
        imports_by_file.setdefault(imp.file_id, []).append({
            "module": imp.module,
            "names": imp.names or [],
            "is_relative": imp.is_relative,
        })

    file_imports = [
        {"path": f.path, "language": f.language, "loc": f.loc, "imports": imports_by_file.get(f.id, [])}
        for f in files
    ]

    graph = build_graph_from_files(file_imports)
    impact = graph.impact_analysis(file_path)
    return impact




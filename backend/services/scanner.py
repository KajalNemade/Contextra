"""
Repository scanner.
Clones / reads a repo and produces a filtered file list.
"""
import os
import hashlib
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import git
import structlog

from config.settings import settings
from services.sanitizer import is_blocked_file

log = structlog.get_logger()

# Folders to always skip
IGNORE_DIRS = {
    "node_modules", ".git", "dist", "build", "coverage",
    "venv", ".venv", "__pycache__", ".cache", "target",
    "vendor", ".next", ".nuxt", "out", ".svelte-kit",
    "generated", "migrations",
}

# Extensions we can parse
SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
}


def _should_skip_dir(name: str) -> bool:
    return name in IGNORE_DIRS or name.startswith(".")


def _get_language(path: str) -> Optional[str]:
    ext = Path(path).suffix.lower()
    return SUPPORTED_EXTENSIONS.get(ext)


def _file_hash(path: str) -> str:
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def _count_loc(path: str) -> int:
    try:
        with open(path, "r", errors="ignore") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def clone_repo(url: str, repo_id: int) -> str:
    """Clone a git repo and return local path."""
    dest = os.path.join(settings.repos_path, str(repo_id))
    os.makedirs(settings.repos_path, exist_ok=True)
    if os.path.exists(dest):
        shutil.rmtree(dest)
    log.info("Cloning repo", url=url, dest=dest)
    git.Repo.clone_from(url, dest, depth=1)
    return dest


def get_commit_hash(local_path: str) -> Optional[str]:
    try:
        repo = git.Repo(local_path)
        return repo.head.commit.hexsha
    except Exception:
        return None


def scan_directory(local_path: str) -> Dict:
    """
    Walk the directory, filter junk, collect file metadata.
    Returns: {
        "files": [...],
        "file_count": int,
        "total_loc": int,
        "languages": {"python": N, ...}
    }
    """
    files = []
    total_loc = 0
    languages: Dict[str, int] = {}

    for root, dirs, filenames in os.walk(local_path):
        # Prune skip dirs in-place
        dirs[:] = [d for d in dirs if not _should_skip_dir(d)]

        for filename in filenames:
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, local_path)

            # Skip blocked filenames
            if is_blocked_file(filename):
                continue

            lang = _get_language(filename)
            if lang is None:
                continue  # Only index supported languages in V1

            try:
                size = os.path.getsize(full_path)
                loc = _count_loc(full_path)
                fhash = _file_hash(full_path)
            except Exception as e:
                log.warning("Could not read file", path=full_path, error=str(e))
                continue

            total_loc += loc
            languages[lang] = languages.get(lang, 0) + 1

            files.append({
                "path": rel_path,
                "language": lang,
                "size_bytes": size,
                "loc": loc,
                "file_hash": fhash,
                "full_path": full_path,
            })

    return {
        "files": files,
        "file_count": len(files),
        "total_loc": total_loc,
        "languages": languages,
    }


def check_limits(file_count: int, total_loc: int) -> Optional[str]:
    """Returns error message if repo exceeds limits, else None."""
    if file_count > settings.max_files:
        return f"Repo has {file_count} files (max {settings.max_files}). Use a smaller scope."
    if total_loc > settings.max_loc:
        return f"Repo has {total_loc} LOC (max {settings.max_loc})."
    return None

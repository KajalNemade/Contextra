"""
Shared utility helpers used across the backend.
"""
import re
import os


def format_loc(n: int) -> str:
    """Format lines-of-code count to human readable."""
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}k"
    return str(n)


def truncate(text: str, max_len: int = 200, suffix: str = "…") -> str:
    """Truncate a string to max_len characters."""
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len - len(suffix)] + suffix


def safe_filename(name: str) -> str:
    """Strip unsafe characters from a filename."""
    return re.sub(r'[^\w\-_.]', '_', name)


def lang_color(language: str) -> str:
    """Return a hex color for a language (for UI badges)."""
    colors = {
        "python":     "#3572A5",
        "javascript": "#f1e05a",
        "typescript": "#2b7489",
        "go":         "#00ADD8",
        "rust":       "#dea584",
        "java":       "#b07219",
        "c":          "#555555",
        "cpp":        "#f34b7d",
        "ruby":       "#701516",
        "php":        "#4F5D95",
    }
    return colors.get(language.lower(), "#8b949e")


def chunk_list(lst: list, size: int) -> list:
    """Split list into chunks of given size."""
    return [lst[i:i + size] for i in range(0, len(lst), size)]


def relative_path(base: str, full: str) -> str:
    """Get path of full relative to base."""
    return os.path.relpath(full, base)

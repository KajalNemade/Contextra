"""
Secret sanitizer — scans file content for likely secrets.
Must run BEFORE any embedding or LLM call.
"""
import re
from typing import List, Tuple
from config.settings import settings


# Patterns for common secret-like content
_SECRET_REGEXES = [
    re.compile(r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?[\w\-]{16,}'),
    re.compile(r'(?i)(secret[_-]?key|secret)\s*[=:]\s*["\']?[\w\-]{16,}'),
    re.compile(r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']?.{6,}'),
    re.compile(r'(?i)(token|auth[_-]?token)\s*[=:]\s*["\']?[\w\-]{16,}'),
    re.compile(r'(?i)(private[_-]?key)\s*[=:]\s*["\']?.{10,}'),
    re.compile(r'(?i)(aws[_-]?access[_-]?key[_-]?id)\s*[=:]\s*["\']?[A-Z0-9]{16,}'),
    re.compile(r'(?i)(aws[_-]?secret[_-]?access[_-]?key)\s*[=:]\s*["\']?[\w\+\/]{30,}'),
    re.compile(r'-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    re.compile(r'(?i)ghp_[A-Za-z0-9]{36}'),   # GitHub PAT
    re.compile(r'(?i)sk-[A-Za-z0-9]{32,}'),    # OpenAI-style key
]

# File names that should NEVER be indexed
_BLOCKED_FILENAMES = {
    ".env", ".env.local", ".env.production", ".env.staging",
    "id_rsa", "id_ecdsa", "id_ed25519", "id_dsa",
    "*.pem", "*.key", "*.pfx", "*.p12", "*.crt", "*.cer",
}


def is_blocked_file(filename: str) -> bool:
    """Returns True if the file should not be indexed at all."""
    basename = filename.split("/")[-1].split("\\")[-1]
    if basename in _BLOCKED_FILENAMES:
        return True
    for ext in (".pem", ".key", ".pfx", ".p12", ".crt", ".cer"):
        if basename.endswith(ext):
            return True
    return False


def redact_secrets(content: str) -> Tuple[str, List[str]]:
    """
    Redact secret-like strings from content.
    Returns (redacted_content, list_of_warnings).
    """
    warnings: List[str] = []
    redacted = content
    for pattern in _SECRET_REGEXES:
        matches = pattern.findall(redacted)
        if matches:
            warnings.append(f"Potential secret detected (pattern: {pattern.pattern[:40]})")
            redacted = pattern.sub("[REDACTED]", redacted)
    return redacted, warnings


def scan_for_secrets(content: str) -> List[str]:
    """Returns list of warnings if secrets found, empty list if clean."""
    _, warnings = redact_secrets(content)
    return warnings

"""Read-only repo-inspection tools.

Three stdlib-only functions that let the agent enumerate, read, and search
files in the repo. None of these tools write, fetch over the network, or
escape the repo root.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

EXCLUDED_DIR_NAMES = frozenset({
    ".git",
    ".gnhf",
    ".cache",
    "__pycache__",
    ".venv",
    "node_modules",
    ".DS_Store",
})

# Suffixes we consider safely text-grep-able. Keep small and explicit; agents
# that need to read a non-listed extension can still use `read_repo_file`.
TEXT_SUFFIXES = frozenset({
    ".md", ".py", ".txt", ".json", ".yml", ".yaml", ".toml",
    ".cfg", ".ini", ".jsonl", ".gitignore",
})

MAX_GREP_FILE_BYTES = 1_000_000  # skip files larger than 1 MB to stay snappy


def find_repo_root(start: Path) -> Path:
    """Walk up from `start` until OBJECTIVE.md is found."""
    for candidate in [start, *start.parents]:
        if (candidate / "OBJECTIVE.md").is_file():
            return candidate
    raise FileNotFoundError(
        f"Could not locate repo root above {start} (no OBJECTIVE.md found)"
    )


def _resolve_inside_repo(repo_root: Path, relative: str) -> Path | None:
    """Resolve `relative` against `repo_root`, refusing anything outside.

    Returns None if the resolved path escapes the repo (so callers can emit a
    structured error to the agent rather than raising).
    """
    candidate = (repo_root / relative).resolve()
    try:
        candidate.relative_to(repo_root.resolve())
    except ValueError:
        return None
    return candidate


def _excluded(path: Path, repo_root: Path) -> bool:
    rel_parts = path.resolve().relative_to(repo_root.resolve()).parts
    return any(part in EXCLUDED_DIR_NAMES for part in rel_parts)


@dataclass(frozen=True)
class GrepMatch:
    path: str
    line_number: int
    line: str


def list_repo_files(
    repo_root: Path,
    directory: str = ".",
    pattern: str = "*.md",
) -> list[str]:
    """Enumerate repo-relative paths matching `pattern` under `directory`.

    Pattern is a glob. `**` segments are honored (recursive). Excluded
    directories (`.git`, `.cache`, etc.) are filtered out of the result.
    Always returns repo-relative POSIX paths, sorted, deduplicated.
    """
    base = _resolve_inside_repo(repo_root, directory)
    if base is None or not base.is_dir():
        return []
    # If pattern has no `**`, we still do a recursive search so the default
    # `*.md` finds nested markdown — the README explicitly framed this tool
    # as "enumerate paths matching a pattern under a directory" (recursive).
    glob_pattern = pattern if "**" in pattern else f"**/{pattern}"
    matches: set[str] = set()
    for match in base.glob(glob_pattern):
        if not match.is_file():
            continue
        if _excluded(match, repo_root):
            continue
        rel = match.resolve().relative_to(repo_root.resolve()).as_posix()
        matches.add(rel)
    return sorted(matches)


def read_repo_file(
    repo_root: Path,
    path: str,
    start_line: int = 1,
    end_line: int | None = None,
) -> str:
    """Return a 1-indexed inclusive line slice of `path`, or an error string.

    Returns a sentinel `"ERROR: ..."` string (rather than raising) for the
    failure cases an agent could plausibly trigger: path outside repo, file
    missing, file is a directory, invalid line range. The agent receives this
    as a tool_result and can recover.
    """
    if start_line < 1:
        return f"ERROR: start_line must be >= 1 (got {start_line})"
    if end_line is not None and end_line < start_line:
        return (
            f"ERROR: end_line ({end_line}) must be >= start_line "
            f"({start_line})"
        )
    resolved = _resolve_inside_repo(repo_root, path)
    if resolved is None:
        return f"ERROR: path {path!r} escapes the repo root"
    if not resolved.exists():
        return f"ERROR: no such file: {path!r}"
    if not resolved.is_file():
        return f"ERROR: not a regular file: {path!r}"
    try:
        text = resolved.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"ERROR: cannot decode {path!r} as UTF-8 text"
    lines = text.splitlines()
    last = len(lines) if end_line is None else min(end_line, len(lines))
    if start_line > len(lines):
        return f"ERROR: start_line {start_line} > file length {len(lines)}"
    return "\n".join(lines[start_line - 1 : last])


def grep_repo(
    repo_root: Path,
    query: str,
    path: str = ".",
    max_matches: int = 20,
) -> list[GrepMatch]:
    """Case-insensitive substring search over text files under `path`.

    Path may be a directory (walk text files under it) or a single file.
    Binary files and excluded directories are skipped. Returns up to
    `max_matches` records in deterministic order (file path, then line
    number).
    """
    if not query:
        return []
    if max_matches < 1:
        return []
    base = _resolve_inside_repo(repo_root, path)
    if base is None or not base.exists():
        return []

    if base.is_file():
        candidates = [base]
    else:
        candidates = sorted(p for p in base.rglob("*") if p.is_file())

    needle = query.lower()
    matches: list[GrepMatch] = []
    for file_path in candidates:
        if _excluded(file_path, repo_root):
            continue
        if file_path.suffix and file_path.suffix not in TEXT_SUFFIXES:
            continue
        try:
            if file_path.stat().st_size > MAX_GREP_FILE_BYTES:
                continue
            text = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = file_path.resolve().relative_to(repo_root.resolve()).as_posix()
        for line_number, line in enumerate(text.splitlines(), start=1):
            if needle in line.lower():
                matches.append(
                    GrepMatch(path=rel, line_number=line_number, line=line)
                )
                if len(matches) >= max_matches:
                    return matches
    return matches

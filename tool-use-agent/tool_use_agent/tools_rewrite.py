"""Sandboxed file-rewrite tool.

Accepts a sandbox-relative path plus a structured edit operation
(``replace`` / ``append`` / ``prepend``) and a ``content`` string, applies
the edit to a file under ``tool-use-agent/sandbox/`` only, and returns a
unified diff describing the change. Refuses paths that resolve outside
the sandbox root.

Two-layer safety guardrail mirroring ``tools_sql.sql_query``:
  Layer 1 — operation enum + structured input. The caller picks one of
            three named operations; anything else is rejected before any
            file work. Eliminates command-injection-style fuzz.
  Layer 2 — sandbox-root resolve. The target path is resolved against the
            fixed sandbox root (``tool-use-agent/sandbox`` under the repo
            root) and ``.relative_to`` checked against the resolved
            sandbox root. Symlinks and ``..`` traversal both surface as
            an out-of-sandbox refusal.

The sandbox root is created lazily if missing — the directory must exist
for the tool to function, and rather than refusing on missing-sandbox we
create it once on first call so a freshly-cloned repo Just Works. The
agent must still pre-populate the sandbox with seed files for non-replace
operations; ``append``/``prepend``/``replace`` all require the target
file to already exist (the tool refuses missing files to keep the
"rewrite" contract honest — a separate "file_create" tool would own the
create-new-file surface if/when added).

The return shape mirrors ``sql_query``: structured success or a sentinel
``ERROR: ...`` string the agent can recover from.
"""

from __future__ import annotations

import difflib
from pathlib import Path
from typing import Any

# Repo-relative location of the sandbox. The tool refuses any path that
# does not resolve under this directory.
SANDBOX_RELDIR = "tool-use-agent/sandbox"

# The three supported edit operations. Anything else is rejected by the
# static-operation-enum layer of the guardrail.
OPERATIONS: frozenset[str] = frozenset({"replace", "append", "prepend"})

# Hard cap on file size before/after the edit. Keeps the diff bounded and
# the tool's response size under the agent's context budget.
MAX_FILE_BYTES = 1_000_000

# Hard cap on incoming `content`. Independent of MAX_FILE_BYTES so an
# append/prepend can't push the file over the file cap via repeated calls
# with smaller-than-file-cap payloads — the after-write size is checked
# explicitly below.
MAX_CONTENT_BYTES = 1_000_000


def _sandbox_root(repo_root: Path) -> Path:
    """Return the resolved sandbox root, creating it if missing.

    The sandbox directory itself is part of the build's committed
    layout, so this lazy-create is defensive (handles a freshly-cloned
    repo where the directory might exist with only a ``.gitkeep``). It
    does not create any files inside the sandbox.
    """
    root = (repo_root / SANDBOX_RELDIR).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _resolve_inside_sandbox(repo_root: Path, relative: str) -> Path | None:
    """Resolve ``relative`` against the sandbox root, refusing escapes.

    Returns None if the resolved path is not strictly inside the sandbox
    root (after symlink resolution). Callers emit a structured ERROR
    string to the agent rather than raising.
    """
    sandbox = _sandbox_root(repo_root)
    candidate = (sandbox / relative).resolve()
    try:
        candidate.relative_to(sandbox)
    except ValueError:
        return None
    if candidate == sandbox:
        # The sandbox root itself is a directory, not a target file.
        return None
    return candidate


def _unified_diff(
    before: str,
    after: str,
    relpath: str,
) -> str:
    """Return a unified diff string for ``relpath`` (no trailing newline)."""
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{relpath}",
            tofile=f"b/{relpath}",
            n=3,
        )
    )


def file_rewrite(
    repo_root: Path,
    path: str,
    operation: str,
    content: str,
) -> dict[str, Any] | str:
    """Apply a structured edit to a sandboxed file and return the diff.

    Path is sandbox-relative (NOT repo-relative): ``"notes.md"`` maps to
    ``tool-use-agent/sandbox/notes.md``. Anything that resolves outside
    the sandbox root is refused — both ``..`` traversal and symlinks
    pointing outside.

    On success returns::

        {
            "path": str,            # sandbox-relative path
            "operation": str,       # echoed
            "bytes_before": int,    # file size before edit (utf-8 bytes)
            "bytes_after": int,     # file size after edit (utf-8 bytes)
            "diff": str,            # unified diff, empty if no change
        }

    On failure returns a sentinel ``"ERROR: ..."`` string matching the
    recovery contract of ``tools_repo.read_repo_file`` /
    ``tools_sql.sql_query``.
    """
    if not isinstance(path, str) or not path.strip():
        return "ERROR: empty path"
    if operation not in OPERATIONS:
        return (
            f"ERROR: unknown operation {operation!r} "
            f"(expected one of {sorted(OPERATIONS)})"
        )
    if not isinstance(content, str):
        return "ERROR: content must be a string"
    if len(content.encode("utf-8")) > MAX_CONTENT_BYTES:
        return (
            f"ERROR: content exceeds {MAX_CONTENT_BYTES}-byte cap "
            f"({len(content.encode('utf-8'))} bytes given)"
        )

    resolved = _resolve_inside_sandbox(repo_root, path)
    if resolved is None:
        return f"ERROR: path {path!r} escapes the sandbox root"
    if not resolved.exists():
        return f"ERROR: no such file in sandbox: {path!r}"
    if not resolved.is_file():
        return f"ERROR: not a regular file: {path!r}"

    try:
        before = resolved.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"ERROR: cannot decode {path!r} as UTF-8 text"

    if operation == "replace":
        after = content
    elif operation == "append":
        after = before + content
    else:  # prepend
        after = content + before

    after_bytes = len(after.encode("utf-8"))
    if after_bytes > MAX_FILE_BYTES:
        return (
            f"ERROR: post-edit file size {after_bytes} exceeds "
            f"{MAX_FILE_BYTES}-byte cap"
        )

    resolved.write_text(after, encoding="utf-8")

    return {
        "path": path,
        "operation": operation,
        "bytes_before": len(before.encode("utf-8")),
        "bytes_after": after_bytes,
        "diff": _unified_diff(before, after, path),
    }


__all__ = [
    "MAX_CONTENT_BYTES",
    "MAX_FILE_BYTES",
    "OPERATIONS",
    "SANDBOX_RELDIR",
    "file_rewrite",
]

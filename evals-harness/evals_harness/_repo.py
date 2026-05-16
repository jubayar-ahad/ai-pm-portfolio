"""Repo-root discovery + sibling-build import-path setup.

The harness lives at ``<repo>/evals-harness/evals_harness/`` and needs to
import the two prior builds' ``verify`` and ``trace`` modules to run the
startup invariants (see ``invariants.py``). Those builds are sibling
top-level directories (``<repo>/rag-app/rag_app/...`` and
``<repo>/tool-use-agent/tool_use_agent/...``) — not installed packages,
so the harness adds each build's directory to ``sys.path`` at import
time.

This is the harness's job, not the builds'. Per the iteration-14 lock,
each build remains self-contained and does not import its sibling; the
harness is the third party that imports both and asserts they agree.
"""

from __future__ import annotations

import sys
from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    """Walk up from ``start`` until ``OBJECTIVE.md`` is found.

    Mirrors the rag-app loader's repo-root detection so the harness works
    regardless of the user's cwd.
    """
    cur = (start or Path(__file__)).resolve()
    for parent in [cur, *cur.parents]:
        if (parent / "OBJECTIVE.md").is_file():
            return parent
    raise RuntimeError(
        "evals-harness could not locate the repo root (no OBJECTIVE.md "
        "found while walking up from %s)" % cur
    )


def ensure_build_imports_on_path(repo_root: Path | None = None) -> Path:
    """Prepend ``rag-app/`` and ``tool-use-agent/`` to ``sys.path``.

    Idempotent: re-running does not duplicate entries. Returns the repo
    root for callers that want to use it directly.
    """
    root = repo_root or find_repo_root()
    for sub in ("rag-app", "tool-use-agent"):
        p = str(root / sub)
        if p not in sys.path:
            sys.path.insert(0, p)
    return root

# `tool-use-agent/sandbox/`

Writable scratch directory used by the `file_rewrite` tool.

The tool refuses any path that does not resolve under this directory —
`..` traversal and symlinks pointing outside both surface as an
out-of-sandbox refusal. Combined with the operation enum
(`replace`/`append`/`prepend`), this gives `file_rewrite` a two-layer
safety guardrail comparable to `sql_query`'s static denylist plus
`mode=ro` URI connection.

## Seed files

Two seed text files ship with the build so a freshly-cloned checkout has
something for `file_rewrite` to edit without first running a setup
script:

- `notes.md` — a short note buffer with three placeholder bullets the
  agent can append/prepend/replace against.
- `todos.md` — a short todo list with three placeholder tasks the agent
  can rewrite in similar ways.

These files are intentionally simple and uninformative — they exist to
make the rewrite demo executable, not to convey any project content.

## Why build-root, not `tests/fixtures/`

NEXT_WORK item 6 sub-checkbox 2 specifies `tool-use-agent/sandbox/`
literally — the sandbox is for the tool's *users* (the agent, the CLI,
the demo invocation), not just for the pytest suite. The package's
`pyproject.toml` excludes `tests/` from the built wheel; the
build-root `sandbox/` directory is where data the package's runtime
demos depend on belongs. This mirrors the iteration-65 decision for
`fixtures/sample.db`.

## What the tool will NOT do

- Create new files inside the sandbox. The three operations all require
  the target file to already exist. A future `file_create` tool would
  own that surface; `file_rewrite` only rewrites.
- Touch anything outside this directory. Even a path that *looks*
  sandbox-relative (e.g. `../foo`) is refused after symlink resolution.
- Accept content larger than 1 MB, or produce a file larger than 1 MB
  after the edit. Either cap returns an `ERROR: ...` sentinel rather
  than a partial write.

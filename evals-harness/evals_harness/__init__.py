"""evals-harness — cross-build evaluation for rag-app and tool-use-agent.

The harness performs no LLM calls of its own. It scores trace records the
two LLM builds (``rag-app`` and ``tool-use-agent``) emit via their
``ask --json`` output, against a labeled query set the user maintains in
``evals-harness/queries.jsonl``.

Stdlib-only by design. See ``evals-harness/README.md`` for the per-slice
contract and ``DECISIONS.md`` for the locked schema / CLI shape.
"""

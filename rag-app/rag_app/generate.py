"""Prompt construction and Claude call for the rag-app demo.

The generation slice has two parts that are kept separate on purpose:

1. ``build_prompt`` is pure: given a question and the BM25 top-k chunks, it
   produces the system + user messages that will be sent to the model.
   Pure means it is fully verifiable with ``--dry-run``, no API key needed.

2. ``call_claude`` wraps the Anthropic SDK. It imports the SDK lazily so the
   ``load`` and ``retrieve`` subcommands keep running on a stdlib-only
   install, and so the ``--dry-run`` path on ``ask`` works the same way.

Citation format: ``[<source>#<start>-<end>]`` where the numbers are the
character span the chunker recorded for that chunk. The next iteration
(refusal + citation hardening) will parse this back and verify every
citation resolves to a real chunk; the format is chosen to be regex-clean
and to avoid collision with the ``::`` separator inside chunk IDs.
"""

from __future__ import annotations

from dataclasses import dataclass

from rag_app.retrieve import RetrievedChunk
from rag_app.verify import REFUSAL_SENTENCE

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_MAX_TOKENS = 1024

SYSTEM_PROMPT = f"""\
You are a careful question-answering assistant for the AI PM 90-day project repo.

You answer questions using ONLY the context chunks provided in the user message.

Rules, in order of priority:

1. If the provided context does not contain enough information to answer
   the question, reply exactly with this sentence and nothing else:
   "{REFUSAL_SENTENCE}"

2. Every factual claim in your answer must be followed by a citation in the
   form [<source>#<start>-<end>], where <source> is the chunk's source path
   and <start>-<end> is its character span. Use the exact source and span
   values from the chunk tags. Multiple citations for one claim are fine.

3. Do not use any knowledge from outside the provided context, even if you
   happen to know the answer. If the context contradicts your prior, the
   context wins.

4. Be concise. Prefer short, direct answers over restating the question.
"""


def format_chunk(chunk: RetrievedChunk) -> str:
    start, end = chunk.span
    return (
        f'<chunk source="{chunk.source}" span="{start}-{end}">\n'
        f"{chunk.text}\n"
        f"</chunk>"
    )


@dataclass(frozen=True)
class Prompt:
    system: str
    user: str


def build_prompt(question: str, retrieved: list[RetrievedChunk]) -> Prompt:
    if retrieved:
        context = "\n\n".join(format_chunk(c) for c in retrieved)
    else:
        context = "(no chunks were retrieved)"
    user = (
        f"Question: {question}\n\n"
        f"Context chunks:\n{context}\n\n"
        f"Answer using only the context above. "
        f"Cite each claim with [<source>#<start>-<end>] as instructed."
    )
    return Prompt(system=SYSTEM_PROMPT, user=user)


@dataclass(frozen=True)
class Answer:
    text: str
    model: str
    input_tokens: int
    output_tokens: int


def call_claude(
    prompt: Prompt,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> Answer:
    """Send the prompt to the Anthropic Messages API and return the answer.

    Imports the SDK lazily so the dry-run path (and the load/retrieve
    subcommands) keep working when ``anthropic`` is not installed.
    """
    try:
        from anthropic import Anthropic
    except ImportError as exc:  # pragma: no cover - install-time error
        raise RuntimeError(
            "The 'anthropic' package is required for live generation. "
            "Install it with `pip install -r rag-app/requirements.txt`, "
            "or re-run with --dry-run to inspect the prompt without "
            "calling the model."
        ) from exc

    client = Anthropic()
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=prompt.system,
        messages=[{"role": "user", "content": prompt.user}],
    )
    text_parts: list[str] = []
    for block in message.content:
        block_text = getattr(block, "text", None)
        if block_text:
            text_parts.append(block_text)
    return Answer(
        text="".join(text_parts),
        model=message.model,
        input_tokens=message.usage.input_tokens,
        output_tokens=message.usage.output_tokens,
    )

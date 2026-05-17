"""Tests for tool_use_agent.trace: schema_version + fingerprint + record_id."""

from __future__ import annotations

import re

from tool_use_agent.catalog import catalog_as_anthropic_tools
from tool_use_agent.trace import (
    SCHEMA_VERSION,
    catalog_canonical_bytes,
    compute_corpus_fingerprint,
    compute_record_id,
    now_iso,
)


def test_schema_version_is_locked():
    assert SCHEMA_VERSION == "tool-use-agent.ask.v1"


def test_catalog_canonical_bytes_is_deterministic():
    catalog = catalog_as_anthropic_tools()
    a = catalog_canonical_bytes(catalog)
    b = catalog_canonical_bytes(catalog)
    assert a == b
    assert isinstance(a, bytes)


def test_catalog_canonical_bytes_sorts_keys():
    # Same data with different key insertion order → same canonical bytes.
    payload_a = [{"name": "t", "description": "d", "input_schema": {"type": "object"}}]
    payload_b = [{"input_schema": {"type": "object"}, "description": "d", "name": "t"}]
    assert catalog_canonical_bytes(payload_a) == catalog_canonical_bytes(payload_b)


def test_compute_corpus_fingerprint_is_16_hex_chars():
    fp = compute_corpus_fingerprint(catalog_as_anthropic_tools())
    assert re.fullmatch(r"[0-9a-f]{16}", fp), fp


def test_compute_corpus_fingerprint_is_deterministic():
    catalog = catalog_as_anthropic_tools()
    assert compute_corpus_fingerprint(catalog) == compute_corpus_fingerprint(catalog)


def test_compute_corpus_fingerprint_changes_with_catalog():
    catalog = catalog_as_anthropic_tools()
    fp_original = compute_corpus_fingerprint(catalog)
    perturbed = catalog + [
        {"name": "extra", "description": "x", "input_schema": {"type": "object"}}
    ]
    fp_changed = compute_corpus_fingerprint(perturbed)
    assert fp_original != fp_changed


def test_compute_record_id_is_16_hex_chars():
    rid = compute_record_id(
        question="q", model="m", max_steps=4, mode="dry-run",
        corpus_fingerprint="0123456789abcdef",
    )
    assert re.fullmatch(r"[0-9a-f]{16}", rid), rid


def test_compute_record_id_is_deterministic():
    args = dict(
        question="q", model="m", max_steps=4, mode="dry-run",
        corpus_fingerprint="0123456789abcdef",
    )
    assert compute_record_id(**args) == compute_record_id(**args)


def test_compute_record_id_changes_with_inputs():
    base = dict(
        question="q", model="m", max_steps=4, mode="dry-run",
        corpus_fingerprint="0123456789abcdef",
    )
    base_id = compute_record_id(**base)
    assert compute_record_id(**{**base, "question": "q2"}) != base_id
    assert compute_record_id(**{**base, "model": "m2"}) != base_id
    assert compute_record_id(**{**base, "max_steps": 5}) != base_id
    assert compute_record_id(**{**base, "mode": "live"}) != base_id
    assert compute_record_id(
        **{**base, "corpus_fingerprint": "fedcba9876543210"}
    ) != base_id


def test_now_iso_format():
    s = now_iso()
    # YYYY-MM-DDTHH:MM:SSZ — second precision, Z suffix, no microseconds.
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", s), s

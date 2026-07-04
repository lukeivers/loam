# Copyright 2026 Luke Ivers and contributors
# SPDX-License-Identifier: Apache-2.0
"""AC.AR.9 (P6) — the corpus is checked before any pull; a kept doc is indexed
with citations and reused by a later same-domain review; the two seed docs are
present; an uncited pull is refused (claim-or-cite)."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from adversarial_review.corpus import CorpusStore

_SHIPPED_CORPUS = Path(__file__).resolve().parents[1] / "corpus"


def test_AC_AR_9_shipped_corpus_has_the_two_seed_docs():
    store = CorpusStore(root=_SHIPPED_CORPUS)
    text = store.domain_agnostic_methodology()
    # Both seed docs present + concatenated.
    assert "Adversarial review — how the discipline works" in text
    assert "AI as the adversarial critic" in text


def test_AC_AR_9_resolve_returns_none_for_uncovered_domain(tmp_path):
    # Fresh corpus with only the index -> uncovered domain -> None (the
    # signal to pull). This is the CHECK-BEFORE-PULL contract.
    shutil.copytree(_SHIPPED_CORPUS, tmp_path / "corpus")
    store = CorpusStore(root=tmp_path / "corpus")
    assert store.resolve("statistical-white-paper") is None


def test_AC_AR_9_kept_doc_is_indexed_and_reused(tmp_path):
    shutil.copytree(_SHIPPED_CORPUS, tmp_path / "corpus")
    store = CorpusStore(root=tmp_path / "corpus")
    # KEEP a pulled doc with real citations.
    store.record_pull(
        "statistical-white-paper",
        text="Failure taxonomy for statistical white papers: p-hacking, ...",
        citations=["Ioannidis 2005 PLoS Med, Why Most Published Findings Are False"],
    )
    # A LATER review in the same domain REUSES it (no re-pull).
    reused = CorpusStore(root=tmp_path / "corpus").resolve("statistical-white-paper")
    assert reused is not None
    assert "p-hacking" in reused.text
    assert reused.citations and "Ioannidis" in reused.citations[0]


def test_AC_AR_9_uncited_pull_is_refused(tmp_path):
    shutil.copytree(_SHIPPED_CORPUS, tmp_path / "corpus")
    store = CorpusStore(root=tmp_path / "corpus")
    with pytest.raises(ValueError):
        store.record_pull("legal-contract", text="some taxonomy", citations=[])

"""D9 — upgrade-fidelity harness tests."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import upgrade


class _FakeEdge:
    """Duck-typed stand-in for graphiti EntityEdge."""

    def __init__(self, fact: str) -> None:
        self.fact = fact
        self.uuid = "u-" + fact[:8]
        self.source_node_uuid = "s-" + fact[:8]
        self.target_node_uuid = "t-" + fact[:8]
        self.valid_at = None
        self.invalid_at = None


def test_score_one_probe_hits_expected_facts() -> None:
    question = {
        "id": "q01",
        "mode": "semantic",
        "question": "Who is the CEO of Halcyon?",
        "expected_facts": ["tobi imari", "halcyon"],
    }
    hits = [
        _FakeEdge("Tobi Imari is the CEO of Halcyon Cartography"),
        _FakeEdge("Halcyon Cartography is based in Bristol"),
    ]
    result = upgrade.score_one_probe(question, hits)
    assert result.passed is True
    assert result.recall == 1.0


def test_score_one_probe_detects_negative_fact() -> None:
    question = {
        "id": "q99",
        "mode": "context_aware",
        "question": "delivered closing report",
        "expected_facts_any": ["cinnabar"],
        "negative_facts": ["halcyon"],
    }
    hits = [
        _FakeEdge("Tomek Vrbas delivered the Halcyon closing report"),  # BAD — negative
        _FakeEdge("Tomek Vrbas delivered Cinnabar closing report"),
    ]
    result = upgrade.score_one_probe(question, hits)
    # Negative fact appears in top-5; that fails the question.
    assert result.passed is False
    assert "halcyon" in result.negative_hits


def test_compare_identical_results_pass() -> None:
    q = {
        "id": "q01",
        "mode": "semantic",
        "question": "test",
        "expected_facts": ["a"],
    }
    hits = [_FakeEdge("fact containing a")]
    pre = [upgrade.score_one_probe(q, hits)]
    post = [upgrade.score_one_probe(q, hits)]
    report = upgrade.compare(pre, post)
    assert report.passed is True
    assert report.verdict_flip_fraction == 0.0


def test_compare_drift_over_threshold_fails() -> None:
    q = {
        "id": "q01",
        "mode": "semantic",
        "question": "test",
        "expected_facts": ["expected-token-42"],
    }
    pre = [upgrade.score_one_probe(q, [_FakeEdge("contains expected-token-42 explicitly")])]
    post = [upgrade.score_one_probe(q, [_FakeEdge("totally unrelated signal")])]
    report = upgrade.compare(pre, post, thresholds={"max_drift_fraction": 0.0, "per_query_recall_tolerance": 0.0})
    assert report.passed is False
    assert report.verdict_flip_fraction == 1.0


def test_snapshot_copies_db_files(tmp_path) -> None:
    fake_db = tmp_path / "kuzu_db"
    fake_db.write_bytes(b"fake kuzu file")
    (tmp_path / "kuzu_db.wal").write_bytes(b"fake wal")

    out_dir = tmp_path / "snaps"
    snap = upgrade.snapshot(str(fake_db), out_dir=out_dir, tag="test")

    files = {p.name for p in snap.iterdir()}
    assert "kuzu_db" in files
    assert "kuzu_db.wal" in files


def test_restore_round_trip(tmp_path) -> None:
    fake_db = tmp_path / "kuzu_db"
    fake_db.write_bytes(b"original")
    (tmp_path / "kuzu_db.wal").write_bytes(b"wal-orig")

    snap = upgrade.snapshot(str(fake_db), out_dir=tmp_path / "snaps", tag="pre")

    # Mutate current state.
    fake_db.write_bytes(b"mutated")
    (tmp_path / "kuzu_db.wal").write_bytes(b"wal-mutated")

    upgrade.restore(snap, str(fake_db))
    assert fake_db.read_bytes() == b"original"
    assert (tmp_path / "kuzu_db.wal").read_bytes() == b"wal-orig"

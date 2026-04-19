"""D6 — post-upgrade clause verification tests."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import pytest

from self_upgrade.clause_checks import (
    ClauseResult,
    check_clause_a,
    check_clause_b,
    check_clause_c,
    check_clause_d,
    check_clause_e,
    check_clause_f,
    check_clause_g,
    run_all_clauses,
)
from self_upgrade.manifest import Manifest
from self_upgrade.paths import Paths


# ---- clause (a) -----------------------------------------------------


def test_clause_a_pass_on_rpc_success() -> None:
    r = check_clause_a(no_op_rpc=lambda: True)
    assert r.passed and r.clause == "a"


def test_clause_a_fail_on_rpc_false() -> None:
    r = check_clause_a(no_op_rpc=lambda: False)
    assert not r.passed
    assert "returned False" in r.reason


def test_clause_a_fail_on_rpc_raise() -> None:
    def boom() -> bool:
        raise ConnectionRefusedError("socket rebinding")

    r = check_clause_a(no_op_rpc=boom)
    assert not r.passed
    assert "ConnectionRefusedError" in r.reason


# ---- clause (b) -----------------------------------------------------


def _good_survival_payload() -> dict:
    return {
        "persona_identity": {"handle": "eve", "given_name": "Eve"},
        "authority_boundary": {"tier_a": "require", "tier_b": "require",
                               "tier_c": "execute", "tier_d": "execute"},
        "current_scope_context": [],
        "pending_decisions": [],
        "recent_corrections": [],
    }


def test_clause_b_pass_all_personas_populated() -> None:
    r = check_clause_b({"eve": _good_survival_payload()})
    assert r.passed


def test_clause_b_fail_missing_persona() -> None:
    r = check_clause_b({})
    assert not r.passed
    assert "no personas" in r.reason


def test_clause_b_fail_unpopulated_field() -> None:
    bad = _good_survival_payload()
    bad["authority_boundary"] = None
    r = check_clause_b({"eve": bad})
    assert not r.passed
    assert "eve" in str(r.details)


# ---- clause (c) -----------------------------------------------------


@dataclass
class _FakeDrift:
    passed: bool
    verdict_flip_fraction: float = 0.0
    mean_recall_delta: float = 0.0
    over_tolerance_fraction: float = 0.0


def test_clause_c_pass() -> None:
    r = check_clause_c(_FakeDrift(passed=True))
    assert r.passed


def test_clause_c_fail() -> None:
    r = check_clause_c(_FakeDrift(passed=False, over_tolerance_fraction=0.4))
    assert not r.passed
    assert "drift" in r.reason.lower()


# ---- clause (d) -----------------------------------------------------


@dataclass
class _FakeScopeDrift:
    total_drift: int


def test_clause_d_pass_zero_drift() -> None:
    r = check_clause_d(_FakeScopeDrift(0), _FakeScopeDrift(0))
    assert r.passed


def test_clause_d_fail_scope_drift() -> None:
    r = check_clause_d(_FakeScopeDrift(2), _FakeScopeDrift(0))
    assert not r.passed
    assert "scope_of_work=2" in r.reason


def test_clause_d_fail_objective_drift() -> None:
    r = check_clause_d(_FakeScopeDrift(0), _FakeScopeDrift(3))
    assert not r.passed
    assert "objective_tracker=3" in r.reason


# ---- clause (e) -----------------------------------------------------


def test_clause_e_pass_no_schema_bumps(sample_manifest_dict: dict) -> None:
    m = Manifest.model_validate(sample_manifest_dict)
    assert check_clause_e(m).passed


def test_clause_e_fail_silent_bump(sample_manifest_dict: dict) -> None:
    sample_manifest_dict["component_schemas"][0]["version_post"] = 4
    m = Manifest.model_validate(sample_manifest_dict)
    r = check_clause_e(m)
    assert not r.passed
    assert "memory" in str(r.details)


def test_clause_e_pass_declared_bump(sample_manifest_dict: dict) -> None:
    sample_manifest_dict["component_schemas"][0]["version_post"] = 4
    sample_manifest_dict["breaking_changes"] = [
        {
            "id": "mem-v4",
            "component": "memory",
            "description": "node identity normalisation",
            "migration_path": "framework/memory_system/migrations/v3_to_v4.py",
        }
    ]
    m = Manifest.model_validate(sample_manifest_dict)
    assert check_clause_e(m).passed


# ---- clause (f) -----------------------------------------------------


def test_clause_f_pass_with_snapshot(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("POS_BASE_DIR", str(tmp_path))
    p = Paths.from_env()
    tag = "pos-v2-v0.2.0"
    p.ensure_history(tag)
    for comp in ("memory", "orchestrator"):
        d = p.history_dir_pre(tag) / comp
        d.mkdir(parents=True, exist_ok=True)
        (d / "file.sqlite").write_bytes(b"snapshot")
    r = check_clause_f(
        p, tag, required_components=("memory", "orchestrator")
    )
    assert r.passed


def test_clause_f_fail_missing_snapshot(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("POS_BASE_DIR", str(tmp_path))
    p = Paths.from_env()
    tag = "pos-v2-v0.2.0"
    p.ensure_history(tag)
    # memory snapshot present, orchestrator missing
    (p.history_dir_pre(tag) / "memory").mkdir(parents=True)
    (p.history_dir_pre(tag) / "memory" / "f").write_bytes(b"x")
    r = check_clause_f(
        p, tag, required_components=("memory", "orchestrator")
    )
    assert not r.passed
    assert "orchestrator" in r.reason


def test_clause_f_fail_no_snapshot_dir(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("POS_BASE_DIR", str(tmp_path))
    p = Paths.from_env()
    r = check_clause_f(p, "pos-v2-v0.2.0", required_components=("memory",))
    assert not r.passed


# ---- clause (g) -----------------------------------------------------


def test_clause_g_pass_when_shas_match(tmp_path: Path) -> None:
    root = tmp_path / "live"
    content = b"print('hello')\n"
    sha = hashlib.sha256(content).hexdigest()
    (root / "framework" / "new.py").parent.mkdir(parents=True)
    (root / "framework" / "new.py").write_bytes(content)

    m = Manifest.model_validate(
        {
            "release_tag": "pos-v2-v0.2.0",
            "commit_sha": "abcdef1",
            "files": [
                {
                    "path": "framework/new.py",
                    "expected_pre_sha": None,
                    "expected_post_sha": sha,
                    "change_kind": "new",
                }
            ],
        }
    )
    r = check_clause_g(m, root)
    assert r.passed


def test_clause_g_fail_on_sha_mismatch(tmp_path: Path) -> None:
    root = tmp_path / "live"
    (root / "framework").mkdir(parents=True)
    (root / "framework" / "new.py").write_bytes(b"different")

    m = Manifest.model_validate(
        {
            "release_tag": "pos-v2-v0.2.0",
            "commit_sha": "abcdef1",
            "files": [
                {
                    "path": "framework/new.py",
                    "expected_pre_sha": None,
                    "expected_post_sha": "a" * 64,
                    "change_kind": "new",
                }
            ],
        }
    )
    r = check_clause_g(m, root)
    assert not r.passed
    assert r.details["mismatches"]
    assert r.details["mismatches"][0]["path"] == "framework/new.py"


def test_clause_g_fail_on_missing_file(tmp_path: Path) -> None:
    root = tmp_path / "live"
    root.mkdir()
    m = Manifest.model_validate(
        {
            "release_tag": "pos-v2-v0.2.0",
            "commit_sha": "abcdef1",
            "files": [
                {
                    "path": "framework/missing.py",
                    "expected_pre_sha": None,
                    "expected_post_sha": "a" * 64,
                    "change_kind": "new",
                }
            ],
        }
    )
    r = check_clause_g(m, root)
    assert not r.passed
    assert r.details["missing"] == ["framework/missing.py"]


def test_clause_g_pass_with_deleted_absent(tmp_path: Path) -> None:
    root = tmp_path / "live"
    root.mkdir()
    m = Manifest.model_validate(
        {
            "release_tag": "pos-v2-v0.2.0",
            "commit_sha": "abcdef1",
            "files": [
                {
                    "path": "framework/gone.py",
                    "expected_pre_sha": "a" * 64,
                    "expected_post_sha": None,
                    "change_kind": "deleted",
                }
            ],
        }
    )
    r = check_clause_g(m, root)
    assert r.passed


# ---- full bundle ----------------------------------------------------


def test_run_all_clauses_happy_path(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("POS_BASE_DIR", str(tmp_path))
    p = Paths.from_env()
    tag = "pos-v2-v0.2.0"
    p.ensure_history(tag)
    for comp in ("memory",):
        d = p.history_dir_pre(tag) / comp
        d.mkdir(parents=True)
        (d / "f").write_bytes(b"x")

    content = b"ok\n"
    sha = hashlib.sha256(content).hexdigest()
    live = tmp_path / "live"
    (live / "framework").mkdir(parents=True)
    (live / "framework" / "a.py").write_bytes(content)

    m = Manifest.model_validate(
        {
            "release_tag": "pos-v2-v0.2.0",
            "commit_sha": "abcdef1",
            "files": [
                {
                    "path": "framework/a.py",
                    "expected_pre_sha": None,
                    "expected_post_sha": sha,
                    "change_kind": "new",
                }
            ],
        }
    )

    bundle = run_all_clauses(
        no_op_rpc=lambda: True,
        survival_payloads={"eve": _good_survival_payload()},
        memory_drift_report=_FakeDrift(passed=True),
        scope_drift=_FakeScopeDrift(0),
        objective_drift=_FakeScopeDrift(0),
        manifest=m,
        paths=p,
        tag=tag,
        live_root=live,
        snapshot_components=("memory",),
    )
    assert bundle.all_passed, bundle.failing()
    assert set(bundle.results.keys()) == {"a", "b", "c", "d", "e", "f", "g"}


def test_run_all_clauses_evaluates_every_clause_even_on_early_failure(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("POS_BASE_DIR", str(tmp_path))
    p = Paths.from_env()
    live = tmp_path / "live"
    live.mkdir()

    m = Manifest.model_validate(
        {
            "release_tag": "pos-v2-v0.2.0",
            "commit_sha": "abcdef1",
        }
    )
    bundle = run_all_clauses(
        no_op_rpc=lambda: False,  # clause a fails
        survival_payloads={},  # clause b fails
        memory_drift_report=_FakeDrift(passed=False),  # c fails
        scope_drift=_FakeScopeDrift(5),  # d fails
        objective_drift=_FakeScopeDrift(0),
        manifest=m,
        paths=p,
        tag="pos-v2-v0.2.0",  # f fails (no snapshot)
        live_root=live,
        snapshot_components=("memory",),
    )
    assert set(bundle.results.keys()) == {"a", "b", "c", "d", "e", "f", "g"}
    assert set(bundle.failing()) >= {"a", "b", "c", "d", "f"}

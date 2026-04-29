"""AC.WS.2, AC.WS.10 — sync-protected envelope tests."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam.workspace_sync.sync_protected import (
    FRAMEWORK_FLOOR,
    FileClass,
    SyncProtected,
    SyncProtectedRule,
    classify,
    default_sync_protected,
    load_sync_protected,
    save_sync_protected,
    write_default_if_absent,
)


def test_class_a_paths_classify_as_a() -> None:
    sp = default_sync_protected()
    assert sp.classify("workspace/personas/luke/contract.yaml") is FileClass.A
    assert sp.classify("workspace/.pos/objective_tracker.sqlite") is FileClass.A
    assert sp.classify("workspace/.pos/state.yaml") is FileClass.A
    assert sp.classify("workspace/.scratch/tmp.txt") is FileClass.A
    assert sp.classify("workspace/.mcp.json") is FileClass.A


def test_class_b_memory_yaml_classifies_as_b() -> None:
    sp = default_sync_protected()
    assert sp.classify("workspace/memory.yaml") is FileClass.B


def test_class_c_default_for_unmatched() -> None:
    sp = default_sync_protected()
    # Framework code path; default unmatched goes to C.
    assert sp.classify("self-upgrade/src/foo.py") is FileClass.C
    assert sp.classify("orchestrator/src/bar.py") is FileClass.C


def test_framework_floor_refusal_on_removal() -> None:
    """A workspace cannot opt out of the framework floor (AC.WS.10)."""
    incomplete_floor = [
        SyncProtectedRule(pattern=p, klass=k)
        for p, k in FRAMEWORK_FLOOR
        if p != "workspace/.pos/**"  # remove a floor entry
    ]
    with pytest.raises(ValueError):
        SyncProtected(framework_floor=incomplete_floor, workspace_rules=[])


def test_write_default_if_absent_idempotent(tmp_path: Path) -> None:
    """First-call writes; subsequent calls do not overwrite."""
    target = write_default_if_absent(tmp_path)
    assert target == tmp_path / "workspace" / ".pos" / "sync-protected.yaml"
    assert target.exists()

    # Hand-edit a workspace_rule then call again.
    raw = yaml.safe_load(target.read_text())
    raw["workspace_rules"].append({"pattern": "secret/**", "klass": "A"})
    target.write_text(yaml.safe_dump(raw, sort_keys=False))

    write_default_if_absent(tmp_path)
    raw_after = yaml.safe_load(target.read_text())
    assert any(
        r["pattern"] == "secret/**" for r in raw_after["workspace_rules"]
    ), "second call must not clobber operator-edited workspace_rules"


def test_workspace_rules_first_match_wins() -> None:
    """An operator can tighten Class-A coverage via workspace_rules."""
    sp = SyncProtected(
        framework_floor=[
            SyncProtectedRule(pattern=p, klass=k)
            for p, k in FRAMEWORK_FLOOR
        ],
        workspace_rules=[
            SyncProtectedRule(pattern="custom/**", klass=FileClass.A),
        ],
    )
    assert sp.classify("custom/secret.txt") is FileClass.A


def test_classify_module_level_wrapper() -> None:
    sp = default_sync_protected()
    # D-migration D.2 (amendment #63): post-D.2 the framework-floor
    # patterns prefix every workspace-state path with ``workspace/``.
    assert classify("workspace/memory.yaml", sp) is FileClass.B

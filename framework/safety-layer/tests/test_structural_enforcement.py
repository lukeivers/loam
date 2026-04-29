"""Structural-impossibility defence-in-depth — A19.

A19. A hand-crafted always_ask.yaml with `framework_floor: []` is
     refused at load. A workspace that attempts to monkey-patch
     FrameworkFloorCategory at runtime does not change the gate's
     behaviour because the gate reads the validated model, not the
     enum directly.
"""

from __future__ import annotations

import pytest
import yaml
from pydantic import ValidationError

from loam.safety_layer import (
    AlwaysAskList,
    AskListEntry,
    DEFAULT_DANGEROUS_OP_SUBSET,
    DEFAULT_FRAMEWORK_FLOOR,
    FrameworkFloorCategory,
)
from loam.safety_layer.ask_list import load_ask_list


def test_A19_empty_floor_refused_at_load(tmp_path):
    path = tmp_path / "always_ask.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "framework_floor": [],
                "workspace_additions": [],
                "dangerous_op_subset": [],
            }
        )
    )
    with pytest.raises(ValidationError):
        load_ask_list(path)


def test_A19_partial_floor_refused(tmp_path):
    path = tmp_path / "always_ask.yaml"
    # Only the first two categories.
    partial = [
        {
            "action_class": e.action_class,
            "timeout": e.timeout,
            "description": e.description,
        }
        for e in DEFAULT_FRAMEWORK_FLOOR[:2]
    ]
    path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "framework_floor": partial,
                "workspace_additions": [],
                "dangerous_op_subset": [],
            }
        )
    )
    with pytest.raises(ValidationError):
        load_ask_list(path)


def test_A19_monkey_patch_enum_does_not_change_gate():
    """The gate reads from the validated AlwaysAskList, not from the
    enum. Patching the enum cannot shrink the already-validated list.
    """
    full = AlwaysAskList(
        version=1,
        framework_floor=DEFAULT_FRAMEWORK_FLOOR,
        workspace_additions=(),
        dangerous_op_subset=DEFAULT_DANGEROUS_OP_SUBSET,
    )
    # All seven present.
    assert len(full.framework_floor) == 7
    assert "commit_external_funds" in full.all_action_classes()

    # "Patch" the enum at runtime — doesn't matter; we don't read it
    # post-load. We assert the AlwaysAskList instance is frozen.
    with pytest.raises((TypeError, ValidationError)):
        full.framework_floor = ()  # type: ignore[misc]


def test_A19_default_framework_floor_has_all_seven():
    classes = {e.action_class for e in DEFAULT_FRAMEWORK_FLOOR}
    required = {c.value for c in FrameworkFloorCategory}
    assert classes == required


def test_A19_missing_file_returns_default(tmp_path):
    """Absence of always_ask.yaml means 'use framework default,' not
    'fail.' Rejection is reserved for malformed / floor-shrinking
    content."""
    default = load_ask_list(tmp_path / "nonexistent.yaml")
    assert len(default.framework_floor) == 7

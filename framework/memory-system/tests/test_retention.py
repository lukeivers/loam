"""D10 — retention-class tagger tests."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import retention


def test_default_class_is_normal() -> None:
    assert retention.default_class() == retention.RetentionClass.NORMAL


def test_resolve_known_strings() -> None:
    assert retention.resolve("normal").cls == retention.RetentionClass.NORMAL
    assert retention.resolve("derived-only").cls == retention.RetentionClass.DERIVED_ONLY
    assert retention.resolve("ephemeral").cls == retention.RetentionClass.EPHEMERAL


def test_resolve_unknown_falls_back_to_default() -> None:
    plan = retention.resolve("purple")
    assert plan.cls == retention.RetentionClass.NORMAL


def test_persists_and_persists_raw_flags() -> None:
    normal = retention.resolve("normal")
    derived = retention.resolve("derived-only")
    ephem = retention.resolve("ephemeral")

    assert normal.persists is True
    assert normal.persists_raw_text is True

    assert derived.persists is True
    assert derived.persists_raw_text is False

    assert ephem.persists is False
    assert ephem.persists_raw_text is False

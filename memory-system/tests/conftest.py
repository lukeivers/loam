"""Pytest-wide configuration for the memory-system test suite.

Landed by amendment #16 (d12-chaos-durability-split-pytest) to register
the ``slow`` marker used by the D12 chaos-durability full-runner test.
A plain ``@pytest.mark.slow`` without registration produces
``PytestUnknownMarkWarning`` and future pytest versions may treat
unknown markers as errors; registering here is the narrowest-scope fix
(this component has no ``pyproject.toml``, no ``pytest.ini``, no
pre-existing marker convention).

Cadence for ``-m slow`` tests is documented in
``docs/rebuild/plans/d12-chaos-durability-split-pytest.md`` §6: run
manually before any pos-v2 release cut, and on any PR whose diff
touches ``memory-system/src/factory.py``,
``memory-system/src/retention.py``, or kuzu-adjacent surfaces in
``memory-system/src/``.

Runbook: ``cd memory-system && .venv/bin/pytest -m slow -v``.
"""

from __future__ import annotations

import pytest


def pytest_configure(config):
    """Register custom markers so ``pytest -m slow`` is a first-class
    selector and ``@pytest.mark.slow`` does not emit a warning.
    """
    config.addinivalue_line(
        "markers",
        "slow: tests that take seconds-to-minutes to run; excluded from "
        "the default run and invoked explicitly via ``pytest -m slow``.",
    )


def pytest_collection_modifyitems(config, items):
    """Skip ``@pytest.mark.slow`` tests unless ``-m slow`` (or a marker
    expression that admits ``slow``) is passed.

    The brief-full-build contract for D12 requires the slow bucket to
    be "skipped by default; runs only under ``pytest -m slow``"; this
    hook enforces that without requiring callers to remember
    ``-m "not slow"`` on every default-run invocation.
    """
    markexpr = config.getoption("-m", default="") or ""
    # If the user explicitly selected a marker expression, respect it
    # entirely (don't second-guess). Only auto-skip when no marker
    # expression is in play.
    if markexpr.strip():
        return
    skip_slow = pytest.mark.skip(reason="slow test; invoke with ``pytest -m slow``")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)

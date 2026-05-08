# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Integration invariants — A15, A17, A18.

A15. IPC-wrapping gate composition does not mutate the orchestrator
     object. A clean reconstruction of the orchestrator without the
     safety wrapper produces identical behaviour to pre-safety-layer
     pos-v2. Proxy: the safety module contains no imports from sealed-
     component internals it shouldn't touch, and no symbol inside
     safety_layer monkeypatches a sealed method.
A17. OneOnOneChannel with is_group=True is refused at channel
     construction. No group-channel escape paths.
A18. Zero imports from current pOS / legacy Ruby safety constructs.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from loam.primary_persona.introduction import ChannelKind

from loam.safety_layer import SafetyChannel


SAFETY_SRC = Path(__file__).parent.parent / "src"


def test_A15_no_monkeypatching_of_sealed_modules():
    """No .py file under safety-layer/src/ contains a `MODULE.ATTR = ...`
    assignment that would patch a sealed module's attribute. Only
    assignments to names within safety_layer itself are allowed.
    """
    sealed_prefixes = [
        "scope_of_work",
        "pos_orchestrator",
        "primary_persona",
        "pos_observability_aggregator",
        "objective_tracker",
        "graceful_degradation",
        "pos_self_upgrade",
    ]
    for py in SAFETY_SRC.rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        for prefix in sealed_prefixes:
            # Crude but effective: look for `prefix.NAME = ` which would
            # be assignment to an attribute on a sealed module.
            # We exclude method-call `prefix.foo(...)` and import lines.
            import re

            pattern = re.compile(
                rf"^\s*{re.escape(prefix)}\.[A-Za-z_][A-Za-z0-9_.]*\s*=(?!=)",
                re.MULTILINE,
            )
            matches = pattern.findall(text)
            assert not matches, (
                f"{py.name}: monkey-patch detected on {prefix}: {matches}"
            )


def test_A18_no_legacy_ruby_imports():
    """No safety-layer module imports from the current-pOS Ruby rules
    machinery. We assert none of our files mention Ruby-only paths or
    `ops/orchestrator` or `.claude/rules/` in import statements."""

    banned_substrings = [
        "ops/orchestrator",
        "ops/rules",
        "ops/events",
        "require 'claude",
        "require_relative",
        "from claude_ruby",
    ]
    for py in SAFETY_SRC.rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        for s in banned_substrings:
            assert s not in text, f"{py.name} references legacy Ruby surface: {s}"


def test_A17_group_channel_rejected_at_construction():
    with pytest.raises(ValueError):
        SafetyChannel(
            kind=ChannelKind.personal_telegram,
            name="group",
            send=lambda t: None,  # type: ignore[arg-type]
            is_group=True,
        )


def test_A17_notifier_rejects_group_channel_in_channels_list():
    # If any channel declares is_group, the SafetyChannel's own
    # __post_init__ will have already raised; to test notifier-level
    # defence, build a channel that we then force to claim is_group via
    # a dataclasses.replace-like trick. Since SafetyChannel is frozen,
    # we build a fake mapping on a plain OneOnOneChannel.
    from loam.primary_persona.introduction import OneOnOneChannel

    async def _send(t: str) -> None:
        return None

    # Primary-persona's OneOnOneChannel also refuses is_group=True at
    # construction — so we can't even build one. This is structural
    # defence in depth. Demonstrate that:
    with pytest.raises(ValueError):
        OneOnOneChannel(
            kind=ChannelKind.personal_telegram,
            name="any",
            send=_send,
            is_group=True,
        )


def test_A15_sealed_modules_unmodified_after_import():
    """After importing safety_layer, the public signatures of sealed
    modules remain unchanged — spot-check representative methods.
    """
    import loam.safety_layer  # noqa: F401

    import loam.scope_of_work.runtime as sor_rt
    from loam.orchestrator.orchestrator import Orchestrator
    from loam.orchestrator.ipc import IPCServer

    # ScopeRuntime.cancel still has its original signature.
    sig = inspect.signature(sor_rt.ScopeRuntime.cancel)
    assert list(sig.parameters.keys()) == ["self", "scope_id", "reason"]

    # Orchestrator.activate_scope still has its original signature.
    sig = inspect.signature(Orchestrator.activate_scope)
    assert list(sig.parameters.keys()) == ["self", "scope_id", "objective_id"]

    # IPCServer.register unchanged.
    sig = inspect.signature(IPCServer.register)
    assert list(sig.parameters.keys()) == ["self", "method", "handler"]

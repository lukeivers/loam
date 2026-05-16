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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.

"""AC.PROMO.3 — THE DOGFOOD-RECURSION CLOSURE (structural, mandatory).

Plan: docs/plans/telegram-5-fix.md §3.3 / §6.  NON-NEGOTIABLE per the
binding contract — encoded as a dedicated AC, not a method note.

The #5 failure mode WAS: *a harness built to test/re-harden the
Telegram fix spawned un-isolated `claude` and killed Telegram while
purporting to verify Telegram protection.*  The fix's own lead AC
(AC.PROMO.1) MUST itself spawn real `claude` (empirical
poller-survival is the only honest proof).  This AC makes it
STRUCTURALLY IMPOSSIBLE for the fix's own acceptance test to be the
next #5:

  A STATIC / STRUCTURAL check on AC.PROMO.1's OWN test-module source
  asserts (1) it spawns through the shared isolation surface
  (`spawn_isolated_claude` / `inject_isolation` from
  `loam_spawn_isolation`), and (2) it contains NO raw
  `subprocess.<run|Popen|call|...>(["claude", ...])` literal — the
  exact hand-rolled pattern that caused #5.

This is a STATIC source/AST inspection — it does NOT spawn `claude`
and does NOT require the opt-in real-binary env-var, so it goes RED
*before* AC.PROMO.1's real-binary path can ever run.  The recursion
that caused #5 is closed *for the verification of the fix itself*,
not merely for production code.

Note on the sentinel: AC.PROMO.1 holds a poller-slot sentinel with a
plain `subprocess.Popen([sys.executable, "-c", "import time; ..."])`
(NOT a `claude` spawn — it is a Python sleeper modelling the
operator's single-consumer poller, exactly as the sealed
`test_AC_TPI_1_*` does).  The AST check below keys on the *first argv
element resolving to `claude`*, so the sleeper sentinel is correctly
NOT flagged while a hand-rolled `["claude", ...]` IS.
"""

from __future__ import annotations

import ast
from pathlib import Path

_LEAD_AC_TEST = (
    Path(__file__).resolve().parent
    / "test_AC_PROMO_1_harness_multispawn_sentinel_survives.py"
)


def _first_elt_is_claude(node: ast.AST) -> bool:
    """True iff `node` is a list/tuple literal whose first element is
    a string literal resolving (basename) to ``claude``."""
    elts: list[ast.expr] = []
    if isinstance(node, (ast.List, ast.Tuple)):
        elts = list(node.elts)
    if not elts:
        return False
    first = elts[0]
    if isinstance(first, ast.Constant) and isinstance(
        first.value, str
    ):
        return Path(first.value).name == "claude"
    return False


def _raw_claude_spawn_calls(tree: ast.AST) -> list[str]:
    """Find any `subprocess.<run|Popen|call|check_output|check_call>(
    ["claude", ...], ...)` — the hand-rolled #5 pattern — anywhere in
    the lead-AC test's source."""
    offenders: list[str] = []
    spawn_attrs = {
        "run",
        "Popen",
        "call",
        "check_call",
        "check_output",
    }
    for call in ast.walk(tree):
        if not isinstance(call, ast.Call):
            continue
        func = call.func
        # subprocess.run([...]) / subprocess.Popen([...]) / etc.
        if isinstance(func, ast.Attribute) and func.attr in spawn_attrs:
            mod = func.value
            is_subprocess = (
                isinstance(mod, ast.Name) and mod.id == "subprocess"
            )
            if not is_subprocess:
                continue
            if call.args and _first_elt_is_claude(call.args[0]):
                offenders.append(
                    f"line {call.lineno}: subprocess.{func.attr}"
                    f"([\"claude\", ...]) — the hand-rolled #5 "
                    f"pattern"
                )
        # bare run(...) / Popen(...) imported `from subprocess import`
        elif isinstance(func, ast.Name) and func.id in spawn_attrs:
            if call.args and _first_elt_is_claude(call.args[0]):
                offenders.append(
                    f"line {call.lineno}: {func.id}([\"claude\", "
                    f"...]) — the hand-rolled #5 pattern"
                )
    return offenders


def test_AC_PROMO_3_lead_ac_test_exists() -> None:
    """The lead-AC test module must exist for this closure to mean
    anything (a missing target would vacuously pass — guard it)."""
    assert _LEAD_AC_TEST.exists(), (
        f"AC.PROMO.1's test module is missing at {_LEAD_AC_TEST} — "
        f"the dogfood-recursion closure has nothing to protect "
        f"(AC.PROMO.3)."
    )


def test_AC_PROMO_3_lead_ac_test_has_no_raw_claude_spawn() -> None:
    """STRUCTURAL: AC.PROMO.1's own test module contains NO
    hand-rolled `subprocess.<spawn>(["claude", ...])` literal — it is
    structurally impossible for the fix's own acceptance test to be
    the next #5.  Goes RED on a static AST inspection BEFORE the
    real-binary path can run (no opt-in env-var gates this test)."""
    src = _LEAD_AC_TEST.read_text(encoding="utf-8")
    tree = ast.parse(src)
    offenders = _raw_claude_spawn_calls(tree)
    assert offenders == [], (
        "AC.PROMO.1's test hand-rolls a raw claude spawn instead of "
        "routing through the shared isolation surface — this IS the "
        "Telegram-death #5 recursion (a verify harness killing "
        "Telegram while proving Telegram protected). Build the spawn "
        "via loam_spawn_isolation.spawn_isolated_claude / "
        "inject_isolation. Offenders: " + "; ".join(offenders)
    )


def test_AC_PROMO_3_lead_ac_test_routes_through_shared_surface() -> (
    None
):
    """STRUCTURAL: AC.PROMO.1's own test module imports the shared
    isolation surface and constructs its real-`claude` spawns through
    it (positive side of the closure — the absence of a raw spawn is
    necessary but not sufficient; the test must actively use the
    mandated surface)."""
    src = _LEAD_AC_TEST.read_text(encoding="utf-8")
    tree = ast.parse(src)

    imported_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (
            node.module == "loam_spawn_isolation"
        ):
            for alias in node.names:
                imported_names.add(alias.asname or alias.name)

    assert imported_names, (
        "AC.PROMO.1's test does not import from "
        "`loam_spawn_isolation` — its real-`claude` spawns are not "
        "routed through the mandated shared surface (AC.PROMO.3)."
    )
    # At least one mandated spawn entry point must be imported AND
    # called.
    mandated = {"spawn_isolated_claude", "inject_isolation"}
    assert imported_names & mandated, (
        f"AC.PROMO.1's test imports {sorted(imported_names)} from "
        f"loam_spawn_isolation but none of the mandated spawn entry "
        f"points {sorted(mandated)} — it must spawn THROUGH the "
        f"surface, not merely reference it (AC.PROMO.3)."
    )
    called = {
        n.func.id
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id in mandated
    }
    assert called & mandated, (
        f"AC.PROMO.1's test imports a mandated spawn entry point but "
        f"never CALLS it — the real-`claude` spawn is not actually "
        f"routed through the shared surface (AC.PROMO.3). Called: "
        f"{sorted(called)}"
    )

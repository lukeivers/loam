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

"""AC.SACH.2 — the microkernel's governing lines are if-then
implementation intentions (each has an antecedent + a consequent), per
Gollwitzer & Sheeran 2006 — NOT flat-declarative. A flat-declarative
governing line is a failure.

The test reads the kernel file (the source of the bundle's microkernel
tier) and asserts every governing trigger line matches the IF ... THEN
shape.
"""

from __future__ import annotations

import re

from conftest import KERNEL_FILE


def _governing_lines() -> list[str]:
    """Return the kernel's governing trigger lines.

    The trigger lines are the bulleted ``- IF ... THEN ...`` items under
    "The core, as triggers:". Markdown comments, headers, and the
    narrative WHAT/THREE-ROLES prose are not governing-trigger lines —
    they set context; the triggers are what GOVERN.
    """
    text = KERNEL_FILE.read_text(encoding="utf-8")
    # Drop HTML comment blocks (license + authoring notes).
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    # Each trigger is a single LOGICAL bullet that may wrap across
    # several physical lines (cosmetic line-wrapping in the markdown).
    # Assemble logical bullets: a "- " line opens a bullet; subsequent
    # non-bullet, non-blank lines continue it until the next bullet /
    # blank / header.
    lines: list[str] = []
    current: list[str] | None = None

    def _flush() -> None:
        nonlocal current
        if current is not None:
            lines.append(" ".join(current).strip())
            current = None

    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith("- "):
            _flush()
            current = [stripped[2:].strip()]
        elif current is not None and stripped and not stripped.startswith("="):
            # Continuation of the open bullet (wrapped line).
            current.append(stripped)
        else:
            _flush()
    _flush()
    # Keep only the IF-prefixed governing trigger bullets.
    return [ln for ln in lines if ln.upper().startswith("IF ")]


def test_kernel_has_governing_trigger_lines() -> None:
    """The kernel actually carries if-then trigger lines (guards against
    a future edit that flattens the whole core into prose)."""
    triggers = _governing_lines()
    assert len(triggers) >= 4, (
        f"expected >=4 if-then trigger lines; found {len(triggers)}: {triggers}"
    )


def test_every_governing_line_is_if_then() -> None:
    """Each governing line has an IF antecedent AND a THEN consequent —
    the if-then implementation-intention shape. A flat-declarative line
    (no THEN) fails."""
    triggers = _governing_lines()
    for line in triggers:
        upper = line.upper()
        assert upper.startswith("IF "), (
            f"governing line lacks an IF antecedent (flat-declarative): {line!r}"
        )
        assert "THEN" in upper, (
            f"governing line lacks a THEN consequent (flat-declarative): {line!r}"
        )
        # Antecedent must precede consequent.
        assert upper.index("IF ") < upper.index("THEN"), (
            f"if-then ordering inverted: {line!r}"
        )


def test_required_core_triggers_present() -> None:
    """The four named core triggers from the dispatch are present in
    if-then form: verify-before-assert, native-primitive-first,
    follow-the-natural-shape, pause-if-lost. (Plus the core-wins trigger.)"""
    blob = " ".join(_governing_lines()).lower()
    # verify before asserting a tool/state/fact
    assert "verify" in blob and "ground truth" in blob
    # check for a native Claude primitive before building a loop/orchestrator
    assert "native" in blob and "primitive" in blob
    # follow the natural shape + say you widened
    assert "natural shape" in blob and "widened" in blob
    # pause + re-establish position when you lose your place
    assert "lose your place" in blob

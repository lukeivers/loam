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

"""AC.SACH.1 — when a subagent is dispatched, its received context
contains the microkernel content: prime directive (per-user translation)
+ three-role identity (runtime/platform/product) + protection floor +
pause-if-lost.

The hook composes the bundle from a SubagentStart envelope; the emitted
``additionalContext`` is asserted to carry each of the four microkernel
elements.
"""

from __future__ import annotations

import json
from pathlib import Path

from conftest import make_envelope

from loam.frame_kernel.bundle import (
    MICROKERNEL_PRIME_MARKER,
    compose_bundle,
    render_envelope,
)


def _normalized(bundle: str) -> str:
    """Collapse all whitespace runs to single spaces + lowercase.

    The microkernel prose wraps across physical lines for readability;
    these are CONTENT assertions (the named element is present), so
    cosmetic line-wrapping must not break them. Single-token checks
    (markers, role names) do not need this.
    """
    return " ".join(bundle.split()).lower()


def test_bundle_carries_prime_directive_translation(real_kernel_workspace: Path) -> None:
    """The microkernel tier carries the per-user-translation prime
    directive (the WHAT-loam-is element)."""
    bundle = compose_bundle(make_envelope(real_kernel_workspace))
    assert MICROKERNEL_PRIME_MARKER in bundle
    text = _normalized(bundle)
    # Prime directive: person brings WHAT, loam owns HOW, tuned to the
    # specific person.
    assert "owns the how" in text
    assert "tuned to" in text


def test_bundle_carries_three_role_identity(real_kernel_workspace: Path) -> None:
    """The microkernel tier names all THREE roles (runtime / platform /
    product) — the three-role identity must not be collapsed."""
    bundle = compose_bundle(make_envelope(real_kernel_workspace))
    upper = bundle.upper()
    assert "RUNTIME" in upper
    assert "PLATFORM" in upper
    assert "PRODUCT" in upper


def test_bundle_carries_protection_floor(real_kernel_workspace: Path) -> None:
    """The microkernel tier carries the protection floor — the named ways
    AI betrays its users by default."""
    bundle = compose_bundle(make_envelope(real_kernel_workspace))
    text = _normalized(bundle)
    # Protection floor: no invention, no lost context, no broken goal,
    # real memory.
    assert "inventing" in text
    assert "losing context" in text or "lost context" in text
    assert "real memory" in text


def test_bundle_carries_pause_if_lost(real_kernel_workspace: Path) -> None:
    """The microkernel tier carries the pause-if-you-lose-your-place
    flow-position rule."""
    bundle = compose_bundle(make_envelope(real_kernel_workspace))
    text = _normalized(bundle)
    assert "lose your place" in text
    assert "pause" in text


def test_emitted_additional_context_envelope_contains_microkernel(
    real_kernel_workspace: Path,
) -> None:
    """End-to-end through the emit path: the JSON additionalContext
    envelope the hook writes carries the microkernel prime marker."""
    bundle = compose_bundle(make_envelope(real_kernel_workspace))
    envelope = json.loads(render_envelope(bundle))
    injected = envelope["hookSpecificOutput"]["additionalContext"]
    assert MICROKERNEL_PRIME_MARKER in injected

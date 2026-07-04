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
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""Activation switch — default OFF (INACTIVE), owner-gated (AC.AR.12).

The capability ships READY but INACTIVE, same discipline as loam's
frame-kernel activation: the GATE / automation mode (auto-fire at a real
boundary, block a real ship/seal/send) does NOT fire until an explicit
owner activation. The MANUAL on-demand mode is unaffected — it always
works, because it never touches a live gate (that is the whole point of
shipping manual-first).

Activation is intentionally awkward to flip by accident: it requires an
explicit, present activation file whose content is the exact activation
token. An env var alone is NOT sufficient — a stray env export must not
silently arm a production gate. Absence of the file, or wrong content,
means INACTIVE.

Per ODD §2.5: :func:`gate_active` -> AC.AR.12 (default OFF; gate is a
no-op while inactive); the manual path never consults this (AC.AR.12).
"""

from __future__ import annotations

import os
from pathlib import Path

# The activation token. The activation file must contain EXACTLY this
# (stripped) for the gate to be considered active. A misc file with other
# content does not arm the gate.
ACTIVATION_TOKEN = "adversarial-review: ACTIVE"

# Default activation-file location. Overridable via the env var for
# tests / alternate deployments, but the FILE (not the env var) is the
# switch — the env var only says WHERE the switch is.
_DEFAULT_ACTIVATION_FILE = (
    Path.home() / ".loam" / "adversarial-review.activation"
)
_ENV_ACTIVATION_PATH = "ADVERSARIAL_REVIEW_ACTIVATION_FILE"


def activation_file() -> Path:
    """Resolve the activation-file path (env-overridable location)."""
    override = os.environ.get(_ENV_ACTIVATION_PATH)
    return Path(override) if override else _DEFAULT_ACTIVATION_FILE


def gate_active() -> bool:
    """Is the GATE / automation mode active? Default False (AC.AR.12).

    True only when the activation file exists AND contains exactly the
    activation token. Any other state — absent file, wrong content, read
    error — is INACTIVE. This is the switch the boundary-fire path
    consults; the manual path never calls it.
    """
    path = activation_file()
    try:
        if not path.exists():
            return False
        return path.read_text(encoding="utf-8").strip() == ACTIVATION_TOKEN
    except OSError:
        return False

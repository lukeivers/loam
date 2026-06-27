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

"""AC.SBB.4 — the baseline is a NON-tunable floor.

The three secure-build guarantees are on for every build by default and
cannot be turned off by ordinary project config. The ONLY tunable is each
guarantee's *strictness* — whether a finding BLOCKS the boundary or merely
SURFACES a notice. And even that tunable is constrained: the
``secret-commit`` guarantee (a secret is never committed) is NOT among the
tunables — an attempt to downgrade it to surface-only is ignored and the
floor stays at BLOCK.

Policy is read from an optional ``<workspace>/.loam/secure-build.yaml``:

    strictness:
      dependency-audit: surface   # block | surface
      artifact-cleanliness: block

Absent file / absent key => the default (BLOCK). An attempt to set
``secret-commit: surface`` parses but is overridden to BLOCK by
``resolve_strictness`` (the floor is enforced in code, not trusted to the
config).
"""

from __future__ import annotations

import enum
from pathlib import Path
from typing import Any


class Strictness(enum.Enum):
    """How a guarantee reacts to a finding."""

    BLOCK = "block"
    SURFACE = "surface"


# The guarantees whose strictness MAY be tuned down to ``surface``.
TUNABLE_GUARANTEES: frozenset[str] = frozenset(
    {"dependency-audit", "artifact-cleanliness"}
)

# The guarantees that are NOT tunable — always BLOCK, regardless of config.
# ``secret-commit`` (AC.SBB.1) is the floor of the floor.
NON_TUNABLE_GUARANTEES: frozenset[str] = frozenset({"secret-commit"})

ALL_GUARANTEES: frozenset[str] = TUNABLE_GUARANTEES | NON_TUNABLE_GUARANTEES

DEFAULT_STRICTNESS: Strictness = Strictness.BLOCK

_CONFIG_RELATIVE = (".loam", "secure-build.yaml")


def load_secure_build_config(workspace_root: Path) -> dict[str, Any] | None:
    """Load ``<workspace>/.loam/secure-build.yaml`` if present.

    Returns the parsed mapping, ``None`` when the file is absent. Raises
    on a malformed YAML / non-mapping document — the caller (the hook)
    turns a raise into a fail-soft allow so a broken config never blocks
    the build (the floor is on-by-default; a broken *tuning* file does not
    escalate strictness, it falls back to the default)."""
    target = workspace_root.joinpath(*_CONFIG_RELATIVE)
    if not target.exists():
        return None
    import yaml  # local import: only when a config file actually exists

    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    if data is None:
        return None
    if not isinstance(data, dict):
        raise ValueError(
            f"{target}: top-level secure-build config must be a mapping"
        )
    return data


def resolve_strictness(
    guarantee: str, config: dict[str, Any] | None
) -> Strictness:
    """Resolve the effective strictness for *guarantee*.

    * A NON-tunable guarantee (``secret-commit``) is ALWAYS ``BLOCK`` — any
      config value is ignored (the floor is enforced in code).
    * A tunable guarantee reads ``config['strictness'][guarantee]``; a
      missing key or unrecognized value falls back to ``DEFAULT_STRICTNESS``
      (BLOCK). ``surface`` is the only downgrade.
    """
    if guarantee in NON_TUNABLE_GUARANTEES:
        return Strictness.BLOCK
    if guarantee not in TUNABLE_GUARANTEES:
        raise ValueError(f"unknown secure-build guarantee: {guarantee!r}")
    if not config:
        return DEFAULT_STRICTNESS
    block = config.get("strictness")
    if not isinstance(block, dict):
        return DEFAULT_STRICTNESS
    raw = block.get(guarantee)
    if not isinstance(raw, str):
        return DEFAULT_STRICTNESS
    val = raw.strip().lower()
    if val == "surface":
        return Strictness.SURFACE
    # Any other value (incl. "block" and typos) => the safe default.
    return Strictness.BLOCK


def is_tunable(guarantee: str) -> bool:
    """True iff *guarantee*'s strictness may be tuned down to surface."""
    return guarantee in TUNABLE_GUARANTEES

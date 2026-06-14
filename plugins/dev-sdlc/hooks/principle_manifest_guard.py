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

"""PreToolUse guard — the principle-manifest integrity check
(principle-foundation-structural-enforcement, AC.PFSE.1, D-PFSE.4).

Sibling of the dev-sdlc PreToolUse guard family (objective-binding /
tdd / bash / agent / primitive-check). Matcher ``Write|Edit`` — fires
only when an edit TARGETS the principle-manifest or the derivation-map,
adding ZERO latency to every other tool call (Claude Code's matcher
primitive does the path-scoping; this code scopes further by file).

WHAT IT DOES

When an edit lands on ``docs/design/principle-manifest.yaml`` (or the
companion ``docs/design/principle-derivation-map.md``), the guard reads
the CURRENT on-disk manifest and WARNs on two observable-drift classes:

  * STRUCTURAL: the manifest no longer parses, a row is missing a
    required key, an unknown enforcement value, OR a required frame-rule
    / M5 row (FR.1/FR.2/FR.3/M5) has gone missing — AC.PFSE.1's
    enumerate-from-code contract is broken.
  * COVERAGE: a manifest row names a ``memory_basename`` that the
    derivation-map does not reference — manifest <-> map drift, the
    risk D-PFSE.2 / RF-4 names.

The guard is WARN-tier only (never deny): editing the manifest is
legitimate work; the guard surfaces drift so the editor fixes it, but
must never block the edit (the manifest IS how principles are declared,
and the seal-time coverage guard test is the hard gate). This mirrors
the primitive-check guard's posture for the warn case.

The fire path reads the on-disk manifest + map (two repo-local files);
it makes NO network/LLM call. DEV-MODE short-circuit + fail-open mirror
the sibling guards.

Stdlib only (json, os, sys) plus shared ``_gate_helpers`` +
``principle_manifest_reader``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

_CANONICAL_HOOKS_DIR = (
    Path(__file__).resolve().parents[3]
    / "framework"
    / "hands-off-lifecycle"
    / "hooks"
)
if (
    _CANONICAL_HOOKS_DIR.exists()
    and str(_CANONICAL_HOOKS_DIR) not in sys.path
):
    sys.path.insert(0, str(_CANONICAL_HOOKS_DIR))


import _gate_helpers as _helpers  # noqa: E402
import principle_manifest_reader as _reader  # noqa: E402


AUDIT_LOG_FILENAME = "principle-manifest-guard.log"

TOOLS_GATED = ("Write", "Edit", "MultiEdit")

# The workspace-relative paths whose edit triggers the integrity check.
WATCHED_PATHS: frozenset[str] = frozenset(
    {
        _reader.PRINCIPLE_MANIFEST_PATH,
        _reader.DERIVATION_MAP_PATH,
    }
)


class Decision:
    """Outcome of one principle-manifest-guard fire.

    ``decision`` in {"allow", "warn", "no-op"}. ``kind`` names the
    sub-shape for the audit row: {"structural", "coverage", "ok",
    "no-op", None}.
    """

    __slots__ = ("decision", "reason", "kind")

    def __init__(
        self,
        decision: str,
        *,
        reason: str | None = None,
        kind: str | None = None,
    ) -> None:
        self.decision = decision
        self.reason = reason
        self.kind = kind


def _targets_watched_path(
    tool_input: dict[str, Any], workspace_root: Path
) -> bool:
    """True iff the edit's file_path canonicalises to a watched path."""
    file_path = tool_input.get("file_path")
    if not isinstance(file_path, str) or not file_path:
        return False
    rel = _helpers.workspace_relative(file_path, workspace_root)
    if rel is None:
        return False
    return rel in WATCHED_PATHS


def evaluate(
    *,
    workspace_root: Path,
    tool_name: str,
    tool_input: dict[str, Any],
) -> Decision:
    """Decide allow / warn / no-op for one PreToolUse Write/Edit fire.

    DEV-MODE-only (NORMAL-USE short-circuits to no-op, sibling-guard
    convention). Fires only when the edit targets a watched path.
    Reads the CURRENT on-disk manifest — the warn surfaces drift the
    editor is about to compound or has already introduced; the hard
    gate is the seal-time coverage guard test.
    """
    if tool_name not in TOOLS_GATED:
        return Decision("no-op")
    if not _targets_watched_path(tool_input, workspace_root):
        return Decision("no-op")

    mode = _helpers.read_workspace_mode_or_normal_use(workspace_root)
    if mode != "dev-mode":
        return Decision("no-op")

    # STRUCTURAL check — does the current manifest parse + carry the
    # required rows?
    try:
        rows = _reader.load_rows(workspace_root)
    except _reader.ManifestError as exc:
        return Decision(
            "warn", reason=_reason_structural(str(exc)), kind="structural"
        )
    except FileNotFoundError:
        # Manifest absent — only meaningful if the workspace is meant to
        # carry it; treat as no-op (the seal guard test is the hard
        # gate, and a fresh workspace legitimately has no manifest yet).
        return Decision("no-op")
    except OSError:
        return Decision("no-op")

    missing = _reader.missing_required_ids(rows)
    if missing:
        return Decision(
            "warn",
            reason=_reason_missing_ids(missing),
            kind="structural",
        )

    # COVERAGE check — manifest memory_basenames must be referenced by
    # the derivation-map (manifest <-> map drift, D-PFSE.2 / RF-4).
    try:
        map_basenames = _reader.derivation_map_basenames(workspace_root)
    except OSError:
        return Decision("allow", kind="ok")
    manifest_basenames = _reader.coverage_basenames(rows)
    uncovered = sorted(manifest_basenames - map_basenames)
    if uncovered:
        return Decision(
            "warn",
            reason=_reason_coverage(uncovered),
            kind="coverage",
        )

    return Decision("allow", kind="ok")


def _reason_structural(detail: str) -> str:
    return (
        f"principle-manifest integrity (DEV-MODE) — note: the "
        f"principle-manifest "
        f"(`{_reader.PRINCIPLE_MANIFEST_PATH}`) is structurally invalid: "
        f"{detail}. AC.PFSE.1 requires a checker can enumerate FR.1 / "
        f"FR.2 / FR.3 + M5 from this file; a malformed manifest breaks "
        f"that contract. Fix the row before sealing — the seal-time "
        f"coverage guard is the hard gate. (Allowed; advisory.)"
    )


def _reason_missing_ids(missing: list[str]) -> str:
    return (
        f"principle-manifest integrity (DEV-MODE) — note: the "
        f"principle-manifest is missing required rows: "
        f"{', '.join(missing)}. AC.PFSE.1 requires FR.1 / FR.2 / FR.3 + "
        f"M5 declared as rows. Restore the row(s) before sealing. "
        f"(Allowed; advisory.)"
    )


def _reason_coverage(uncovered: list[str]) -> str:
    return (
        f"principle-manifest integrity (DEV-MODE) — note: manifest "
        f"row(s) reference corpus file(s) the derivation-map "
        f"(`{_reader.DERIVATION_MAP_PATH}`) does not: "
        f"{', '.join(uncovered)}. Manifest <-> map drift (D-PFSE.2 / "
        f"RF-4). Add the principle to the derivation-map, OR correct the "
        f"manifest `memory_basename`. (Allowed; advisory.)"
    )


def _append_audit_line(
    workspace_root: Path,
    *,
    mode: str,
    decision: Decision,
    target: str | None,
) -> None:
    payload = {
        "ts": _helpers.now_iso_z(),
        "tool": "Write/Edit",
        "target": target,
        "mode": mode,
        "decision": decision.decision,
        "kind": decision.kind,
    }
    _helpers.append_audit_line(
        workspace_root, AUDIT_LOG_FILENAME, payload
    )


def _emit_warn_response(message: str) -> None:
    payload = {"systemMessage": message}
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    """Read the PreToolUse envelope from stdin; emit warn/no-op; exit 0.

    Fail-open on every environmental / parse failure (a broken check
    must never block an edit).
    """
    try:
        raw = sys.stdin.read()
    except Exception:  # noqa: BLE001 — fail-open
        return 0
    if not raw.strip():
        return 0
    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError:
        return 0
    if not isinstance(envelope, dict):
        return 0

    tool_name = envelope.get("tool_name")
    if not isinstance(tool_name, str):
        return 0
    tool_input = envelope.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    cwd = envelope.get("cwd")
    if not isinstance(cwd, str) or not cwd:
        return 0
    workspace_root = Path(cwd)

    try:
        decision = evaluate(
            workspace_root=workspace_root,
            tool_name=tool_name,
            tool_input=tool_input,
        )
    except Exception:  # noqa: BLE001 — fail-open on any internal error
        return 0

    file_path = tool_input.get("file_path")
    target = (
        _helpers.workspace_relative(file_path, workspace_root)
        if isinstance(file_path, str)
        else None
    )
    mode = _helpers.read_workspace_mode_or_normal_use(workspace_root)

    if decision.decision != "no-op":
        _append_audit_line(
            workspace_root,
            mode=mode,
            decision=decision,
            target=target,
        )

    if decision.decision == "warn" and decision.reason is not None:
        _emit_warn_response(decision.reason)
    # allow / no-op -> empty stdout.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

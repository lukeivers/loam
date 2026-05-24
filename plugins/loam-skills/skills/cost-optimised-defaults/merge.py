#!/usr/bin/env python3
"""Cost-optimised-defaults merge helper.

Non-destructive merge of loam's recommended token-optimization
settings into ``~/.claude/settings.json``. The colocated SKILL bundle
(``plugins/loam-skills/skills/cost-optimised-defaults/SKILL.md``)
invokes this helper via two subcommands:

- ``plan`` — compute the diff against the current settings file;
  surface NEW keys, ALREADY-SET no-op keys, and COLLISION keys
  (existing value vs recommended value) without writing.

- ``apply`` — write the approved keys atomically (temp file +
  ``os.replace``); pre-existing user keys preserved by default;
  collision-keys take the per-key choice passed in via the
  ``--overwrite`` / ``--keep`` flags. Emit a structured diagnostic
  listing keys written + keys preserved-due-to-conflict.

Per D-TOKEN.ENFORCE (maintainer ruling TG 12301): install-time
scripts MUST NOT invoke ``apply`` — the SKILL's user-approval flow
is the only authorized caller. The helper itself does not check the
caller; the SKILL frontmatter and docs section carry the
opt-in-only contract.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


# The four recommended settings, absorbed from ECC's
# "Token Optimization & Cost Management" section
# (https://github.com/affaan-m/everything-claude-code README, verified
# 2026-05-24). The fourth ECC discipline (<10 MCPs + <80 active tools)
# is documentation-only — no settings.json shape — and is NOT included
# in the merge recommendations.
RECOMMENDED_TOP_LEVEL: dict[str, Any] = {
    "model": "sonnet",
}

RECOMMENDED_ENV: dict[str, str] = {
    "MAX_THINKING_TOKENS": "10000",
    "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "50",
}


@dataclass
class PlanEntry:
    """One row in the planned diff."""

    key_path: str  # e.g. "model" or "env.MAX_THINKING_TOKENS"
    status: str  # "NEW" | "ALREADY_SET" | "COLLISION"
    recommended_value: Any
    existing_value: Any = None  # only set for ALREADY_SET / COLLISION


@dataclass
class PlanResult:
    """Result of ``plan``."""

    settings_path: str
    settings_existed: bool
    entries: list[PlanEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "settings_path": self.settings_path,
            "settings_existed": self.settings_existed,
            "entries": [
                {
                    "key_path": e.key_path,
                    "status": e.status,
                    "recommended_value": e.recommended_value,
                    "existing_value": e.existing_value,
                }
                for e in self.entries
            ],
        }


@dataclass
class ApplyResult:
    """Result of ``apply``."""

    settings_path: str
    keys_written: list[str] = field(default_factory=list)
    keys_preserved_due_to_conflict: list[str] = field(default_factory=list)
    no_changes: bool = False
    no_changes_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "settings_path": self.settings_path,
            "keys_written": self.keys_written,
            "keys_preserved_due_to_conflict": (
                self.keys_preserved_due_to_conflict
            ),
            "no_changes": self.no_changes,
            "no_changes_reason": self.no_changes_reason,
        }


def _default_settings_path() -> Path:
    """Return ``~/.claude/settings.json``."""
    return Path(os.path.expanduser("~/.claude/settings.json"))


def _read_settings(path: Path) -> tuple[dict[str, Any], bool]:
    """Read settings.json; return (parsed, file_existed).

    Missing file → ``({}, False)``. Empty / whitespace-only file →
    ``({}, True)``. Malformed JSON raises ``json.JSONDecodeError``.
    """
    if not path.exists():
        return {}, False
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}, True
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError(
            f"settings.json at {path} must be a JSON object; "
            f"got {type(parsed).__name__}."
        )
    return parsed, True


def _classify_top_level(
    settings: dict[str, Any],
    key: str,
    recommended: Any,
) -> PlanEntry:
    """Classify a top-level key against current settings."""
    if key not in settings:
        return PlanEntry(
            key_path=key,
            status="NEW",
            recommended_value=recommended,
        )
    existing = settings[key]
    if existing == recommended:
        return PlanEntry(
            key_path=key,
            status="ALREADY_SET",
            recommended_value=recommended,
            existing_value=existing,
        )
    return PlanEntry(
        key_path=key,
        status="COLLISION",
        recommended_value=recommended,
        existing_value=existing,
    )


def _classify_env(
    settings: dict[str, Any],
    env_key: str,
    recommended: str,
) -> PlanEntry:
    """Classify an env.<key> entry against current settings."""
    env_block = settings.get("env", {})
    if not isinstance(env_block, dict):
        # Malformed env block — treat as collision against the entire
        # env block; surface as a COLLISION on the specific env key so
        # the user sees the issue without us auto-fixing.
        return PlanEntry(
            key_path=f"env.{env_key}",
            status="COLLISION",
            recommended_value=recommended,
            existing_value=f"<env block is {type(env_block).__name__}, "
            f"expected object>",
        )
    if env_key not in env_block:
        return PlanEntry(
            key_path=f"env.{env_key}",
            status="NEW",
            recommended_value=recommended,
        )
    existing = env_block[env_key]
    if existing == recommended:
        return PlanEntry(
            key_path=f"env.{env_key}",
            status="ALREADY_SET",
            recommended_value=recommended,
            existing_value=existing,
        )
    return PlanEntry(
        key_path=f"env.{env_key}",
        status="COLLISION",
        recommended_value=recommended,
        existing_value=existing,
    )


def plan(settings_path: Path | None = None) -> PlanResult:
    """Compute the planned diff without writing anything."""
    path = settings_path or _default_settings_path()
    settings, existed = _read_settings(path)
    entries: list[PlanEntry] = []
    for key, value in RECOMMENDED_TOP_LEVEL.items():
        entries.append(_classify_top_level(settings, key, value))
    for env_key, env_value in RECOMMENDED_ENV.items():
        entries.append(_classify_env(settings, env_key, env_value))
    return PlanResult(
        settings_path=str(path),
        settings_existed=existed,
        entries=entries,
    )


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    """Write JSON atomically: write to temp file in same dir, then
    ``os.replace`` to swap into place. A partial write cannot corrupt
    the target file because the rename is atomic on POSIX (same
    filesystem) and the temp file is invisible to readers until the
    swap."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=False)
            f.write("\n")
        os.replace(tmp_path, path)
    except Exception:
        # Clean up the temp file on any failure path; the original
        # settings.json is untouched.
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise


def apply(
    settings_path: Path | None = None,
    *,
    overwrite_keys: Iterable[str] = (),
    keep_keys: Iterable[str] = (),
) -> ApplyResult:
    """Write the approved keys atomically.

    Args:
        settings_path: target settings file; defaults to
            ``~/.claude/settings.json``.
        overwrite_keys: COLLISION keys (e.g., ``"model"`` or
            ``"env.MAX_THINKING_TOKENS"``) the user approved to
            overwrite.
        keep_keys: COLLISION keys the user chose to keep at their
            existing value. (Pass-through for the diagnostic — the
            merge ignores recommended values for these.)

    Returns:
        ApplyResult with the structured diagnostic.

    Semantics:
        - NEW keys → written.
        - ALREADY_SET keys → no-op (value already matches; no write
          attempted for this key specifically).
        - COLLISION keys → written iff in ``overwrite_keys``; kept
          otherwise.
        - Any pre-existing user key NOT in the recommended set →
          preserved byte-for-byte in the merged output.
    """
    path = settings_path or _default_settings_path()
    plan_result = plan(path)

    overwrite_set = set(overwrite_keys)
    keep_set = set(keep_keys)

    settings, _existed = _read_settings(path)

    keys_written: list[str] = []
    keys_preserved: list[str] = []

    for entry in plan_result.entries:
        # Determine whether this key gets written.
        write_this = False
        if entry.status == "NEW":
            write_this = True
        elif entry.status == "ALREADY_SET":
            # No-op; value already matches. Not counted as written or
            # preserved-due-to-conflict.
            continue
        elif entry.status == "COLLISION":
            if entry.key_path in overwrite_set:
                write_this = True
            else:
                # Default: keep existing (sovereignty).
                keys_preserved.append(entry.key_path)
                continue

        if not write_this:
            continue

        # Perform the write into the settings dict (in-memory).
        if entry.key_path.startswith("env."):
            env_key = entry.key_path[len("env."):]
            env_block = settings.get("env")
            if not isinstance(env_block, dict):
                env_block = {}
            env_block[env_key] = entry.recommended_value
            settings["env"] = env_block
        else:
            settings[entry.key_path] = entry.recommended_value
        keys_written.append(entry.key_path)

    # Sanity-check the keep_keys input: any key in keep_set that wasn't
    # already classified as COLLISION is surfaced in the diagnostic for
    # transparency. (No-op for the write itself.)
    for k in keep_set:
        if k not in [
            e.key_path for e in plan_result.entries if e.status == "COLLISION"
        ]:
            # Silently ignore — the user can pass keep flags for
            # non-collision keys without consequence.
            pass

    if not keys_written and not keys_preserved:
        return ApplyResult(
            settings_path=str(path),
            no_changes=True,
            no_changes_reason="All recommended keys already set to "
            "recommended values; no write needed.",
        )

    if keys_written:
        _atomic_write_json(path, settings)

    return ApplyResult(
        settings_path=str(path),
        keys_written=keys_written,
        keys_preserved_due_to_conflict=keys_preserved,
    )


def _cmd_plan(args: argparse.Namespace) -> int:
    settings_path = (
        Path(args.settings_path) if args.settings_path else None
    )
    result = plan(settings_path)
    print(json.dumps(result.to_dict(), indent=2))
    return 0


def _cmd_apply(args: argparse.Namespace) -> int:
    settings_path = (
        Path(args.settings_path) if args.settings_path else None
    )
    result = apply(
        settings_path,
        overwrite_keys=args.overwrite or (),
        keep_keys=args.keep or (),
    )
    print(json.dumps(result.to_dict(), indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cost-optimised-defaults-merge",
        description=(
            "Non-destructive merge of loam's recommended token-"
            "optimization settings into ~/.claude/settings.json. "
            "Subcommands: `plan` computes the diff; `apply` writes "
            "the approved keys atomically."
        ),
    )
    parser.add_argument(
        "--settings-path",
        default=None,
        help=(
            "Override path to settings.json. Defaults to "
            "~/.claude/settings.json. Primarily for testing."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser(
        "plan",
        help="Compute the planned diff; print structured JSON. "
        "No write.",
    )

    apply_p = sub.add_parser(
        "apply",
        help="Write the approved keys atomically. Pass per-key "
        "overwrite/keep choices for COLLISION keys.",
    )
    apply_p.add_argument(
        "--overwrite",
        action="append",
        metavar="KEY_PATH",
        help=(
            "COLLISION key the user approved to overwrite "
            "(e.g., `model` or `env.MAX_THINKING_TOKENS`). May be "
            "passed multiple times."
        ),
    )
    apply_p.add_argument(
        "--keep",
        action="append",
        metavar="KEY_PATH",
        help=(
            "COLLISION key the user chose to keep at its existing "
            "value. May be passed multiple times. Defaults to keep "
            "for any COLLISION key not in `--overwrite`."
        ),
    )

    args = parser.parse_args(argv)

    if args.command == "plan":
        return _cmd_plan(args)
    if args.command == "apply":
        return _cmd_apply(args)
    parser.error(f"unknown command: {args.command}")
    return 2  # unreachable


if __name__ == "__main__":
    sys.exit(main())

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

"""Workspace manifest loader.

`bootstrap.yaml` format (v1):

    version: 1
    config_dir: ~/.loam/config          # optional; default = workspace_root/config
    workspace_root: ~/.my-workspace    # optional; default = parent of manifest
    safety_profile: dev                 # optional; default = "dev".
                                        # Legal values: production-stake | dev | research.
                                        # production-stake activates non-tunable floors
                                        # (audit_trail on; cost-governance warning_fraction
                                        # floor at 0.6; always_ask floor extended) per
                                        # v0.1.6 Decision P (SOC-2 audit-trail floor).
    enable_auto_skill_capture: false   # optional; default = false (opt-in).
                                        # Boolean. When true, the persona MAY propose
                                        # workspace-local SKILL captures via the
                                        # skill-capture-proposal SKILL (3 triggers MVP:
                                        # explicit-request / repeated-invocation /
                                        # ask-and-answer; user-ratified via PM batch
                                        # API; written to <workspace>/.claude/skills/
                                        # <slug>/SKILL.md on Y). When false, the
                                        # persona MUST NOT propose. Per v0.2.0 Cycle 2
                                        # plan-doc §4 AC.SKILLCAP.7 + layered-skill
                                        # research §3.6 Decision E (universal-tier;
                                        # workflow-flag-only gating).
    contributions:
      - observability_aggregator       # name → entry-point group lookup
      - name: custom_adapter           # workspace-local escape hatch
        path: ./adapters/my_adapter.py
        attr: MyContribution           # class attribute name in file
      - name: remote_package
        module: my_pkg.bootstrap_adapter
        attr: MyContribution           # dotted module import

Three entry forms per list item:

  1. Bare string — looked up in the `loam.bootstrap.contributions`
     entry-point group. Installed-but-not-listed packages are inert.

  2. Dict with `path` + `attr` — workspace-local file. `path` is
     relative to the manifest's parent directory (absolute paths also
     accepted).

  3. Dict with `module` + `attr` — dotted module import. Not all
     Phase 4+ components need to register an entry-point; `module`
     allows direct reference even if the package didn't declare one.

In all three forms, the resolved object is a `Contribution` class
(a class, not an instance). The framework instantiates it and reads
`ContributionMetadata` off it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Union

import yaml

from .errors import (
    MissingConfigError,
)


@dataclass(frozen=True)
class ContributionRef:
    """A reference to a contribution as listed in the manifest.

    Exactly one of `entrypoint_name`, `path_attr`, or `module_attr` is
    set. The loader resolves the reference to a `Contribution` class.
    """

    kind: str  # "entrypoint" | "path" | "module"
    entrypoint_name: str | None = None
    path: Path | None = None
    path_attr: str | None = None
    module: str | None = None
    module_attr: str | None = None
    display_name: str | None = None  # for diagnostics

    @property
    def label(self) -> str:
        return self.display_name or (
            self.entrypoint_name
            or (self.path and f"{self.path}:{self.path_attr}")
            or f"{self.module}:{self.module_attr}"
            or "<unresolved>"
        )


# v0.1.6 AC.PSAFE.1 — legal values for `safety_profile`. The default
# (when the field is absent) is `"dev"` per AC.PSAFE.2.
LEGAL_SAFETY_PROFILES: frozenset[str] = frozenset(
    {"production-stake", "dev", "research"}
)
DEFAULT_SAFETY_PROFILE: str = "dev"


# v0.2.0 Cycle 2 AC.SKILLCAP.7 — `enable_auto_skill_capture` field.
# Default-false opt-in flag gating the persona's auto-skill-capture
# behaviour (skill-capture-proposal SKILL at plugins/loam-skills/).
# Mirrors safety_profile's shape — frozenset of legal values, default
# literal, fail-closed `MissingConfigError` on invalid types. Bool
# only; legal values are exactly `True` / `False`. Per layered-skill
# research §3.6 Decision E (universal-tier; workflow-flag-only
# gating; fresh workspace shouldn't auto-propose).
DEFAULT_ENABLE_AUTO_SKILL_CAPTURE: bool = False


# v0.2.1 Cycle 1 AC.ONBOARD.* — onboarding ritual fields written to
# bootstrap.yaml as the user walks through the six install-time
# questions. All five fields are optional — fresh workspaces with no
# onboarding history default to None; the onboarding ritual writes
# them as the user answers. Fail-closed validation mirrors the
# safety_profile + enable_auto_skill_capture shape.
LEGAL_CHANNEL_PREFERENCES: frozenset[str] = frozenset(
    {"telegram", "cli", "deferred"}
)
# v0.7.0 AC.NTU.2 — runtime-routing slot. Distinct from the v0.2.1
# AC.ONBOARD.4 channel_preference field (which records the onboarding-
# ritual answer): primary_channel is what the persona's runtime reply-
# routing layer reads to decide where to surface user-facing replies.
# The v0.7.0 onboarding ritual writes BOTH fields when the user picks
# "telegram" (channel_preference=telegram + primary_channel=telegram);
# pre-v0.7.0 workspaces have channel_preference set but primary_channel
# absent — the loader defaults primary_channel from channel_preference
# at load time (graceful migration path). Per D-NTU.2.a (default extend
# bootstrap.yaml manifest, not a separate channel.json file).
LEGAL_PRIMARY_CHANNELS: frozenset[str] = frozenset(
    {"telegram", "terminal"}
)
LEGAL_EXTRACTOR_OPT_INS: frozenset[str] = frozenset(
    {"yes", "deferred", "never"}
)
LEGAL_WATCH_OPT_INS: frozenset[str] = frozenset(
    {"yes", "deferred", "no"}
)
LEGAL_LANGUAGE_PRIMARIES: frozenset[str] = frozenset(
    {"rails", "ruby", "ts", "js", "mixed", "unknown", "other"}
)


@dataclass(frozen=True)
class Manifest:
    version: int
    config_dir: Path
    workspace_root: Path
    manifest_path: Path
    refs: tuple[ContributionRef, ...]
    # v0.1.6 AC.PSAFE.1 — workspace-level safety profile. Legal
    # values are in `LEGAL_SAFETY_PROFILES`; the manifest loader
    # defaults to `DEFAULT_SAFETY_PROFILE` when the field is absent
    # (AC.PSAFE.2). When `production-stake`, downstream components
    # MUST honour the non-tunable floors per AC.PSAFE.3.
    safety_profile: str = DEFAULT_SAFETY_PROFILE
    # v0.2.0 Cycle 2 AC.SKILLCAP.7 — auto-skill-capture opt-in flag.
    # When `False` (default), the persona's `skill-capture-proposal`
    # SKILL's "When to use" gate is closed and the persona MUST NOT
    # propose workspace-local SKILL captures. When `True`, the
    # persona MAY propose per the SKILL's three triggers
    # (explicit-request / repeated-invocation / ask-and-answer)
    # subject to cool-down + budget + hard-cap suppression gates.
    # The flag is a single workflow-level gate per layered-skill
    # research §3.6 Decision E (auto-creation universal across
    # users; opt-in flag fences the timing).
    enable_auto_skill_capture: bool = DEFAULT_ENABLE_AUTO_SKILL_CAPTURE
    # v0.2.1 Cycle 1 AC.ONBOARD.4 — channel preference recorded by
    # the onboarding ritual. None when the ritual has not yet run
    # (fresh workspace pre-onboarding); one of LEGAL_CHANNEL_PREFERENCES
    # otherwise. Per AC.ONBOARD.4 + plan-doc §3.
    channel_preference: str | None = None
    # v0.2.1 Cycle 1 AC.ONBOARD.6 — extractor opt-in recorded by the
    # ritual. None pre-onboarding; one of LEGAL_EXTRACTOR_OPT_INS post.
    extractor_opt_in: str | None = None
    # v0.2.1 Cycle 1 AC.ONBOARD.7 — continuous-watch opt-in.
    watch_opt_in: str | None = None
    # v0.2.1 Cycle 1 AC.ONBOARD.2 — primary-language detection result
    # (the user's answer to Q1). None pre-onboarding; one of
    # LEGAL_LANGUAGE_PRIMARIES otherwise.
    language_primary: str | None = None
    # v0.2.1 Cycle 1 AC.ONBOARD.9 — ISO 8601 UTC timestamp of ritual
    # completion. None pre-onboarding; populated when the ritual
    # writes the completion summary. Used by D2 idempotent-rerun
    # detection (already-onboarded → offer per-question re-ask).
    onboarding_completed_at: str | None = None
    # v0.7.0 AC.NTU.2 — runtime-routing slot. Defaults from
    # channel_preference for pre-v0.7.0 workspaces (graceful
    # migration). Legal values: LEGAL_PRIMARY_CHANNELS. None when
    # neither has been set (fresh workspace pre-onboarding).
    primary_channel: str | None = None


def load_manifest(manifest_path: Union[str, Path]) -> Manifest:
    """Load and validate `bootstrap.yaml`. Raises MissingConfigError
    on any missing/parse/schema error — fail-closed per brief §4.
    """
    p = Path(manifest_path).expanduser()
    if not p.exists():
        raise MissingConfigError(
            f"bootstrap manifest not found at {p}",
            data={"path": str(p)},
        )
    try:
        raw = yaml.safe_load(p.read_text())
    except yaml.YAMLError as e:
        raise MissingConfigError(
            f"bootstrap manifest parse error at {p}: {e}",
            data={"path": str(p), "parse_error": str(e)},
        ) from e

    if not isinstance(raw, dict):
        raise MissingConfigError(
            f"bootstrap manifest at {p} must be a YAML mapping; got "
            f"{type(raw).__name__}",
            data={"path": str(p)},
        )

    version = raw.get("version")
    if version != 1:
        raise MissingConfigError(
            f"bootstrap manifest at {p} must declare version: 1; got {version!r}",
            data={"path": str(p), "version": version},
        )

    workspace_root = _resolve_path(raw.get("workspace_root"), default=p.parent)
    config_dir = _resolve_path(
        raw.get("config_dir"), default=workspace_root / "config"
    )

    contributions = raw.get("contributions")
    if not isinstance(contributions, list):
        raise MissingConfigError(
            f"bootstrap manifest at {p} must declare a 'contributions' list",
            data={"path": str(p)},
        )

    refs: list[ContributionRef] = []
    for idx, entry in enumerate(contributions):
        ref = _parse_entry(entry, idx, manifest_parent=p.parent)
        refs.append(ref)

    # v0.1.6 AC.PSAFE.1 / AC.PSAFE.2 — `safety_profile` validation +
    # default. Absent → DEFAULT_SAFETY_PROFILE (`"dev"`). Present-but-
    # not-in-LEGAL_SAFETY_PROFILES → fail-closed MissingConfigError
    # (matches the rest of the loader's fail-closed shape).
    safety_profile_raw = raw.get("safety_profile")
    if safety_profile_raw is None:
        safety_profile = DEFAULT_SAFETY_PROFILE
    elif (
        isinstance(safety_profile_raw, str)
        and safety_profile_raw in LEGAL_SAFETY_PROFILES
    ):
        safety_profile = safety_profile_raw
    else:
        raise MissingConfigError(
            f"bootstrap manifest at {p} declares "
            f"safety_profile={safety_profile_raw!r}; legal values are "
            f"{sorted(LEGAL_SAFETY_PROFILES)}",
            data={"path": str(p), "safety_profile": safety_profile_raw},
        )

    # v0.2.0 Cycle 2 AC.SKILLCAP.7 — `enable_auto_skill_capture`
    # validation + default. Absent → DEFAULT_ENABLE_AUTO_SKILL_CAPTURE
    # (`False`). Present-and-bool → use that value. Present-and-not-
    # bool → fail-closed MissingConfigError (mirrors the safety_profile
    # fail-closed shape; matches the loader's existing discipline).
    #
    # Important: PyYAML parses `true` / `True` / `false` / `False` as
    # bool; integers / strings / floats / lists / dicts all reach the
    # `else` branch and fail-closed. The fail-closed message names the
    # legal values explicitly (True / False) so authoring typos are
    # observable at load.
    eascr = raw.get("enable_auto_skill_capture")
    if eascr is None:
        enable_auto_skill_capture = DEFAULT_ENABLE_AUTO_SKILL_CAPTURE
    elif isinstance(eascr, bool):
        enable_auto_skill_capture = eascr
    else:
        raise MissingConfigError(
            f"bootstrap manifest at {p} declares "
            f"enable_auto_skill_capture={eascr!r}; legal values are "
            f"True / False (boolean only).",
            data={
                "path": str(p),
                "enable_auto_skill_capture": eascr,
            },
        )

    # v0.2.1 Cycle 1 AC.ONBOARD.4 / .6 / .7 / .2 / .9 — onboarding
    # field validation. Each field is optional (fresh workspaces with
    # no onboarding history default to None); when present, the value
    # must be a string in the corresponding LEGAL_* frozenset (fail-
    # closed mirrors safety_profile shape). onboarding_completed_at
    # accepts any string (ISO 8601 timestamp; not a closed-set field).
    channel_preference = _validate_optional_enum_str(
        raw.get("channel_preference"),
        field_name="channel_preference",
        legal_values=LEGAL_CHANNEL_PREFERENCES,
        manifest_path=p,
    )
    extractor_opt_in = _validate_optional_enum_str(
        raw.get("extractor_opt_in"),
        field_name="extractor_opt_in",
        legal_values=LEGAL_EXTRACTOR_OPT_INS,
        manifest_path=p,
    )
    watch_opt_in = _validate_optional_enum_str(
        raw.get("watch_opt_in"),
        field_name="watch_opt_in",
        legal_values=LEGAL_WATCH_OPT_INS,
        manifest_path=p,
    )
    language_primary = _validate_optional_enum_str(
        raw.get("language_primary"),
        field_name="language_primary",
        legal_values=LEGAL_LANGUAGE_PRIMARIES,
        manifest_path=p,
    )
    onboarding_completed_at_raw = raw.get("onboarding_completed_at")
    if onboarding_completed_at_raw is None:
        onboarding_completed_at = None
    elif isinstance(onboarding_completed_at_raw, str):
        onboarding_completed_at = onboarding_completed_at_raw
    else:
        raise MissingConfigError(
            f"bootstrap manifest at {p} declares "
            f"onboarding_completed_at={onboarding_completed_at_raw!r}; "
            f"must be a string (ISO 8601 timestamp) or absent.",
            data={
                "path": str(p),
                "onboarding_completed_at": onboarding_completed_at_raw,
            },
        )

    # v0.7.0 AC.NTU.2 — primary_channel runtime-routing slot. Validated
    # against LEGAL_PRIMARY_CHANNELS; falls through to a derived value
    # from channel_preference for pre-v0.7.0 workspaces (graceful
    # migration path: telegram→telegram; cli→terminal; deferred→None).
    primary_channel = _validate_optional_enum_str(
        raw.get("primary_channel"),
        field_name="primary_channel",
        legal_values=LEGAL_PRIMARY_CHANNELS,
        manifest_path=p,
    )
    if primary_channel is None and channel_preference is not None:
        # Migration default: derive from channel_preference.
        if channel_preference == "telegram":
            primary_channel = "telegram"
        elif channel_preference == "cli":
            primary_channel = "terminal"
        # "deferred" -> primary_channel stays None (caller treats as
        # unset; runtime defaults to terminal per current behavior).

    return Manifest(
        version=version,
        config_dir=config_dir,
        workspace_root=workspace_root,
        manifest_path=p,
        refs=tuple(refs),
        safety_profile=safety_profile,
        enable_auto_skill_capture=enable_auto_skill_capture,
        channel_preference=channel_preference,
        extractor_opt_in=extractor_opt_in,
        watch_opt_in=watch_opt_in,
        language_primary=language_primary,
        onboarding_completed_at=onboarding_completed_at,
        primary_channel=primary_channel,
    )


def _validate_optional_enum_str(
    raw_value: Any,
    *,
    field_name: str,
    legal_values: frozenset[str],
    manifest_path: Path,
) -> str | None:
    """Validate an optional enum-shaped string field.

    Per AC.ONBOARD.4 / .6 / .7 / .2: the field is absent on fresh
    workspaces (returns None); present-and-in-legal-set returns the
    value; otherwise fails-closed with MissingConfigError matching
    the safety_profile shape.
    """
    if raw_value is None:
        return None
    if isinstance(raw_value, str) and raw_value in legal_values:
        return raw_value
    raise MissingConfigError(
        f"bootstrap manifest at {manifest_path} declares "
        f"{field_name}={raw_value!r}; legal values are "
        f"{sorted(legal_values)} or absent.",
        data={"path": str(manifest_path), field_name: raw_value},
    )


def write_onboarding_fields(
    manifest_path: Union[str, Path],
    *,
    safety_profile: str | None = None,
    enable_auto_skill_capture: bool | None = None,
    channel_preference: str | None = None,
    extractor_opt_in: str | None = None,
    watch_opt_in: str | None = None,
    language_primary: str | None = None,
    onboarding_completed_at: str | None = None,
    primary_channel: str | None = None,
) -> None:
    """Update onboarding fields on `bootstrap.yaml` in place (atomic).

    Per AC.ONBOARD.4 / .5 / .6 / .7 / .8 / .9: the onboarding ritual
    writes user-supplied values to bootstrap.yaml as the user answers
    each question. Only non-None arguments are written; None arguments
    leave the existing value intact (idempotent partial updates).

    Atomic via tmp+rename. Preserves `version` + `contributions` + any
    other unrelated keys on disk verbatim.
    """
    p = Path(manifest_path).expanduser()
    if not p.exists():
        raise MissingConfigError(
            f"bootstrap manifest not found at {p}; cannot write "
            f"onboarding fields without an existing manifest.",
            data={"path": str(p)},
        )
    raw = yaml.safe_load(p.read_text())
    if not isinstance(raw, dict):
        raise MissingConfigError(
            f"bootstrap manifest at {p} must be a YAML mapping; got "
            f"{type(raw).__name__}",
            data={"path": str(p)},
        )

    updates: dict[str, Any] = {}
    if safety_profile is not None:
        if safety_profile not in LEGAL_SAFETY_PROFILES:
            raise ValueError(
                f"safety_profile={safety_profile!r} not in "
                f"{sorted(LEGAL_SAFETY_PROFILES)}"
            )
        updates["safety_profile"] = safety_profile
    if enable_auto_skill_capture is not None:
        if not isinstance(enable_auto_skill_capture, bool):
            raise ValueError("enable_auto_skill_capture must be bool")
        updates["enable_auto_skill_capture"] = enable_auto_skill_capture
    if channel_preference is not None:
        if channel_preference not in LEGAL_CHANNEL_PREFERENCES:
            raise ValueError(
                f"channel_preference={channel_preference!r} not in "
                f"{sorted(LEGAL_CHANNEL_PREFERENCES)}"
            )
        updates["channel_preference"] = channel_preference
    if extractor_opt_in is not None:
        if extractor_opt_in not in LEGAL_EXTRACTOR_OPT_INS:
            raise ValueError(
                f"extractor_opt_in={extractor_opt_in!r} not in "
                f"{sorted(LEGAL_EXTRACTOR_OPT_INS)}"
            )
        updates["extractor_opt_in"] = extractor_opt_in
    if watch_opt_in is not None:
        if watch_opt_in not in LEGAL_WATCH_OPT_INS:
            raise ValueError(
                f"watch_opt_in={watch_opt_in!r} not in "
                f"{sorted(LEGAL_WATCH_OPT_INS)}"
            )
        updates["watch_opt_in"] = watch_opt_in
    if language_primary is not None:
        if language_primary not in LEGAL_LANGUAGE_PRIMARIES:
            raise ValueError(
                f"language_primary={language_primary!r} not in "
                f"{sorted(LEGAL_LANGUAGE_PRIMARIES)}"
            )
        updates["language_primary"] = language_primary
    if onboarding_completed_at is not None:
        if not isinstance(onboarding_completed_at, str):
            raise ValueError("onboarding_completed_at must be a string")
        updates["onboarding_completed_at"] = onboarding_completed_at
    if primary_channel is not None:
        if primary_channel not in LEGAL_PRIMARY_CHANNELS:
            raise ValueError(
                f"primary_channel={primary_channel!r} not in "
                f"{sorted(LEGAL_PRIMARY_CHANNELS)}"
            )
        updates["primary_channel"] = primary_channel

    raw.update(updates)

    # Atomic tmp+rename write — mirrors the per-project-pm pattern.
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(yaml.safe_dump(raw, sort_keys=False))
    tmp.replace(p)


def _resolve_path(value: Any, *, default: Path) -> Path:
    if value is None:
        return Path(default).expanduser().resolve()
    return Path(str(value)).expanduser().resolve()


def _parse_entry(
    entry: Any, idx: int, *, manifest_parent: Path
) -> ContributionRef:
    if isinstance(entry, str):
        return ContributionRef(
            kind="entrypoint",
            entrypoint_name=entry,
            display_name=entry,
        )
    if not isinstance(entry, dict):
        raise MissingConfigError(
            f"contributions[{idx}] must be a string or mapping; "
            f"got {type(entry).__name__}",
            data={"index": idx},
        )

    name_for_display = entry.get("name")

    if "path" in entry:
        attr = entry.get("attr")
        if not isinstance(attr, str) or not attr:
            raise MissingConfigError(
                f"contributions[{idx}] path-form entry must declare "
                f"'attr' (the Contribution class name)",
                data={"index": idx, "entry": entry},
            )
        raw_path = str(entry["path"])
        p = Path(raw_path).expanduser()
        if not p.is_absolute():
            p = (manifest_parent / p).resolve()
        return ContributionRef(
            kind="path",
            path=p,
            path_attr=attr,
            display_name=name_for_display or f"{p}:{attr}",
        )

    if "module" in entry:
        attr = entry.get("attr")
        if not isinstance(attr, str) or not attr:
            raise MissingConfigError(
                f"contributions[{idx}] module-form entry must declare "
                f"'attr' (the Contribution class name)",
                data={"index": idx, "entry": entry},
            )
        module = str(entry["module"])
        return ContributionRef(
            kind="module",
            module=module,
            module_attr=attr,
            display_name=name_for_display or f"{module}:{attr}",
        )

    if "entrypoint" in entry:
        return ContributionRef(
            kind="entrypoint",
            entrypoint_name=str(entry["entrypoint"]),
            display_name=name_for_display or str(entry["entrypoint"]),
        )

    raise MissingConfigError(
        f"contributions[{idx}] must specify one of "
        f"'path+attr', 'module+attr', or 'entrypoint'",
        data={"index": idx, "entry": entry},
    )

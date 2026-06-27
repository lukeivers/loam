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

"""Floor gate-decision orchestration.

Ties the config (AC.DSF.1), the destructive classifier + resolved-target
gate strength (AC.DSF.2/.3), and the attestation contract + refuse-all
default (AC.DSF.6) into a single decision for the hook. Two surfaces:

* :func:`evaluate_bash` — a Bash command's destructive action against a
  production-class target with no fresh attestation is DENIED.
* :func:`evaluate_write` — a production connection string written into a
  non-production / local config file is DENIED, with the value never echoed
  (AC.DSF.4).

These are pure functions over already-loaded inputs. They may RAISE if a
downstream read is malformed (e.g. a corrupt attestations file surfaces as
``AttestationError``); the hook entry-point wraps the destructive-evaluation
path so any such raise becomes a fail-CLOSED deny (AC.DSF.7), never a silent
allow.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath

from .attestation import AttestationStore, attestation_status
from .classifier import (
    DestructiveMatch,
    GateStrength,
    classify_destructive,
    compute_gate_strength,
)
from .config import DeployConfig, Environment
from .deny_message import (
    PRODUCTION_TARGET_PHRASE,
    destructive_unattested_message,
    prod_string_write_message,
)


@dataclass(frozen=True)
class Decision:
    """A floor gate decision. ``action`` is ``"allow"`` or ``"deny"``."""

    action: str
    reason: str  # plain-words deny message; "" for allow
    sub_action: str = ""
    gate_strength: GateStrength | None = None
    target_environment: Environment | None = None

    @property
    def denied(self) -> bool:
        return self.action == "deny"


def _allow() -> Decision:
    return Decision(action="allow", reason="")


def _relevant_production_target(
    strength: GateStrength, config: DeployConfig
) -> Environment | None:
    """The production-class environment whose attestation governs this command.

    The resolved target wins when the command points at a declared-prod
    identity (AC.DSF.2); otherwise the active environment governs when it is
    itself production-class. ``None`` when no production-class environment is
    in play (the floor does not refuse non-production destructive ops)."""
    resolved = strength.resolved_environment
    if resolved is not None and resolved.is_production_class:
        return resolved
    active = config.active_environment()
    if active is not None and active.is_production_class:
        return active
    return None


def evaluate_bash(
    command: str,
    config: DeployConfig,
    attestations: AttestationStore,
    now: datetime,
) -> Decision:
    """Decide a Bash command against the floor (AC.DSF.2/.3/.6).

    A non-destructive command is always allowed (the floor gates destructive
    verbs only). A destructive command against a production-class target with
    no FRESH attestation is denied (refuse-all-destructive default). A
    destructive command against a production-class target WITH a fresh
    attestation is allowed by the floor — the deploy-tier capability owns the
    higher approval; the floor's job is the default-refuse, not the approval."""
    match: DestructiveMatch = classify_destructive(command)
    strength = compute_gate_strength(command, config)
    if not match.is_destructive:
        return Decision(action="allow", reason="", gate_strength=strength)

    prod_env = _relevant_production_target(strength, config)
    if prod_env is None:
        # Destructive, but no production-class target in play — below the
        # floor's refuse threshold (a non-prod env is the deploy tier's to
        # gate, not the floor's).
        return Decision(
            action="allow",
            reason="",
            sub_action=match.sub_action,
            gate_strength=strength,
        )

    status = attestation_status(prod_env.id, attestations, now)
    if status.fresh:
        return Decision(
            action="allow",
            reason="",
            sub_action=match.sub_action,
            gate_strength=strength,
            target_environment=prod_env,
        )
    return Decision(
        action="deny",
        reason=destructive_unattested_message(
            sub_action=match.sub_action,
            target_phrase=PRODUCTION_TARGET_PHRASE,
            reason=status.reason,
        ),
        sub_action=match.sub_action,
        gate_strength=strength,
        target_environment=prod_env,
    )


# Filename shapes that signal a NON-production / local / shared config file —
# the destination AC.DSF.4 forbids a production connection string from
# entering. Matched against the file's basename, case-insensitively.
_LOCAL_CONFIG_BASENAMES: frozenset[str] = frozenset(
    {
        ".env",
        ".env.local",
        ".env.development",
        ".env.dev",
        ".env.test",
        ".env.example",
        ".env.sample",
        "config.local.yaml",
        "config.local.yml",
        "config.local.json",
        "settings.local.json",
        "local.settings.json",
    }
)

_LOCAL_CONFIG_SUBSTRINGS: tuple[str, ...] = (
    ".local.",
    ".development.",
    ".dev.",
)


def _is_local_config_file(file_path: str) -> bool:
    """True iff *file_path* names a non-production / local config file."""
    if not isinstance(file_path, str) or not file_path:
        return False
    name = PurePosixPath(file_path.replace("\\", "/")).name.lower()
    if name in _LOCAL_CONFIG_BASENAMES:
        return True
    if name.startswith(".env."):
        # Any .env.<suffix> that is not an explicit production file.
        return not name.endswith((".production", ".prod"))
    return any(sub in name for sub in _LOCAL_CONFIG_SUBSTRINGS)


def _production_identity_in(content: str, config: DeployConfig) -> bool:
    """True iff *content* contains a declared production-class identity token."""
    if not isinstance(content, str) or not content:
        return False
    for env in config.production_environments():
        for token in env.identities.all_tokens():
            if token and token in content:
                return True
    return False


def evaluate_write(
    file_path: str, content: str, config: DeployConfig
) -> Decision:
    """Decide a Write/Edit against the floor (AC.DSF.4).

    A production connection string (matching a declared production-class
    identity) written into a non-production / local config file is denied.
    The secret value is NEVER placed in the decision's reason — only the
    destination file is named."""
    if not _is_local_config_file(file_path):
        return _allow()
    if not _production_identity_in(content, config):
        return _allow()
    descriptor = PurePosixPath(file_path.replace("\\", "/")).name
    return Decision(
        action="deny",
        reason=prod_string_write_message(file_descriptor=descriptor),
    )

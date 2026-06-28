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

"""AC.LOCAL.2 — the LOCAL command set carries no irreversible action, and the
destructive-SQL guard warns (never blocks) against a disposable local target.

Two facts the floor relies on at LOCAL:

1. **The floor idles at LOCAL because nothing irreversible is reachable.** The
   enabled LOCAL verb set is exactly the build/run/inspect loop — bring up,
   migrate, seed, serve, reset, status. None of those is a production or
   destroy verb (``promote`` / ``deploy --prod`` / ``provision`` / ``destroy``
   / ``force-unlock`` belong to P2/P3 and are absent here). The absence is the
   guarantee — there is no prod/destroy verb to gate, so the floor has nothing
   to refuse.

2. **A destructive-SQL action against a *local* target WARNS, it does not
   block.** Locally the database is disposable — ``reset`` / ``drop`` / a
   truncate is a free undo, the trust-building safety net (local-target
   research §4). So at a *provably local* target the guard surfaces a plain
   advisory ("this wipes your local copy") and proceeds. The destructiveness
   is in the TARGET, not the verb (research §8.2): the IDENTICAL operation
   against a non-local target is left to the sealed floor, which gates it.

Fail-closed on the local predicate (research §8.4): the warn-not-block
downgrade applies ONLY when the target is provably local. An UNKNOWN target is
NOT treated as disposable — the guard defers to the floor rather than warn,
because a false "local" on a managed-DB URL is the one mistake with prod blast
radius.

Deterministic, stdlib-only. The floor owns the deny; this module owns only the
LOCAL warn layer above an idle floor.
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass


# The verbs LOCAL enables — the build/run/inspect loop (local-target research
# §1 + §7.1). Every one is reversible or inspect-only at LOCAL; the local DB is
# disposable, so even ``reset`` is a free undo, not an irreversible action.
LOCAL_ENABLED_VERBS: frozenset[str] = frozenset(
    {
        "build",     # produce the artifact locally
        "verify",    # run the independent check
        "run",       # serve the app on this machine
        "migrate",   # apply schema to the local DB
        "seed",      # load fixture data into the local DB
        "reset",     # recreate the local DB (free undo — disposable)
        "status",    # plain-language "what is running / what it touches"
        "open",      # open the local URL
    }
)

# The verbs that ARE irreversible / production / destroy actions — the set that
# MUST be absent from the LOCAL command set. These belong to P2 (Vercel) and P3
# (real-infra); LOCAL exposes none of them.
IRREVERSIBLE_VERBS: frozenset[str] = frozenset(
    {
        "promote",       # promote to production (P2)
        "deploy-prod",   # go live (P2)
        "provision",     # stand up real infrastructure (P3)
        "destroy",       # tear down live infrastructure (P3)
        "force-unlock",  # state-backend surgery (P3)
        "drop-prod",     # destructive op against a production target
        "apply-prod",    # tofu/terraform apply against real infra (P3)
    }
)


def enabled_local_verbs() -> frozenset[str]:
    """The verb set the LOCAL tier enables."""
    return LOCAL_ENABLED_VERBS


def local_set_irreversible_overlap() -> frozenset[str]:
    """The intersection of the LOCAL verb set and the irreversible/prod set.
    The AC.LOCAL.2 guarantee is that this is EMPTY — the LOCAL command set
    contains no irreversible action by construction."""
    return frozenset(LOCAL_ENABLED_VERBS & IRREVERSIBLE_VERBS)


def local_command_set_is_floor_idle() -> bool:
    """True iff the LOCAL command set exposes no irreversible/prod verb — the
    condition under which the sealed floor idles at LOCAL (nothing to gate)."""
    return not local_set_irreversible_overlap()


class SqlGuardLevel(enum.Enum):
    """The LOCAL destructive-SQL guard outcome. Note there is no ``BLOCK`` for
    a provably-local target — the local DB is disposable, so the guard never
    blocks it; a non-local target is DEFERRED to the sealed floor (which may
    deny), never blocked by this LOCAL layer."""

    NONE = "none"      # not a destructive statement
    WARN = "warn"      # destructive against a provably-local target — advise, proceed
    DEFER = "defer"    # destructive against an unknown/non-local target — floor decides


# Destructive-SQL shapes the LOCAL guard recognises. Mirrors the floor's
# vocabulary (deploy_safety_floor.classifier) without importing it, so this
# tier adds no coupling to the sealed fence.
_DESTRUCTIVE_SQL: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bdrop\s+database\b", re.IGNORECASE), "delete the whole database"),
    (re.compile(r"\bdrop\s+table\b", re.IGNORECASE), "delete a database table"),
    (re.compile(r"\btruncate\s+table\b", re.IGNORECASE), "erase every row in a table"),
    (re.compile(r"\btruncate\b\s+\w", re.IGNORECASE), "erase every row in a table"),
    (re.compile(r"\bdelete\s+from\b", re.IGNORECASE), "delete records from the database"),
    (re.compile(r"\bdropdb\b", re.IGNORECASE), "delete the whole database"),
    (re.compile(r"\bdb\s+reset\b", re.IGNORECASE), "recreate the database from scratch"),
)

# Provably-local target markers (research §8.4). A connection string / target
# containing one of these is local with high confidence. Anything else is
# UNKNOWN and treated as non-local (fail-closed).
_LOCAL_TARGET_MARKERS: tuple[str, ...] = (
    "localhost",
    "127.0.0.1",
    "::1",
    "0.0.0.0",
    "@db:",        # a compose service hostname on the local network
    "@localhost",
    "sqlite:///",  # a local sqlite file
    "file::memory:",
)


@dataclass(frozen=True)
class SqlGuardDecision:
    """The LOCAL guard's decision over a destructive-SQL command."""

    level: SqlGuardLevel
    sub_action: str   # plain-words label, "" when not destructive
    message: str      # plain-language advisory (WARN) or deferral note


def is_local_target(target: str) -> bool:
    """Is *target* a PROVABLY-local database/connection target?

    True only for the recognised local markers. An empty or unrecognised
    target is NOT local (fail-closed) — the §8.4 caution: a false "local" on a
    managed-DB URL is the one error with production blast radius, so the
    default leans non-local."""
    if not isinstance(target, str) or not target:
        return False
    low = target.lower()
    return any(marker in low for marker in _LOCAL_TARGET_MARKERS)


def _classify_destructive_sql(command: str) -> tuple[bool, str]:
    for pattern, label in _DESTRUCTIVE_SQL:
        if pattern.search(command):
            return True, label
    return False, ""


def guard_local_sql(command: str, target: str) -> SqlGuardDecision:
    """The LOCAL destructive-SQL guard (AC.LOCAL.2).

    * Non-destructive command -> ``NONE``.
    * Destructive command against a PROVABLY-local target -> ``WARN`` with a
      plain-language advisory; the local DB is disposable, so it proceeds.
    * Destructive command against an UNKNOWN/non-local target -> ``DEFER``: the
      LOCAL layer takes no warn-downgrade and hands the decision to the sealed
      floor (fail-closed — never silently allow a non-local destructive op)."""
    if not isinstance(command, str):
        raise TypeError("command must be a string")
    is_destructive, label = _classify_destructive_sql(command)
    if not is_destructive:
        return SqlGuardDecision(level=SqlGuardLevel.NONE, sub_action="", message="")

    if is_local_target(target):
        return SqlGuardDecision(
            level=SqlGuardLevel.WARN,
            sub_action=label,
            message=(
                f"Heads up: this will {label} on your local copy. That is fine "
                "locally — nothing here is public and you can rebuild it in one "
                "step. Running it now."
            ),
        )

    return SqlGuardDecision(
        level=SqlGuardLevel.DEFER,
        sub_action=label,
        message=(
            f"This would {label}, and the target does not look like your local "
            "machine. Leaving this to the safety check before anything runs."
        ),
    )

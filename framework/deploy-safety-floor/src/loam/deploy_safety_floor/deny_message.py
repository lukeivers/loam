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

"""Plain-words deny messages (AC.DSF.7, Lens 0).

The floor betrays no user: the deny message exposes the SUBSTANCE — what
would happen, to what, and why it is blocked — in the vocabulary a
non-technical owner knows. No ``is_production`` / ``prevent_destroy`` /
``permission_mode`` jargon; the substance is named, only the words adapt
(doctrine: "Always expose the substance; adapt only the vocabulary").

A secret value (a prod connection string written into a config file, per
AC.DSF.4) is NEVER echoed into a message — the caller passes a redacted
descriptor, not the value.
"""

from __future__ import annotations

# The user-facing target descriptor for a production-class environment. The
# floor never leaks the environment's internal id or the matched identity
# token into the message — it names the KIND of target in plain words.
PRODUCTION_TARGET_PHRASE = "a live production system"


def destructive_unattested_message(*, sub_action: str, target_phrase: str, reason: str) -> str:
    """Deny message for a destructive action against an unattested
    (or stale) production-class target (AC.DSF.6/.7).

    Names the TARGET and the destructive SUB-ACTION in non-technical words."""
    return (
        f"Blocked: this would {sub_action} on {target_phrase}, and that system "
        f"is not yet confirmed safe to change — {reason}. loam refuses changes "
        f"that could destroy data on a live system until it has been confirmed "
        f"protected. What to do: confirm the system's safety protections are in "
        f"place (the deploy step that checks them has not run, or its check has "
        f"lapsed); or, if this is genuinely intended and the system is not live, "
        f"correct the environment settings so it is not marked as a production "
        f"system."
    )


def destructive_fail_closed_message(*, target_phrase: str) -> str:
    """Deny message when the floor could NOT confirm a destructive action is
    safe because its own safety check errored (fail-CLOSED, AC.DSF.7).

    The floor refuses rather than guesses — it cannot prove the action is
    safe, so it does not let it through."""
    return (
        f"Blocked: loam could not confirm this change is safe on {target_phrase} "
        f"— its safety check ran into an error and could not complete. Rather "
        f"than risk an unsafe change to a live system, loam is refusing this "
        f"action. What to do: fix the environment or safety-confirmation file "
        f"that the check could not read, then try again."
    )


def prod_string_write_message(*, file_descriptor: str) -> str:
    """Deny message for writing a production connection string into a
    non-production / local config file (AC.DSF.4).

    The secret value is NOT echoed — only the destination file is named."""
    return (
        f"Blocked: this would write a live-production connection address into "
        f"{file_descriptor}, a file meant for non-production use. That mixes "
        f"production access into a place that is treated as safe to share or "
        f"experiment in. loam has kept the address out of the file and out of "
        f"this message. What to do: keep production addresses in the production "
        f"environment's own settings, not in a local or shared config file."
    )

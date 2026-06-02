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

"""Transient OAuth-token read from the macOS keychain.

The token is read FRESH on every probe (plan §10 risk 1: the token rotates
~hourly; the probe must never cache it across calls) and is **never
persisted, never logged, never returned to a caller**. It exists only as a
local string inside :func:`read_access_token`'s frame for the duration of one
HTTP request. This is the no-secrets discipline (the env-scrub fence).

Recipe (verified working — ``usage_cap.sh`` /
``feedback_real_claude_usage_oauth_endpoint.md``):
``security find-generic-password -s "Claude Code-credentials" -w`` returns the
``claudeAiOauth`` JSON blob; ``.claudeAiOauth.accessToken`` is the bearer
token.

macOS-only for v1 (owner set, Luke 13512). The Linux file-path read
(``~/.claude/.credentials.json``) is a recorded follow-on (design D-USG.4),
not this slice.
"""

from __future__ import annotations

import json
import subprocess

KEYCHAIN_SERVICE = "Claude Code-credentials"
"""The keychain *service* that stores Claude Code's OAuth credential blob.
NOT ``CLAUDE_CODE_OAUTH_TOKEN`` (the bare token that 401s — see the design's
STEP 1 provenance note)."""


def read_access_token() -> str | None:
    """Read the OAuth access token transiently from the macOS keychain.

    Returns the token string on success, or ``None`` if no credential could
    be read (keychain item absent, blob unparseable, or the access token
    missing/empty). ``None`` is the fail-open signal the probe maps to
    :class:`~loam.usage_window_guard.model.UnavailableReason.MISSING_CREDENTIAL`.

    NEVER caches the token. NEVER logs it. The returned value is handed
    straight to the request builder and dropped; nothing in this module
    retains it.
    """
    try:
        # ``-w`` prints only the password (the JSON blob) to stdout.
        # No ``-a`` account filter: the service name alone is unique, and
        # omitting it keeps the read account-agnostic across machines.
        completed = subprocess.run(
            ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        # `security` missing (non-macOS) or the subprocess failed — treat as
        # no-credential (fail-open).
        return None

    if completed.returncode != 0:
        # Keychain item not found / access denied — no credential.
        return None

    raw = completed.stdout.strip()
    if not raw:
        return None

    try:
        blob = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return None

    token = blob.get("claudeAiOauth", {}).get("accessToken")
    if not isinstance(token, str) or not token:
        return None
    return token

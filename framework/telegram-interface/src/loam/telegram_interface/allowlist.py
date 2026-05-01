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

"""Allowlist reader/writer for ``~/.claude/channels/telegram/access.json``.

The plugin owns the canonical schema: ``dmPolicy``, ``allowFrom`` (list
of string user IDs), ``groups``, ``pending``. The plugin ignores
unknown top-level keys when loading (server.ts:162–165), which means
pos-v2 can extend the file with its own multi-identity metadata
orthogonally — the extension lives under a ``pos_identities`` key so
the plugin's loader never sees it.

Schema extension (pos_identities — owner-populated, never plugin-owned):

    {
      "pos_identities": {
        "<user_id>": {
          "user_id": "<str>",
          "display_name": "<str>",
          "relationship": "<str>",      # owner | spouse | colleague | ...
          "authority_class": "owner" | "reduced_bound",
          "added_at": "<iso-8601>",
          "blocked_at": "<iso-8601>" | null
        }
      }
    }

Owner-mediated add flow: the in-session helper validates the owner is
the actor (the session owns the workspace; the plugin's own prompt
guard rejects Telegram-originated add requests — server.ts:401–405 —
so this module never runs from a Telegram-originated request). A
write from any other actor is a programming error.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import observability as obs


DEFAULT_ACCESS_PATH = Path("~/.claude/channels/telegram/access.json").expanduser()


class AuthorityClass:
    """v1 values — `owner` and `reduced_bound` only. Proposal §2.2,
    Eve's inference #4. Challenge note: keeping v1 narrow because
    richer per-domain authority (wife-gets-full-on-household) needs the
    safety-layer's domain taxonomy to land first; a richer enum here
    without that taxonomy would be under-constrained by the consumer.
    """

    OWNER = "owner"
    REDUCED_BOUND = "reduced_bound"

    VALID: frozenset[str] = frozenset({"owner", "reduced_bound"})

    @classmethod
    def validate(cls, value: str) -> str:
        if value not in cls.VALID:
            raise ValueError(
                f"authority_class must be one of {sorted(cls.VALID)}; got {value!r}"
            )
        return value


@dataclass(frozen=True)
class Identity:
    user_id: str
    display_name: str
    relationship: str
    authority_class: str
    added_at: str
    blocked_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "display_name": self.display_name,
            "relationship": self.relationship,
            "authority_class": self.authority_class,
            "added_at": self.added_at,
            "blocked_at": self.blocked_at,
        }


@dataclass
class AccessFile:
    path: Path
    data: dict[str, Any]

    @classmethod
    def load(cls, path: Path | None = None) -> "AccessFile":
        p = Path(path or DEFAULT_ACCESS_PATH).expanduser()
        if not p.exists():
            return cls(path=p, data=_default_data())
        try:
            raw = p.read_text()
            parsed = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            # Corrupt file. The plugin moves it aside on next load; we
            # return defaults so the adapter can run but loud-escalate.
            obs.inbound_rejected(
                user_id="<unknown>", reason="allowlist.access_json_corrupt"
            )
            return cls(path=p, data=_default_data())
        parsed.setdefault("dmPolicy", "pairing")
        parsed.setdefault("allowFrom", [])
        parsed.setdefault("groups", {})
        parsed.setdefault("pending", {})
        parsed.setdefault("pos_identities", {})
        return cls(path=p, data=parsed)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Atomic write. fs.writeFileSync is atomic for files under a
        # single block on Unix (research §13 Q5); we mirror that by
        # writing to a tmp and renaming. Belt-and-braces against the
        # plugin's concurrent re-read.
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.data, indent=2))
        os.chmod(tmp, 0o600)
        tmp.replace(self.path)

    # ---- query ----------------------------------------------------

    @property
    def allow_from(self) -> list[str]:
        return list(self.data.get("allowFrom", []))

    @property
    def dm_policy(self) -> str:
        return self.data.get("dmPolicy", "pairing")

    def identities(self) -> dict[str, Identity]:
        out: dict[str, Identity] = {}
        for uid, rec in (self.data.get("pos_identities") or {}).items():
            try:
                out[str(uid)] = Identity(
                    user_id=str(rec["user_id"]),
                    display_name=rec["display_name"],
                    relationship=rec.get("relationship", "unknown"),
                    authority_class=rec["authority_class"],
                    added_at=rec["added_at"],
                    blocked_at=rec.get("blocked_at"),
                )
            except (KeyError, TypeError) as exc:
                # Amendment #21 S3 silent-except bundle: surface the
                # previously silent per-record skip via OTel so an
                # operator can distinguish "record corrupt" from "user
                # unknown" on a downstream `lookup(...)` miss. The
                # `continue` remains — a record missing a required
                # field is unrecoverable at read time, so dropping it
                # from the returned dict is the only correct action.
                missing_key: str | None = None
                if isinstance(exc, KeyError) and exc.args:
                    missing_key = str(exc.args[0])
                obs.allowlist_record_malformed(
                    user_id=str(uid),
                    exception_class=type(exc).__name__,
                    missing_key=missing_key,
                )
                continue
        return out

    def lookup(self, user_id: str) -> Identity | None:
        return self.identities().get(str(user_id))

    def owner(self) -> Identity | None:
        for ident in self.identities().values():
            if ident.authority_class == AuthorityClass.OWNER:
                return ident
        # Fallback: first entry in allowFrom is treated as canonical
        # owner when pos_identities has not been populated yet (the
        # power-user case from research §6.5 and the single-user
        # default from research §9.1).
        allow = self.allow_from
        if not allow:
            return None
        return Identity(
            user_id=allow[0],
            display_name="owner",
            relationship="owner",
            authority_class=AuthorityClass.OWNER,
            added_at="<inferred>",
        )

    # ---- mutation -------------------------------------------------
    # All mutations below are explicitly "actor = workspace_owner" —
    # per the plugin's server-side prompt guard, this module is never
    # invoked as a consequence of a Telegram-originated request. The
    # `actor` parameter is retained as a logging field for OTel.

    def add_identity(
        self,
        *,
        user_id: str,
        display_name: str,
        relationship: str,
        authority_class: str,
        actor: str = "workspace_owner",
        now: datetime | None = None,
    ) -> Identity:
        AuthorityClass.validate(authority_class)
        now = now or datetime.now(timezone.utc)
        ident = Identity(
            user_id=str(user_id),
            display_name=display_name,
            relationship=relationship,
            authority_class=authority_class,
            added_at=now.isoformat(),
        )
        identities = dict(self.data.get("pos_identities") or {})
        identities[ident.user_id] = ident.to_dict()
        self.data["pos_identities"] = identities

        # Keep plugin's own allowFrom in sync. The plugin drops
        # messages from IDs not in allowFrom, so identity registration
        # must also extend allowFrom or the plugin will still reject.
        allow = list(self.data.get("allowFrom") or [])
        if ident.user_id not in allow:
            allow.append(ident.user_id)
            self.data["allowFrom"] = allow

        obs.allowlist_modified(
            action="add",
            user_id=ident.user_id,
            authority_class=authority_class,
            actor=actor,
        )
        return ident

    def mark_blocked(
        self, user_id: str, *, actor: str = "system", now: datetime | None = None
    ) -> None:
        identities = dict(self.data.get("pos_identities") or {})
        rec = dict(identities.get(str(user_id)) or {})
        if not rec:
            return
        rec["blocked_at"] = (now or datetime.now(timezone.utc)).isoformat()
        identities[str(user_id)] = rec
        self.data["pos_identities"] = identities
        obs.allowlist_modified(
            action="block",
            user_id=str(user_id),
            authority_class=rec.get("authority_class", "<unknown>"),
            actor=actor,
        )

    def clear_blocked(self, user_id: str, *, actor: str = "workspace_owner") -> None:
        identities = dict(self.data.get("pos_identities") or {})
        rec = dict(identities.get(str(user_id)) or {})
        if not rec:
            return
        rec["blocked_at"] = None
        identities[str(user_id)] = rec
        self.data["pos_identities"] = identities
        obs.allowlist_modified(
            action="unblock",
            user_id=str(user_id),
            authority_class=rec.get("authority_class", "<unknown>"),
            actor=actor,
        )


def _default_data() -> dict[str, Any]:
    return {
        "dmPolicy": "pairing",
        "allowFrom": [],
        "groups": {},
        "pending": {},
        "pos_identities": {},
    }

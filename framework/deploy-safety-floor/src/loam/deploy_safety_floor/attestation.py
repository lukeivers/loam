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

"""Attestation-record contract + refuse-all-destructive default (AC.DSF.6).

The framework-side half of F-0/G1. An environment may not operate as
``is_production`` / ``tier: real-infra`` without a NON-STALE attestation
record; absent or stale ⇒ refuse-all-destructive + plain-words "not yet
protected".

Scope boundary (plan §3 HALT-2, NON-NEGOTIABLE): the record is POPULATED by
deploy-tier provider probes (the live Tier-0 reads that prove
deletion-protection on / Object-Lock on / app-role-lacks-DDL /
``prevent_destroy`` present / OIDC scoped). Those probes are OUT of scope.
What this module owns is the CONTRACT (the record shape + the staleness
rule) and the DEFAULT POSTURE (no fresh record ⇒ refuse). The default
posture is enforced framework-side even though the proof that flips it is
provider-side — which is why the floor's promise ("an unattested production
environment refuses all destructive verbs") is TRUE today.

Record schema (``.loam/attestations.yaml``):

    attestations:
      - environment_id: 01J9Z...        # matches Environment.id
        attested_at: 2026-06-27T10:00:00Z
        ttl_seconds: 86400              # freshness window
        probes:                         # deploy-tier populated; named checks
          - name: deletion_protection
            passed: true

Stdlib + PyYAML only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


class AttestationError(ValueError):
    """The attestation-records file is present but unparseable/malformed.

    A floor gate that catches this fails CLOSED (it cannot prove freshness,
    so it must not allow a destructive prod op) — see the hook entry-point.
    """


@dataclass(frozen=True)
class Probe:
    """One named provider probe result (deploy-tier populated)."""

    name: str
    passed: bool


@dataclass(frozen=True)
class AttestationRecord:
    """An environment's protection attestation."""

    environment_id: str
    attested_at: datetime
    ttl_seconds: int
    probes: tuple[Probe, ...]

    def is_fresh(self, now: datetime) -> bool:
        """Fresh iff the attestation has not aged past its TTL AND every
        recorded probe passed. A record with a failed probe is treated as
        not-fresh (the protection it attested is no longer proven)."""
        if self.ttl_seconds <= 0:
            return False
        age = (now - self.attested_at).total_seconds()
        if age < 0 or age > self.ttl_seconds:
            return False
        return all(p.passed for p in self.probes)


@dataclass(frozen=True)
class AttestationStore:
    """The parsed set of attestation records, keyed by environment id."""

    records: tuple[AttestationRecord, ...]

    def for_environment(self, environment_id: str) -> AttestationRecord | None:
        for r in self.records:
            if r.environment_id == environment_id:
                return r
        return None


def _parse_dt(raw: Any, where: str) -> datetime:
    if isinstance(raw, datetime):
        dt = raw
    elif isinstance(raw, str):
        text = raw.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError as exc:
            raise AttestationError(
                f"{where}: 'attested_at' is not an ISO-8601 timestamp: {raw!r}"
            ) from exc
    else:
        raise AttestationError(
            f"{where}: 'attested_at' must be an ISO-8601 timestamp string"
        )
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def parse_attestations(text: str) -> AttestationStore:
    """Parse + validate ``.loam/attestations.yaml`` text.

    Raises ``AttestationError`` on a malformed file — the caller (the floor
    gate) treats that as fail-CLOSED for a destructive prod op."""
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise AttestationError(f"attestations file does not parse: {exc}") from exc
    if data is None:
        return AttestationStore(records=())
    if not isinstance(data, dict):
        raise AttestationError("attestations top-level must be a mapping")
    rows = data.get("attestations")
    if rows is None:
        return AttestationStore(records=())
    if not isinstance(rows, list):
        raise AttestationError("'attestations' must be a list")
    records: list[AttestationRecord] = []
    for i, raw in enumerate(rows):
        where = f"attestations[{i}]"
        if not isinstance(raw, dict):
            raise AttestationError(f"{where}: must be a mapping")
        env_id = raw.get("environment_id")
        if not isinstance(env_id, str) or not env_id:
            raise AttestationError(f"{where}: 'environment_id' must be a non-empty string")
        attested_at = _parse_dt(raw.get("attested_at"), where)
        ttl = raw.get("ttl_seconds")
        if not isinstance(ttl, int) or isinstance(ttl, bool):
            raise AttestationError(f"{where}: 'ttl_seconds' must be an integer")
        probes_raw = raw.get("probes", []) or []
        if not isinstance(probes_raw, list):
            raise AttestationError(f"{where}: 'probes' must be a list if present")
        probes: list[Probe] = []
        for j, p in enumerate(probes_raw):
            if not isinstance(p, dict):
                raise AttestationError(f"{where}.probes[{j}]: must be a mapping")
            pname = p.get("name")
            ppassed = p.get("passed")
            if not isinstance(pname, str) or not pname:
                raise AttestationError(f"{where}.probes[{j}]: 'name' must be a non-empty string")
            if not isinstance(ppassed, bool):
                raise AttestationError(f"{where}.probes[{j}]: 'passed' must be a boolean")
            probes.append(Probe(name=pname, passed=ppassed))
        records.append(
            AttestationRecord(
                environment_id=env_id,
                attested_at=attested_at,
                ttl_seconds=ttl,
                probes=tuple(probes),
            )
        )
    return AttestationStore(records=tuple(records))


ATTESTATIONS_RELATIVE_PATH: tuple[str, ...] = (".loam", "attestations.yaml")


def load_attestations(workspace_root: Path) -> AttestationStore:
    """Load the attestation store under *workspace_root*.

    An ABSENT file yields an empty store (no records ⇒ refuse-all-destructive
    default posture, the in-scope case). A PRESENT-but-malformed file raises
    ``AttestationError`` (fail-CLOSED at the gate)."""
    path = workspace_root.joinpath(*ATTESTATIONS_RELATIVE_PATH)
    if not path.is_file():
        return AttestationStore(records=())
    return parse_attestations(path.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class AttestationStatus:
    """Whether an environment is currently attested-protected."""

    fresh: bool
    reason: str  # plain-words, for the deny message when not fresh


def attestation_status(
    environment_id: str, store: AttestationStore, now: datetime
) -> AttestationStatus:
    """Resolve an environment's protection status (AC.DSF.6).

    No record ⇒ not fresh ("never confirmed protected"). Stale record ⇒ not
    fresh ("its safety check has expired"). A failed probe ⇒ not fresh ("a
    safety check is failing"). Only a present, in-window, all-probes-passed
    record is fresh."""
    record = store.for_environment(environment_id)
    if record is None:
        return AttestationStatus(
            fresh=False, reason="it has never been confirmed safe to change"
        )
    if not record.is_fresh(now):
        if any(not p.passed for p in record.probes):
            return AttestationStatus(
                fresh=False, reason="one of its safety checks is currently failing"
            )
        return AttestationStatus(
            fresh=False, reason="its safety confirmation has expired and needs re-checking"
        )
    return AttestationStatus(fresh=True, reason="")

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

"""The privacy-safe bug-report consumer (plan §6) — user-initiated.

A non-technical user who hit a problem can report it without any data leaving
their machine that they did not see and approve, and without needing to know
what GitHub is. The consumer routes 100% of its egress through the core gate
(``gate.release``) — there is no second egress path.

Flow:

1. **Understand it** — a short plain-language interview characterizes the
   problem (the persona conducts the conversation; the entry-point consumes
   the answers, so the flow is testable without an interactive prompt —
   AC.BR.1).
2. **Assemble** a candidate bundle from LOCAL signals only. Files + logs
   default to ``declined`` (AC.BR.2). Every candidate item's bytes are
   scanned against the safety secret floor and auto-redacted BEFORE the
   review surface (AC.BR.3).
3. **Review** through the two-layer surface (caller-driven decisions).
4. **Release or fallback** (AC.BR.4): send to the friendly intake (no
   "GitHub" jargon shown) through the gate, OR take the always-available
   local-only fallback — a real on-disk artefact, zero egress.

Deterministic — makes NO LLM call and spawns NO Claude session.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .binding import approval_binding
from .bundle import (
    BundleState,
    EgressBundle,
    EgressItem,
    ItemDecision,
    ItemKind,
)
from .gate import EgressReleaseGate, SendTransport
from .redaction import redact_secrets

#: The plain-language name the user sees for the default destination — NO
#: "GitHub" / "issue" / "repo" jargon (AC.BR.4). The maintainer wires the
#: concrete intake behind this allow-listed endpoint identifier (F-BR-1).
FRIENDLY_INTAKE_NAME = "the loam team"
FRIENDLY_INTAKE_ENDPOINT = "loam-feedback-intake"

REPORT_PURPOSE = "bug-report"


@dataclass(frozen=True)
class ReportInterview:
    """The plain-language interview answers (AC.BR.1).

    The persona conducts the interview (one question at a time); these are the
    user's own words, fed to the entry-point. ``what_doing`` / ``expected`` /
    ``happened`` mirror the three triage questions in the design §2.2.
    """

    what_doing: str
    expected: str
    happened: str

    def note(self) -> str:
        """The plain-language note built from the interview — the user's words."""
        return (
            f"What I was doing: {self.what_doing}\n"
            f"What I expected: {self.expected}\n"
            f"What happened instead: {self.happened}"
        )


@dataclass(frozen=True)
class CandidateFile:
    """A file/log the user *might* attach — defaults to DECLINED (AC.BR.2)."""

    plain_summary: str
    content: bytes
    is_log: bool = False


@dataclass(frozen=True)
class ReportOutcome:
    """The result of a bug-report run.

    Exactly one of ``released`` / ``local_path`` is set:

    * ``released`` — the bundle that went through the gate (state RELEASED);
      ``egress_occurred`` is True.
    * ``local_path`` — the on-disk artefact the local fallback wrote;
      ``egress_occurred`` is False (nothing left the machine).
    """

    bundle: EgressBundle
    egress_occurred: bool
    released: EgressBundle | None = None
    local_path: Path | None = None
    redacted_patterns: tuple[str, ...] = ()


def _redacted_item(
    *, kind: ItemKind, plain_summary: str, raw: bytes,
    decision: ItemDecision,
) -> tuple[EgressItem, tuple[str, ...]]:
    """Build an item with the secret floor run over its bytes PRE-review.

    The redaction happens at assembly time (AC.BR.3): the item the user later
    sees in the review surface already has any caught secret replaced with a
    plain-language placeholder — the secret is gone from the bundle entirely.
    """
    clean, matched = redact_secrets(raw)
    item = EgressItem.new(
        kind=kind,
        plain_summary=plain_summary,
        exact_bytes=clean,
        decision=decision,
    )
    return item, matched


def assemble_report_bundle(
    *,
    interview: ReportInterview,
    loam_version: str,
    os_name: str,
    candidate_files: tuple[CandidateFile, ...] = (),
    error_observed: bytes | None = None,
) -> tuple[EgressBundle, tuple[str, ...]]:
    """Assemble a candidate bug-report bundle (DRAFTING -> AWAITING_REVIEW).

    Local signals only — nothing has left the machine. Returns the bundle +
    the names of every secret pattern auto-redacted across all items.

    Decision defaults (the privacy posture):

    * the note (the user's words), the loam version, and the coarse OS fact
      default to ``approved`` — the user explicitly typed / consented to these
      and they carry no path/username/secret (and the secret floor runs over
      them regardless).
    * any error/what-went-wrong text loam observed defaults to ``approved``
      AFTER secret redaction (it is the error message, the core report value).
    * EVERY file / log defaults to ``declined`` (AC.BR.2): the user must
      actively approve a file to include it. Files NEVER default to "will
      send."
    """
    items: list[EgressItem] = []
    all_matched: list[str] = []

    note_item, m = _redacted_item(
        kind=ItemKind.freeform_text,
        plain_summary="A note describing what went wrong",
        raw=interview.note().encode("utf-8"),
        decision=ItemDecision.approved,
    )
    items.append(note_item)
    all_matched.extend(m)

    ver_item, m = _redacted_item(
        kind=ItemKind.system_fact,
        plain_summary="Which version of loam you are on",
        raw=loam_version.encode("utf-8"),
        decision=ItemDecision.approved,
    )
    items.append(ver_item)
    all_matched.extend(m)

    os_item, m = _redacted_item(
        kind=ItemKind.system_fact,
        plain_summary="The kind of computer you are on",
        raw=os_name.encode("utf-8"),
        decision=ItemDecision.approved,
    )
    items.append(os_item)
    all_matched.extend(m)

    if error_observed is not None:
        err_item, m = _redacted_item(
            kind=ItemKind.log_line,
            plain_summary="The error message loam saw",
            raw=error_observed,
            decision=ItemDecision.approved,
        )
        items.append(err_item)
        all_matched.extend(m)

    for cf in candidate_files:
        # Files + logs DEFAULT-DECLINED (AC.BR.2) — but the secret floor still
        # runs now, so if the user later approves it, no secret rides along.
        file_item, m = _redacted_item(
            kind=ItemKind.log_line if cf.is_log else ItemKind.file,
            plain_summary=cf.plain_summary,
            raw=cf.content,
            decision=ItemDecision.declined,
        )
        items.append(file_item)
        all_matched.extend(m)

    bundle = EgressBundle.new(
        purpose=REPORT_PURPOSE,
        destination_name=FRIENDLY_INTAKE_NAME,
        destination_endpoint=FRIENDLY_INTAKE_ENDPOINT,
        items=tuple(items),
    ).to_awaiting_review()
    return bundle, tuple(all_matched)


def take_local_fallback(
    bundle: EgressBundle, *, out_path: Path
) -> ReportOutcome:
    """The always-available local-only fallback (AC.BR.4) — ZERO egress.

    Writes the report (the items + their plain summaries + the bytes the user
    chose to keep) to the user's own disk and returns a ``ReportOutcome`` with
    ``egress_occurred=False``. The bundle terminates in ``NO_EGRESS`` —
    nothing left the machine. This is a first-class choice, never a dead end.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = [
        "loam problem report (saved on your computer — nothing was sent)",
        "",
    ]
    for idx, it in enumerate(bundle.items, start=1):
        lines.append(f"--- {idx}. {it.plain_summary} ---")
        # The local file is the user's own; show the content they are keeping.
        body = it.exact_bytes.decode("utf-8", errors="replace")
        lines.append(body)
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return ReportOutcome(
        bundle=bundle.to_no_egress(),
        egress_occurred=False,
        local_path=out_path,
    )


def send_report(
    bundle: EgressBundle,
    *,
    transport: SendTransport,
    allowed_endpoints: frozenset[str] | set[str] | tuple[str, ...] = (
        FRIENDLY_INTAKE_ENDPOINT,
    ),
) -> ReportOutcome:
    """Send the approved set to the friendly intake THROUGH the gate (AC.BR.4).

    Records the approval binding over the current shippable set, drives the
    bundle to APPROVED, then releases through the single fail-closed gate. If
    the gate refuses (an unreviewed item, a mutated set, an unknown
    destination), it raises ``EgressRefused`` and sends NOTHING — there is no
    bypass.
    """
    approved = bundle.approve(approval_binding(bundle))
    gate = EgressReleaseGate(
        allowed_endpoints=allowed_endpoints, transport=transport
    )
    released = gate.release(approved)
    return ReportOutcome(
        bundle=released,
        egress_occurred=True,
        released=released,
    )


def run_bug_report(
    *,
    interview: ReportInterview,
    loam_version: str,
    os_name: str,
    candidate_files: tuple[CandidateFile, ...] = (),
    error_observed: bytes | None = None,
    decisions: tuple[tuple[int | str, ItemDecision], ...] = (),
    choice: str = "local",
    transport: SendTransport | None = None,
    out_path: Path | None = None,
    allowed_endpoints: frozenset[str] | set[str] | tuple[str, ...] = (
        FRIENDLY_INTAKE_ENDPOINT,
    ),
) -> ReportOutcome:
    """The production bug-report entry-point (AC.BR-S.1 outcome-altitude).

    Drives the full flow with NO pre-arranged state: assemble from real local
    signals -> apply the user's per-item ``decisions`` -> either take the
    local fallback (``choice="local"``, zero egress, real on-disk file) or
    send through the gate (``choice="send"``, approved set only).

    ``decisions`` is a tuple of ``(item_ref, decision)`` the user made on the
    review surface. ``item_ref`` is EITHER the 1-based position the user typed
    on the review list (an ``int`` — the number "1", "2", ... they actually
    see) OR an item id (a ``str``). Position-keyed decisions are the real UX:
    the entry-point assembles the bundle internally with fresh ids the caller
    cannot know in advance, so a non-tech user (or the persona) refers to an
    item by the number on the list, not a generated id. ``redaction`` bytes
    are not threaded here for brevity — callers needing redaction use
    :func:`assemble_report_bundle` + :func:`review.apply_decision` directly.
    The two terminal choices are the user's: "send" routes through the gate;
    "local" / "don't send anything" routes to the fallback.
    """
    bundle, _matched = assemble_report_bundle(
        interview=interview,
        loam_version=loam_version,
        os_name=os_name,
        candidate_files=candidate_files,
        error_observed=error_observed,
    )

    # Apply the user's review decisions (approve / decline per item). An int
    # ref is the 1-based list position the user typed; a str ref is an id.
    from .review import apply_decision

    for item_ref, decision in decisions:
        if isinstance(item_ref, int):
            item_id = bundle.items[item_ref - 1].item_id
        else:
            item_id = item_ref
        bundle = apply_decision(bundle, item_id, decision)

    if choice == "send":
        if transport is None:
            raise ValueError("send chosen but no transport provided")
        return send_report(
            bundle, transport=transport, allowed_endpoints=allowed_endpoints
        )

    # Default + "don't send anything" -> local fallback (zero egress).
    target = out_path or (Path.cwd() / "loam-report.txt")
    return take_local_fallback(bundle, out_path=target)

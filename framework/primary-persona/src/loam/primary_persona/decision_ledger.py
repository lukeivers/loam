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

"""Decision ledger — owner rulings as first-class structured records.

Memory recall cycle, Slice 3 (plan:
``docs/plans/memory-decision-ledger-surfacing-dispatch-packs.md``).

The 2026-06-09 $750k-Tilth failure proved that a ruling living only as
chat is unretrievable by construction: the deciding turn contains
neither "Tilth" nor "750" (pure deixis), so no ranking quality can
bridge "the Tilth raise" to it. The fix is write-side: the in-session
persona — which HOLDS the entity context — writes the ruling as a
structured record at ruling time (D2, owner-ratified), carrying the
vocabulary that makes ask-time loading possible.

Surfaces (all deterministic; NO LLM/API call anywhere — every entry
point here sits on a turn-close / session-start / per-turn hot path):

- **Write surface (AC.DLG.1)** — :func:`write_decision`: one
  frontmatter'd markdown record per ruling under
  ``<memory_dir>/decisions/`` (the episode store's sibling orbit —
  composes BESIDE ``write_episode``, never reshapes it). Atomic via
  tmp + ``os.replace``. Append-not-rewrite: supersession MARKS via the
  sealed frontmatter convention (``supersession.mark_superseded``),
  never edits a record in place.
- **Ruling detector + steer (AC.DLG.2)** — :func:`is_ruling_shaped`
  (deterministic grammar) + :func:`detect_and_flag_ruling_gap` (the
  Stop-seam call: a ruling-shaped turn that closed with no record
  written during the turn flags a pending steer) +
  :func:`consume_pending_steer` (the next turn's model-facing nag —
  steer-not-block, fail-open). :func:`run_catch_up_sweep` is the
  session-start backstop for turns the live detector missed.
- **Retrieval integration (AC.DLG.3)** — :func:`search_decisions`
  (entity-vocabulary token match, whole-record hits) +
  :func:`open_decisions` (``status: open`` records surface without an
  explicit query). Consumed by ``keep_pace.retrieval`` as a third
  merged source rendering per the AC.SRF.3 whole-record contract.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from .supersession import mark_superseded, read_supersession

#: Records live beside episodes in the workspace memory tree:
#: ``<memory_dir>/decisions/<date>-<slug>.md``.
DECISIONS_SUBDIR = "decisions"

#: AC.DLG.3 — cap on query-matched decision records surfaced per turn
#: (the AC.SRF.3 budget fits >=3 whole records; matched + open share it).
DECISION_TOP_N = 3

#: AC.DLG.3 — cap on no-query ``status: open`` records surfaced per turn.
OPEN_DECISION_CAP = 2

#: Pending-steer marker (one at a time — a newer gap replaces an older
#: unconsumed one; the catch-up sweep is the completeness backstop).
_PENDING_STEER_FILE = ".pending-ruling-steer.json"

#: Catch-up sweep bookkeeping (epoch-seconds of the last sweep).
_LAST_SWEEP_FILE = ".last-catch-up-sweep"

#: Bound on episode files examined per catch-up sweep (newest first) so
#: a long-idle workspace cannot make session-start unboundedly slow.
_SWEEP_EPISODE_BOUND = 200

#: A record written within this window BEFORE the ruling-shaped turn
#: closed counts as "corresponding" when the previous-turn-close marker
#: is unavailable (fresh workspace fallback).
_FALLBACK_RECORD_WINDOW_S = 3600.0


# ---- record schema + write surface (AC.DLG.1) ------------------------


@dataclass
class DecisionRecord:
    """One owner ruling, structured (AC.DLG.1's named fields)."""

    question: str
    ruling: str
    reasoning: str
    entities: tuple[str, ...]
    source: str
    workstream: str = ""
    aliases: tuple[str, ...] = ()
    status: str = "ruled"  # open | ruled | superseded
    date: str = ""
    path: str = ""  # populated on read/write
    extra: dict = field(default_factory=dict)

    def record_text(self) -> str:
        """The WHOLE-record injection text (AC.SRF.3 contract):
        question + ruling + reasoning + source pointer + status —
        never truncated to a one-line pointer by any render path."""
        lines = [
            f"question: {self.question}",
            f"ruling: {self.ruling}",
            f"reasoning: {self.reasoning}",
            f"source: {self.source}",
            f"status: {self.status}",
        ]
        if self.workstream:
            lines.append(f"workstream: {self.workstream}")
        return "\n".join(lines)


def decisions_dir(memory_dir: Path | str) -> Path:
    return Path(memory_dir) / DECISIONS_SUBDIR


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(text: str) -> str:
    slug = _SLUG_RE.sub("-", text.lower()).strip("-")
    return slug[:60] or "decision"


def _yaml_list(values: Iterable[str]) -> str:
    quoted = ", ".join(json.dumps(v, ensure_ascii=False) for v in values)
    return f"[{quoted}]"


def write_decision(
    memory_dir: Path | str,
    *,
    question: str,
    ruling: str,
    reasoning: str,
    entities: Iterable[str],
    source: str,
    workstream: str = "",
    aliases: Iterable[str] = (),
    status: str = "ruled",
    date: Optional[str] = None,
    supersedes: Iterable[Path | str] = (),
) -> dict:
    """Persist one owner ruling as a structured decision record
    (AC.DLG.1 — the production write surface).

    Machine-readable frontmatter (entities + aliases + question +
    workstream + status + source + date) over a reasoning body, one
    file per record under ``<memory_dir>/decisions/`` — atomic via
    tmp + ``os.replace``, append-not-rewrite (a new ruling on the same
    question is a NEW record that supersedes the old one via
    :func:`supersede_decision`; nothing edits in place).

    ``supersedes``: paths of CORPUS documents (rules, plan lines) this
    ruling supersedes — marked via the sealed supersession mechanism
    (AC.DLG.3; the existing retrieval honor applies unchanged).

    Returns ``{"path": <str>, "slug": <str>}``.
    """
    when = date or datetime.now(timezone.utc).date().isoformat()
    slug = _slugify(question)
    target_dir = decisions_dir(memory_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{when}-{slug}.md"
    # Append-not-rewrite: never overwrite an existing record file —
    # disambiguate with a numeric suffix instead.
    n = 2
    while target.exists():
        target = target_dir / f"{when}-{slug}-{n}.md"
        n += 1

    front = [
        "---",
        "record: decision",
        f"question: {json.dumps(question, ensure_ascii=False)}",
        f"ruling: {json.dumps(ruling, ensure_ascii=False)}",
        f"entities: {_yaml_list(entities)}",
        f"aliases: {_yaml_list(aliases)}",
        f"workstream: {json.dumps(workstream, ensure_ascii=False)}",
        f"status: {status}",
        f"source: {json.dumps(source, ensure_ascii=False)}",
        f"date: {when}",
        "---",
    ]
    body = "\n".join(front) + "\n" + reasoning.strip() + "\n"
    tmp = target.with_suffix(".tmp")
    tmp.write_text(body, encoding="utf-8")
    os.replace(tmp, target)

    for doc in supersedes:
        # Sealed mechanism; the record is the successor pointer.
        mark_superseded(doc, str(target))
    return {"path": str(target), "slug": slug}


def supersede_decision(
    old_record: Path | str, successor: Path | str
) -> None:
    """Mark an existing decision record superseded by a newer one —
    the sealed frontmatter mark, never an in-place rewrite (AC.DLG.1
    append-not-rewrite)."""
    mark_superseded(old_record, str(successor))


_FRONT_RE = re.compile(r"\A---[ \t]*\r?\n(.*?\r?\n)---[ \t]*\r?\n", re.DOTALL)
_LIST_ITEM_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')


def _parse_scalar(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith('"'):
        try:
            return json.loads(raw)
        except ValueError:
            return raw.strip('"')
    return raw


def _parse_list(raw: str) -> tuple[str, ...]:
    return tuple(m.group(1) for m in _LIST_ITEM_RE.finditer(raw))


def read_decision(path: Path | str) -> Optional[DecisionRecord]:
    """Machine-read one record; ``None`` on a missing / malformed /
    non-decision file (fail-soft — read surfaces never raise)."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    m = _FRONT_RE.match(text)
    if not m:
        return None
    fields: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    if fields.get("record") != "decision":
        return None
    status = fields.get("status", "ruled")
    # A sealed supersession mark outranks the authored status field
    # (the mark is the append-not-rewrite supersession mechanism).
    if read_supersession(path) is not None:
        status = "superseded"
    return DecisionRecord(
        question=_parse_scalar(fields.get("question", "")),
        ruling=_parse_scalar(fields.get("ruling", "")),
        reasoning=text[m.end():].strip(),
        entities=_parse_list(fields.get("entities", "")),
        aliases=_parse_list(fields.get("aliases", "")),
        workstream=_parse_scalar(fields.get("workstream", "")),
        status=status,
        source=_parse_scalar(fields.get("source", "")),
        date=fields.get("date", ""),
        path=str(path),
    )


def iter_decisions(memory_dir: Path | str) -> list[DecisionRecord]:
    """Every readable record in the ledger, newest filename first.
    Fail-soft: an absent dir or unreadable file contributes nothing."""
    d = decisions_dir(memory_dir)
    if not d.is_dir():
        return []
    records: list[DecisionRecord] = []
    try:
        paths = sorted(d.glob("*.md"), reverse=True)
    except OSError:
        return []
    for p in paths:
        rec = read_decision(p)
        if rec is not None:
            records.append(rec)
    return records


# ---- retrieval integration (AC.DLG.3) --------------------------------

_TOKEN_RE = re.compile(r"[A-Za-z0-9_$]+")


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN_RE.findall(text or "") if len(t) > 1}


def search_decisions(
    memory_dir: Path | str,
    query_tokens: Iterable[str],
    *,
    num_results: int = DECISION_TOP_N,
) -> list[DecisionRecord]:
    """Entity-vocabulary match: records whose entities / aliases /
    question / workstream vocabulary intersects the query, scored by
    overlap (entity + alias matches weighted over body matches — the
    guaranteed-vocabulary frontmatter is the load-bearing index, per
    D2's encode-time-links design). Superseded records never surface
    (the existing supersession honor, applied to the ledger itself).
    """
    q = {str(t).lower() for t in query_tokens if str(t).strip()}
    if not q:
        return []
    scored: list[tuple[float, DecisionRecord]] = []
    for rec in iter_decisions(memory_dir):
        if rec.status == "superseded":
            continue
        keyed = _tokens(" ".join(rec.entities) + " " + " ".join(rec.aliases))
        keyed |= _tokens(rec.workstream)
        question_toks = _tokens(rec.question)
        body_toks = _tokens(rec.reasoning) | _tokens(rec.ruling)
        key_overlap = len(q & keyed)
        question_overlap = len(q & question_toks)
        body_overlap = len(q & body_toks)
        # A record must match on its DECLARED vocabulary (entities /
        # aliases / question / workstream) to surface — body-only
        # overlap is too weak a signal for whole-record injection.
        if key_overlap + question_overlap == 0:
            continue
        score = 2.0 * key_overlap + 1.5 * question_overlap + 0.5 * body_overlap
        scored.append((score, rec))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [rec for _, rec in scored[: max(num_results, 0)]]


def open_decisions(
    memory_dir: Path | str, *, limit: int = OPEN_DECISION_CAP
) -> list[DecisionRecord]:
    """``status: open`` records — surfaced WITHOUT an explicit query
    (AC.DLG.3: an open question on an active workstream rides along on
    work-anchored turns until it is ruled or superseded)."""
    out = [r for r in iter_decisions(memory_dir) if r.status == "open"]
    return out[: max(limit, 0)]


# ---- ruling detector (AC.DLG.2 — deterministic grammar) --------------

# Owner-ruling shapes. Built against the real failure cases (the
# 2026-06-07 "go the higher route" Tilth turn; the 2026-06-09
# "1. Agree with you" D2 ratification) plus the recurring ruling
# phrasings in the live turn corpus. Deterministic regex only — the
# detector sits on the Stop hot path (no LLM, ever; halt trigger §8#1).
_RULING_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        # Declarative "approved" / message-initial "Approve(d)" — the
        # bare infinitive mid-sentence ("do I need to approve any
        # PRs?") is an ASK, not a ruling (live-store measured FP).
        r"\bapproved\b",
        r"^\s*approved?\b",
        r"\bratif(?:y|ied)\b",
        r"\bgo (?:with|ahead with)\b",
        r"\blet'?s (?:go with|do|use)\b",
        r"\bagree with (?:you|that|option)\b",
        r"\bi agree\b",
        r"\bthe answer is\b",
        r"\bship it\b",
        r"\bgreen-?light\b",
        r"\bmy (?:call|ruling|decision)\b",
        r"\bdecision\s*:",
        r"\bruling\s*:",
        r"\bwe(?:'ll| will) (?:go with|do|use)\b",
        r"\byes,? do (?:it|that|this)\b",
        r"\b(?:should|let's) go the \w+(?:\s\w+)? route\b",
        r"^\s*(?:option\s*)?\d\s*[.)]\s*(?:agree|yes|that one|do it)\b",
        r"\bgo for it\b",
        r"\bsounds (?:good|right),? (?:do|go|proceed)\b",
        r"\bproceed with\b",
        r"\bsign(?:ed)? off\b",
    )
)

# Interrogative openers: a message that ASKS rather than RULES. A
# question-shaped message only counts as a ruling when it ALSO carries
# an explicit decision verb (e.g. "approved — but why did X?").
_INTERROGATIVE_RE = re.compile(
    r"^\s*(?:what|how|why|when|where|who|which|should|could|would|"
    r"can|do you|did you|is there|are there|will)\b",
    re.IGNORECASE,
)
_STRONG_RULING_RE = re.compile(
    r"\b(?:approved|ratif(?:y|ied)|my (?:call|ruling|decision)|"
    r"decision\s*:|ruling\s*:|sign(?:ed)? off)\b",
    re.IGNORECASE,
)

_CHANNEL_TAG_RE = re.compile(r"<[^<>]{0,400}>")

# Non-owner STRUCTURAL turn shapes (Tier-0 verified against the live
# episode store during build): payloads recorded on the user role that
# no human wrote — skill-load preambles and bracketed all-caps system
# banners (e.g. the autonomous-restart tick runbook). The sealed
# ``compute_salience`` junk classifier covers the rest of the class
# (task-notification turns, compaction-summary dumps, empty/ack
# turns); these two shapes ride at full salience there (they ARE
# substantive content for recall) but are never OWNER speech, so the
# ruling detector excludes them explicitly.
_NON_OWNER_PREFIXES: tuple[str, ...] = (
    "base directory for this skill",
)
_SYSTEM_BANNER_RE = re.compile(r"^\[[A-Z0-9 ——\-]{8,}")


def _strip_envelopes(text: str) -> str:
    """Drop transport envelope tags so the grammar sees the words the
    OWNER wrote, not channel metadata (which contains e.g. ``user=``
    attribute soup that must never trip a pattern)."""
    return _CHANNEL_TAG_RE.sub(" ", text or "")


def _is_owner_authored(user_message: str) -> bool:
    """Eligibility gate (AC.DLG.2 precision floor): only OWNER-authored
    turn content can be ruling-shaped. Composes the SEALED structural
    junk classifier (``file_memory.compute_salience`` — Lens 1: the
    task-notification / compaction-dump / empty / bare-ack shapes are
    already classified there) plus the two named non-owner shapes the
    live-store measurement surfaced that ride at full salience.
    Fail-safe toward NOT-owner (a missed steer is recoverable via the
    catch-up sweep + the record itself; a false steer is alarm
    fatigue — the AC's named failure mode)."""
    raw = (user_message or "").strip()
    if not raw:
        return False
    try:
        from .file_memory import SALIENCE_JUNK, compute_salience

        if compute_salience(raw) == SALIENCE_JUNK:
            return False
    except Exception:  # noqa: BLE001 — degrade to the prefix checks
        pass
    lowered = raw.lower()
    if any(lowered.startswith(p) for p in _NON_OWNER_PREFIXES):
        return False
    if _SYSTEM_BANNER_RE.match(raw):
        return False
    return True


def is_ruling_shaped(user_message: str) -> bool:
    """Deterministic: does this turn's user message look like an owner
    ruling? (AC.DLG.2 — precision >= 80% on the labeled real-turn
    sample; ordinary prose / non-owner structural turns draw no flag.)
    """
    if not _is_owner_authored(user_message):
        return False
    text = _strip_envelopes(user_message)
    if not text.strip():
        return False
    matched = any(p.search(text) for p in _RULING_PATTERNS)
    if not matched:
        return False
    # Question guard: an interrogative opener without a strong ruling
    # verb is an ASK, not a ruling ("should we go with A or B?").
    if _INTERROGATIVE_RE.match(text.strip()) and not _STRONG_RULING_RE.search(
        text
    ):
        return False
    return True


# ---- Stop-seam gap detection + steer (AC.DLG.2) ----------------------


def _pending_steer_path(memory_dir: Path | str) -> Path:
    return decisions_dir(memory_dir) / _PENDING_STEER_FILE


def detect_and_flag_ruling_gap(
    *,
    memory_dir: Path | str,
    user_message: str,
    turn_started_at: Optional[float] = None,
) -> bool:
    """The Stop-seam check (called from the turn-close pipeline,
    fail-open at the call site): when the closing turn is ruling-shaped
    and NO decision record was written during it, flag a pending steer
    for the next turn. Returns whether a gap was flagged.

    "During the turn" is anchored on ``turn_started_at`` (epoch
    seconds — the caller passes the previous turn-close marker's
    mtime); a record file modified at-or-after that anchor counts as
    the corresponding record. With no anchor available the fallback
    window is :data:`_FALLBACK_RECORD_WINDOW_S`.
    """
    if not is_ruling_shaped(user_message):
        return False
    anchor = (
        turn_started_at
        if turn_started_at is not None
        else time.time() - _FALLBACK_RECORD_WINDOW_S
    )
    d = decisions_dir(memory_dir)
    if d.is_dir():
        for p in d.glob("*.md"):
            try:
                if p.stat().st_mtime >= anchor:
                    return False  # a record landed this turn — no gap
            except OSError:
                continue
    snippet = _strip_envelopes(user_message).strip().replace("\n", " ")[:300]
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "snippet": snippet,
    }
    try:
        d.mkdir(parents=True, exist_ok=True)
        tmp = _pending_steer_path(memory_dir).with_suffix(".tmp")
        tmp.write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8"
        )
        os.replace(tmp, _pending_steer_path(memory_dir))
    except OSError:
        return False  # fail-open: a steer we couldn't write is dropped
    return True


def consume_pending_steer(memory_dir: Path | str) -> str:
    """The next-turn model-facing nag (AC.DLG.2 — steer-not-block):
    read-and-clear the pending marker; ``""`` when none. Deterministic
    text carrying the evidence (the ruling-shaped snippet) and the
    action (write the record via the ledger, or note why it is not a
    ruling)."""
    path = _pending_steer_path(memory_dir)
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""
    try:
        path.unlink()
    except OSError:
        pass
    try:
        payload = json.loads(raw)
        snippet = str(payload.get("snippet", ""))
        ts = str(payload.get("ts", ""))
    except (ValueError, TypeError):
        return ""
    return (
        "[decision-ledger] The previous turn closed ruling-shaped with "
        "no decision record written. Evidence (turn snippet, "
        f"{ts}): \"{snippet}\". If the owner made a ruling, write the "
        "decision record now (entities, question, ruling, reasoning, "
        "source pointer) before continuing; if this was not a ruling, "
        "proceed — no record is needed."
    )


# ---- session-start catch-up sweep (AC.DLG.2) --------------------------

_USER_HALF_RE = re.compile(
    r"\[user\]\s*\n(.*?)(?:\n\[(?:assistant|persona)\]|\Z)", re.DOTALL
)


def _episode_user_half(episode_text: str) -> str:
    """The recorded turn's user half (the aggregator's ``[user]``
    section), envelope-stripped."""
    m = _FRONT_RE.match(episode_text)
    body = episode_text[m.end():] if m else episode_text
    um = _USER_HALF_RE.search(body)
    return um.group(1) if um else ""


def run_catch_up_sweep(
    memory_dir: Path | str,
    *,
    episodes_dir: Optional[Path] = None,
    now: Optional[float] = None,
) -> str:
    """Session-start backstop (AC.DLG.2): surface ruling-shaped turns
    recorded since the last sweep that still lack a decision record.
    Returns a model-facing block ("" when none). Bounded
    (:data:`_SWEEP_EPISODE_BOUND` newest episodes), deterministic,
    fail-soft — a sweep that cannot read state contributes nothing.
    """
    mem = Path(memory_dir)
    ep_root = episodes_dir if episodes_dir is not None else mem / "episodes"
    if not ep_root.is_dir():
        return ""
    sweep_marker = decisions_dir(mem) / _LAST_SWEEP_FILE
    try:
        last_sweep = float(sweep_marker.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        last_sweep = 0.0
    current = now if now is not None else time.time()

    try:
        candidates = sorted(
            ep_root.rglob("*.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )[:_SWEEP_EPISODE_BOUND]
    except OSError:
        return ""

    # Record mtimes once — a record written near an episode's close
    # covers that episode.
    record_mtimes: list[float] = []
    d = decisions_dir(mem)
    if d.is_dir():
        for p in d.glob("*.md"):
            try:
                record_mtimes.append(p.stat().st_mtime)
            except OSError:
                continue

    missed: list[str] = []
    for p in candidates:
        try:
            mtime = p.stat().st_mtime
        except OSError:
            continue
        if mtime <= last_sweep:
            break  # newest-first: everything older was already swept
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        user_half = _episode_user_half(text)
        if not is_ruling_shaped(user_half):
            continue
        if any(rm >= mtime - 60.0 for rm in record_mtimes):
            continue  # a record landed with (or after) this turn
        snippet = (
            _strip_envelopes(user_half).strip().replace("\n", " ")[:200]
        )
        missed.append(f'  - {snippet} [source: {p}]')
        if len(missed) >= 5:
            break

    try:
        sweep_marker.parent.mkdir(parents=True, exist_ok=True)
        tmp = sweep_marker.with_suffix(".tmp")
        tmp.write_text(str(current), encoding="utf-8")
        os.replace(tmp, sweep_marker)
    except OSError:
        pass  # fail-soft: an unwritable marker re-sweeps next session

    if not missed:
        return ""
    return (
        "[decision-ledger] Catch-up: ruling-shaped turns since the "
        "last sweep with NO decision record on file. Review each — "
        "write the record (entities, question, ruling, reasoning, "
        "source) or dismiss as not-a-ruling:\n" + "\n".join(missed)
    )

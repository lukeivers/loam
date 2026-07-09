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

"""Rules store (store **c**) — behavioral directives, provenance-bearing.

Memory redesign, Stage 4 (plan:
``docs/plans/memory-redesign-s4-rules-store-situational-recall.md``).

The three-way split's third leg. Store **a** is the always-on
constitutional floor; store **b** is topical facts/episodes/decisions
recalled by relevance; store **c** — this module — is *behavioral
directives* ("how to behave") recalled by the turn's SITUATION, never
always-on. A single utterance is a memory always, a rule only sometimes
(owner refinement round 2): the fact-half lands in (b), and — when it
carries an obvious behavioral consequence — the rule-half lands here.

The store mirrors the sealed ``decision_ledger.py`` write discipline
EXACTLY (AC.RSR.1): one frontmatter'd markdown record per rule under
``<memory_dir>/rules/`` (the decision-ledger's ``decisions/`` sibling
orbit — composes BESIDE it, never reshapes it), atomic via tmp +
``os.replace``, append-not-rewrite (supersession MARKS a new record,
never edits in place), human-readable + prunable on disk.

Two load-bearing disciplines distinguish (c) from (b):

- **Write-side classification (AC.RSR.2).** A rule is REJECTED without
  >=1 provenance pointer to a store-(b) record — a directive is
  auditable to the fact(s) that justify it (info-trust applied to (c)).
  The fact-half and rule-half of one event are authored APART at write
  time; there is no read-time scoring that re-merges them.
- **Situational recall (AC.RSR.3).** :func:`rules_for_situation`
  surfaces a rule ONLY when the turn's detected situation tags intersect
  the rule's situation set — EXACT set-membership, NO relevance/BM25
  score can admit a rule (a score is the over-injection mechanism the
  redesign killed; halt trigger §6.1). A rule with an empty situation
  set never fires.

The recall CAP, the byte sub-budget, the master reversibility lever, and
the situation DETECTOR live in ``keep_pace/retrieval.py`` (the recall
surface); this module is the STORE + the exact-match query.

Stdlib-only. No LLM, no API key, no embeddings — every surface here is
deterministic and sits on write / per-turn read paths.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from .supersession import mark_superseded, read_supersession

#: Records live beside decisions in the workspace memory tree:
#: ``<memory_dir>/rules/<date>-<slug>.md`` (the ``decisions/`` sibling).
RULES_SUBDIR = "rules"

#: Threshold-marker vocabulary (Fork C). A rule records WHY it cleared
#: the high extraction bar so S5's offline engine has a target to fit;
#: the empty string is the "unmarked / hand-seeded" default. Not a gate
#: (any marker is accepted) — a provenance-bearing label only.
RULE_TRIGGER_MARKERS = ("frustration", "bad-outcome", "key-idea", "")


class RuleValidationError(ValueError):
    """A rule write violated the auditable-to-evidence discipline
    (AC.RSR.2) — a missing directive or missing provenance pointer. The
    write API raises rather than persisting a floating rule (halt
    trigger §6.2: an un-auditable rule is never written)."""


# ---- record schema + write surface (AC.RSR.1 / AC.RSR.2) -------------


@dataclass
class RuleRecord:
    """One behavioral directive, structured (AC.RSR.1's named fields).

    ``situation`` is the tag SET matched by exact set-membership at
    recall (AC.RSR.3); ``provenance`` is the >=1 pointer(s) to the
    store-(b) record(s) that justify the rule (AC.RSR.2). ``strength``
    is the deterministic budget-arbitration weight (higher kept first
    when the cap bites, AC.RSR.5). ``floor_promote`` is the Fork B
    mitigation flag — CARRIED in the schema only; wiring it to the
    always-on floor is S1b, out of this fence (halt trigger §6.3).
    """

    directive: str
    situation: tuple[str, ...]
    provenance: tuple[str, ...]
    status: str = "active"  # active | superseded
    strength: int = 0
    floor_promote: bool = False
    trigger: str = ""  # frustration | bad-outcome | key-idea | ""
    date: str = ""
    source: str = ""
    path: str = ""  # populated on read/write

    def directive_text(self) -> str:
        """The MODEL-facing injection text for a fired rule — the
        directive plus a compact provenance pointer so the surfaced rule
        stays auditable in-context (AC.RSR.2)."""
        prov = self.provenance[0] if self.provenance else ""
        tail = f" [rule-provenance: {prov}]" if prov else ""
        return f"{self.directive}{tail}"


def rules_dir(memory_dir: Path | str) -> Path:
    return Path(memory_dir) / RULES_SUBDIR


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(text: str) -> str:
    slug = _SLUG_RE.sub("-", text.lower()).strip("-")
    return slug[:60] or "rule"


def _yaml_list(values: Iterable[str]) -> str:
    quoted = ", ".join(json.dumps(v, ensure_ascii=False) for v in values)
    return f"[{quoted}]"


def _clean_tuple(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(v for v in (str(x).strip() for x in values) if v)


def write_rule(
    memory_dir: Path | str,
    *,
    directive: str,
    situation: Iterable[str],
    provenance: Iterable[str],
    strength: int = 0,
    floor_promote: bool = False,
    trigger: str = "",
    status: str = "active",
    date: Optional[str] = None,
    source: str = "",
    supersedes: Iterable[Path | str] = (),
) -> dict:
    """Persist one behavioral rule as a structured record (AC.RSR.1 —
    the production write surface), enforcing the write-side classification
    (AC.RSR.2).

    Rejects (raises :class:`RuleValidationError`) a rule with an empty
    directive or with NO provenance pointer — a directive must be
    auditable to the fact(s) that justify it. An empty ``situation`` set
    is ALLOWED (the rule is stored but never fires through recall,
    AC.RSR.3) so an author can park a directive whose situation is not
    yet detectable and promote it to the floor later (Fork B).

    Machine-readable frontmatter over the directive body, one file per
    record under ``<memory_dir>/rules/`` — atomic via tmp + ``os.replace``,
    append-not-rewrite (a revised rule is a NEW record that supersedes the
    old one; nothing edits in place). Returns ``{"path", "slug"}``.
    """
    d = (directive or "").strip()
    if not d:
        raise RuleValidationError("a rule requires a non-empty directive")
    prov = _clean_tuple(provenance)
    if not prov:
        raise RuleValidationError(
            "a rule requires >=1 provenance pointer to a store-(b) record "
            "(AC.RSR.2 — a directive is auditable to the fact that justifies it)"
        )
    sits = _clean_tuple(situation)

    when = date or datetime.now(timezone.utc).date().isoformat()
    slug = _slugify(d)
    target_dir = rules_dir(memory_dir)
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
        "record: rule",
        f"directive: {json.dumps(d, ensure_ascii=False)}",
        f"situation: {_yaml_list(sits)}",
        f"provenance: {_yaml_list(prov)}",
        f"strength: {int(strength)}",
        f"floor_promote: {str(bool(floor_promote)).lower()}",
        f"trigger: {json.dumps(trigger, ensure_ascii=False)}",
        f"status: {status}",
        f"source: {json.dumps(source, ensure_ascii=False)}",
        f"date: {when}",
        "---",
    ]
    body = "\n".join(front) + "\n" + d + "\n"
    tmp = target.with_suffix(".tmp")
    tmp.write_text(body, encoding="utf-8")
    os.replace(tmp, target)

    for doc in supersedes:
        mark_superseded(doc, str(target))
    return {"path": str(target), "slug": slug}


def supersede_rule(old_record: Path | str, successor: Path | str) -> None:
    """Mark an existing rule superseded by a newer one — the sealed
    frontmatter mark, never an in-place rewrite (AC.RSR.1
    append-not-rewrite)."""
    mark_superseded(old_record, str(successor))


# ---- read surface (fail-soft — read surfaces never raise) ------------

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


def _parse_int(raw: str, default: int = 0) -> int:
    try:
        return int(_parse_scalar(raw))
    except (ValueError, TypeError):
        return default


def _parse_bool(raw: str) -> bool:
    return _parse_scalar(raw).strip().lower() in ("true", "1", "yes")


def read_rule(path: Path | str) -> Optional[RuleRecord]:
    """Machine-read one rule; ``None`` on a missing / malformed /
    non-rule file (fail-soft — read surfaces never raise). A sealed
    supersession mark outranks the authored status field."""
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
    if fields.get("record") != "rule":
        return None
    status = fields.get("status", "active")
    if read_supersession(path) is not None:
        status = "superseded"
    return RuleRecord(
        directive=_parse_scalar(fields.get("directive", "")),
        situation=_parse_list(fields.get("situation", "")),
        provenance=_parse_list(fields.get("provenance", "")),
        status=status,
        strength=_parse_int(fields.get("strength", "0")),
        floor_promote=_parse_bool(fields.get("floor_promote", "false")),
        trigger=_parse_scalar(fields.get("trigger", "")),
        source=_parse_scalar(fields.get("source", "")),
        date=fields.get("date", ""),
        path=str(path),
    )


def iter_rules(memory_dir: Path | str) -> list[RuleRecord]:
    """Every readable rule in the store, newest filename first. Fail-soft:
    an absent dir or unreadable file contributes nothing."""
    d = rules_dir(memory_dir)
    if not d.is_dir():
        return []
    records: list[RuleRecord] = []
    try:
        paths = sorted(d.glob("*.md"), reverse=True)
    except OSError:
        return []
    for p in paths:
        rec = read_rule(p)
        if rec is not None:
            records.append(rec)
    return records


# ---- situational recall (AC.RSR.3) -----------------------------------


def rules_for_situation(
    memory_dir: Path | str, situation_tags: Iterable[str]
) -> list[RuleRecord]:
    """The rules whose situation set intersects the turn's detected tags
    (AC.RSR.3 — EXACT set-membership, NO relevance score).

    A rule surfaces IFF at least one of its situation tags is in
    ``situation_tags``. An empty turn-tag set (the cautious detector
    firing on nothing) matches NO rule; a rule with an empty situation
    set never fires (it is parked, not recalled). Superseded rules never
    surface. The result is ordered by a DETERMINISTIC priority — strength
    desc, then newer date, then path — so the recall cap (AC.RSR.5) drops
    the lowest-priority excess, never a nondeterministic slice.
    """
    tags = {str(t).strip() for t in situation_tags if str(t).strip()}
    if not tags:
        return []
    out: list[RuleRecord] = []
    for rec in iter_rules(memory_dir):
        if rec.status == "superseded":
            continue
        if not rec.situation:
            continue  # empty situation set never fires (AC.RSR.3)
        if tags & set(rec.situation):
            out.append(rec)
    # Stable chained sort: ascending-priority keys applied last-first so
    # the final primary key is strength (Python's sort is stable).
    out.sort(key=lambda r: r.path)
    out.sort(key=lambda r: r.date, reverse=True)
    out.sort(key=lambda r: int(r.strength or 0), reverse=True)
    return out


# ---- hand-seeded starter rule set (AC.RSR.7 exercises recall) --------

#: A SMALL hand-seeded starter set (scope item 6) — enough to exercise
#: situational recall end-to-end. Each rule points its provenance at a
#: real corpus feedback record (auditable to evidence, AC.RSR.2) and a
#: situation tag the conservative day-one detector
#: (``retrieval.SITUATION_TRIGGERS``) can fire. NOT auto-loaded live: a
#: workspace's rules store stays EMPTY until :func:`seed_starter_rules`
#: is run, so S4's live recall is a dormant no-op until seeded (the S1b
#: gated flip populates the live store).
SEEDED_RULES: tuple[dict, ...] = (
    {
        "directive": (
            "Dispatch briefs carry scope only — objective, constraints, "
            "acceptance, halt triggers, ODD-check. Never enumerate files, "
            "symbols, or ACs; method stays the builder's call."
        ),
        "situation": ("dispatching-subagent",),
        "provenance": ("feedback_agent_prompts_scope_only.md",),
        "trigger": "key-idea",
    },
    {
        "directive": (
            "Run the de-AI scrub on all external-bound text before it "
            "ships; the loudest tell is em-dash overuse. Keep the human's "
            "voice."
        ),
        "situation": ("authoring-outbound-text",),
        "provenance": ("feedback_de_ai_external_text.md",),
        "trigger": "bad-outcome",
    },
    {
        "directive": (
            "Agents make NEW corrective commits if they miss a file; never "
            "git commit --amend (it collapses the audit trail)."
        ),
        "situation": ("amending-sealed-component",),
        "provenance": ("feedback_no_amend_in_agent_dispatches.md",),
        "trigger": "bad-outcome",
    },
    {
        # AC.RVL.9 — the cap-bias structural catch's in-context leg. Fires on an
        # ``authoring-plan`` turn (the altitude where every numeric limit first
        # enters a plan) directing floor+budget over count caps. The inaugural
        # real situational rule (the S4 channel's first non-demo case).
        "directive": (
            "Authoring a plan-doc: every numeric limit must name (a) the "
            "RESOURCE it derives from and (b) why the relevance floor + byte "
            "budget don't already cover it. A quantity cap with no named "
            "resource is a defect; prefer a relevance floor + byte budget over "
            "a count cap. Named exceptions: a channel with no relevance signal "
            "(count as budget denomination), or temporary scaffolding carrying "
            "a written retirement criterion."
        ),
        "situation": ("authoring-plan",),
        "provenance": (
            "2026-07-08-memory-recall-volume-limits-fable-review-rulings.md",
            "memory-recall-volume-limits-and-cap-bias-2026-07-08.md",
        ),
        "trigger": "bad-outcome",
    },
)


def seed_starter_rules(memory_dir: Path | str) -> list[dict]:
    """Write the :data:`SEEDED_RULES` starter set into ``memory_dir``,
    IDEMPOTENTLY (skip any whose directive is already stored active).
    Returns the list of ``{"path", "slug"}`` for the rules written this
    call (empty when all already present). Used by AC.RSR.7 to seed a
    store and by the S1b gated flip to populate the live store."""
    existing = {r.directive for r in iter_rules(memory_dir) if r.status != "superseded"}
    written: list[dict] = []
    for spec in SEEDED_RULES:
        if spec["directive"] in existing:
            continue
        written.append(write_rule(memory_dir, **spec))
    return written

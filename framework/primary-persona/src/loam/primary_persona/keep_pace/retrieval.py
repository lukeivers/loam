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

"""KP1 — the work-anchored per-prompt retrieval entry-point.

This module is the PRODUCTION entry-point (the surface AC.KP1.6's
cold-walk invokes with no pre-arranged state) + the KP0-chain
``Contributor``-compatible callable that the staged live wiring
registers.

Flow per turn (design §1 fix #1):
  1. Skip trivial prompts (greetings / acks) — AC.KP1.4.
  2. Read the active objectives + subgoals FRESH from the OBJECTIVES
     register (AC.KP5.5 binding; falls back to the in-source seed so
     the anchor always has the two real objectives — AC.KP1.6 no
     pre-arranged state).
  3. Build the work-anchored key (prompt + objective + subgoal +
     last-topic) — AC.KP1.2.
  4. BM25-rank the markdown corpus on the key, fresh-read each turn
     (AC.KP1.1 / AC.KP1.5).
  5. Inject the top-N <=5 pointers as plain-language additionalContext
     (AC.KP1.3); silent on no-match (AC.KP1.4).

The objective anchor is what rescues a vague prompt: "continue the
batch" tokenizes to almost nothing, but the active fiction objective's
text ("LitRPG", "Patch Notes for Reality", "production pipeline",
"canon") pulls the litrpg canon pointer out of the corpus. That is
tonight's failure, fixed (AC.KP1.6).

Registration into the KP0 chain (the
``framework/hands-off-lifecycle/hooks/keep_pace/user_prompt_submit.py``
``contributors()`` surface) is part of the GATED live wiring — STAGED,
not done in this cycle (RF-6: live activation waits for a quiescent
production window). :func:`build_keep_pace_contributor` returns the
callable that staged wiring imports; its shape matches the chain's
``Contributor.fn`` contract (``fn(envelope: dict) -> Optional[str]``).

Stdlib-only. Fail-soft throughout — any boundary error yields an empty
injection and the turn proceeds (composes with the chain's
fail-open-whole-chain guarantee, AC.KP0.4).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from . import objectives as _objectives
from .corpus_index import (
    CorpusIndex,
    default_index_path,
    discover_corpus,
)
from .work_anchor import WorkAnchor, is_trivial_prompt


# AC.KP1.3 — top-N injection cap. The design recipe is N <= 5.
DEFAULT_TOP_N = 5

# Soft cap on the injected block so a long corpus title set cannot
# bloat the turn payload. The pointers are short plain-language titles;
# this is a generous ceiling.
INJECTION_CHAR_CAP = 1200


@dataclass
class RetrievalConfig:
    """Resolution config for the work-anchored retrieval entry-point.

    All paths are injectable so AC.KP1.6's cold-walk + the unit tests
    point at fixture dirs rather than the live machine. In live wiring
    these default to the user-scope memory dir + ``~/.claude`` home.
    """

    workspace_root: Path
    memory_dir: Optional[Path] = None
    claude_homes: tuple[Path, ...] = ()
    objectives_home: Optional[Path] = None  # base for OBJECTIVES.md
    top_n: int = DEFAULT_TOP_N

    def objectives_path(self) -> Path:
        return _objectives.user_scope_objectives_path(self.objectives_home)


def _build_index(config: RetrievalConfig) -> CorpusIndex:
    """Construct the CorpusIndex with a FRESH corpus discovery closure.

    The discover closure re-runs on every sync so a corpus file added
    mid-session is picked up (AC.KP1.5 fresh-read).
    """
    obj_path = config.objectives_path()

    def _discover() -> list[Path]:
        return discover_corpus(
            memory_dir=config.memory_dir,
            claude_homes=config.claude_homes,
            objectives_path=obj_path if obj_path.is_file() else None,
        )

    return CorpusIndex(
        index_path=default_index_path(config.workspace_root),
        discover=_discover,
    )


def _render_injection(hits: list[dict[str, object]], *, cap: int) -> str:
    """Render the top-N corpus hits as plain-language additionalContext.

    AC.KP1.3: a ``[keep-pace]`` block listing the on-file topics the
    live work points at — plain English, NO file paths / ``.md`` names
    (authored plain-by-construction so it passes KP9's Cycle-3 lint).
    Silent on no hits (AC.KP1.4) — returns ``""``.
    """
    if not hits:
        return ""
    lines = ["[keep-pace] On-file context relevant to what you're working on:"]
    for h in hits:
        pointer = str(h.get("pointer", "")).strip()
        if pointer:
            lines.append(f"  - {pointer}")
    block = "\n".join(lines)
    if len(block) > cap:
        block = block[:cap].rstrip()
    return block if len(lines) > 1 else ""


def retrieve(
    *,
    prompt: str,
    config: RetrievalConfig,
    last_topic: str = "",
) -> str:
    """The PRODUCTION work-anchored retrieval entry-point (AC.KP1.6).

    Invoked with no pre-arranged retrieval state — it reads the
    objectives fresh, builds the work-anchored key, syncs + searches
    the corpus, and returns the plain-language injection (or ``""``).

    AC.KP1.4: a trivial prompt returns ``""`` (skipped) before any
    work; a no-match returns ``""`` (silent).
    AC.KP1.6: a vague "continue" + an active fiction objective surfaces
    the litrpg canon pointer via the objective anchor — the objective
    text supplies the tokens the bare prompt cannot.
    """
    if is_trivial_prompt(prompt):
        return ""

    # Read objectives FRESH (AC.KP5.5 binding; seed fallback => no
    # pre-arranged state needed for AC.KP1.6).
    try:
        objs = _objectives.load_user_scope_register(config.objectives_home)
    except Exception:  # noqa: BLE001 — fail-soft; anchor degrades to prompt-only
        objs = list(_objectives.SEEDED_OBJECTIVES)

    anchor = WorkAnchor(
        prompt=prompt,
        objective_texts=_objectives.active_objective_texts(objs),
        subgoals=_objectives.active_subgoals(objs),
        last_topic=last_topic,
    )
    query_tokens = anchor.query_tokens()
    if not query_tokens:
        return ""

    index = _build_index(config)
    try:
        hits = index.search(query_tokens=query_tokens, num_results=config.top_n)
    except Exception:  # noqa: BLE001 — fail-soft per chain fail-open contract
        hits = []
    finally:
        index.close()
    return _render_injection(hits, cap=INJECTION_CHAR_CAP)


# ---- KP0-chain contributor (STAGED live wiring import target) ------


def _resolve_live_config(envelope: dict) -> RetrievalConfig:
    """Resolve the live RetrievalConfig from a UserPromptSubmit envelope.

    Live defaults: the workspace project dir from the envelope (for the
    ``.scratch/`` index) + the user-scope memory dir + ``~/.claude``
    home for the corpus + OBJECTIVES.md. Used only by the staged live
    wiring; tests construct RetrievalConfig directly against fixtures.
    """
    ws = envelope.get("workspace") if isinstance(envelope, dict) else None
    project_dir = None
    if isinstance(ws, dict):
        project_dir = ws.get("project_dir")
    workspace_root = Path(project_dir) if project_dir else Path.cwd()
    claude_home = Path.home() / ".claude"
    # The user-scope memory dir (the feedback_*.md corpus lives under
    # the project-scoped auto-memory path; the live wiring resolves the
    # active project slug from cwd). Kept resolvable-from-home so the
    # corpus is discoverable without threading the slug through.
    memory_dir = None
    projects_root = claude_home / "projects"
    if projects_root.is_dir():
        # Prefer the memory dir whose slug matches the cwd path shape.
        slug = "-" + str(workspace_root).strip("/").replace("/", "-")
        candidate = projects_root / slug / "memory"
        if candidate.is_dir():
            memory_dir = candidate
    return RetrievalConfig(
        workspace_root=workspace_root,
        memory_dir=memory_dir,
        claude_homes=(claude_home,),
        objectives_home=claude_home,
    )


def build_keep_pace_contributor(
    config: Optional[RetrievalConfig] = None,
) -> Callable[[dict], Optional[str]]:
    """Return the KP0-chain ``Contributor.fn``-compatible callable.

    Shape matches the chain contract
    (``fn(envelope: dict) -> Optional[str]``). The STAGED live wiring
    registers this on the
    ``framework/hands-off-lifecycle/hooks/keep_pace/user_prompt_submit.py``
    ``contributors()`` list — that registration is the GATED live step
    (RF-6), NOT done in this cycle.

    When ``config`` is None the callable resolves a live config from
    the envelope per turn (the live-wiring path); when supplied the
    callable uses it (the test path). The ``last_topic`` is read from
    the envelope's ``keep_pace.last_topic`` slot when present (the
    KP7 re-assert / session-continuity threads it; absent at MVP =>
    empty, graceful per AC.KP1.2).

    Fail-soft: any error yields ``None`` (no injection) so the chain's
    fail-open-whole-chain guarantee holds (AC.KP0.4).
    """

    def contributor(envelope: dict) -> Optional[str]:
        try:
            prompt = ""
            last_topic = ""
            if isinstance(envelope, dict):
                prompt = str(envelope.get("prompt", "") or "")
                kp = envelope.get("keep_pace")
                if isinstance(kp, dict):
                    last_topic = str(kp.get("last_topic", "") or "")
            cfg = config if config is not None else _resolve_live_config(envelope)
            block = retrieve(prompt=prompt, config=cfg, last_topic=last_topic)
            return block or None
        except Exception:  # noqa: BLE001 — fail-soft; chain fail-open
            return None

    return contributor

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

"""The runner — drives the REAL production first-run intake through one
role-played non-technical user, end to end (design §4.2, AC.SMOKE.1
outcome-altitude).

It does NOT unit-test inner modules. It:

  1. instantiates a THROWAWAY fresh loam workspace via the REAL ``loam init``
     into a temp dir (zero pre-arranged state; self-cleaning, AC.SMOKE.5);
  2. runs the REAL ``run_first_run_intake`` orchestrator (the production
     entry-point the ``loam init-intake`` verb drives) with an ISOLATED-
     GLOBAL-HOME so the cold-walk never touches the operator's real
     ``~/.claude`` (live-state protection);
  3. supplies the user side of the conversation via a role-played-user
     ``Answerer`` backed by an isolated ``claude -p`` (the persona embodies the
     variant brief; one spawn per intake turn);
  4. for the idea-vacuum variant, wires the REAL ``RoleResearchProvider`` so the
     deep-role-research path can actually fire (the research subagent is itself
     an isolated ``claude -p``) — within the sealed ≤3 round-trip budget;
  5. captures the full transcript + the resulting seed artefacts
     (``~/.claude/OBJECTIVES.md`` + ``INTERACTION-MODEL.md`` in the isolated
     home) for the judge.

The intake's question WORDING is the production code's (not pinned by the
smoke); the role-played user answers whatever the production intake actually
asks, turn by turn — so the smoke measures the production conversation, not a
script the harness imposed on it.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .spawn import isolated_claude_text
from .variants import VariantSpec


# The system framing that turns an isolated `claude -p` into the role-played
# user. It is told to STAY in persona, answer only the assistant's latest
# message, and never break character into tech-speak.
_ROLEPLAY_SYSTEM = (
    "You are role-playing a specific non-technical person being onboarded by an "
    "AI assistant called loam. Stay fully in character. You will be shown the "
    "assistant's latest message; reply ONLY as your character would — in their "
    "voice, 1-3 sentences, answering that message directly. Never narrate, "
    "never use tech vocabulary your character wouldn't know, never break "
    "character, never explain that you are an AI. Here is your character:\n\n"
    "{persona_brief}"
)


@dataclass
class VariantRun:
    """The captured end-state of one role-played intake walk (the judge input)."""

    variant: VariantSpec
    workspace_root: Path
    global_home: Path
    transcript: list[tuple[str, str, str]] = field(default_factory=list)
    # (slug, assistant_prompt, user_reply) per intake turn.
    objectives_text: str = ""
    interaction_model_text: str = ""
    confirmed: bool = False
    seeded_objective_text: str | None = None
    invoked_deep_research: bool = False
    offered_deep_research: bool = False
    research_roundtrips: int | None = None
    research_is_stub: bool | None = None
    leverage_idea_texts: list[str] = field(default_factory=list)
    init_returncode: int | None = None
    error: str | None = None

    def transcript_blob(self) -> str:
        """A flat, judge-readable rendering of the whole conversation."""
        lines: list[str] = []
        for slug, prompt, reply in self.transcript:
            lines.append(f"[loam asks — {slug}]\n{prompt}")
            lines.append(f"[{self.variant.role_label} replies]\n{reply}")
        if self.leverage_idea_texts:
            lines.append("[loam's closing leverage idea(s)]")
            lines.extend(f"  >> {t}" for t in self.leverage_idea_texts)
        return "\n\n".join(lines)


class _RolePlayAnswerer:
    """The user side of the intake: each ``answerer(slug, prompt)`` call is a
    fresh isolated ``claude -p`` turn that role-plays the variant persona and
    answers the production intake's actual question.

    Stateful only for transcript capture + turn numbering; the persona context
    is re-supplied each turn (the conversation so far is folded into the prompt
    so the character stays coherent without a long-lived session)."""

    def __init__(self, variant: VariantSpec, run: VariantRun) -> None:
        self._variant = variant
        self._run = run
        self._turn = 0

    def __call__(self, slug: str, prompt: str) -> str:
        self._turn += 1
        history = "\n\n".join(
            f"Assistant: {p}\nYou ({self._variant.role_label}): {r}"
            for _, p, r in self._run.transcript
        )
        user_prompt = (
            (f"Conversation so far:\n{history}\n\n" if history else "")
            + "The assistant's latest message to you:\n"
            + f'"{prompt}"\n\n'
            + "Reply now, in character, 1-3 sentences."
        )
        reply = isolated_claude_text(
            user_prompt,
            purpose=f"role-play:{self._variant.key}:turn{self._turn}",
            system_prompt=_ROLEPLAY_SYSTEM.format(
                persona_brief=self._variant.persona_brief
            ),
            timeout=180.0,
        )
        self._run.transcript.append((slug, prompt, reply))
        return reply


def _loam_init_throwaway(
    canonical_source: Path, temp_root: Path
) -> tuple[Path, int]:
    """Run the REAL ``loam init`` into a throwaway temp workspace (AC.SMOKE.1).

    Returns (workspace_root, returncode). ONBOARDING_SKIP=1 so the six-question
    capability ritual does not block on a TTY; the load-bearing N3 intake is
    driven separately via ``run_first_run_intake`` (the real entry-point).
    """
    ws = temp_root / "ws"
    env = dict(os.environ)
    env["LOAM_ONBOARDING_SKIP"] = "1"
    proc = subprocess.run(
        [
            "loam",
            "init",
            str(ws),
            "--from",
            str(canonical_source),
        ],
        env=env,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        timeout=300.0,
    )
    return ws, proc.returncode


def run_variant(
    variant: VariantSpec,
    *,
    canonical_source: Path,
    keep_workspace: bool = False,
) -> VariantRun:
    """Drive ONE role-played variant through the real fresh-init + intake.

    Self-cleaning (AC.SMOKE.5): the throwaway workspace + isolated global home
    live under a temp dir removed on exit (unless ``keep_workspace``); the
    operator's real ``~/.claude`` is NEVER written (the intake's ``global_home``
    is the isolated temp home).
    """
    from loam.workspace_bootstrap.first_run_intake import run_first_run_intake

    temp_root = Path(tempfile.mkdtemp(prefix=f"loam-smoke-{variant.key}-"))
    home = temp_root / "home" / ".claude"
    run = VariantRun(
        variant=variant,
        workspace_root=temp_root / "ws",
        global_home=home,
    )
    try:
        # --- 1. REAL fresh loam init into the throwaway workspace. ---
        ws, rc = _loam_init_throwaway(canonical_source, temp_root)
        run.workspace_root = ws
        run.init_returncode = rc
        if rc != 0:
            run.error = f"loam init exited {rc}"
            return run

        # --- 2/3/4. REAL first-run intake, role-played user, real research. ---
        research_provider = _build_research_provider(variant)
        answerer = _RolePlayAnswerer(variant, run)
        result = run_first_run_intake(
            ws,
            answerer=answerer,
            global_home=home,
            research_provider=research_provider,
            run_capability_ritual=False,
        )

        # --- 5. Capture the resulting seed artefacts + telemetry. ---
        run.confirmed = bool(result.intake.confirmed)
        run.seeded_objective_text = result.intake.seeded_objective_text
        run.invoked_deep_research = bool(result.intake.invoked_deep_research)
        run.offered_deep_research = bool(result.intake.offered_deep_research)
        run.leverage_idea_texts = [
            li.text for li in result.intake.leverage_ideas
        ]
        if result.intake.research_result is not None:
            run.research_is_stub = result.intake.research_result.is_stub
        if research_provider is not None and hasattr(
            research_provider, "last_roundtrips"
        ):
            run.research_roundtrips = research_provider.last_roundtrips

        obj = home / "OBJECTIVES.md"
        im = home / "INTERACTION-MODEL.md"
        run.objectives_text = obj.read_text(encoding="utf-8") if obj.exists() else ""
        run.interaction_model_text = (
            im.read_text(encoding="utf-8") if im.exists() else ""
        )
        return run
    except Exception as exc:  # noqa: BLE001 — capture, never crash the whole smoke
        run.error = f"{type(exc).__name__}: {exc}"
        return run
    finally:
        if not keep_workspace:
            shutil.rmtree(temp_root, ignore_errors=True)


def _build_research_provider(variant: VariantSpec):
    """Wire the REAL deep-role-research provider for the idea-vacuum variant.

    For variants A/B the provider is left as None — the production intake's
    featherlight default (the stub) is used, and the gating logic guarantees
    they never reach it anyway (AC.SMOKE.3 / AC.DRRSEAM.2). For variant C, the
    REAL ``RoleResearchProvider`` is wired so the opt-in deep dive actually
    runs a bounded ``claude -p`` research subagent (≤3 round-trips), routed
    through the same isolation primitive — the real outcome the variant exists
    to exercise.
    """
    if not variant.expect_deep_research:
        return None
    from loam.workspace_bootstrap.deep_role_research_provider import (
        RoleResearchProvider,
    )

    # The provider's default ResearchSource is the isolated claude -p research
    # subagent (ClaudeSubagentResearchSource) — itself spawn-isolated via
    # loam_spawn_isolation. We do NOT inject a stub: the smoke wants the REAL
    # bounded research to run.
    return RoleResearchProvider()

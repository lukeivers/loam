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

"""UserPromptSubmit intent classifier — promoted to canonical from
pos3-local ``intent_classifier_inbound.py`` per amendment #144 Scope A.

Structural enforcement of the persona prompt's translate-inbound
discipline (``framework/primary-persona/templates/persona-template/
prompt.md`` §"Translate inbound — soft user language into the canonical
SKILL-trigger form"). The persona prompt directive alone proved
insufficient across four iterations of the Eric-demo smoke (v1-v4, all
inline builds despite progressively-stronger persona-prompt directives).
The intervention has to happen BEFORE the persona's interpretation —
at the UserPromptSubmit hook layer — to override the in-the-moment
"this is small enough to inline" judgment.

What this hook does:

1. Read the user's prompt from stdin (Claude Code's standard hook
   payload).
2. Classify the intent: build-with-verification, pure question,
   tiny tweak, or ambiguous. Lightweight regex scoring — no LLM
   call (deterministic + instant + zero token cost per turn,
   <5ms typical).
3. If intent is build-with-verification, emit ``additionalContext``
   markup that injects into the model's context: an explicit
   imperative-form restatement of the user's request + a directive
   that Claude Code's SKILL auto-load is the primary mechanism for
   engaging the matching SKILL (``handsoff-loop``). The slash
   command is NOT prescribed verbatim — per amendment #144 Scope B
   (TG 11881 ruling) slash commands are persona-internal mechanism,
   never user-facing output.
4. Pass through otherwise (intent is question / tiny-tweak /
   ambiguous → empty stdout, exit 0).

The ``additionalContext`` mechanism is Claude Code's UserPromptSubmit
hook output field that gets injected into the model's context before
it sees the user's prompt. Documented at code.claude.com/docs/en/hooks.

Designed to be cheap (<5ms typical). No external deps beyond stdlib.

Composes with:

  - ``framework/primary-persona/templates/persona-template/prompt.md``
    "Translate inbound" stanza (the documented discipline).
  - ``framework/hands-off-lifecycle/hooks/first_run_settings.py``
    ``merge_user_prompt_submit`` (the multi-contributor envelope this
    hook registers as an ``extra_inner_hooks`` entry alongside the
    persona's existing ``user-prompt-submit`` subcommand).
  - ``plugins/loam-skills/skills/handsoff-loop/SKILL.md`` (the SKILL
    whose description the ``additionalContext`` body references for
    Claude Code's matcher).

Per amendment #144 plan §3 D-CLE.HOOK-LOCATION, the classifier lives
co-located with the persona surface it structurally enforces: the
persona prompt is canonical primary-persona surface; the hook is the
backstop for the prompt's discipline; co-locating them keeps the rule
+ its enforcement in one place.
"""

from __future__ import annotations

import json
import re
import sys
from typing import Iterable


# ---- intent classification ---------------------------------------------

# Build-with-verification triggers — buildable-artifact phrasing plus
# evidence-of-working phrasing in the same prompt.
_BUILD_TRIGGERS: tuple[re.Pattern[str], ...] = (
    # Imperative with article ("build me a", "make me a", etc.)
    re.compile(
        r"\b(build|make|create|write|author)\s+(me\s+)?(a|an|some)\b",
        re.IGNORECASE,
    ),
    # Imperative with explicit recipient + bare noun ("build me X",
    # "make me X" — captures imperative phrasing without article).
    re.compile(
        r"\b(build|make|create|write|author)\s+me\s+\w+", re.IGNORECASE,
    ),
    # Direct imperative without "me" ("build X", "make X" — covers
    # terse asks).
    re.compile(
        r"^\s*(build|make|create|write|author)\s+\w+",
        re.IGNORECASE | re.MULTILINE,
    ),
    # "I want a/an/some/something" + "I want to build/make/..."
    re.compile(
        r"\bi\s+want\s+(a|an|some|something)\b", re.IGNORECASE,
    ),
    re.compile(
        r"\bi\s+want\s+to\s+(build|make|create|have)\b", re.IGNORECASE,
    ),
    re.compile(
        r"\bi\s+need\s+(a|an|some|something)\b", re.IGNORECASE,
    ),
    re.compile(
        r"\bi\s+need\s+to\s+(build|make|create|have)\b", re.IGNORECASE,
    ),
    re.compile(
        r"\bcan\s+you\s+(build|make|create|write|author)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bgive\s+me\s+(a|an|some)\b", re.IGNORECASE),
    # Soft request ("a/an/some X that does Y" — works whenever a
    # buildable-artifact noun phrase appears).
    re.compile(
        r"\b(a|an)\s+(tool|script|program|package|library|cli|"
        r"thing|converter|app|application|utility|helper)\b",
        re.IGNORECASE,
    ),
)


# Verification-expectation triggers — user wants evidence of working.
_VERIFICATION_TRIGGERS: tuple[re.Pattern[str], ...] = (
    # Imperative + pronoun + works ("prove it works", "show me it works").
    re.compile(
        r"\b(prove|show|verify|test|check)\s+"
        r"(it|that|this|me\s+it|me\s+that)\b.*\bworks?\b",
        re.IGNORECASE,
    ),
    # Verb + ANY phrase + works (catches "verify X works",
    # "check that the converter works").
    re.compile(
        r"\b(prove|show|verify|test|check|demonstrate)\b.*\bworks?\b",
        re.IGNORECASE,
    ),
    # "run an example" / "run a small example".
    re.compile(
        r"\b(run|do)\s+(a|an|some)?\s*(small\s+)?example\b",
        re.IGNORECASE,
    ),
    # "make sure it works".
    re.compile(
        r"\bmake\s+sure\s+(it|that|this|the\s+\w+)\s+works?\b",
        re.IGNORECASE,
    ),
    # "I want to see/know it works".
    re.compile(
        r"\bi\s+want\s+to\s+(see|know)\s+(it|that|this)\s+works?\b",
        re.IGNORECASE,
    ),
    # "I can verify works".
    re.compile(
        r"\bi\s+can\s+(verify|check|see|test)\b.*\bworks?\b",
        re.IGNORECASE,
    ),
    # "with tests" / "includes tests".
    re.compile(
        r"\b(includes?|with)\s+tests?\b", re.IGNORECASE,
    ),
    # "don't come back until".
    re.compile(
        r"\bdon'?t\s+come\s+back\s+until\b", re.IGNORECASE,
    ),
    # "and check it works" / "and test it".
    re.compile(
        r"\band\s+(check|test|verify)\s+(it|that|this)\b",
        re.IGNORECASE,
    ),
    # "I can verify" alone (the user wants verifiability).
    re.compile(r"\bi\s+can\s+(verify|check|test)\b", re.IGNORECASE),
)


# Anti-triggers — definitely NOT build-with-verification.
_ANTI_TRIGGERS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bwhat\s+does\s+.+?\s+do\b", re.IGNORECASE),
    re.compile(r"\bhow\s+does\s+.+?\s+work\b", re.IGNORECASE),
    # "show me how X works" is pure-question.
    re.compile(r"\bshow\s+me\s+how\b", re.IGNORECASE),
    re.compile(
        r"\b(rename|fix\s+the\s+typo|update\s+the\s+comment)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bexplain\b", re.IGNORECASE),
    re.compile(r"\bwhy\s+(did|do|does)\b", re.IGNORECASE),
)


# Recognised classification outputs (AC.CLE.HOOK.1 enumeration).
INTENT_BUILD_WITH_VERIFICATION = "build-with-verification"
INTENT_PURE_QUESTION = "pure-question"
INTENT_TINY_TWEAK = "tiny-tweak"
INTENT_AMBIGUOUS = "ambiguous"


def _any_match(prompt: str, patterns: Iterable[re.Pattern[str]]) -> bool:
    return any(p.search(prompt) for p in patterns)


def classify_intent(prompt: str) -> str:
    """Classify a user prompt's intent.

    Returns one of:

      - ``"build-with-verification"`` — soft phrasing for a buildable
        artifact + evidence-it-works expectation.
      - ``"pure-question"`` — explanation / how-does-X-work / why-did-Y
        (anti-trigger fires, no build trigger).
      - ``"ambiguous"`` — build trigger fires without verification, or
        no triggers fire at all. The persona uses its own judgment
        on these.

    ``"tiny-tweak"`` is reserved for a future extension (the original
    pos3-local hook enumerated it for completeness; current logic
    folds tiny-tweak signals into the anti-trigger / ambiguous paths
    rather than emitting a distinct class).

    The classifier is deterministic, stdlib-only, and runs in <5ms on
    typical prompts (matching pos3-local pre-promotion behaviour).
    """
    if not prompt or not prompt.strip():
        return INTENT_AMBIGUOUS

    has_build = _any_match(prompt, _BUILD_TRIGGERS)
    has_verification = _any_match(prompt, _VERIFICATION_TRIGGERS)
    has_anti = _any_match(prompt, _ANTI_TRIGGERS)

    if has_anti and not has_build:
        return INTENT_PURE_QUESTION
    if has_build and has_verification:
        return INTENT_BUILD_WITH_VERIFICATION
    if has_build and not has_verification:
        # User asked to build but didn't ask for proof. The pos3-local
        # classifier marked this ambiguous to let the persona judge.
        # Preserved verbatim here — closed-loop forcing only fires on
        # the high-confidence "build + verification" join.
        return INTENT_AMBIGUOUS
    return INTENT_AMBIGUOUS


# ---- additionalContext injection ---------------------------------------

# CANONICAL_FORM_TEMPLATE — the additionalContext body injected when
# the classifier fires build-with-verification. Per amendment #144
# Scope B (TG 11881 ruling), the body MUST:
#
#   - reference the ``handsoff-loop`` SKILL by name so Claude Code's
#     SKILL matcher can fire on the injected context;
#   - state that auto-load is the primary mechanism;
#   - NOT prescribe typing ``/handsoff-loop`` verbatim into the
#     persona's response (slash commands are persona-internal
#     mechanism, NOT user-facing output);
#   - hard-forbid inline build on build-with-verification intent
#     (the structural backstop the persona prompt's softer prose
#     was insufficient to enforce).
CANONICAL_FORM_TEMPLATE = """[INTENT-CLASSIFICATION FROM USER-PROMPT-SUBMIT HOOK]

The user's prompt has been classified as BUILD-WITH-VERIFICATION intent — the user wants a buildable artifact AND wants evidence it works. Per the persona's translate-inbound discipline, the canonical imperative form of this request is:

  *"Build me a tool that does X. Don't come back until it works and you've tested it. Go."*

The persona's FIRST move on this turn must be to engage the closed-loop build methodology (the `handsoff-loop` SKILL — see `.claude/skills/handsoff-loop/SKILL.md`). Claude Code's standard SKILL auto-load mechanism should match this prompt against the SKILL's description and inject it into the model's context automatically; no slash command typing is required. The persona just FOLLOWS the SKILL's procedure (intake -> approval -> decompose -> dispatch -> judge). The slash command is available as a backup invocation if auto-load doesn't fire; otherwise it's redundant + leaks to the user's chat view.

DO NOT build inline. DO NOT negotiate the intent classification. Inline-build on build-with-verification intent is a Lens 2 violation per the persona's operational rules.

If the SKILL is not available in this workspace (no `.claude/skills/handsoff-loop/` symlink or canonical path), surface that as a halt with the missing-SKILL diagnostic rather than defaulting to inline build.

[END INTENT-CLASSIFICATION]
"""


def build_hook_output(intent: str) -> dict | None:
    """Build the Claude Code hookSpecificOutput JSON for a classified
    intent, or ``None`` when no injection is warranted.

    Pure function — testable without stdio. The CLI entry point (
    :func:`cli_intent_classifier`) wraps this with JSON envelope IO.
    """
    if intent != INTENT_BUILD_WITH_VERIFICATION:
        return None
    return {
        "hookEventName": "UserPromptSubmit",
        "hookSpecificOutput": {
            "additionalContext": CANONICAL_FORM_TEMPLATE,
        },
    }


# ---- CLI entry point ----------------------------------------------------


def cli_intent_classifier() -> int:
    """Read Claude Code's UserPromptSubmit JSON envelope from stdin,
    classify the embedded prompt, and emit ``additionalContext`` to
    stdout when the classification is build-with-verification.

    Always exits 0. A non-zero exit on a UserPromptSubmit hook blocks
    Claude Code's prompt-submit fan-out; the hook is observe-+-enrich,
    never deny — malformed input, missing fields, or any exception
    routes to silent pass-through (no stdout output).

    Mirrors :func:`cli_user_prompt_submit` shape:

      - stdin envelope dict with a ``"prompt"`` field;
      - empty / non-JSON / non-dict stdin -> empty stdout, exit 0;
      - missing prompt field or non-string value -> empty stdout, exit 0;
      - non-build-with-verification classification -> empty stdout, exit 0;
      - build-with-verification classification -> JSON
        ``hookSpecificOutput`` to stdout with ``additionalContext``
        body.
    """
    try:
        raw = sys.stdin.read()
    except Exception:  # noqa: BLE001 — fail-soft
        return 0
    if not raw.strip():
        return 0
    try:
        envelope = json.loads(raw)
    except (ValueError, TypeError):
        return 0
    if not isinstance(envelope, dict):
        return 0

    # Claude Code's UserPromptSubmit hook payload includes the user's
    # prompt under ``"prompt"``. We tolerate three legacy variants
    # (``"user_prompt"``, ``"input"``, ``"text"``) for forward-compat
    # with potential schema changes; the canonical field is ``prompt``.
    prompt = (
        envelope.get("prompt")
        or envelope.get("user_prompt")
        or envelope.get("input")
        or envelope.get("text")
        or ""
    )
    if not isinstance(prompt, str):
        prompt = str(prompt)

    intent = classify_intent(prompt)
    output = build_hook_output(intent)
    if output is None:
        return 0
    sys.stdout.write(json.dumps(output))
    sys.stdout.write("\n")
    return 0


def build_persona_intent_classifier_inner_hook(loam_root) -> dict:
    """Return the inner-hook dict the UserPromptSubmit envelope
    composes against the persona's ``intent-classifier`` subcommand.

    Wired into the UserPromptSubmit chain via the multi-contributor
    generalisation of :func:`merge_user_prompt_submit` (amendment
    #144 Scope A) as an ``extra_inner_hooks`` entry alongside the
    persona's existing ``user-prompt-submit`` contributor.

    Timeout 5s — bounded by the regex-only classifier (<5ms typical
    on a stdlib re.search loop); the 5s ceiling mirrors the persona's
    other inner-hook entries to keep envelope-level uniformity.
    """
    from pathlib import Path  # local import — keeps the module body
    # importable without forcing pathlib at the top in callers that
    # only consume classify_intent / CANONICAL_FORM_TEMPLATE.
    loam_root = Path(loam_root)
    python = loam_root / ".venv" / "bin" / "python"
    return {
        "type": "command",
        "command": (
            f"{python} -m loam.primary_persona.cli intent-classifier"
        ),
        "async": False,
        "timeout": 5,
    }


if __name__ == "__main__":  # pragma: no cover — module-level entry-point
    sys.exit(cli_intent_classifier())

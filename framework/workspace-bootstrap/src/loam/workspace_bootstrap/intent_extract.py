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

"""The LLM intent-extraction SEAM (AC.INTENT.*).

The intake's deterministic regex distillation (``translate_in_intake.
_distill_intent``) drove the acceptance-smoke EXTRACTION layer clean over six
hardening rounds, but the smoke's ``four-step-loop-ran`` dimension stayed PARTIAL
across all three variants: novel free-form phrasing keeps producing extraction
misses that a regex cannot generalise, and leg 4 (adjust from the answer) needs
a richer read of what the user said than a pattern match gives.

This seam replaces the regex distillation as the PRIMARY path with a SCOPED,
spawn-isolated, FAIL-SOFT model call that reads the user's RAW reply and extracts
(a) the real intent and (b) a slightly-DEEPER inferred end-intent than the literal
ask — while keeping the regex distillation as the FALLBACK so onboarding NEVER
breaks or hangs when the model call fails.

**Design (mirrors the sealed ``deep_role_research`` seam exactly):**

  - ``IntentExtractor`` Protocol — the clean injectable boundary the intake
    composes on.
  - ``DisabledIntentExtractor`` — the DEFAULT. It always DECLINES (raises
    ``IntentExtractUnavailableError``) so the baseline distillation path stays
    PURE REGEX: no spawn, no network, the existing distillation suite unaffected.
    The model call is opt-in at the seam (D-SEAM-1).
  - ``ClaudeIntentExtractor`` — the real provider. ONE bounded ``claude -p`` call
    through the MANDATED ``loam_spawn_isolation.spawn_isolated_claude`` primitive
    (``--strict-mcp-config`` + empty ``mcpServers`` + ANTHROPIC_API_KEY /
    TELEGRAM_BOT_TOKEN scrubbed env), a HARD timeout, ``{"result": ...}`` envelope
    parse. On ANY failure it raises ``IntentExtractUnavailableError`` — NEVER
    propagates (D-SEAM-2/.3). No Anthropic SDK, no API key
    (``feedback_no_anthropic_api_key``).
  - ``register_intent_extractor`` / ``reset_intent_extractor`` — the swap seam the
    smoke runner / production CLI use to install the real extractor without the
    baseline importing it.

**Fail-soft is the load-bearing invariant (AC.INTENT.2).** The caller
(``translate_in_intake._distill_intent_via_seam``) catches
``IntentExtractUnavailableError`` and falls back to the deterministic regex
``_distill_intent``. ONE extraction per distillation, bounded. The model call is
a quality LIFT layered ON TOP of a path that already works — never a dependency.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol

# The default model for the one bounded extraction call (subscription-routed via
# claude -p; feedback_no_anthropic_api_key). Sonnet is the loam default tier.
DEFAULT_INTENT_MODEL = "sonnet"

# The hard wall-clock ceiling for the synchronous extraction dispatch. On timeout
# the extractor raises IntentExtractUnavailableError and the caller falls back to
# the regex distillation rather than hanging (AC.INTENT.2 fail-soft, bounded).
DEFAULT_INTENT_TIMEOUT_SECONDS = 45.0


@dataclass
class ExtractedIntent:
    """The model's read of a free-form stop/start reply (AC.INTENT.1).

    ``intent`` is the SHORT distilled intent phrase (what the user actually wants
    offloaded/enabled) — the drop-in replacement for the regex distillation's
    output. ``deeper_end_intent`` is the slightly-DEEPER inferred end-intent (one
    step beyond the literal ask — the four-step loop's infer leg, richer than the
    literal phrasing). ``adjustment`` is an optional one-line read of any detail
    or doubt the reply added that the leg-4 close should reflect (AC.INTENT.4);
    it is None when the reply added nothing to adjust from.
    """

    intent: str
    deeper_end_intent: str = ""
    adjustment: str = ""

    @property
    def is_usable(self) -> bool:
        """A non-empty intent phrase is the minimum usable extraction."""
        return bool(self.intent and self.intent.strip())


class IntentExtractUnavailableError(Exception):
    """The bounded extraction primitive could not produce a usable result.

    Raised by an ``IntentExtractor`` when the ``claude`` binary / spawn-isolation
    primitive is absent, the dispatch fails, it times out, the output is
    unparseable, or the extraction is empty. The intake catches it and falls back
    to the deterministic regex distillation — it NEVER propagates out of the
    distillation path (AC.INTENT.2 fail-soft)."""


class IntentExtractor(Protocol):
    """The clean injectable boundary the intake composes on (AC.INTENT.1).

    Input: the user's RAW stop/start reply (and, for the adjustment read, the
    inferred-intent context loam proposed). Output: an :class:`ExtractedIntent`.
    Production registers :class:`ClaudeIntentExtractor`; the baseline default is
    :class:`DisabledIntentExtractor` so the path stays pure regex until a real
    extractor is installed.
    """

    def extract(
        self, raw_reply: str, *, prior_proposal: str = ""
    ) -> ExtractedIntent:  # pragma: no cover - structural
        ...


class DisabledIntentExtractor:
    """The DEFAULT baseline extractor — always declines (D-SEAM-1).

    It performs NO spawn and NO network call; it raises
    ``IntentExtractUnavailableError`` immediately so the distillation path falls
    back to the deterministic regex ``_distill_intent``. This keeps the baseline
    featherlight + offline-clean and leaves the existing distillation suite
    byte-identical (the model call is opt-in, installed explicitly by the smoke
    runner / production CLI via :func:`register_intent_extractor`)."""

    def extract(self, raw_reply: str, *, prior_proposal: str = "") -> ExtractedIntent:
        raise IntentExtractUnavailableError(
            "intent extraction disabled by default (baseline stays pure-regex); "
            "register a real extractor to enable the LLM path"
        )


# The prompt the bounded extraction subagent runs. It is told to return ONLY a
# JSON object on the three fields — short intent / deeper end-intent / a one-line
# adjustment read — so the parse is deterministic. It is a SINGLE scoped call (no
# tool use, no loop): the user's reply in, a structured read out.
_EXTRACT_PROMPT = """\
You are loam's intent-extraction step in a first-touch onboarding conversation \
with a non-technical professional. The user was asked for ONE thing they'd love \
to STOP or START doing. Read their RAW reply and extract a structured read.

Their reply:
\"\"\"{raw_reply}\"\"\"

{prior_block}\
Return ONLY a JSON object (no prose, no code fence) with EXACTLY these keys:
  - "intent": a SHORT phrase (<= 12 words) naming the concrete thing they want \
offloaded or enabled, in THEIR words (e.g. "writing listing descriptions"). No \
leading verb like "stop"/"start" — just the thing.
  - "deeper_end_intent": one short clause naming the slightly-deeper end they're \
really after (one step beyond the literal ask), e.g. "get their evenings back".
  - "adjustment": if their reply added a concrete DETAIL worth reflecting back, \
or raised a DOUBT/QUESTION about whether loam can actually do it, a ONE-LINE \
honest read of that detail/doubt loam should acknowledge; otherwise "".

Be honest in "adjustment": if they doubt a capability, name the doubt — do NOT \
invent a capability claim.
"""

_PRIOR_BLOCK = (
    "Earlier loam proposed this back to them and they were responding to it:\n"
    "\"\"\"{prior_proposal}\"\"\"\n\n"
)


class ClaudeIntentExtractor:
    """The real intent-extractor — ONE bounded ``claude -p`` call, spawn-isolated.

    Mirrors the sealed ``deep_role_research_provider.ClaudeSubagentResearchSource``
    dispatch verbatim: LAZY-imports ``loam_spawn_isolation`` inside ``extract``
    (it is a separate package, not a workspace-bootstrap dependency), dispatches a
    single scoped ``claude -p`` with a HARD timeout through the MANDATED
    ``spawn_isolated_claude`` (``--strict-mcp-config`` + empty mcpServers +
    ANTHROPIC_API_KEY / TELEGRAM_BOT_TOKEN scrubbed), parses the ``{"result": ...}``
    envelope, and raises :class:`IntentExtractUnavailableError` on ANY failure so
    the caller degrades to the regex distillation (AC.INTENT.2/.3).

    No Anthropic SDK, no API key — subscription-only via ``claude -p``
    (``feedback_no_anthropic_api_key``)."""

    def __init__(
        self,
        *,
        model: str = DEFAULT_INTENT_MODEL,
        timeout_seconds: float = DEFAULT_INTENT_TIMEOUT_SECONDS,
    ) -> None:
        self._model = model
        self._timeout_seconds = timeout_seconds

    def extract(self, raw_reply: str, *, prior_proposal: str = "") -> ExtractedIntent:
        if not (raw_reply or "").strip():
            raise IntentExtractUnavailableError("empty reply — nothing to extract")
        try:
            from loam_spawn_isolation import spawn_isolated_claude
        except ImportError as exc:  # pragma: no cover - environmental
            raise IntentExtractUnavailableError(
                f"loam_spawn_isolation not importable ({exc}); the bounded "
                "intent-extract call cannot be spawned isolated — degrading to "
                "the regex distillation."
            ) from exc

        prior_block = (
            _PRIOR_BLOCK.format(prior_proposal=prior_proposal)
            if (prior_proposal or "").strip()
            else ""
        )
        prompt = _EXTRACT_PROMPT.format(
            raw_reply=raw_reply.strip(), prior_block=prior_block
        )
        argv = [
            "claude",
            "-p",
            prompt,
            "--model",
            self._model,
            "--output-format",
            "json",
            "--permission-mode",
            "bypassPermissions",
        ]
        try:
            proc = spawn_isolated_claude(
                argv,
                capture_output=True,
                text=True,
                timeout=self._timeout_seconds,
            )
        except Exception as exc:  # noqa: BLE001 — any spawn/timeout failure -> fallback
            raise IntentExtractUnavailableError(
                f"intent-extract dispatch failed: {exc}"
            ) from exc

        if proc.returncode != 0:
            raise IntentExtractUnavailableError(
                f"intent-extract subagent exited {proc.returncode}: "
                f"{(proc.stderr or '')[:300]}"
            )
        raw = (proc.stdout or "").strip()
        try:
            envelope = json.loads(raw)
        except (json.JSONDecodeError, ValueError) as exc:
            raise IntentExtractUnavailableError(
                f"intent-extract stdout not a claude -p JSON envelope: {exc}"
            ) from exc
        if not isinstance(envelope, dict):
            raise IntentExtractUnavailableError(
                "intent-extract envelope not an object"
            )
        result_text = envelope.get("result") or ""
        return _parse_extraction(result_text)


def _parse_extraction(result_text: str) -> ExtractedIntent:
    """Parse the subagent's JSON result into an :class:`ExtractedIntent`.

    The subagent is told to return ONLY a JSON object on the three fields. We
    tolerate a leading/trailing code fence the model sometimes adds. Raise
    ``IntentExtractUnavailableError`` on anything that does not yield a usable
    (non-empty) intent so the caller falls back to the regex distillation."""
    text = (result_text or "").strip()
    if text.startswith("```"):
        # Strip a ```json … ``` fence the model occasionally wraps the object in.
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise IntentExtractUnavailableError(
            f"intent-extract result not JSON: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise IntentExtractUnavailableError("intent-extract result not an object")
    extracted = ExtractedIntent(
        intent=str(payload.get("intent", "") or "").strip(),
        deeper_end_intent=str(payload.get("deeper_end_intent", "") or "").strip(),
        adjustment=str(payload.get("adjustment", "") or "").strip(),
    )
    if not extracted.is_usable:
        raise IntentExtractUnavailableError(
            "intent-extract produced no usable intent phrase"
        )
    return extracted


# The default extractor the baseline intake resolves at call time. The smoke
# runner / production CLI swap it for a real ClaudeIntentExtractor; the baseline
# default DECLINES so the distillation path stays pure regex (D-SEAM-1).
_DEFAULT_EXTRACTOR: IntentExtractor = DisabledIntentExtractor()


def default_intent_extractor() -> IntentExtractor:
    """The extractor the baseline intake composes on — resolved at CALL time so a
    consumer can register a real extractor without the baseline importing it
    (graceful degradation: the seam is present, the model call is opt-in)."""
    return _DEFAULT_EXTRACTOR


def register_intent_extractor(extractor: IntentExtractor) -> None:
    """Swap the default extractor the baseline intake resolves at call time.

    The seam the smoke runner / production CLI fill to install the real
    ``ClaudeIntentExtractor`` WITHOUT the baseline importing it and WITHOUT
    touching the intake's distillation/gating logic. Fail-soft is unaffected — the
    caller still catches ``IntentExtractUnavailableError`` and falls back to the
    regex distillation, whichever extractor is registered."""
    global _DEFAULT_EXTRACTOR
    _DEFAULT_EXTRACTOR = extractor


def reset_intent_extractor() -> None:
    """Restore the baseline disabled (pure-regex) extractor — test-hygiene seam so
    a test that registers a real/fake extractor can undo it without leaking module
    state across the suite."""
    global _DEFAULT_EXTRACTOR
    _DEFAULT_EXTRACTOR = DisabledIntentExtractor()

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

"""The Codex adversarial-critic leg — a second critic on a DIFFERENT model
family (WS-D2), landed as the WS-D1 registry's first non-default entry.

The default critic is an isolated Claude spawn (``spawn.run_isolated_critic``).
A same-family critic shares the writer's blind spots; a critic on a different
model family (OpenAI Codex) de-correlates them. This leg lets the ``CRITIC``
role run BOTH — Claude AND Codex, in parallel — so their findings de-correlate
(the objective's ``model-rationale``: *different model family de-correlates
reviewer blind spots vs a same-family critic*).

Shape (D-CDX.1): this leg is a plain text :data:`~adversarial_review.critic.ModelFn`
(``prompt -> str | None``). It slots into WS-D1's ``run_critic_registry``, which
calls it for BOTH the DERIVE phase (free-form spec) and the DIFF phase
(``FINDING…END`` blocks) of the UNCHANGED two-phase ``run_critic`` — reusing the
sealed critic primitive rather than re-implementing a parallel single-phase
codex pass.

Auth (D2, owner-ratified): ChatGPT sign-in, operator-triggered ONLY — NOT an
unattended API key. Sign-in is file-based (``~/.codex/…``), so the child env is
``os.environ`` with the sensitive keys DELETED (D-CDX.3), never a minimal
whitelist that would strip the ``HOME``/``PATH`` the credential lookup needs.

Fail-soft (D-CDX.5): ``codex`` absent, auth dead, non-zero exit, timeout, or
empty output ⇒ the leg returns ``None``. WS-D1's ``run_critic_registry`` records
that as a MISSING leg and the review proceeds on the remaining legs — a named
missing leg, never a false clean bill.

The ``--output-schema`` flag the plan hint named is DROPPED (D-CDX.2): a fixed
findings schema is incompatible with the two-phase reuse (DERIVE must emit a
free-form spec, and one ``ModelFn`` serves both phases). ``--sandbox read-only``
is KEPT and required (a critic reads and emits, never mutates).

Per ODD §2.5: :func:`codex_env` -> AC.CDX.3; :func:`build_codex_argv` /
:func:`_extract_text` / :func:`run_codex_critic` -> AC.CDX.1 (+ AC.CDX.2 fail-soft
+ AC.CDX.3 scrubbed spawn); :func:`codex_leg` / :func:`codex_critic_registry` ->
AC.CDX.1/2 (the ``(claude, codex)`` parallel-critic registry).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from functools import partial
from typing import Dict, List, Mapping, Optional

from .critic import ModelFn
from .registry import DEFAULT_LEG_NAME, ModelLeg, ModelRoleRegistry, Role

# The name every finding this leg produces is tagged with (Lens 0 — the
# review says which model found which flaw), and the name the render layer
# surfaces when the leg is missing (AC.CDX.2).
CODEX_LEG_NAME = "codex"

DEFAULT_CODEX_BIN = "codex"
# Codex reviews a whole artifact through the two-phase critic; a generous
# ceiling since a single call is one derive/diff phase, not a whole session.
DEFAULT_TIMEOUT_S = 300

# Sensitive env keys scrubbed from the codex child by DELETION (D-CDX.3 /
# AC.CDX.3). ``OPENAI_API_KEY`` is scrubbed under D2's ratified sign-in-only
# auth so a metered key can NEVER silently bill via this leg (the print
# -clients' scrub exists to prevent exactly that silent billed fall-through);
# the Anthropic keys have no business in a non-claude subprocess.
SCRUBBED_ENV_KEYS = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
)


def codex_env(
    *,
    allow_openai_key: bool = False,
    base_env: Optional[Mapping[str, str]] = None,
) -> Dict[str, str]:
    """Build the codex child env by DELETING sensitive keys (AC.CDX.3).

    Copies ``base_env`` (default ``os.environ``) and removes
    :data:`SCRUBBED_ENV_KEYS`, so ``HOME``/``PATH`` (which the file-based
    ChatGPT sign-in credential lookup needs) survive while any inherited API
    key does not. ``allow_openai_key=True`` relaxes the ``OPENAI_API_KEY``
    scrub for THIS subprocess only — D2's "if the metered-key variant is ever
    enabled" clause — never globally; the default is sign-in-only.
    """
    env: Dict[str, str] = dict(os.environ if base_env is None else base_env)
    for key in SCRUBBED_ENV_KEYS:
        if key == "OPENAI_API_KEY" and allow_openai_key:
            continue
        env.pop(key, None)
    return env


def build_codex_argv(prompt: str, *, codex_bin: str = DEFAULT_CODEX_BIN) -> List[str]:
    """The ``codex exec`` argv the leg spawns (AC.CDX.1).

    ``--sandbox read-only`` is REQUIRED (a critic reads and emits, never
    mutates — D-CDX.2). ``--json`` gives a parseable event stream; the
    ``--output-schema`` hint is intentionally dropped (D-CDX.2 — a fixed
    findings schema breaks the DERIVE phase, and the downstream
    ``parse_findings`` regex is format-agnostic). The prompt is the positional
    task; the child never reads stdin (``stdin=DEVNULL`` at spawn).
    """
    return [
        codex_bin,
        "exec",
        "--json",
        "--sandbox",
        "read-only",
        prompt,
    ]


# Event-stream keys, in priority order, under which a codex ``--json`` line may
# carry model text. Tolerant by construction: whatever key the live binary
# uses, one of these (or the raw fallback) recovers the text.
_TEXT_KEYS = ("text", "message", "content", "delta", "output")
_NESTED_KEYS = ("msg", "message", "item", "data", "payload")


def _text_from_event(obj: object) -> Optional[str]:
    """Best-effort: pull model text out of one parsed ``--json`` event."""
    if isinstance(obj, str):
        return obj if obj.strip() else None
    if isinstance(obj, dict):
        for key in _TEXT_KEYS:
            val = obj.get(key)
            if isinstance(val, str) and val.strip():
                return val
        for key in _NESTED_KEYS:
            nested = obj.get(key)
            if isinstance(nested, (dict, str)):
                got = _text_from_event(nested)
                if got:
                    return got
    return None


def _extract_text(raw: str) -> str:
    """Extract the model text from codex stdout, tolerantly (AC.CDX.1).

    ``codex exec --json`` emits JSONL events; collect the text carried by each
    parseable event and join it. If NOTHING parses as a text-bearing event (a
    format change, a plain-text build, log noise), fall back to the raw
    stdout — the downstream ``parse_findings`` regex scans for ``FINDING…END``
    anywhere, so a raw fallback still recovers findings. Mirrors
    ``spawn.py:_unwrap_json``'s tolerant posture.
    """
    collected: List[str] = []
    saw_json = False
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        saw_json = True
        got = _text_from_event(obj)
        if got:
            collected.append(got)
    if collected:
        return "\n".join(collected)
    # Not JSONL, or JSONL carried no recognizable text — hand back the raw
    # stdout so the format-agnostic FINDING…END parse still gets a chance.
    if not saw_json:
        return raw.strip()
    return raw.strip()


def _resolve_bin(codex_bin: str) -> Optional[str]:
    """Resolve the codex binary, or ``None`` if it is not runnable (AC.CDX.2).

    ``shutil.which`` for a bare name; an absolute/relative path is accepted
    only if it exists and is executable. ``None`` ⇒ the leg is unavailable and
    ``run_codex_critic`` fails soft.
    """
    found = shutil.which(codex_bin)
    if found:
        return found
    if os.path.sep in codex_bin and os.access(codex_bin, os.X_OK):
        return codex_bin
    return None


def run_codex_critic(
    prompt: str,
    *,
    codex_bin: str = DEFAULT_CODEX_BIN,
    timeout: int = DEFAULT_TIMEOUT_S,
    allow_openai_key: bool = False,
) -> Optional[str]:
    """Run one ``codex exec`` critic phase and return the text (AC.CDX.1).

    A plain ``ModelFn`` (``prompt -> str | None``): WS-D1's
    ``run_critic_registry`` calls it for both the DERIVE and DIFF phases.
    Fail-soft (AC.CDX.2, D-CDX.5): ``codex`` absent, spawn failure, timeout,
    non-zero exit, or empty output ⇒ ``None`` (the caller records a MISSING
    leg — never a false clean bill). Spawns with the scrubbed env (AC.CDX.3)
    and ``stdin=DEVNULL`` (the child never blocks reading stdin).
    """
    exe = _resolve_bin(codex_bin)
    if exe is None:
        return None
    argv = build_codex_argv(prompt, codex_bin=exe)
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
            env=codex_env(allow_openai_key=allow_openai_key),
            check=False,
        )
    except Exception:  # noqa: BLE001 — spawn/timeout is fail-soft
        return None
    if getattr(proc, "returncode", 1) != 0:
        return None
    stdout = getattr(proc, "stdout", None)
    if not isinstance(stdout, str) or not stdout.strip():
        return None
    return _extract_text(stdout)


def codex_leg(*, allow_openai_key: bool = False) -> ModelLeg:
    """The Codex ``CRITIC`` leg (AC.CDX.1) — ``ModelLeg("codex", run_codex_critic)``.

    ``allow_openai_key`` (default ``False``) is bound into the leg's ``fn`` so
    the metered-key relaxation, if ever enabled, stays scoped to this leg.
    """
    fn: ModelFn = (
        partial(run_codex_critic, allow_openai_key=True)
        if allow_openai_key
        else run_codex_critic
    )
    return ModelLeg(CODEX_LEG_NAME, fn)


def codex_critic_registry(
    *,
    include_claude: bool = True,
    allow_openai_key: bool = False,
) -> ModelRoleRegistry:
    """The registry that puts a PARALLEL ``(claude, codex)`` critic on the CRITIC role.

    This is WS-D1's registry's first non-default entry (AC.CDX.1). With
    ``include_claude=True`` (the default, the production shape) the CRITIC role
    resolves to the default Claude leg (``fn=None`` ⇒ isolated real spawn) AND
    the Codex leg, run in parallel — author=Claude / adversary=Codex, findings
    de-correlated and each tagged with its producing model. ``include_claude=
    False`` yields a codex-only CRITIC (used to isolate the leg in the n=1
    calibration proof). ``WRITER``/``JUDGE`` fall back to the default leg.
    """
    legs: List[ModelLeg] = []
    if include_claude:
        legs.append(ModelLeg(DEFAULT_LEG_NAME))
    legs.append(codex_leg(allow_openai_key=allow_openai_key))
    return ModelRoleRegistry(legs={Role.CRITIC: tuple(legs)})

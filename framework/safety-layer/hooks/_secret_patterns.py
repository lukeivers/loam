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

"""Shared secret-pattern data + workspace-additions loader.

Two pattern families:

* **CONTENT patterns** (the 14-pattern ECC floor) — match against
  content that appears in a Bash command argument or in an
  Edit/Write/MultiEdit tool input. Each pattern matches a
  well-known credential token shape (sk-..., ghp_..., AKIA..., etc.).
* **FILE patterns** (migrated from
  ``plugins/dev-sdlc/hooks/bash_guard.py`` per D-SECHK.OVERLAP
  partial-absorb) — match against a path token that names a
  secret-class file (``.env``, ``*.pem``, ``id_rsa``, etc.) being
  staged / committed / stashed via ``git``.

Workspace-additions loader: callers may extend the CONTENT pattern
set per workspace via ``<workspace>/.loam/secret-patterns.yaml``
(additive only — cannot remove framework-floor patterns). Schema:

    patterns:
      - name: workspace-internal-token
        regex: "internal-key-[A-Z0-9]{16}"

YAML parse failures fail-open (return the floor only); the hook
records the failure to its NDJSON log.

Stdlib only: ``re``, ``pathlib``. YAML parse uses a minimal
hand-rolled parser to avoid adding a dependency to a hook script
that the runtime loads on every PreToolUse event.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SecretPattern:
    """One named secret-pattern entry.

    ``name`` is the diagnostic-facing label (surfaced in
    ``permissionDecisionReason``). ``regex`` is the compiled pattern.
    """

    name: str
    regex: re.Pattern[str]


# ---------------------------------------------------------------------
# CONTENT patterns — the 14-pattern ECC floor
# ---------------------------------------------------------------------
#
# Sourced from the ECC (everything-claude-code) hooks bundle (per the
# Wave 1 ECC absorption master plan §4). The patterns target
# well-known credential token shapes; false-positive direction is
# deny (per D-SECHK.FAIL-OPEN's belt-not-suspenders framing).

_CONTENT_PATTERN_DEFS: tuple[tuple[str, str], ...] = (
    # Anthropic API keys
    ("anthropic-api-key", r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"),
    # OpenAI API keys (legacy + project-scoped)
    ("openai-api-key", r"\bsk-[A-Za-z0-9]{20,}\b"),
    ("openai-project-key", r"\bsk-proj-[A-Za-z0-9_-]{20,}\b"),
    # GitHub personal access tokens
    ("github-pat", r"\bghp_[A-Za-z0-9]{36,}\b"),
    ("github-oauth", r"\bgho_[A-Za-z0-9]{36,}\b"),
    ("github-user-server", r"\bghu_[A-Za-z0-9]{36,}\b"),
    ("github-server-server", r"\bghs_[A-Za-z0-9]{36,}\b"),
    ("github-refresh", r"\bghr_[A-Za-z0-9]{36,}\b"),
    # AWS access keys
    ("aws-access-key", r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    # Google API keys
    ("google-api-key", r"\bAIza[A-Za-z0-9_-]{35}\b"),
    # Slack tokens
    ("slack-token", r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    # Stripe live keys
    ("stripe-live-secret", r"\bsk_live_[A-Za-z0-9]{20,}\b"),
    ("stripe-live-publishable", r"\bpk_live_[A-Za-z0-9]{20,}\b"),
    # Private-key PEM headers
    (
        "private-key-pem",
        r"-----BEGIN (?:RSA |OPENSSH |EC |DSA |ENCRYPTED |PRIVATE )?PRIVATE KEY-----",
    ),
)


def _compile_content_patterns() -> tuple[SecretPattern, ...]:
    return tuple(
        SecretPattern(name=name, regex=re.compile(rx))
        for name, rx in _CONTENT_PATTERN_DEFS
    )


CONTENT_PATTERNS: tuple[SecretPattern, ...] = _compile_content_patterns()


# ---------------------------------------------------------------------
# FILE patterns — migrated from plugins/dev-sdlc/hooks/bash_guard.py
# (D-SECHK.OVERLAP partial-absorb)
# ---------------------------------------------------------------------
#
# These match a token in a `git add | commit | stash` command that
# names a secret-class FILE (the credential file itself, not the
# credential content inside it). Behavior parity with the prior
# bash_guard B2 surface is required (AC.SECHK.B2-MIGRATION-1).
#
# The carve-out (``.env-example``, ``.env.sample``, etc.) is preserved
# verbatim from bash_guard so that documentation patterns continue to
# pass through.

_SECRET_FILE_PATTERN_DEFS: tuple[str, ...] = (
    # .env, .env.production, .env.local — but NOT .env-example (carved
    # out below).
    r"(?:^|[\s/])\.env(?:\.[A-Za-z0-9_-]+)?(?=$|\s|[^A-Za-z0-9_.-])",
    # credentials.json
    r"(?:^|[\s/])credentials\.json(?=$|\s|[^A-Za-z0-9_.-])",
    # .aws/credentials
    r"(?:^|[\s/])\.aws/credentials(?=$|\s|[^A-Za-z0-9_.-])",
    # *.pem, *.key — matched as suffix only.
    r"(?:^|[\s/])[\S]+\.pem(?=$|\s|[^A-Za-z0-9_.-])",
    r"(?:^|[\s/])[\S]+\.key(?=$|\s|[^A-Za-z0-9_.-])",
    # SSH private key files
    r"(?:^|[\s/])id_(?:rsa|ed25519|ecdsa|dsa)(?=$|\s|[^A-Za-z0-9_.-])",
    # .npmrc / .pypirc — credential-bearing configs.
    r"(?:^|[\s/])\.npmrc(?=$|\s|[^A-Za-z0-9_.-])",
    r"(?:^|[\s/])\.pypirc(?=$|\s|[^A-Za-z0-9_.-])",
)


_SECRET_FILE_CARVE_OUT_SUFFIXES: tuple[str, ...] = (
    "-example",
    ".example",
    "-sample",
    ".sample",
    "-template",
    ".template",
)


_GIT_STAGING_SUBCOMMANDS: tuple[str, ...] = (
    "add",
    "commit",
    "stash",
)


_FILE_PATTERNS_COMPILED: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p) for p in _SECRET_FILE_PATTERN_DEFS
)


def is_secret_file_commit(command: str) -> tuple[bool, list[str]]:
    """Classify ``command`` as a secret-FILE commit (B2 surface).

    Migrated from ``plugins/dev-sdlc/hooks/bash_guard.py`` per
    D-SECHK.OVERLAP partial-absorb. Behavior parity with the prior
    ``_gate_helpers.is_secret_commit_command`` is the test contract
    (AC.SECHK.B2-MIGRATION-1).

    Returns ``(matched, list of detected paths)``. Matches when:

    * the command invokes ``git`` with a staging subcommand
      (``add``, ``commit``, ``stash``); AND
    * at least one token matches a secret-file pattern (``.env``
      family, ``.pem``, ``.key``, ``id_rsa``, etc.); AND
    * the matched token does not end in a carve-out suffix
      (``-example``, ``.example``, ``-sample``, ``.sample``,
      ``-template``, ``.template``).
    """
    if not isinstance(command, str) or not command:
        return (False, [])

    if not _is_git_staging_subcommand(command):
        return (False, [])

    matched: list[str] = []
    seen: set[str] = set()
    for pattern in _FILE_PATTERNS_COMPILED:
        for m in pattern.finditer(command):
            token = m.group(0).lstrip().lstrip("/").strip()
            if not token:
                continue
            lower = token.lower()
            if any(
                lower.endswith(s) for s in _SECRET_FILE_CARVE_OUT_SUFFIXES
            ):
                continue
            tail = token.rsplit("/", 1)[-1]
            tail_lower = tail.lower()
            if any(
                s in tail_lower
                and tail_lower.find(s) + len(s)
                >= len(tail_lower) - 16
                for s in ("-example", ".example", "-sample", ".sample")
            ):
                if any(
                    tail_lower.endswith(s)
                    or s in tail_lower.split(".")[-2:]
                    for s in (
                        "example",
                        "sample",
                        "template",
                    )
                ):
                    continue
            if token in seen:
                continue
            seen.add(token)
            matched.append(token)

    return (bool(matched), matched)


def _is_git_staging_subcommand(command: str) -> bool:
    """True iff ``command`` invokes ``git`` with a staging subcommand.

    Mirror of the bash_guard helper — tolerates env-var prefixes,
    sudo / env / nice / ionice / time prefixes, and pipeline
    segments.
    """
    segments = re.split(r"[|;]|&&|\|\|", command)
    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue
        tokens = seg.split()
        i = 0
        while i < len(tokens) and re.match(
            r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[i]
        ):
            i += 1
        while i < len(tokens) and tokens[i] in (
            "sudo",
            "env",
            "nice",
            "ionice",
            "time",
        ):
            i += 1
            while i < len(tokens) and re.match(
                r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[i]
            ):
                i += 1
        if i + 1 >= len(tokens):
            continue
        if tokens[i] != "git":
            continue
        j = i + 1
        while j < len(tokens) and tokens[j] == "-c":
            j += 2
        if j >= len(tokens):
            continue
        if tokens[j] in _GIT_STAGING_SUBCOMMANDS:
            return True
    return False


# ---------------------------------------------------------------------
# Workspace-additions loader
# ---------------------------------------------------------------------


def load_workspace_additions(workspace_root: Path) -> tuple[SecretPattern, ...]:
    """Load workspace-additions content patterns; fail-open to empty.

    Reads ``<workspace>/.loam/secret-patterns.yaml`` if present.
    Schema (minimal YAML subset; no PyYAML dependency on the hook
    path):

        patterns:
          - name: workspace-internal-token
            regex: "internal-key-[A-Z0-9]{16}"

    Parse failures fail-open: returns ``()``. Caller may log the
    failure to its NDJSON log; this loader never raises.
    """
    additions_path = workspace_root / ".loam" / "secret-patterns.yaml"
    if not additions_path.is_file():
        return ()
    try:
        text = additions_path.read_text(encoding="utf-8")
    except OSError:
        return ()
    parsed = _parse_minimal_yaml(text)
    if not isinstance(parsed, dict):
        return ()
    entries = parsed.get("patterns")
    if not isinstance(entries, list):
        return ()
    out: list[SecretPattern] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        regex = entry.get("regex")
        if not isinstance(name, str) or not isinstance(regex, str):
            continue
        try:
            compiled = re.compile(regex)
        except re.error:
            continue
        out.append(SecretPattern(name=name, regex=compiled))
    return tuple(out)


def _parse_minimal_yaml(text: str) -> object:
    """Minimal YAML parser sufficient for the workspace-additions
    schema. Supports a single top-level dict whose ``patterns`` key
    holds a list of ``{name, regex}`` dicts.

    Not a general YAML parser; the loader's contract is that anything
    outside the supported subset fails-open to an empty result.
    """
    result: dict[str, object] = {}
    current_list: list[object] | None = None
    current_item: dict[str, object] | None = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if indent == 0 and stripped.endswith(":"):
            key = stripped[:-1].strip()
            if key == "patterns":
                current_list = []
                result[key] = current_list
                current_item = None
            else:
                current_list = None
                current_item = None
            continue
        if current_list is None:
            continue
        if stripped.startswith("- "):
            item_body = stripped[2:].strip()
            current_item = {}
            current_list.append(current_item)
            if ":" in item_body:
                k, _, v = item_body.partition(":")
                current_item[k.strip()] = _yaml_scalar(v.strip())
            continue
        if current_item is None:
            continue
        if ":" in stripped:
            k, _, v = stripped.partition(":")
            current_item[k.strip()] = _yaml_scalar(v.strip())
    return result


def _yaml_scalar(raw: str) -> str:
    """Unquote a YAML scalar (quoted or bare). Conservative: returns
    a string; numeric/null coercion is not needed for this schema.
    """
    if not raw:
        return ""
    if (raw.startswith('"') and raw.endswith('"')) or (
        raw.startswith("'") and raw.endswith("'")
    ):
        return raw[1:-1]
    return raw


# ---------------------------------------------------------------------
# Pattern-set assembly
# ---------------------------------------------------------------------


def all_content_patterns(
    workspace_root: Path,
) -> tuple[SecretPattern, ...]:
    """Floor + additive workspace patterns. Additive only — never
    removes a floor pattern. Order: floor first, then workspace
    additions in declaration order.
    """
    additions = load_workspace_additions(workspace_root)
    return CONTENT_PATTERNS + additions

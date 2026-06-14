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

"""Bootstrap-wiring contract for the knowledge-pack marketplace
(claude-leverage-program Slice 4b — WIRE; D-PUSH.2).

The IN-FENCE buildable half of distribution. A bootstrapped workspace's
``<workspace>/.claude/settings.json`` gains an ``extraKnownMarketplaces``
stanza carrying ``"autoUpdate": true`` for the loam knowledge-pack
marketplace. This is the §3.1.2 live-verified zero-user-action
mechanism: third-party marketplaces default to auto-update OFF, so the
managed ``extraKnownMarketplaces`` stanza is what delivers TRUE
zero-user-action-after-the-bootstrap (the bootstrap IS the one-time
setup). With the stanza present + the marketplace registered, Claude
Code refreshes the marketplace and updates installed plugins to their
latest versions at startup — the user takes no per-cycle action beyond
the platform's own one-keystroke ``/reload-plugins`` activation prompt
(named, not owned — plan §10 F2.2).

The settings shape is verified against the live Claude Code docs +
the published settings JSON schema (plan-author 2026-06-14;
re-verified at S4b build, ``code.claude.com/docs/en/discover-plugins``
§"Configure team marketplaces" + ``schemastore.org`` claude-code-
settings.json ``extraKnownMarketplaces``):

    {
      "extraKnownMarketplaces": {
        "<name>": {
          "source": { "source": "directory", "path": "<abs-path>" },
          "autoUpdate": true
        }
      }
    }

``extraKnownMarketplaces`` is a top-level object keyed by marketplace
name; ``source`` is an object whose inner ``source`` field is the
type discriminator (``"directory"`` carries a sibling ``"path"``;
``"github"`` carries a sibling ``"repo"``); ``autoUpdate`` is a
boolean sibling to ``source`` inside each named entry.

Behaviour summary (per AC.CLP-PUSH-WIRE.1 / .4):

- WIRE.1: a fresh bootstrapped workspace gains the stanza, with the
  marketplace entry carrying ``autoUpdate: true`` and a ``source``
  pointing at the knowledge-pack marketplace.
- WIRE.4: the write is idempotent — a re-run is a strict no-op when
  the on-disk content already equals the merged target (no mtime
  churn). Operator-customised top-level keys and OTHER marketplace
  entries under ``extraKnownMarketplaces`` are preserved (deep-merge;
  the framework owns only the identity of the knowledge-pack key).

Composes on the same idempotent-deep-merge + fail-soft + atomic-write
idiom as ``mcp_json_writer`` (amendment #47): a malformed pre-existing
settings.json or any IO error is fail-soft (structured result, scaffold
proceeds) — never aborts the bootstrap, never clobbers user content.

NO public action: the writer stages a LOCAL settings stanza only. The
``source`` it writes is supplied by the caller — for the LOCAL leg
(AC.CLP-PUSH-WIRE.2 ★) a ``directory`` source pointing at a local-path
marketplace; for the eventual public channel (S4c ⛔OWNER) a ``github``
source. This adapter creates NO repo, performs NO push, and contacts
no network. NO Anthropic API key.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# ---- WIRE.1 constants ------------------------------------------------


# The marketplace name the knowledge-pack registers under in
# ``extraKnownMarketplaces``. The framework owns the identity of this
# key (re-merges overwrite only this entry; other entries survive).
KNOWLEDGE_PACK_MARKETPLACE_NAME = "loam-knowledge"

# Workspace-root-relative file Claude Code reads for project-scoped
# settings (``<workspace>/.claude/settings.json`` — the same file the
# FBE.5b scaffold + the persona binding write).
SETTINGS_JSON_FILENAME = "settings.json"


# ---- WIRE.1 result dataclass -----------------------------------------


@dataclass(frozen=True)
class MarketplaceWiringResult:
    """Structured outcome of a ``write_marketplace_wiring`` invocation.

    WIRE.1 / WIRE.4: ``wrote`` is True iff the file content changed;
    False on idempotent no-op or skipped failure. ``reason`` carries
    one of:

    - ``"fresh_write"`` — settings.json did not exist; written from
      scratch carrying the stanza.
    - ``"merged"`` — settings.json existed; the stanza was deep-merged
      and the file rewritten.
    - ``"already_current"`` — settings.json existed and content was
      already byte-equal to the merged target; no write performed
      (WIRE.4 idempotency).
    - ``"skipped_malformed_existing"`` — pre-existing settings.json
      failed JSON parse or its top-level was not an object; skipped to
      preserve user content (fail-soft).
    - ``"skipped_io_error"`` — IO/permissions error during read/write;
      scaffold continues.

    ``path`` is the absolute path to the target settings.json.
    """

    wrote: bool
    reason: str
    path: Path | None


# ---- WIRE.1 pure-function source builders ----------------------------


def build_directory_source(path: str | Path) -> dict[str, Any]:
    """Return a ``directory`` (local-path) marketplace source object.

    Pure; no IO. Shape per the published settings JSON schema:
    ``{"source": "directory", "path": "<abs-path>"}``. ``path`` is the
    local directory containing ``.claude-plugin/marketplace.json``.
    Used by the AC.CLP-PUSH-WIRE.2 ★ LOCAL leg (a local-path
    marketplace; NO public surface).
    """
    return {"source": "directory", "path": str(path)}


def build_github_source(repo: str) -> dict[str, Any]:
    """Return a ``github`` marketplace source object.

    Pure; no IO. Shape per the published settings JSON schema:
    ``{"source": "github", "repo": "<owner>/<repo>"}``. This is the
    eventual S4c ⛔OWNER public-channel form; provided here so the same
    wiring writer serves both legs, but S4b NEVER invokes it against a
    real public repo (that is the owner-gated S4c step). NO repo is
    created and NO push happens here.
    """
    return {"source": "github", "repo": repo}


def build_marketplace_entry(
    *, source: dict[str, Any], auto_update: bool = True
) -> dict[str, Any]:
    """Return a single ``extraKnownMarketplaces`` entry.

    Pure; no IO. ``autoUpdate`` is a boolean sibling to ``source``
    inside the entry (WIRE.1 — ``autoUpdate: true`` is what flips a
    third-party marketplace from its default-OFF auto-update to ON, the
    §3.1.2 zero-user-action mechanism).
    """
    return {"source": dict(source), "autoUpdate": bool(auto_update)}


def merge_marketplace_wiring(
    existing: dict[str, Any],
    *,
    marketplace_name: str,
    entry: dict[str, Any],
) -> dict[str, Any]:
    """Return a deep-merged copy of ``existing`` settings with the
    knowledge-pack marketplace entry installed under
    ``extraKnownMarketplaces``.

    Pure; no IO. WIRE.4 contract:

    - Other top-level keys in ``existing`` are preserved (the persona
      binding's ``agent`` key, SessionStart hooks, operator keys).
    - Other entries under ``extraKnownMarketplaces`` are preserved.
    - The knowledge-pack entry is set to ``entry`` (overwriting any
      stale value — the framework owns the identity of this one key).

    ``existing`` is not mutated; shallow-copied top-level +
    ``extraKnownMarketplaces`` dicts are returned.
    """
    merged: dict[str, Any] = dict(existing)
    markets_in = existing.get("extraKnownMarketplaces")
    if isinstance(markets_in, dict):
        markets_out: dict[str, Any] = dict(markets_in)
    else:
        # Fresh write OR a malformed prior value (non-dict). The
        # malformed-existing top-level case is caught earlier in
        # ``write_marketplace_wiring``; a non-dict
        # ``extraKnownMarketplaces`` specifically is replaced with a
        # well-formed map carrying our entry rather than re-raising
        # inside a pure function.
        markets_out = {}
    markets_out[marketplace_name] = entry
    merged["extraKnownMarketplaces"] = markets_out
    return merged


# ---- WIRE.1 / WIRE.4 IO entrypoint -----------------------------------


def _serialise(data: dict[str, Any]) -> str:
    """Render merged settings as canonical settings.json text.

    Two-space indent + sorted top-level keys + trailing newline:
    matches the ``mcp_json_writer`` serialisation so the byte-stable
    idempotent no-op check (WIRE.4 ``already_current``) holds across
    re-merges, and keeps diff churn against hand-edits minimal.
    """
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def write_marketplace_wiring(
    *,
    workspace_root: Path,
    source: dict[str, Any] | None = None,
    marketplace_name: str = KNOWLEDGE_PACK_MARKETPLACE_NAME,
    auto_update: bool = True,
) -> MarketplaceWiringResult:
    """Write or deep-merge the ``extraKnownMarketplaces`` stanza into
    ``<workspace_root>/.claude/settings.json``.

    WIRE.1: writes the knowledge-pack marketplace entry carrying
    ``autoUpdate: true`` so a bootstrapped workspace auto-receives the
    S4a-rendered pack with zero user action after the one-time
    bootstrap.

    WIRE.4: idempotent — a re-run whose merged content is byte-equal to
    the on-disk content returns ``wrote=False, reason="already_current"``
    with no mtime churn; operator keys + other marketplace entries
    survive the merge.

    Fail-soft (mirrors ``mcp_json_writer`` AC47.3): a malformed
    pre-existing settings.json (parse error / non-object root) returns
    ``skipped_malformed_existing`` and preserves the file unmodified; an
    IO/permissions error returns ``skipped_io_error`` with a stderr
    diagnostic; the scaffold proceeds either way.

    Atomic write via ``.tmp`` + ``os.replace`` (no torn-file state).

    The caller supplies ``source`` — a ``directory`` source for the
    LOCAL leg (AC.CLP-PUSH-WIRE.2 ★), a ``github`` source for the S4c
    ⛔OWNER public channel. The writer assumes no default source: when
    ``source`` is ``None`` it declines and returns
    ``wrote=False, reason="no_source"`` (distinct from the IO /
    malformed skips, so the call site can tell "no marketplace
    configured yet" from "failed").
    """
    from ..workspace_paths import claude_dir as _claude_dir

    workspace_root = Path(workspace_root).resolve()
    target = _claude_dir(workspace_root) / SETTINGS_JSON_FILENAME

    if source is None:
        # No marketplace source supplied — nothing to wire. This keeps
        # the bootstrap call site honest: the writer wires a stanza
        # only when a concrete (directory / github) source is provided.
        # Distinct from the IO/ malformed skips so the caller can tell
        # "declined, no source" from "failed".
        return MarketplaceWiringResult(
            wrote=False, reason="no_source", path=target
        )

    entry = build_marketplace_entry(source=source, auto_update=auto_update)

    target.parent.mkdir(parents=True, exist_ok=True)

    existing: dict[str, Any]
    pre_existed = target.exists()
    if pre_existed:
        try:
            raw = target.read_text(encoding="utf-8")
        except OSError as exc:
            sys.stderr.write(
                f"workspace-bootstrap: marketplace_wiring skipped — "
                f"could not read {target}: {exc!r}\n"
            )
            return MarketplaceWiringResult(
                wrote=False, reason="skipped_io_error", path=target
            )
        try:
            loaded = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError as exc:
            sys.stderr.write(
                f"workspace-bootstrap: marketplace_wiring skipped — "
                f"existing {target} is not valid JSON: {exc!r}\n"
            )
            return MarketplaceWiringResult(
                wrote=False,
                reason="skipped_malformed_existing",
                path=target,
            )
        if not isinstance(loaded, dict):
            sys.stderr.write(
                f"workspace-bootstrap: marketplace_wiring skipped — "
                f"existing {target} top-level is not a JSON object\n"
            )
            return MarketplaceWiringResult(
                wrote=False,
                reason="skipped_malformed_existing",
                path=target,
            )
        existing = loaded
    else:
        existing = {}

    merged = merge_marketplace_wiring(
        existing, marketplace_name=marketplace_name, entry=entry
    )
    serialised = _serialise(merged)

    # WIRE.4 idempotency-on-equal: byte-equal serialised output vs
    # on-disk content → skip the write (no mtime churn).
    if pre_existed:
        try:
            current_bytes = target.read_bytes()
        except OSError:
            current_bytes = b""
        if current_bytes == serialised.encode("utf-8"):
            return MarketplaceWiringResult(
                wrote=False, reason="already_current", path=target
            )

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(target.parent),
            prefix=".settings.json.",
            suffix=".tmp",
            delete=False,
        ) as fh:
            fh.write(serialised)
            tmp_path = Path(fh.name)
        os.replace(tmp_path, target)
    except OSError as exc:
        sys.stderr.write(
            f"workspace-bootstrap: marketplace_wiring skipped — "
            f"could not write {target}: {exc!r}\n"
        )
        try:
            if "tmp_path" in locals() and tmp_path.exists():  # type: ignore[has-type]
                tmp_path.unlink()  # type: ignore[has-type]
        except OSError:
            pass
        return MarketplaceWiringResult(
            wrote=False, reason="skipped_io_error", path=target
        )

    reason = "merged" if pre_existed else "fresh_write"
    return MarketplaceWiringResult(wrote=True, reason=reason, path=target)


# ---- WIRE.3 persona knowledge-surfacing rule (AC.CLP-PUSH.4) ---------
#
# The persona surfaces newly-arrived leverage knowledge per the Lens 0
# substance/vocabulary rule: the SUBSTANCE (what new leverage knowledge
# arrived + what it lets the user do) is always exposed; only the
# VOCABULARY adapts to the user's known terms. NOT a raw changelog dump.
#
# This is a deterministic surfacing-rule artefact, not a primary-persona
# spine edit: AC.CLP-PUSH.4's verification ("observe the persona's
# surfacing on a fixture user profile") is satisfied by a pure function
# the persona consumes — it takes arrived-pack metadata + a per-user
# vocabulary level and returns the surfacing text. Routing through the
# workspace-bootstrap fence (where the wiring that brings the pack in
# lives) keeps the fence equal to the work (the conditional
# primary-persona component is therefore NOT needed and is removed at
# apply — a fence wider than the work is its own ODD violation).
#
# The same precedent shape as the ONRUNG leverage-ladder surfacing in
# onboarding_activations: a substance-exposed, vocabulary-tuned
# suggestion emitted as a deterministic artefact.


# Vocabulary levels the surfacing tunes to (Lens 0: expose substance,
# adapt vocabulary). ``plain`` for a non-technical user (no coined /
# internal terms); ``technical`` for a user who has shown they know the
# platform vocabulary (marketplace / plugin / skills-pack may appear).
SURFACING_VOCAB_PLAIN = "plain"
SURFACING_VOCAB_TECHNICAL = "technical"


@dataclass(frozen=True)
class ArrivedKnowledge:
    """Metadata about a newly-arrived knowledge pack (the substance the
    surfacing must expose).

    ``skill_titles`` are the human-facing names of the leverage skills
    the pack carries (what the user can now do); ``generated_ts`` +
    ``content_hash`` identify the pack version (carried from the S4a
    render — D-PUSH.5). ``stale_note`` carries any stale-entry signal so
    the surfacing never silently presents stale-as-current.
    """

    skill_titles: tuple[str, ...]
    generated_ts: str
    content_hash: str
    stale_note: str | None = None


def surface_arrived_knowledge(
    arrived: ArrivedKnowledge, *, vocab: str = SURFACING_VOCAB_PLAIN
) -> str:
    """Return the persona's surfacing of newly-arrived leverage
    knowledge — substance exposed, vocabulary tuned (AC.CLP-PUSH.4).

    Pure; no IO. The SUBSTANCE — that new leverage knowledge arrived
    and *what it lets the user do* (the skill titles) — is present at
    BOTH vocab levels; only the framing words change. A raw changelog
    dump (bare titles + hash, no "what this does for you") is exactly
    what this avoids: every line ties the arrival to a user-facing
    capability.

    ``vocab=plain`` (default): no coined / platform-internal terms
    (no "marketplace", "plugin", "skills-pack", "content-hash"). Frames
    the arrival as "loam learned some new ways to get more out of AI"
    and lists what each lets the user do.

    ``vocab=technical``: the same substance, but platform vocabulary is
    permitted (the user has shown they know it).

    A ``stale_note`` is always surfaced when present (never dropped —
    stale-never-silently-current, propagated from the corpus rule).
    """
    titles = list(arrived.skill_titles)
    if vocab == SURFACING_VOCAB_TECHNICAL:
        head = (
            f"New leverage knowledge arrived (pack {arrived.content_hash[:12]}, "
            f"rendered {arrived.generated_ts}). It adds:"
        )
        bullets = [f"  - {t}" for t in titles]
        body = "\n".join([head, *bullets]) if bullets else head
    else:
        # Plain: expose the same substance with no coined terms.
        head = "loam picked up some new ways to help you get more out of AI:"
        bullets = [f"  - {t}" for t in titles]
        body = "\n".join([head, *bullets]) if bullets else (
            "loam refreshed its knowledge of how to get more out of AI."
        )

    if arrived.stale_note:
        body = body + (
            f"\n  (Heads-up: {arrived.stale_note} — flagged so you're not "
            f"relying on something out of date.)"
        )
    return body

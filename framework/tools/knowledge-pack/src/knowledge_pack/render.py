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

"""Deterministic corpus -> skills-pack marketplace render.

AC.CLP-PUSH-RENDER.1 — the pack body is a DETERMINISTIC projection of the
corpus: every projected ``SKILL.md`` body is the corpus entry body
verbatim plus a structural provenance footer. No LLM authors any pack
body text — a hallucinated leverage claim cannot enter by construction
(D-PUSH.1 protection floor, the same shape as Slice-1's refresh).

AC.CLP-PUSH-RENDER.2 — every pack claim carries its corpus citation: each
skill's provenance footer names the corpus path it was projected from and
re-emits the entry's ``[primitive: <class>:<name>]`` cross-references and
``source_url`` so no externally-sourced claim is decoupled from its source.

AC.CLP-PUSH-RENDER.4 ★ — the render emits the live-verified marketplace
shape (``.claude-plugin/marketplace.json`` + ``plugins/<name>/`` each with
``.claude-plugin/plugin.json`` + ``skills/<name>/SKILL.md``) — a
well-formed tree validatable with no pre-arranged state.

AC.CLP-PUSH-RENDER.5 — the pack carries a ``pack-manifest.json`` sidecar
with a generated-ts + a content-hash (over the projected skill bodies,
deterministic) + per-entry ``source_fetch_ts`` / ``source_status``
passthrough, so a stale corpus entry is never rendered as silently
current and "did the pack change?" is a deterministic hash comparison
(D-PUSH.5; pack version derives from (date, content-hash), never
pre-assigned — feedback_version_numbers_at_release_time).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

from knowledge_pack.corpus_read import CorpusEntry, load_corpus

# Marketplace identity (the catalog-level name; the public repo is S4c
# ⛔OWNER, this render only stages the tree in-repo).
MARKETPLACE_NAME = "loam-knowledge"
MARKETPLACE_OWNER = "Luke Ivers"
# One plugin per corpus class — a skills-only pack (plan §3.1.5 verbatim:
# "a skills-only pack is valid").
PLUGIN_BY_CLASS = {
    "claude-code": "loam-knowledge-claude-code",
    "harness": "loam-knowledge-harness",
    "best-practice": "loam-knowledge-best-practice",
}


@dataclass
class RenderResult:
    """The outcome of one render — the pack root + what was written."""

    pack_root: Path
    skill_count: int
    plugin_names: List[str]
    content_hash: str
    generated_ts: str
    stale_entries: List[str]


def _skill_provenance_footer(entry: CorpusEntry) -> str:
    """The structural provenance footer appended to each projected skill
    (RENDER.2). Names the corpus path, the upstream source_url, the entry
    status, and re-emits the entry's cross-reference citations. This is
    structural text — NOT authored prose (RENDER.1)."""
    lines = [
        "",
        "---",
        "",
        "## Provenance",
        "",
        f"- Projected from: `{entry.corpus_path}`",
    ]
    if entry.source_url:
        lines.append(f"- Source: {entry.source_url}")
    if entry.source_fetch_ts:
        lines.append(f"- Source fetched: {entry.source_fetch_ts}")
    if entry.source_status:
        lines.append(f"- Source status: {entry.source_status}")
    if entry.citations:
        refs = ", ".join(c.render() for c in entry.citations)
        lines.append(f"- Cross-references: {refs}")
    lines.append("")
    return "\n".join(lines)


def _skill_md(entry: CorpusEntry) -> str:
    """Render one corpus entry into SKILL.md form (frontmatter + verbatim
    body + provenance footer). The ``description`` frontmatter is the
    entry title — a structural projection of the corpus, not an authored
    summary (RENDER.1)."""
    desc = entry.title.replace('"', "'")
    frontmatter = f'---\ndescription: "{desc}"\n---\n'
    return frontmatter + "\n" + entry.body.rstrip("\n") + "\n" + _skill_provenance_footer(entry)


def _content_hash(skill_bodies: List[str]) -> str:
    """Deterministic content-hash over the projected skill bodies, in a
    fixed order (RENDER.5). Drives "did the pack actually change" without
    depending on the generated-ts (which always changes)."""
    h = hashlib.sha256()
    for body in skill_bodies:
        h.update(body.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


def _pack_version(generated_ts: str, content_hash: str) -> str:
    """Derive the pack version from (date, content-hash) — never
    pre-assigned (D-PUSH.5; feedback_version_numbers_at_release_time).
    Form: ``<YYYY.MM.DD>+<hash12>``."""
    date = generated_ts[:10].replace("-", ".")
    return f"{date}+{content_hash[:12]}"


def render_pack(corpus_root: Path, pack_root: Path, generated_ts: str) -> RenderResult:
    """Render the corpus into a marketplace-shaped skills-pack tree under
    *pack_root*. Deterministic given (corpus_root, generated_ts): the only
    non-content-stable field is the generated-ts (RENDER.1/.4/.5).

    *generated_ts* is injected (not read from the clock here) so the
    render is testable + reproducible; the CLI supplies the real run ts.
    """
    corpus_root = Path(corpus_root)
    pack_root = Path(pack_root)
    entries = load_corpus(corpus_root)

    # Group entries by class -> plugin; project each into a SKILL.md.
    by_plugin: dict[str, List[CorpusEntry]] = {}
    for e in entries:
        plugin = PLUGIN_BY_CLASS.get(e.cls)
        if plugin is None:
            continue
        by_plugin.setdefault(plugin, []).append(e)

    # Deterministic order for the content hash: (plugin, entry name).
    ordered_bodies: List[str] = []
    skill_count = 0
    stale_entries: List[str] = []
    per_entry: List[dict] = []

    plugin_names = sorted(by_plugin)

    # First pass: compute bodies + hash (no writes yet, so a failed
    # render leaves no partial tree — protection-floor hygiene).
    rendered: dict[str, List[tuple]] = {}
    for plugin in plugin_names:
        for e in sorted(by_plugin[plugin], key=lambda x: x.name):
            md = _skill_md(e)
            rendered.setdefault(plugin, []).append((e, md))
            ordered_bodies.append(md)
            skill_count += 1
            if e.is_stale:
                stale_entries.append(e.corpus_path)
            per_entry.append({
                "corpus_path": e.corpus_path,
                "plugin": plugin,
                "skill": e.name,
                "source_url": e.source_url,
                "source_fetch_ts": e.source_fetch_ts,
                "source_status": e.source_status,
            })

    content_hash = _content_hash(ordered_bodies)
    version = _pack_version(generated_ts, content_hash)

    # Second pass: write the tree.
    plugin_dir_root = pack_root / "plugins"
    marketplace_plugins = []
    for plugin in plugin_names:
        pdir = plugin_dir_root / plugin
        (pdir / ".claude-plugin").mkdir(parents=True, exist_ok=True)
        plugin_json = {
            "name": plugin,
            "description": f"loam knowledge pack — {plugin.replace('loam-knowledge-', '')} leverage knowledge, rendered from docs/capability-corpus/",
            "version": version,
        }
        (pdir / ".claude-plugin" / "plugin.json").write_text(
            json.dumps(plugin_json, indent=2) + "\n", encoding="utf-8"
        )
        for (e, md) in rendered[plugin]:
            sdir = pdir / "skills" / e.name
            sdir.mkdir(parents=True, exist_ok=True)
            (sdir / "SKILL.md").write_text(md, encoding="utf-8")
        marketplace_plugins.append({
            "name": plugin,
            "source": f"./plugins/{plugin}",
            "description": plugin_json["description"],
        })

    # Marketplace catalog at the pack root (the §3.1.5 verified shape).
    mp_root = pack_root / ".claude-plugin"
    mp_root.mkdir(parents=True, exist_ok=True)
    marketplace_json = {
        "name": MARKETPLACE_NAME,
        "owner": {"name": MARKETPLACE_OWNER},
        "plugins": marketplace_plugins,
    }
    (mp_root / "marketplace.json").write_text(
        json.dumps(marketplace_json, indent=2) + "\n", encoding="utf-8"
    )

    # Pack manifest sidecar — generated-ts + content-hash + version +
    # per-entry passthrough (RENDER.5; D-PUSH.5).
    pack_manifest = {
        "marketplace": MARKETPLACE_NAME,
        "generated_ts": generated_ts,
        "content_hash": content_hash,
        "version": version,
        "skill_count": skill_count,
        "stale_entries": stale_entries,
        "entries": per_entry,
    }
    (pack_root / "pack-manifest.json").write_text(
        json.dumps(pack_manifest, indent=2) + "\n", encoding="utf-8"
    )

    return RenderResult(
        pack_root=pack_root,
        skill_count=skill_count,
        plugin_names=plugin_names,
        content_hash=content_hash,
        generated_ts=generated_ts,
        stale_entries=stale_entries,
    )

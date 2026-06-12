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

"""Source manifest — sources are DATA, not code (AC.CLP-CUR.3; D-CUR.3).

The manifest is a YAML file (canonical home:
``docs/capability-corpus/sources.yaml``; workspace-overridable by
passing a different path to the CLI). Each source declares:

  - ``id``      — stable identifier (snapshot + delta file naming).
  - ``kind``    — ``entry`` (projects into one Class A / A-prime corpus
                  entry) or ``watch`` (corpus-wide change watcher with
                  no projection target; ALL its deltas are review-class
                  by construction — e.g. the Claude Code changelog).
  - ``entry``   — corpus-relative entry path (``entry`` kind only).
  - ``url``     — ``http(s)://`` / ``file://`` upstream, or
                  ``internal:<repo-relative-path>`` for in-repo
                  canonical sources (Class A-prime).
  - ``cadence`` — locked cadence class per the 2026-04-26 design
                  (research doc section 7bis.1): ``high-velocity``
                  (~daily), ``long-form`` (~weekly), ``on-merge``
                  (A-prime, git-hook-triggered — declared as data now;
                  trigger binding is future work).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import yaml

CADENCE_CLASSES = ("high-velocity", "long-form", "on-merge")
KINDS = ("entry", "watch")


class SourceManifestError(ValueError):
    """The source manifest is malformed."""


@dataclass(frozen=True)
class Source:
    id: str
    kind: str
    url: str
    cadence: str
    entry: Optional[str] = None


def load_sources(manifest_path: Path) -> List[Source]:
    """Parse + validate the source manifest (AC.CLP-CUR.3)."""
    raw = yaml.safe_load(Path(manifest_path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("sources"), list):
        raise SourceManifestError(
            f"{manifest_path}: expected a mapping with a 'sources' list"
        )
    sources: List[Source] = []
    seen = set()
    for i, item in enumerate(raw["sources"]):
        if not isinstance(item, dict):
            raise SourceManifestError(f"{manifest_path}: sources[{i}] not a mapping")
        sid = item.get("id")
        kind = item.get("kind", "entry")
        url = item.get("url")
        cadence = item.get("cadence")
        entry = item.get("entry")
        if not sid or not isinstance(sid, str):
            raise SourceManifestError(f"{manifest_path}: sources[{i}] missing 'id'")
        if sid in seen:
            raise SourceManifestError(f"{manifest_path}: duplicate source id {sid!r}")
        seen.add(sid)
        if kind not in KINDS:
            raise SourceManifestError(f"{sid}: kind must be one of {KINDS}")
        if not url or not isinstance(url, str):
            raise SourceManifestError(f"{sid}: missing 'url'")
        if cadence not in CADENCE_CLASSES:
            raise SourceManifestError(f"{sid}: cadence must be one of {CADENCE_CLASSES}")
        if kind == "entry" and not entry:
            raise SourceManifestError(f"{sid}: 'entry' kind requires an 'entry' path")
        if kind == "watch" and entry:
            raise SourceManifestError(f"{sid}: 'watch' kind must not name an 'entry'")
        sources.append(Source(id=sid, kind=kind, url=url, cadence=cadence, entry=entry))
    return sources


def filter_by_cadence(sources: List[Source], cadence_class: str) -> List[Source]:
    """Cadence selection for a scheduled run (AC.CLP-CUR.3)."""
    if cadence_class == "all":
        return list(sources)
    if cadence_class not in CADENCE_CLASSES:
        raise SourceManifestError(
            f"unknown cadence class {cadence_class!r}; expected 'all' or one of {CADENCE_CLASSES}"
        )
    return [s for s in sources if s.cadence == cadence_class]

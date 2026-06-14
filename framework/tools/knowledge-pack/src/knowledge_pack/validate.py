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

"""Marketplace-tree validator (AC.CLP-PUSH-RENDER.4 ★).

Confirms a rendered pack root is a well-formed marketplace tree per the
live-verified shape (plan §3.1.5): a ``.claude-plugin/marketplace.json``
at the root naming N plugins, each plugin's ``source`` resolving to a
``plugins/<name>/`` dir with a ``.claude-plugin/plugin.json`` and at least
one ``skills/<name>/SKILL.md``. Used by the ★ outcome-altitude test (a
production-CLI render against the live corpus validates with no
pre-arranged state) and by the CLI's ``--validate`` self-check.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List


class PackValidationError(Exception):
    """The rendered pack tree is not a well-formed marketplace."""


def validate_pack(pack_root: Path) -> List[str]:
    """Validate the marketplace tree; return the list of plugin names.

    Raises :class:`PackValidationError` on the first structural defect.
    """
    pack_root = Path(pack_root)
    mp_path = pack_root / ".claude-plugin" / "marketplace.json"
    if not mp_path.is_file():
        raise PackValidationError(f"missing marketplace.json at {mp_path}")
    try:
        mp = json.loads(mp_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PackValidationError(f"marketplace.json is not valid JSON: {exc}") from exc

    for key in ("name", "owner", "plugins"):
        if key not in mp:
            raise PackValidationError(f"marketplace.json missing required key: {key!r}")
    if not isinstance(mp["plugins"], list) or not mp["plugins"]:
        raise PackValidationError("marketplace.json 'plugins' must be a non-empty list")

    plugin_names: List[str] = []
    for entry in mp["plugins"]:
        for key in ("name", "source"):
            if key not in entry:
                raise PackValidationError(f"plugin entry missing required key: {key!r}")
        name = entry["name"]
        source = entry["source"]
        # source is a repo-relative path "./plugins/<name>".
        pdir = (pack_root / source).resolve()
        try:
            pdir.relative_to(pack_root.resolve())
        except ValueError:
            raise PackValidationError(
                f"plugin {name!r} source escapes the pack root: {source!r}"
            )
        pj = pdir / ".claude-plugin" / "plugin.json"
        if not pj.is_file():
            raise PackValidationError(f"plugin {name!r} missing plugin.json at {pj}")
        try:
            pjd = json.loads(pj.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise PackValidationError(
                f"plugin {name!r} plugin.json is not valid JSON: {exc}"
            ) from exc
        if pjd.get("name") != name:
            raise PackValidationError(
                f"plugin.json name {pjd.get('name')!r} != catalog name {name!r}"
            )
        skills = sorted((pdir / "skills").glob("*/SKILL.md")) if (pdir / "skills").is_dir() else []
        if not skills:
            raise PackValidationError(f"plugin {name!r} has no skills/<name>/SKILL.md")
        for skill_md in skills:
            text = skill_md.read_text(encoding="utf-8")
            if not text.startswith("---\n"):
                raise PackValidationError(
                    f"{skill_md} missing SKILL.md frontmatter"
                )
            # Provenance footer is the RENDER.2 citation surface.
            if "## Provenance" not in text:
                raise PackValidationError(
                    f"{skill_md} missing provenance footer (RENDER.2 citation)"
                )
        plugin_names.append(name)
    return plugin_names

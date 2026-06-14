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

"""AC.CLP-PUSH-WIRE.1 (claude-leverage-program Slice 4b).

The bootstrap-wiring contract writes an ``extraKnownMarketplaces``
stanza carrying ``autoUpdate: true`` for the knowledge-pack marketplace
into a workspace's ``.claude/settings.json`` (D-PUSH.2; the §3.1.2
live-verified zero-user-action mechanism). The deep-merge preserves
operator top-level keys and OTHER marketplace entries — the framework
owns only the identity of the knowledge-pack key.

Settings shape verified against the live Claude Code docs + the
published settings JSON schema (S4b build, 2026-06-14): a top-level
``extraKnownMarketplaces`` object keyed by marketplace name; each entry
carries a ``source`` object (inner ``source`` discriminator
``"directory"`` + sibling ``"path"``, or ``"github"`` + ``"repo"``) and
a boolean ``autoUpdate`` sibling.

NO public action — the writer stages a LOCAL settings stanza only.
"""

from __future__ import annotations

import json
from pathlib import Path

from loam.workspace_bootstrap.adapters.marketplace_wiring import (
    KNOWLEDGE_PACK_MARKETPLACE_NAME,
    SETTINGS_JSON_FILENAME,
    build_directory_source,
    build_github_source,
    write_marketplace_wiring,
)


def _settings_path(workspace_root: Path) -> Path:
    return workspace_root / ".claude" / SETTINGS_JSON_FILENAME


def test_WIRE_1_fresh_write_carries_autoupdate_true_directory_source(
    tmp_path: Path,
) -> None:
    """A fresh workspace gains the stanza: the knowledge-pack entry
    carries ``autoUpdate: true`` and a ``directory`` source pointing at
    the supplied local-path marketplace."""
    ws = tmp_path / "fresh-ws"
    ws.mkdir()
    pack_dir = tmp_path / "local-marketplace"
    pack_dir.mkdir()

    result = write_marketplace_wiring(
        workspace_root=ws,
        source=build_directory_source(pack_dir),
    )

    assert result.wrote is True
    assert result.reason == "fresh_write"

    parsed = json.loads(_settings_path(ws).read_text())
    markets = parsed["extraKnownMarketplaces"]
    entry = markets[KNOWLEDGE_PACK_MARKETPLACE_NAME]

    # autoUpdate:true is the §3.1.2 mechanism — third-party
    # marketplaces default auto-update OFF; the stanza flips it ON.
    assert entry["autoUpdate"] is True
    # directory source pins the local-path marketplace (the LOCAL leg).
    assert entry["source"]["source"] == "directory"
    assert entry["source"]["path"] == str(pack_dir)


def test_WIRE_1_deep_merge_preserves_operator_and_other_marketplaces(
    tmp_path: Path,
) -> None:
    """Operator top-level keys and OTHER ``extraKnownMarketplaces``
    entries survive the merge; only the knowledge-pack entry is added."""
    ws = tmp_path / "merge-ws"
    (ws / ".claude").mkdir(parents=True)
    pack_dir = tmp_path / "local-marketplace"
    pack_dir.mkdir()

    pre_existing = {
        "agent": "primary",  # persona binding key — must survive
        "extraKnownMarketplaces": {
            "team-tools": {
                "source": {"source": "github", "repo": "acme/plugins"},
                "autoUpdate": False,
            }
        },
        "_operator_key": "mine",
    }
    _settings_path(ws).write_text(json.dumps(pre_existing, indent=2) + "\n")

    result = write_marketplace_wiring(
        workspace_root=ws,
        source=build_directory_source(pack_dir),
    )
    assert result.wrote is True
    assert result.reason == "merged"

    parsed = json.loads(_settings_path(ws).read_text())
    # Operator keys preserved.
    assert parsed["agent"] == "primary"
    assert parsed["_operator_key"] == "mine"
    # Other marketplace entry preserved verbatim.
    assert parsed["extraKnownMarketplaces"]["team-tools"] == {
        "source": {"source": "github", "repo": "acme/plugins"},
        "autoUpdate": False,
    }
    # Knowledge-pack entry added.
    assert (
        KNOWLEDGE_PACK_MARKETPLACE_NAME in parsed["extraKnownMarketplaces"]
    )


def test_WIRE_1_re_merge_overwrites_stale_knowledge_pack_entry(
    tmp_path: Path,
) -> None:
    """The framework owns the identity of the knowledge-pack key: a
    re-merge replaces a stale entry (e.g. an old path) while leaving
    sibling user entries alone."""
    ws = tmp_path / "stale-ws"
    (ws / ".claude").mkdir(parents=True)
    new_pack = tmp_path / "new-marketplace"
    new_pack.mkdir()

    stale = {
        "extraKnownMarketplaces": {
            KNOWLEDGE_PACK_MARKETPLACE_NAME: {
                "source": {"source": "directory", "path": "/old/stale/path"},
                "autoUpdate": True,
            },
            "team-tools": {
                "source": {"source": "github", "repo": "acme/plugins"},
                "autoUpdate": True,
            },
        }
    }
    _settings_path(ws).write_text(json.dumps(stale, indent=2) + "\n")

    result = write_marketplace_wiring(
        workspace_root=ws,
        source=build_directory_source(new_pack),
    )
    assert result.wrote is True
    assert result.reason == "merged"

    parsed = json.loads(_settings_path(ws).read_text())
    # Knowledge-pack entry updated to the new path.
    assert (
        parsed["extraKnownMarketplaces"][KNOWLEDGE_PACK_MARKETPLACE_NAME][
            "source"
        ]["path"]
        == str(new_pack)
    )
    # Sibling user marketplace untouched.
    assert parsed["extraKnownMarketplaces"]["team-tools"] == {
        "source": {"source": "github", "repo": "acme/plugins"},
        "autoUpdate": True,
    }


def test_WIRE_1_github_source_builder_shape_for_s4c_public_channel(
    tmp_path: Path,
) -> None:
    """The github source builder produces the schema-correct shape the
    S4c ⛔OWNER public channel will use. Building the source object is a
    pure no-IO operation — NO repo is created, NO push happens; this is
    only the source-object constructor the same writer reuses."""
    src = build_github_source("lukeivers/loam-knowledge")
    assert src == {"source": "github", "repo": "lukeivers/loam-knowledge"}


def test_WIRE_1_none_source_declines_no_write(tmp_path: Path) -> None:
    """With no marketplace source supplied, the writer declines (no
    stanza pointing at a non-existent location) and reports
    ``no_source`` — distinct from the IO / malformed skips."""
    ws = tmp_path / "no-source-ws"
    ws.mkdir()
    result = write_marketplace_wiring(workspace_root=ws, source=None)
    assert result.wrote is False
    assert result.reason == "no_source"
    # No settings.json was created.
    assert not _settings_path(ws).exists()

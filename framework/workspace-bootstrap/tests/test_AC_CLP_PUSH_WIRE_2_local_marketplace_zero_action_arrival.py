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

"""AC.CLP-PUSH-WIRE.2 ★ (outcome-altitude) — the AC.CLP-PUSH.3 LOCAL leg.

A second fixture workspace, after one-time setup ONLY, receives a
re-rendered pack via a LOCAL-path marketplace with ZERO further user
action. ★ outcome-altitude: drives the production wiring path against a
real scaffolded workspace + a real local-path marketplace tree (the
§3.1.5-verified ``.claude-plugin/marketplace.json`` + ``plugins/<name>/
skills/`` shape) with NO pre-arranged settings state, then simulates a
re-render (the marketplace content changes on disk) and asserts the
workspace still points at the live local marketplace with
``autoUpdate: true`` and requires NO further user action.

The CONTENT updating on auto-update is the platform's job (Claude Code
refreshes the marketplace + updates installed plugins at startup when
``autoUpdate: true``); loam's in-fence outcome — the one this ★ AC
verifies — is that the one-time bootstrap wiring makes the workspace a
zero-further-action recipient of whatever the local marketplace
re-renders to. The real-publish (github) leg is S4c ⛔OWNER.

NO public surface: the marketplace is a local directory; NO repo is
created, NO push happens, no network is contacted.
"""

from __future__ import annotations

import json
from pathlib import Path

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    DEFAULT_PERSONA_HANDLE,
    run_first_run_scaffold,
)
from loam.workspace_bootstrap.adapters.marketplace_wiring import (
    KNOWLEDGE_PACK_MARKETPLACE_NAME,
    SETTINGS_JSON_FILENAME,
    build_directory_source,
    write_marketplace_wiring,
)


def _render_local_marketplace(root: Path, *, content_token: str) -> Path:
    """Render a minimal valid local-path marketplace tree (the
    §3.1.5-verified shape): ``.claude-plugin/marketplace.json`` at root
    + a ``plugins/<name>/`` skills-pack. ``content_token`` lets the test
    simulate a re-render (a later render with a different token stands
    in for a cadence update of the pack body). Returns ``root``.

    This is a hand-built marketplace fixture (NOT a cross-component
    import of the knowledge-pack renderer) so the workspace-bootstrap
    seal-test stays decoupled from another component's install — the
    wiring contract this AC verifies is agnostic to how the pack was
    produced; it only needs a valid local marketplace to point at.
    """
    mp = {
        "name": "loam-knowledge",
        "owner": {"name": "loam"},
        "plugins": [
            {"name": "loam-leverage", "source": "./plugins/loam-leverage"}
        ],
    }
    (root / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (root / ".claude-plugin" / "marketplace.json").write_text(
        json.dumps(mp, indent=2) + "\n", encoding="utf-8"
    )
    skill_dir = root / "plugins" / "loam-leverage" / "skills" / "leverage"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: leverage\n---\n# Leverage knowledge ({content_token})\n",
        encoding="utf-8",
    )
    return root


def _settings_path(workspace_root: Path) -> Path:
    return workspace_root / ".claude" / SETTINGS_JSON_FILENAME


def _scaffold_workspace(tmp_path: Path) -> Path:
    """Scaffold a real workspace via the production scaffold path (no
    pre-arranged .claude/settings.json beyond what the scaffold writes)."""
    ws = tmp_path / "second-machine-ws"
    ws.mkdir()
    run_first_run_scaffold(
        pos_root=tmp_path / ".pos",
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=tmp_path / "LaunchAgents",
        workspace_root=ws,
        persona_handle=DEFAULT_PERSONA_HANDLE,
    )
    return ws


def test_WIRE_2_one_time_setup_then_rerender_arrives_zero_action(
    tmp_path: Path,
) -> None:
    """★ A second workspace, after one-time setup ONLY, receives a
    re-rendered pack via a local-path marketplace with zero further user
    action."""
    # --- One-time setup: render a local marketplace + wire a fresh ws.
    marketplace = _render_local_marketplace(
        tmp_path / "local-marketplace", content_token="v1"
    )
    ws = _scaffold_workspace(tmp_path)

    setup = write_marketplace_wiring(
        workspace_root=ws,
        source=build_directory_source(marketplace.resolve()),
    )
    assert setup.wrote is True, "one-time setup did not wire the stanza"

    # The wiring delivers the zero-action mechanism: autoUpdate:true +
    # a directory source pointing at the live local marketplace.
    settings_before = json.loads(_settings_path(ws).read_text())
    entry_before = settings_before["extraKnownMarketplaces"][
        KNOWLEDGE_PACK_MARKETPLACE_NAME
    ]
    assert entry_before["autoUpdate"] is True
    assert entry_before["source"]["source"] == "directory"
    assert entry_before["source"]["path"] == str(marketplace.resolve())

    bytes_after_setup = _settings_path(ws).read_bytes()

    # --- Cadence update: the pack re-renders (content changes on disk
    # at the SAME local marketplace path the workspace already points
    # at). This is the "owner-approved publish" analog for the LOCAL
    # leg — a new render lands at the marketplace.
    _render_local_marketplace(marketplace, content_token="v2")
    new_skill = (
        marketplace / "plugins" / "loam-leverage" / "skills" / "leverage"
        / "SKILL.md"
    ).read_text()
    assert "v2" in new_skill, "re-render did not update the marketplace body"

    # --- ZERO further user action: the workspace's wiring is unchanged
    # and still points at the live marketplace with autoUpdate:true.
    # The user took NO action between setup and arrival; the platform's
    # startup auto-update (enabled by autoUpdate:true) is what pulls the
    # re-rendered content — loam's contract is that the workspace is a
    # zero-action recipient, which holds: re-running the wiring is a
    # strict no-op (nothing for the user to do), and the live
    # marketplace now carries v2.
    rewire = write_marketplace_wiring(
        workspace_root=ws,
        source=build_directory_source(marketplace.resolve()),
    )
    assert rewire.wrote is False
    assert rewire.reason == "already_current"
    assert _settings_path(ws).read_bytes() == bytes_after_setup

    # The marketplace the workspace points at carries the re-rendered
    # (v2) content — arrival is available with no user action taken.
    pointed_path = Path(
        json.loads(_settings_path(ws).read_text())[
            "extraKnownMarketplaces"
        ][KNOWLEDGE_PACK_MARKETPLACE_NAME]["source"]["path"]
    )
    arrived = (
        pointed_path / "plugins" / "loam-leverage" / "skills" / "leverage"
        / "SKILL.md"
    ).read_text()
    assert "v2" in arrived


def test_WIRE_2_setup_preserves_persona_binding_on_real_workspace(
    tmp_path: Path,
) -> None:
    """The one-time wiring on a real scaffolded workspace deep-merges
    the marketplace stanza WITHOUT disturbing whatever settings the
    scaffold already wrote (operator/persona keys survive) — the
    second-machine workspace stays fully functional."""
    marketplace = _render_local_marketplace(
        tmp_path / "local-marketplace", content_token="v1"
    )
    ws = _scaffold_workspace(tmp_path)

    # Capture whatever top-level keys the scaffold wrote (if any).
    before = (
        json.loads(_settings_path(ws).read_text())
        if _settings_path(ws).exists()
        else {}
    )
    pre_keys = {k for k in before if k != "extraKnownMarketplaces"}

    write_marketplace_wiring(
        workspace_root=ws,
        source=build_directory_source(marketplace.resolve()),
    )

    after = json.loads(_settings_path(ws).read_text())
    # Every pre-existing top-level key survives the merge.
    for k in pre_keys:
        assert k in after, f"scaffold key {k!r} dropped by marketplace merge"
        assert after[k] == before[k]
    # The marketplace stanza is present.
    assert (
        KNOWLEDGE_PACK_MARKETPLACE_NAME in after["extraKnownMarketplaces"]
    )

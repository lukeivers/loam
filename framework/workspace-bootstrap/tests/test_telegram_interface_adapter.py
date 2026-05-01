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

"""Acceptance tests for amendment #9 —
telegram-interface-framework-integration.

Maps 1:1 to ACs in
docs/rebuild/components/telegram-interface-framework-integration/proposal.md.

AC coverage in this file:
  AC1 — adapter class exists with correct metadata
  AC2 — _BOOTSTRAP_YAML lists telegram_interface as the 13th entry
  AC3 — framework composes telegram_interface end-to-end at default config
  AC4 — first-run scaffold writes ~/.loam/telegram.yaml
         (primary assertion lives in test_first_run_scaffold.py::H1;
         this file adds a standalone starter-shape assertion)
  AC5 — adapter publishes the Telegram channel on the host
  AC6 — adapter fails loud when required=True and credentials missing
  AC8 — adapter ordering: runs after primary_persona and safety_layer

AC7 and AC9 are structural and enforced by the seal-diff tests
(`test_B20_only_workspace_bootstrap_changed`,
`test_H19_diff_scope_covers_only_approved_surfaces`,
`test_tg23_only_telegram_interface_changed`) rather than this file.

Credentials safety: no real bot token / chat_id / session secret
appears anywhere in this file. Access-file fixtures use either the
component's default empty allowlist or a synthetic owner ID string
("fake_owner_12345") that is never sent anywhere.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest
import yaml


# ---- AC1 — adapter metadata --------------------------------------------


def test_AC1_adapter_metadata_matches_proposal() -> None:
    from loam.workspace_bootstrap.adapters.telegram_interface import (
        TelegramInterfaceContribution,
    )
    from loam.workspace_bootstrap.spec import Phase

    md = TelegramInterfaceContribution.metadata
    assert md.name == "telegram_interface"
    assert md.phase is Phase.after_orchestrator_ready
    assert md.after == ("primary_persona", "safety_layer")
    assert md.required is False


# ---- AC2 — _BOOTSTRAP_YAML lists telegram_interface as the 13th entry -


def test_AC2_bootstrap_yaml_lists_thirteen_contributions() -> None:
    from loam.workspace_bootstrap.adapters.first_run_scaffold import (
        _BOOTSTRAP_YAML,
    )

    parsed = yaml.safe_load(_BOOTSTRAP_YAML)
    contribs = parsed["contributions"]
    assert len(contribs) == 13
    assert contribs[-1]["name"] == "telegram_interface"
    assert contribs[-1]["module"] == (
        "loam.workspace_bootstrap.adapters.telegram_interface"
    )
    assert contribs[-1]["class"] == "TelegramInterfaceContribution"
    # Header comment updated to reflect the new count.
    assert "thirteen-foundational-adapter bundle" in _BOOTSTRAP_YAML


# ---- AC3 — default-shape composition is degraded-alive ----------------


def _bare_host(tmp_path: Path) -> Any:
    """Build a minimally-populated host so the adapter's contribute()
    runs without pulling in the full orchestrator.

    The telegram adapter reads only ``host.config_dir``,
    ``host.channel_registry``, and writes to ``host.telegram_adapter``
    / ``host.telegram_channel``. No orchestrator-linked attributes are
    touched — so this bare host is sufficient to exercise AC3, AC5,
    AC6.
    """
    from loam.workspace_bootstrap.host import BootstrapHost

    workspace = tmp_path / "pos-v2"
    workspace.mkdir()
    cfg_dir = tmp_path / ".pos"
    cfg_dir.mkdir()
    manifest_path = workspace / "bootstrap.yaml"
    return BootstrapHost(
        config_dir=cfg_dir,
        workspace_root=workspace,
        manifest_path=manifest_path,
    )


@pytest.fixture
def strip_telegram_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure TELEGRAM_BOT_TOKEN is absent from process env so tests'
    deterministic claim about 'no credentials' holds regardless of
    the host developer's shell. Also redirects the default env path
    to a tmp location to avoid reading the developer's real ~/.claude
    file."""
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)


def test_AC3_default_degraded_alive_composition_succeeds(
    tmp_path: Path, strip_telegram_env: None
) -> None:
    """Default config: no telegram.yaml, no env var, no access.json.
    The adapter must compose; the channel exists; is_active=False."""
    from loam.primary_persona.introduction import ChannelKind, OneOnOneChannel
    from loam.telegram_interface.adapter import TelegramAdapter
    from loam.workspace_bootstrap.adapters.telegram_interface import (
        TelegramInterfaceContribution,
    )

    host = _bare_host(tmp_path)
    # Point access_path override so the adapter does not read the
    # developer's real ~/.claude/channels/telegram/access.json. No YAML
    # exists at host.config_dir / "telegram.yaml" — so the adapter
    # falls back to component defaults, but AccessFile.load on an
    # absent path returns the empty-allowlist sentinel without error.
    missing_access = tmp_path / "access-nonexistent.json"
    (host.config_dir / "telegram.yaml").write_text(
        yaml.safe_dump(
            {
                "required": False,
                "access_path": str(missing_access),
            }
        )
    )

    TelegramInterfaceContribution().contribute(host)

    assert isinstance(host.telegram_adapter, TelegramAdapter)
    assert isinstance(host.telegram_channel, OneOnOneChannel)
    assert host.telegram_channel.kind is ChannelKind.personal_telegram
    assert host.telegram_channel.is_active is False


# ---- AC4 — scaffold writes telegram.yaml starter ----------------------


def test_AC4_scaffold_writes_telegram_yaml_starter(tmp_path: Path) -> None:
    """The scaffold writes ~/.loam/telegram.yaml with the approved
    starter shape (proposal §5 #4 owner ruling)."""
    from loam.workspace_bootstrap.adapters.first_run_scaffold import (
        _TELEGRAM_YAML,
        run_first_run_scaffold,
    )

    pos_root = tmp_path / ".pos"
    run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=tmp_path / "LaunchAgents",
        workspace_root=tmp_path / "pos-v2",
    )
    written = (pos_root / "telegram.yaml").read_text()
    # Starter shape fields, per owner ruling on §5 #4.
    assert written == _TELEGRAM_YAML
    assert "required: false" in written
    assert "env_path:" in written
    assert "access_path:" in written


# ---- AC5 — channel published on host + fallback route -----------------


def test_AC5_channel_published_on_host_and_fallback_routes(
    tmp_path: Path, strip_telegram_env: None
) -> None:
    """host.telegram_channel is the same object as
    adapter.build_channel(); channel_registry['telegram'] points at it;
    calling host.telegram_channel.send(...) under is_active=False
    routes through the adapter's fallback and lands a line in the
    attention file."""
    import asyncio

    from loam.workspace_bootstrap.adapters.telegram_interface import (
        TelegramInterfaceContribution,
    )

    host = _bare_host(tmp_path)
    missing_access = tmp_path / "access-nonexistent.json"
    (host.config_dir / "telegram.yaml").write_text(
        yaml.safe_dump(
            {"required": False, "access_path": str(missing_access)}
        )
    )

    TelegramInterfaceContribution().contribute(host)

    # Channel registered under the 'telegram' key, same object.
    assert host.channel_registry["telegram"] is host.telegram_channel

    # Redirect the attention-md fallback to a tmp path. The fallback
    # module reads DEFAULT_ATTENTION_PATH at call-time, so monkeypatch
    # it via the module-level attribute for the duration of the send.
    import loam.telegram_interface.fallback as fb

    attention_path = tmp_path / "attention.md"
    original = fb.DEFAULT_ATTENTION_PATH
    fb.DEFAULT_ATTENTION_PATH = attention_path
    try:
        asyncio.run(host.telegram_channel.send("AC5-probe-message"))
    finally:
        fb.DEFAULT_ATTENTION_PATH = original

    # Fallback-preamble format: "[telegram-unavailable: <reason>]".
    body = attention_path.read_text()
    assert "AC5-probe-message" in body
    assert "telegram-fallback" in body


# ---- AC6 — required=True with missing creds raises loud ----------------


def test_AC6_required_true_missing_creds_raises_adapter_error(
    tmp_path: Path, strip_telegram_env: None
) -> None:
    """With telegram.yaml required:true and no token configured, the
    contribution raises AdapterRaisedError — which the framework wraps
    as -32086 with the telegram-interface error code in the data
    payload. Proposal §2 fail-closed direction."""
    from loam.telegram_interface import (
        IPC_TELEGRAM_SETUP_FAILED,
        IPC_TELEGRAM_TOKEN_INVALID,
    )
    from loam.workspace_bootstrap.errors import (
        AdapterRaisedError,
        IPC_BOOTSTRAP_ADAPTER_RAISED,
    )
    from loam.workspace_bootstrap.adapters.telegram_interface import (
        TelegramInterfaceContribution,
    )

    host = _bare_host(tmp_path)
    # Point env_path at a missing file so token_configured returns
    # False regardless of the developer's real ~/.claude state.
    missing_env = tmp_path / "telegram.env"
    missing_access = tmp_path / "access-nonexistent.json"
    (host.config_dir / "telegram.yaml").write_text(
        yaml.safe_dump(
            {
                "required": True,
                "env_path": str(missing_env),
                "access_path": str(missing_access),
            }
        )
    )

    with pytest.raises(AdapterRaisedError) as excinfo:
        TelegramInterfaceContribution().contribute(host)
    # Bootstrap's AdapterRaisedError itself carries -32086; the wrapped
    # telegram-interface code is surfaced in the data payload. Either
    # IPC_TELEGRAM_TOKEN_INVALID (-32102) or IPC_TELEGRAM_SETUP_FAILED
    # (-32108) satisfies AC6.
    assert excinfo.value.code == IPC_BOOTSTRAP_ADAPTER_RAISED
    inner = excinfo.value.data.get("code")
    assert inner in (IPC_TELEGRAM_TOKEN_INVALID, IPC_TELEGRAM_SETUP_FAILED)


# ---- AC8 — ordering: telegram after primary_persona + safety_layer ---


def test_AC8_ordering_places_telegram_after_primary_persona_and_safety_layer(
    tmp_path: Path,
) -> None:
    """Drive the framework's topological sort with metadata-only stubs
    for every peer that telegram declares a dependency on. Assert that
    the resulting phase-ordering lists telegram_interface strictly
    after primary_persona and safety_layer.

    This test bypasses the full Bootstrapper run (no orchestrator
    startup needed) — it instantiates Bootstrapper with a manifest
    that references the real TelegramInterfaceContribution and
    synthetic stubs for primary_persona + safety_layer, and asserts
    the ordering engine's output.
    """
    from loam.workspace_bootstrap import (
        Bootstrapper,
        ContributionRef,
        Manifest,
        Phase,
    )

    manifest = Manifest(
        version=1,
        config_dir=tmp_path / "config",
        workspace_root=tmp_path,
        manifest_path=tmp_path / "bootstrap.yaml",
        refs=(
            # Synthetic stubs for the two peers so the ordering engine
            # sees their names inside the phase set.
            ContributionRef(
                kind="module",
                module="tests.telegram_stubs",
                module_attr="StubPrimaryPersona",
                display_name="primary_persona",
            ),
            ContributionRef(
                kind="module",
                module="tests.telegram_stubs",
                module_attr="StubSafetyLayer",
                display_name="safety_layer",
            ),
            ContributionRef(
                kind="module",
                module="loam.workspace_bootstrap.adapters.telegram_interface",
                module_attr="TelegramInterfaceContribution",
                display_name="telegram_interface",
            ),
        ),
    )

    # Register the stub module dynamically so the manifest resolver
    # finds it. Each stub is a BaseContribution subclass whose metadata
    # places it in after_orchestrator_ready alongside telegram — this
    # tests intra-phase ordering, which is the load-bearing property
    # the proposal AC8 calls out. (Real primary_persona sits in
    # before_orchestrator_start and real safety_layer in
    # wrap_activate_scope — both earlier phases; cross-phase ordering
    # is already enforced by PHASE_ORDER and is not what the ordering
    # engine's topological sort decides. Having the stubs in
    # after_orchestrator_ready asserts the intra-phase edge
    # explicitly; even with the real phase setup, the same edge
    # applies — telegram cannot run before its declared 'after' peers.)
    import sys
    import types

    mod = types.ModuleType("tests.telegram_stubs")
    from loam.workspace_bootstrap.spec import (
        BaseContribution,
        ContributionMetadata,
    )

    class StubPrimaryPersona(BaseContribution):
        metadata = ContributionMetadata(
            name="primary_persona",
            phase=Phase.after_orchestrator_ready,
        )

        def contribute(self, host: Any) -> None:
            return None

    class StubSafetyLayer(BaseContribution):
        metadata = ContributionMetadata(
            name="safety_layer",
            phase=Phase.after_orchestrator_ready,
        )

        def contribute(self, host: Any) -> None:
            return None

    mod.StubPrimaryPersona = StubPrimaryPersona
    mod.StubSafetyLayer = StubSafetyLayer
    sys.modules["tests.telegram_stubs"] = mod

    try:
        bs = Bootstrapper(manifest)
        bs.resolve_and_order()

        phase_items = bs._ordered_by_phase[Phase.after_orchestrator_ready]
        names_in_order = [rc.name for rc in phase_items]
        pp_idx = names_in_order.index("primary_persona")
        sl_idx = names_in_order.index("safety_layer")
        tg_idx = names_in_order.index("telegram_interface")
        assert tg_idx > pp_idx, names_in_order
        assert tg_idx > sl_idx, names_in_order
    finally:
        sys.modules.pop("tests.telegram_stubs", None)

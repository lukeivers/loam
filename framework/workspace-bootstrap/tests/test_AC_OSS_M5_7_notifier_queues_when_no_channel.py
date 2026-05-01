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

"""AC.OSS-M5.7 — Notifier composes against pre-empty channel_registry.

Per amendment #86 (M5 wire-dormancy). The dormancy adapter runs in
``before_orchestrator_start`` (after primary_persona); the
``telegram_interface`` adapter that populates ``host.channel_registry``
runs later in ``after_orchestrator_ready``. Therefore at dormancy
adapter run time the registry is empty. The notifier must construct
without error and rely on the existing
queue-on-no-active-channel behaviour (notification.py:119) — pending
notifications accumulate in ``_pending_queue`` until a channel
registers.

Programme: OSS v0.1.0 publish — M5 — wire-dormancy.
Plan: docs/rebuild/plans/oss-v0-1-0-publish-dormancy-constructor.md.
AC family: AC.OSS-M5.7.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def fake_host_empty_channels(tmp_path: Path):
    from loam.orchestrator import Orchestrator
    from loam.orchestrator.config import OrchestratorConfig
    from loam.scope_of_work import ScopeRuntime
    from loam.workspace_bootstrap.host import BootstrapHost

    cfg_dir = tmp_path / ".loam"
    cfg_dir.mkdir()
    workspace = tmp_path / "ws"
    workspace.mkdir()
    manifest = workspace / "bootstrap.yaml"

    pos_root = tmp_path / "pos-root"
    pos_root.mkdir()
    orch_cfg = OrchestratorConfig(root_dir=pos_root)
    orch_cfg.ensure_dirs()
    orch = Orchestrator(orch_cfg)

    host = BootstrapHost(
        config_dir=cfg_dir,
        workspace_root=workspace,
        manifest_path=manifest,
    )
    host.orchestrator = orch
    host.scope_runtime = ScopeRuntime(
        orch_cfg.scope_of_work_db,
        pending_extension_dir=orch_cfg.pending_extension_dir,
    )
    # channel_registry stays empty (no telegram_interface yet).
    assert host.channel_registry == {}

    yield host

    try:
        host.scope_runtime.close()
    except Exception:
        pass


@pytest.mark.asyncio
async def test_AC_OSS_M5_7_notifier_constructed_with_empty_channels(
    fake_host_empty_channels,
) -> None:
    """The adapter completes without error against an empty
    channel_registry; the resulting notifier holds no channels."""
    from loam.workspace_bootstrap.adapters.dormancy import (
        DormancyContribution,
    )

    await DormancyContribution().contribute(fake_host_empty_channels)

    notifier = fake_host_empty_channels.dormancy.notifier
    assert list(notifier.channels) == []


@pytest.mark.asyncio
async def test_AC_OSS_M5_7_notification_queues_when_no_channel(
    fake_host_empty_channels,
) -> None:
    """A synthetic notification fired against the no-channel notifier
    is queued in ``_pending_queue`` rather than raising."""
    from loam.dormancy.notification import (
        DegradationNotification,
        NotificationTier,
        ThresholdTrigger,
    )
    from loam.workspace_bootstrap.adapters.dormancy import (
        DormancyContribution,
    )

    await DormancyContribution().contribute(fake_host_empty_channels)
    notifier = fake_host_empty_channels.dormancy.notifier

    notif = DegradationNotification(
        episode_id="test-ep",
        tier=NotificationTier.tier_2,
        threshold_triggered=ThresholdTrigger.time,
        text="synthetic test alert",
        kind="alert",
    )

    delivered = await notifier.send(notif)

    # No active channel → queued, not delivered.
    assert delivered is False
    assert len(notifier._pending_queue) == 1
    assert notifier._pending_queue[0]["episode_id"] == "test-ep"

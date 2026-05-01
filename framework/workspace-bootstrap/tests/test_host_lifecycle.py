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

"""B10, B11 — BootstrapHost + lifecycle."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import pytest

from loam.workspace_bootstrap import (
    BaseContribution,
    Bootstrapper,
    ContributionMetadata,
    HostAttributeNotYetAvailable,
    Phase,
    load_manifest,
)


# B10 — host exposes singletons, `.require()` errors on too-early read.


def test_B10_require_errors_when_not_populated(tmp_path: Path, write_manifest_fn) -> None:
    path = write_manifest_fn(tmp_path / "bootstrap.yaml", [])
    bs = Bootstrapper(load_manifest(path))
    with pytest.raises(HostAttributeNotYetAvailable):
        bs.host.require("orchestrator")


def test_B10_host_has_framework_singletons(tmp_path: Path, write_manifest_fn) -> None:
    path = write_manifest_fn(tmp_path / "bootstrap.yaml", [])
    bs = Bootstrapper(load_manifest(path))
    assert bs.host.config_dir is not None
    assert bs.host.workspace_root is not None
    assert bs.host.manifest_path is not None
    assert bs.host.tracer is not None
    assert isinstance(bs.host.channel_registry, dict)


# B11 — shutdown reverses startup; a raising adapter cascades teardown
# of earlier-registered hooks.


@pytest.mark.asyncio
async def test_B11_shutdown_reverses_startup(tmp_path: Path, write_manifest_fn) -> None:
    adapter = tmp_path / "adapter.py"
    adapter.write_text(
        "from loam.workspace_bootstrap import BaseContribution, ContributionMetadata, Phase\n"
        "RUN = []\n"
        "SHUT = []\n"
        "class A(BaseContribution):\n"
        "    metadata = ContributionMetadata(name='a', phase=Phase.before_orchestrator_start)\n"
        "    def contribute(self, host):\n"
        "        RUN.append('a')\n"
        "        host.register_shutdown('a', lambda: SHUT.append('a'))\n"
        "class B(BaseContribution):\n"
        "    metadata = ContributionMetadata(name='b', phase=Phase.before_orchestrator_start, after=('a',))\n"
        "    def contribute(self, host):\n"
        "        RUN.append('b')\n"
        "        host.register_shutdown('b', lambda: SHUT.append('b'))\n"
    )
    path = write_manifest_fn(
        tmp_path / "bootstrap.yaml",
        [
            {"name": "a", "path": "./adapter.py", "attr": "A"},
            {"name": "b", "path": "./adapter.py", "attr": "B"},
        ],
    )
    bs = Bootstrapper(load_manifest(path))
    await bs.start()
    await bs.shutdown()

    # Inspect RUN / SHUT by re-importing the sys.modules entry that
    # corresponds to THIS test's adapter file.
    import sys

    wanted_hash = abs(hash(str(adapter.resolve())))
    mod_key = f"_pos_workspace_bootstrap_path_{wanted_hash}"
    assert mod_key in sys.modules, (
        f"adapter module {mod_key!r} should be cached in sys.modules"
    )
    mod = sys.modules[mod_key]
    assert mod.RUN == ["a", "b"]
    assert mod.SHUT == ["b", "a"]  # reverse order.


@pytest.mark.asyncio
async def test_B11_partial_startup_failure_cancels_siblings(
    tmp_path: Path, write_manifest_fn
) -> None:
    """An adapter raising mid-startup propagates (so caller can tear down)
    and earlier shutdown hooks still fire. No adapter is left orphaned."""
    adapter = tmp_path / "adapter.py"
    adapter.write_text(
        "from loam.workspace_bootstrap import BaseContribution, ContributionMetadata, Phase\n"
        "RUN = []\n"
        "SHUT = []\n"
        "class OK(BaseContribution):\n"
        "    metadata = ContributionMetadata(name='ok', phase=Phase.before_orchestrator_start)\n"
        "    def contribute(self, host):\n"
        "        RUN.append('ok')\n"
        "        host.register_shutdown('ok', lambda: SHUT.append('ok'))\n"
        "class BAD(BaseContribution):\n"
        "    metadata = ContributionMetadata(name='bad', phase=Phase.before_orchestrator_start, after=('ok',))\n"
        "    def contribute(self, host):\n"
        "        raise RuntimeError('boom')\n"
    )
    path = write_manifest_fn(
        tmp_path / "bootstrap.yaml",
        [
            {"name": "ok", "path": "./adapter.py", "attr": "OK"},
            {"name": "bad", "path": "./adapter.py", "attr": "BAD"},
        ],
    )
    from loam.workspace_bootstrap import AdapterRaisedError

    bs = Bootstrapper(load_manifest(path))
    with pytest.raises(AdapterRaisedError) as excinfo:
        await bs.start()
    assert "bad" in excinfo.value.message
    # Caller runs shutdown to reverse the partial startup.
    await bs.shutdown()
    import sys

    wanted_hash = abs(hash(str(adapter.resolve())))
    mod_key = f"_pos_workspace_bootstrap_path_{wanted_hash}"
    mod = sys.modules[mod_key]
    assert mod.RUN == ["ok"]
    assert mod.SHUT == ["ok"]  # earlier hook fired.

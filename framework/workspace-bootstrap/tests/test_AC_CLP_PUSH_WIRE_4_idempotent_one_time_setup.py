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

"""AC.CLP-PUSH-WIRE.4 (claude-leverage-program Slice 4b).

Setup is genuinely one-time: a re-run of the wiring on an
already-wired workspace is a strict no-op (``already_current``, no
mtime churn). There is no per-cycle user step beyond the platform's
own ``/reload-plugins`` prompt (named, not owned — plan §10 F2.2). This
is what makes "zero user action after the one-time bootstrap" true: the
bootstrap IS the one-time setup, and re-invocation changes nothing.
"""

from __future__ import annotations

from pathlib import Path

from loam.workspace_bootstrap.adapters.marketplace_wiring import (
    SETTINGS_JSON_FILENAME,
    build_directory_source,
    write_marketplace_wiring,
)


def _settings_path(workspace_root: Path) -> Path:
    return workspace_root / ".claude" / SETTINGS_JSON_FILENAME


def test_WIRE_4_re_run_is_strict_no_op_already_current(
    tmp_path: Path,
) -> None:
    """A second wiring invocation against an already-current
    settings.json returns ``already_current`` / ``wrote=False`` and the
    on-disk bytes are byte-identical (no mtime churn)."""
    ws = tmp_path / "ws"
    ws.mkdir()
    pack_dir = tmp_path / "marketplace"
    pack_dir.mkdir()
    source = build_directory_source(pack_dir)

    first = write_marketplace_wiring(workspace_root=ws, source=source)
    assert first.wrote is True
    assert first.reason == "fresh_write"

    bytes_after_first = _settings_path(ws).read_bytes()

    second = write_marketplace_wiring(workspace_root=ws, source=source)
    assert second.wrote is False
    assert second.reason == "already_current"
    assert _settings_path(ws).read_bytes() == bytes_after_first


def test_WIRE_4_malformed_existing_settings_is_failsoft_preserved(
    tmp_path: Path,
) -> None:
    """A malformed pre-existing settings.json is fail-soft: the writer
    declines (``skipped_malformed_existing``) and preserves the user's
    file unmodified rather than aborting the bootstrap or clobbering
    content."""
    ws = tmp_path / "ws"
    (ws / ".claude").mkdir(parents=True)
    pack_dir = tmp_path / "marketplace"
    pack_dir.mkdir()

    garbage = "{ this is not valid json "
    _settings_path(ws).write_text(garbage)

    result = write_marketplace_wiring(
        workspace_root=ws, source=build_directory_source(pack_dir)
    )
    assert result.wrote is False
    assert result.reason == "skipped_malformed_existing"
    # User's file untouched.
    assert _settings_path(ws).read_text() == garbage

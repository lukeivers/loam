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

"""Shared fixtures for the frame-kernel AC tests.

Puts ``framework/frame-kernel/src`` on ``sys.path`` so ``loam.frame_kernel``
imports in the source tree without an editable install, and exposes the
on-disk repo-root microkernel path the AC tests assert against.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_COMPONENT_ROOT = Path(__file__).resolve().parent.parent
_SRC = _COMPONENT_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# Repo root = framework/frame-kernel/../.. -> the loam repo tip.
REPO_ROOT = _COMPONENT_ROOT.parent.parent
KERNEL_FILE = REPO_ROOT / "kernel" / "loam-microkernel.md"


@pytest.fixture
def real_kernel_workspace(tmp_path: Path) -> Path:
    """A tmp workspace whose ``kernel/loam-microkernel.md`` is a verbatim
    copy of the repo's real microkernel.

    Lets the AC tests exercise the production file-read path against the
    REAL microkernel content (so AC.SACH.1/2 assert the shipped TCB, not
    a fixture stand-in) while keeping the test workspace isolated.
    """
    kernel_dir = tmp_path / "kernel"
    kernel_dir.mkdir(parents=True, exist_ok=True)
    (kernel_dir / "loam-microkernel.md").write_text(
        KERNEL_FILE.read_text(encoding="utf-8"), encoding="utf-8"
    )
    return tmp_path


def make_envelope(workspace_root: Path, *, task_text: str = "") -> dict:
    """Build a SubagentStart envelope of the shape the hook parses."""
    env: dict = {"workspace": {"project_dir": str(workspace_root)}}
    if task_text:
        env["prompt"] = task_text
    return env

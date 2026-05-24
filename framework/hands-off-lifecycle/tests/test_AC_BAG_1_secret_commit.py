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

"""AC.BAG.1 — Post-migration regression: bash_guard NO LONGER fires
on secret-FILE commits.

As of the 2026-05-24 Wave 1 ECC absorption (security-hooks-bundle
amendment, D-SECHK.OVERLAP partial-absorb), the B2 secret-FILE
detection migrated from
``plugins/dev-sdlc/hooks/bash_guard.py`` to
``framework/safety-layer/hooks/secret_pattern_guard.py``. The
canonical detection now lives in safety-layer, in ALL workspaces.

This test file asserts the migration is complete from the
bash_guard side:

  * AC.SECHK.B2-MIGRATION-2 (no-double-fire) — bash_guard's
    ``evaluate()`` returns allow / no-op on the inputs that
    formerly returned deny+secret-commit. Both hooks fire-deny
    would be a regression that the persona surfaces twice.
  * The behavior-parity tests for the migrated detection live at
    ``framework/safety-layer/tests/test_AC_SECHK_B2_MIGRATION_*.py``
    (AC.SECHK.B2-MIGRATION-1 and -3).

Note: prior to the migration this file asserted bash_guard returned
deny+secret-commit; the assertions are NOW inverted (no-deny /
no-secret-commit-failure-class) per the migration spec.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
PLUGIN_HOOKS_DIR = REPO_ROOT / "plugins" / "dev-sdlc" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))
if PLUGIN_HOOKS_DIR.exists():
    sys.path.insert(0, str(PLUGIN_HOOKS_DIR))


@pytest.fixture
def gate(monkeypatch, tmp_path):
    """Import bash_guard fresh."""
    import bash_guard
    return bash_guard


def test_AC_BAG_1_git_add_dotenv_no_longer_denies(tmp_path, gate) -> None:
    """git add .env via bash_guard → allow / no-op (B2 migrated)."""
    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={"command": "git add .env"},
    )
    assert decision.decision in ("allow", "no-op")
    assert decision.failure_class != "secret-commit"


def test_AC_BAG_1_git_commit_pem_no_longer_denies(tmp_path, gate) -> None:
    """git commit foo.pem via bash_guard → allow / no-op."""
    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={"command": "git commit -m 'leak' foo.pem"},
    )
    assert decision.decision in ("allow", "no-op")
    assert decision.failure_class != "secret-commit"


def test_AC_BAG_1_id_rsa_no_longer_denies(tmp_path, gate) -> None:
    """git stash with id_rsa via bash_guard → allow / no-op."""
    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={"command": "git stash push -- id_rsa"},
    )
    assert decision.decision in ("allow", "no-op")
    assert decision.failure_class != "secret-commit"


def test_AC_BAG_1_credentials_json_no_longer_denies(tmp_path, gate) -> None:
    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={"command": "git add credentials.json"},
    )
    assert decision.decision in ("allow", "no-op")
    assert decision.failure_class != "secret-commit"


def test_AC_BAG_1_dotenv_example_admitted(tmp_path, gate) -> None:
    """git add .env-example → no-op (universally admitted)."""
    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={"command": "git add .env-example"},
    )
    assert decision.decision in ("allow", "no-op")
    assert decision.failure_class is None


def test_AC_BAG_1_normal_file_admitted(tmp_path, gate) -> None:
    """git add normal.py → admitted."""
    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={"command": "git add normal.py"},
    )
    assert decision.decision in ("allow", "no-op")


def test_AC_BAG_1_non_bash_tool_no_op(tmp_path, gate) -> None:
    """tool_name != 'Bash' → no-op."""
    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Edit",
        tool_input={"command": "git add .env"},
    )
    assert decision.decision == "no-op"

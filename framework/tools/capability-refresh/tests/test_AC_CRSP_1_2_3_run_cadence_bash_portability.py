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

"""AC.CRSP.1-3 — run-cadence.sh bash-portability (Capability-Refresh Shell
Portability).

The #193 GitHub Actions cadence binding runs
``framework/tools/capability-refresh/scripts/run-cadence.sh`` on
``ubuntu-latest``, which has no ``zsh``. The pre-fix script shipped with a
``#!/bin/zsh`` shebang and a zsh-only ``SCRIPT_DIR="${0:A:h}"`` — the kernel
cannot exec ``/bin/zsh`` there (exit 127) and ``${0:A:h}`` has no bash
equivalent, so the refresh never ran. This module proves the fixed script
runs under bash with zsh ABSENT.

Method (builder's call): each test builds a throwaway repo tree at the same
relative depth the script expects, drops the script in, and runs it under a
CONTROLLED PATH whose only entries are real ``bash`` + ``dirname`` symlinks
and stub ``python3`` + ``git``. ``zsh`` is genuinely unresolvable on that
PATH (asserted as a precondition), so the "zsh absent" condition is real and
portable to both Ubuntu and macOS (macOS ships ``/bin/zsh``, so excluding the
system dirs is what makes the condition hold on the dev machine too). The
stub ``python3`` captures its cwd / PYTHONPATH / argv and does no I/O.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REAL_SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts" / "run-cadence.sh"
)

# The two constructs the fix replaced (reversed here to reconstruct the
# pre-fix zsh-only artifact from the real fixed script — keeps the
# regression coupled to the shipped file rather than a frozen copy).
FIXED_SHEBANG = "#!/usr/bin/env bash"
ZSH_SHEBANG = "#!/bin/zsh"
FIXED_SCRIPT_DIR = 'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"'
ZSH_SCRIPT_DIR = 'SCRIPT_DIR="${0:A:h}"'


def _real_bin(name: str) -> str:
    path = shutil.which(name)
    if path is None:  # pragma: no cover - environment guarantee
        pytest.skip(f"required real binary {name!r} not found on PATH")
    return path


def _build_tree(root: Path, script_text: str) -> Path:
    """Fake repo tree at the depth run-cadence.sh resolves against; returns
    the script path."""
    scripts_dir = root / "framework" / "tools" / "capability-refresh" / "scripts"
    scripts_dir.mkdir(parents=True)
    (root / "docs" / "capability-corpus").mkdir(parents=True)
    script = scripts_dir / "run-cadence.sh"
    script.write_text(script_text, encoding="utf-8")
    script.chmod(0o755)
    return script


def _controlled_bin(
    cbin: Path,
    capture: Path,
    *,
    git_diff_quiet_exit: int = 0,
    git_log: Path | None = None,
) -> Path:
    """A PATH dir with ONLY: real bash + dirname (symlinked), stub python3 +
    git. zsh is absent by construction."""
    cbin.mkdir()
    os.symlink(_real_bin("bash"), cbin / "bash")
    os.symlink(_real_bin("dirname"), cbin / "dirname")

    # stub python3: capture cwd / PYTHONPATH / argv, do nothing else.
    py = cbin / "python3"
    py.write_text(
        "#!/bin/sh\n"
        f'{{\n'
        f'  echo "CWD=$(pwd)"\n'
        f'  echo "PYTHONPATH=$PYTHONPATH"\n'
        f'  echo "ARGS=$*"\n'
        f'}} > "{capture}"\n'
        "exit 0\n",
        encoding="utf-8",
    )
    py.chmod(0o755)

    # stub git: log invocations; `diff` returns the configured code
    # (0 = no corpus changes, 1 = changes present), everything else exits 0.
    gitlog_line = f'echo "$*" >> "{git_log}"\n' if git_log is not None else ""
    git = cbin / "git"
    git.write_text(
        "#!/bin/sh\n"
        f"{gitlog_line}"
        'case "$1" in\n'
        f"  diff) exit {git_diff_quiet_exit} ;;\n"
        "  *) exit 0 ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    git.chmod(0o755)
    return cbin


def _parse_capture(capture: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in capture.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k] = v
    return out


def test_AC_CRSP_1_bash_execution_reaches_entrypoint(tmp_path) -> None:
    """AC.CRSP.1 ★ (outcome-altitude) — the REAL fixed script, executed via
    its own shebang under a genuinely zsh-free PATH, reaches
    ``python3 -m capability_refresh --cadence-class all`` with cwd == repo
    root and PYTHONPATH including the component src."""
    root = tmp_path / "repo"
    script = _build_tree(root, REAL_SCRIPT.read_text(encoding="utf-8"))
    capture = tmp_path / "capture.txt"
    cbin = _controlled_bin(tmp_path / "cbin", capture, git_diff_quiet_exit=0)

    # Precondition: zsh is genuinely absent on the PATH under test.
    assert shutil.which("zsh", path=str(cbin)) is None, (
        "test harness invalid: zsh resolvable on the controlled PATH"
    )
    assert shutil.which("bash", path=str(cbin)) is not None

    # Execute via the script's OWN shebang. Launch from an unrelated cwd to
    # prove REPO_ROOT is resolved from $0, not inherited from the caller.
    proc = subprocess.run(
        [str(script), "all"],
        env={"PATH": str(cbin)},
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, (
        f"script did not exit 0 under bash/zsh-absent: "
        f"rc={proc.returncode} stderr={proc.stderr!r}"
    )
    assert capture.exists(), (
        "python3 entry-point was never reached "
        f"(stdout={proc.stdout!r} stderr={proc.stderr!r})"
    )
    cap = _parse_capture(capture)
    # Working directory correctly resolved to the repo root.
    assert cap["CWD"] == str(root)
    # PYTHONPATH points at the component src.
    assert cap["PYTHONPATH"].startswith(
        str(root / "framework" / "tools" / "capability-refresh" / "src")
    )
    # The deterministic refresh module invoked with the requested class.
    assert cap["ARGS"] == "-m capability_refresh --cadence-class all"


def test_AC_CRSP_2_zsh_only_form_regresses(tmp_path) -> None:
    """AC.CRSP.2 (regression) — the zsh-only ``${0:A:h}`` form fails to reach
    the entry-point under bash while the fixed form reaches it; a
    shell-portability break cannot silently return.

    Both forms are run under ``bash`` explicitly (the shebang is neutralised)
    so the test isolates the body-portability defect and stays identical on
    macOS and Ubuntu — where a shebang-exec RED is impossible because macOS
    ships ``/bin/zsh``."""
    fixed_text = REAL_SCRIPT.read_text(encoding="utf-8")
    # Reconstruct the pre-fix zsh-only artifact from the shipped file.
    assert FIXED_SHEBANG in fixed_text and FIXED_SCRIPT_DIR in fixed_text
    zsh_text = fixed_text.replace(FIXED_SHEBANG, ZSH_SHEBANG).replace(
        FIXED_SCRIPT_DIR, ZSH_SCRIPT_DIR
    )
    assert ZSH_SCRIPT_DIR in zsh_text

    bash = _real_bin("bash")

    def _run(script_text: str, tag: str):
        root = tmp_path / f"repo-{tag}"
        script = _build_tree(root, script_text)
        capture = tmp_path / f"capture-{tag}.txt"
        cbin = _controlled_bin(
            tmp_path / f"cbin-{tag}", capture, git_diff_quiet_exit=0
        )
        assert shutil.which("zsh", path=str(cbin)) is None
        proc = subprocess.run(
            [bash, str(script), "all"],
            env={"PATH": str(cbin)},
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
        )
        return proc, capture, root

    fixed_proc, fixed_cap, fixed_root = _run(fixed_text, "fixed")
    zsh_proc, zsh_cap, _ = _run(zsh_text, "zsh")

    # GREEN on the fix: entry-point reached, repo root correctly resolved.
    assert fixed_proc.returncode == 0
    assert fixed_cap.exists()
    assert _parse_capture(fixed_cap)["CWD"] == str(fixed_root)

    # RED on the old form: the zsh-only expansion breaks under bash, so the
    # entry-point is NEVER reached.
    assert not zsh_cap.exists(), (
        "regression guard defused: the zsh-only form reached python3 "
        "under bash — the portability break would not be caught"
    )
    assert zsh_proc.returncode != 0

    # Shebang tripwire: the shipped shebang resolves to bash via env, never a
    # hardcoded /bin/zsh (the interpreter absent on the Ubuntu runner).
    shipped_shebang = fixed_text.splitlines()[0]
    assert shipped_shebang == FIXED_SHEBANG
    assert "zsh" not in shipped_shebang


def test_AC_CRSP_3a_no_commit_opt_in_preserved(tmp_path) -> None:
    """AC.CRSP.3 (behaviour-preservation) — with corpus changes present and
    ``LOAM_REFRESH_NO_COMMIT=1`` the fixed script exits 0 via the no-commit
    branch and NEVER runs ``git add`` / ``git commit`` (the #193 CI/PR
    opt-in is intact)."""
    root = tmp_path / "repo"
    script = _build_tree(root, REAL_SCRIPT.read_text(encoding="utf-8"))
    capture = tmp_path / "capture.txt"
    gitlog = tmp_path / "gitlog.txt"
    # diff --quiet exit 1 == corpus changes present.
    cbin = _controlled_bin(
        tmp_path / "cbin", capture, git_diff_quiet_exit=1, git_log=gitlog
    )
    assert shutil.which("zsh", path=str(cbin)) is None

    proc = subprocess.run(
        [str(script), "all"],
        env={"PATH": str(cbin), "LOAM_REFRESH_NO_COMMIT": "1"},
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, f"stderr={proc.stderr!r}"
    assert capture.exists(), "python3 entry-point was never reached"
    git_calls = gitlog.read_text(encoding="utf-8") if gitlog.exists() else ""
    # The diff check ran; the commit path did NOT.
    assert "diff" in git_calls
    assert "add" not in git_calls, f"unexpected git add: {git_calls!r}"
    assert "commit" not in git_calls, f"unexpected git commit: {git_calls!r}"


def test_AC_CRSP_3b_strict_mode_arg_guard_preserved(tmp_path) -> None:
    """AC.CRSP.3 (behaviour-preservation) — ``set -euo pipefail`` + the
    ``${1:?…}`` required-arg guard are intact: invoked with no cadence-class
    argument, the script exits non-zero and NEVER reaches ``python3``."""
    root = tmp_path / "repo"
    script = _build_tree(root, REAL_SCRIPT.read_text(encoding="utf-8"))
    capture = tmp_path / "capture.txt"
    cbin = _controlled_bin(tmp_path / "cbin", capture, git_diff_quiet_exit=0)
    assert shutil.which("zsh", path=str(cbin)) is None

    proc = subprocess.run(
        [str(script)],  # no cadence-class argument
        env={"PATH": str(cbin)},
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )

    assert proc.returncode != 0, "missing-arg guard did not fire"
    assert not capture.exists(), (
        "python3 was reached despite the missing required argument"
    )
    assert "usage" in proc.stderr.lower()

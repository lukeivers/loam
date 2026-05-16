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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.

"""AC.PROMO.5 — the shared surface is importable in ONE line by an
arbitrary out-of-tree caller (modelling a dispatched `/tmp` harness)
— i.e. the mandate is *actually reachable* by the class that caused
Telegram-death #5, not only by in-tree callers.

Plan: docs/plans/telegram-5-fix.md §3.3 / §5 Halt-1
Satisfiable iff the surface is packaged/path-resolvable the way the
sealed `handsoff_loop._isolation` resolves subloam-driver today (a
`sys.path.insert(0, <canonical-src>)` + `import`).  Falsifiable: a
`/tmp`-CWD process cannot import it -> the mandate is inert for the
#5 class -> §5 Halt-1 (the test would FAIL straight; an honest
negative is the valid terminal outcome, NOT papered as "contained").

This test spawns a REAL Python subprocess whose CWD is a fresh tmp
dir OUTSIDE the canonical tree (exactly the #5 harness situation:
`/private/tmp/phase-b-reharden-.../reharden.py`) and asserts it can
reach the mandated entry points in one `sys.path.insert` + `import`,
and that `assert_loam_spawn_isolated` enforces the mandate from there
(a hand-rolled raw claude argv raises even out-of-tree).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from loam_spawn_isolation import canonical_src  # noqa: E402


def test_AC_PROMO_5_canonical_src_points_at_importable_package() -> (
    None
):
    """`canonical_src()` returns the package `src` dir an out-of-tree
    caller puts on sys.path — it must contain the importable
    package."""
    src = canonical_src()
    assert src.is_dir(), f"canonical_src() not a dir: {src}"
    assert (
        src / "loam_spawn_isolation" / "__init__.py"
    ).is_file(), (
        f"canonical_src() does not contain the importable package: "
        f"{src}"
    )


def test_AC_PROMO_5_tmp_cwd_process_imports_in_one_line(
    tmp_path: Path,
) -> None:
    """A real Python process whose CWD is a tmp dir OUTSIDE the
    canonical tree (the #5 harness situation) reaches the mandated
    surface in ONE `sys.path.insert` + `import` and the mandate guard
    is enforceable from there.

    The harness-author recipe under test (documented in the package
    docstring):

        import sys; sys.path.insert(0, "<canonical-src>")
        from loam_spawn_isolation import (
            spawn_isolated_claude, inject_isolation,
            assert_loam_spawn_isolated)
    """
    canonical = str(canonical_src())
    # The harness author does NOT live in the canonical tree; it only
    # knows the canonical src path (in-tree dispatchers pass it /
    # `canonical_src()` documents it).  Reproduce that exactly.
    harness = tmp_path / "reharden_like_harness.py"
    harness.write_text(
        "import sys\n"
        f"sys.path.insert(0, {canonical!r})\n"
        "from loam_spawn_isolation import (\n"
        "    spawn_isolated_claude, inject_isolation,\n"
        "    isolated_env, assert_loam_spawn_isolated)\n"
        "\n"
        "# 1. the mandated surface is importable one-line out-of-tree\n"
        "argv = inject_isolation(\n"
        "    ['claude', '-p', 'X', '--model', 'sonnet'])\n"
        "assert '--strict-mcp-config' in argv\n"
        "env = isolated_env({'PATH': '/usr/bin'})\n"
        "assert env['CLAUDE_PERSONA']\n"
        "assert 'TELEGRAM_BOT_TOKEN' not in env\n"
        "\n"
        "# 2. the mandate guard is enforceable from out-of-tree: a\n"
        "#    hand-rolled raw claude argv (the #5 pattern) raises\n"
        "try:\n"
        "    assert_loam_spawn_isolated(\n"
        "        ['claude', '-p', 'X', '--model', 'sonnet'])\n"
        "    raise SystemExit('GUARD-DID-NOT-FIRE')\n"
        "except ValueError:\n"
        "    pass\n"
        "\n"
        "print('OUT-OF-TREE-REACH-OK')\n",
        encoding="utf-8",
    )
    # CWD is the tmp dir — OUTSIDE the canonical tree, exactly like
    # the #5 /tmp reharden harness.
    proc = subprocess.run(
        [sys.executable, str(harness)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, (
        "out-of-tree /tmp-CWD harness could NOT reach the mandated "
        "shared surface in one line — the mandate is inert for the "
        "#5 class (§5 Halt-1 honest-negative). stdout="
        f"{proc.stdout!r} stderr={proc.stderr!r}"
    )
    assert "OUT-OF-TREE-REACH-OK" in proc.stdout, (
        f"unexpected harness output: stdout={proc.stdout!r} "
        f"stderr={proc.stderr!r}"
    )

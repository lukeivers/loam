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

"""AC.DSA.2 — stub content shape (skip-with-reason).

For each ``(component, ac_id, source_path_glob)`` in ``new_acs``, the
dispatcher writes a file at
``framework/<component>/tests/test_AC_<NORM>_placeholder.py`` whose
content (a) defines a function whose name starts with
``test_AC_<NORM>_`` (matching A3's ``_function_prefix(ac_id)``), (b)
the function body invokes ``pytest.skip(...)`` with a reason naming
the dispatcher as author and the AC ID as the replacement target,
(c) the file is otherwise minimal. The stub registers as ``skipped``
(not ``passed``, not ``failed``) in pytest output.

Verifies AC.DSA.2 + halt-trigger 8 (A3 regex match against the
dispatcher's stub).
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from loam.primary_persona.dispatch_wrapper import (
    _render_stub_body,
    _stub_path,
    _STUB_FUNCTION_TEMPLATE,
)


def test_AC_DSA_2_stub_path_under_tests_dir(tmp_path) -> None:
    """The stub file lands at ``framework/<comp>/tests/
    test_AC_<NORM>_placeholder.py`` per A3's expected glob."""
    p = _stub_path(tmp_path, "primary-persona", "AC.DSA.99")
    rel = p.relative_to(tmp_path).as_posix()
    assert rel == (
        "framework/primary-persona/tests/test_AC_DSA_99_placeholder.py"
    )


def test_AC_DSA_2_stub_path_normalises_lowercase_prefix() -> None:
    """A3's normalisation drops a case-insensitive ``AC.`` prefix.
    The dispatcher mirrors that normalisation."""
    p = _stub_path(Path("/ws"), "comp", "ac.x.1")
    assert p.name == "test_AC_X_1_placeholder.py"


def test_AC_DSA_2_stub_body_contains_function_definition() -> None:
    """Body defines a function whose name starts with
    ``test_AC_<NORM>_`` (A3 regex match)."""
    body = _render_stub_body(
        component="primary-persona",
        ac_id="AC.DSA.99",
        scope_id="scope-test",
        plan_path="docs/rebuild/plans/x.md",
    )
    # A3's regex (verbatim from tdd_guard._file_contains_matching_function).
    pattern = r"^def\s+test_AC_DSA_99_\w*\s*\("
    assert re.search(pattern, body, re.MULTILINE) is not None
    # Function name uses the documented template.
    assert _STUB_FUNCTION_TEMPLATE.format(normalised="DSA_99") in body


def test_AC_DSA_2_stub_body_invokes_pytest_skip_with_reason() -> None:
    """Body invokes ``pytest.skip(...)`` with a reason naming the
    dispatcher as author and the AC ID as the replacement target."""
    body = _render_stub_body(
        component="c",
        ac_id="AC.X.1",
        scope_id="scope-t",
        plan_path="docs/p.md",
    )
    assert "pytest.skip(" in body
    assert "stub authored by dispatcher" in body
    assert "AC.X.1" in body


def test_AC_DSA_2_stub_body_imports_pytest() -> None:
    """Stub imports pytest (the function calls ``pytest.skip``)."""
    body = _render_stub_body(
        component="c", ac_id="AC.X.1", scope_id="s", plan_path="p"
    )
    assert "import pytest" in body


def test_AC_DSA_2_stub_minimal_no_class_no_fixture() -> None:
    """Stub is otherwise minimal: no class scaffolding, no fixtures.
    D-DSA.2 alt(ε) was rejected; richer stub is OOS."""
    body = _render_stub_body(
        component="c", ac_id="AC.X.1", scope_id="s", plan_path="p"
    )
    assert "class " not in body
    assert "@pytest.fixture" not in body


def test_AC_DSA_2_stub_registers_as_skipped_in_pytest(tmp_path) -> None:
    """A real pytest run on the dispatcher's stub reports the
    placeholder as ``skipped`` (not passed, not failed) — the
    convention-marker the brief calls for."""
    body = _render_stub_body(
        component="c", ac_id="AC.X.1", scope_id="s", plan_path="p"
    )
    stub = tmp_path / "test_AC_X_1_placeholder.py"
    stub.write_text(body, encoding="utf-8")
    # Use `python -m pytest` so the test discovers the stub via its
    # local working directory; -p no:cacheprovider keeps tmp clean.
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(stub),
            "-q",
            "-p",
            "no:cacheprovider",
            "--no-header",
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    # pytest exits 0 when all tests are skipped; the summary line
    # carries " skipped" for the count.
    assert proc.returncode == 0, proc.stderr or proc.stdout
    combined = (proc.stdout + proc.stderr).lower()
    assert "skipped" in combined
    assert " passed" not in combined  # space-prefixed avoids "1 skipped, 0 passed" false-pos
    assert " failed" not in combined

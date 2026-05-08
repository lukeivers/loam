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

"""AC.OSS-M4.4 — public stub-writer surface in dispatch_wrapper.

Per the locked plan-doc §4 AC.OSS-M4.4: a NEW thin public function
``write_dispatcher_stub(workspace_root, spec, *, scope_id, plan_path)``
exists on ``loam.primary_persona.dispatch_wrapper`` (and is re-exported
from ``loam.primary_persona``). It delegates to the existing private
``_write_stub_idempotent`` byte-for-byte. Backs AC.OSS-M4.4 (M4
wire-dispatch hook); the only addition to ``dispatch_wrapper.py`` in
M4 per plan §10 D-build.M4.5.
"""

from __future__ import annotations

from pathlib import Path

import pytest


def test_AC_OSS_M4_4_public_function_exists_on_dispatch_wrapper() -> None:
    """The public function is importable from the canonical module."""
    from loam.primary_persona.dispatch_wrapper import (
        write_dispatcher_stub,
    )

    assert callable(write_dispatcher_stub)


def test_AC_OSS_M4_4_public_function_re_exported_from_package() -> None:
    """The function is re-exported from ``loam.primary_persona``."""
    import loam.primary_persona as pp

    assert hasattr(pp, "write_dispatcher_stub")
    assert callable(pp.write_dispatcher_stub)
    # Same callable object — re-export, not a duplicate.
    from loam.primary_persona.dispatch_wrapper import (
        write_dispatcher_stub,
    )

    assert pp.write_dispatcher_stub is write_dispatcher_stub


def test_AC_OSS_M4_4_in_dispatch_wrapper_all() -> None:
    """The public surface is named in ``__all__``."""
    from loam.primary_persona import dispatch_wrapper

    assert "write_dispatcher_stub" in dispatch_wrapper.__all__


def test_AC_OSS_M4_4_in_package_all() -> None:
    """The public surface is named in package ``__all__``."""
    import loam.primary_persona as pp

    assert "write_dispatcher_stub" in pp.__all__


def test_AC_OSS_M4_4_writes_stub_on_first_call(
    tmp_path: Path,
) -> None:
    """First call authors a fresh stub at the AC.DSA.2 path; outcome
    is ``"written"`` per the private helper's contract."""
    from loam.primary_persona.dispatch_wrapper import (
        NewACSpec,
        write_dispatcher_stub,
    )

    spec = NewACSpec(
        component="primary-persona",
        ac_id="AC.X.1",
        source_path_glob="framework/primary-persona/src/foo.py",
    )
    outcome = write_dispatcher_stub(
        tmp_path,
        spec,
        scope_id="scope-fixture",
        plan_path="docs/plans/foo.md",
    )
    assert outcome["outcome"] == "written"
    target = Path(outcome["path"])
    assert target.exists()
    body = target.read_text(encoding="utf-8")
    # Sanity-check: the rendered body contains the AC ID + scope ID.
    assert "AC.X.1" in body
    assert "scope-fixture" in body


def test_AC_OSS_M4_4_idempotent_on_second_call(
    tmp_path: Path,
) -> None:
    """Re-call with byte-equal payload returns ``"skipped-identical"``
    per AC.DSA.4 idempotency."""
    from loam.primary_persona.dispatch_wrapper import (
        NewACSpec,
        write_dispatcher_stub,
    )

    spec = NewACSpec(
        component="primary-persona",
        ac_id="AC.X.2",
        source_path_glob="framework/primary-persona/src/bar.py",
    )
    write_dispatcher_stub(
        tmp_path, spec, scope_id="s1", plan_path="docs/p.md"
    )
    second = write_dispatcher_stub(
        tmp_path, spec, scope_id="s1", plan_path="docs/p.md"
    )
    assert second["outcome"] == "skipped-identical"


def test_AC_OSS_M4_4_delegates_to_private_helper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Public function delegates verbatim to ``_write_stub_idempotent``;
    a sentinel return value flows through unchanged."""
    from loam.primary_persona import dispatch_wrapper as dw

    sentinel_return = {"outcome": "test-sentinel", "path": "/dev/null"}
    captured: dict = {}

    def fake_helper(
        workspace_root, spec, *, scope_id, plan_path
    ):  # noqa: ANN001
        captured["workspace_root"] = workspace_root
        captured["spec"] = spec
        captured["scope_id"] = scope_id
        captured["plan_path"] = plan_path
        return sentinel_return

    monkeypatch.setattr(dw, "_write_stub_idempotent", fake_helper)

    spec = dw.NewACSpec(
        component="primary-persona",
        ac_id="AC.X.3",
        source_path_glob="framework/primary-persona/src/baz.py",
    )
    out = dw.write_dispatcher_stub(
        tmp_path, spec, scope_id="abc", plan_path="docs/q.md"
    )
    assert out is sentinel_return
    assert captured["workspace_root"] == tmp_path
    assert captured["spec"] is spec
    assert captured["scope_id"] == "abc"
    assert captured["plan_path"] == "docs/q.md"

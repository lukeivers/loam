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

"""AC.FBE.1.3 — `build_init_subcommand` registers an argparse parser
whose action wraps `bootstrap_new_workspace`.

Exercises the builder against a real `_SubParsersAction`; verifies the
registered subparser carries `init` as its name + accepts the
documented argument shape (`<path>`, `--from`, `--init-existing`,
`--persona-handle`); calls the dispatched function with a parsed
Namespace under a monkeypatched `bootstrap_new_workspace` and asserts
the call kwargs match.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pytest

from loam.loam_init.cli import build_init_subcommand
from .conftest import make_subparsers_action


def _build_loam_init_namespace(argv: list[str]) -> argparse.Namespace:
    """Build a fresh parser with `init` registered + parse argv."""
    parser = argparse.ArgumentParser(prog="loam")
    sub = parser.add_subparsers(dest="subcommand", required=True)
    build_init_subcommand(sub)
    return parser.parse_args(argv)


def test_AC_FBE_1_3_init_subparser_registered() -> None:
    """The builder registers an `init` subparser under the parent."""
    sub = make_subparsers_action()
    build_init_subcommand(sub)
    # _SubParsersAction.choices maps subcommand-name → leaf parser.
    assert "init" in sub.choices, (
        "build_init_subcommand should register a leaf subparser "
        "named 'init'; choices=" + repr(sorted(sub.choices))
    )


def test_AC_FBE_1_3_argparse_surface_accepts_documented_args() -> None:
    """The `init` subparser accepts `<path> --from <src> [--init-existing] [--persona-handle <h>]`."""
    ns = _build_loam_init_namespace(
        [
            "init",
            "/tmp/loam-fbe1-test-ws",
            "--from",
            "/Users/example/loam",
            "--init-existing",
            "--persona-handle",
            "alice",
        ]
    )
    assert ns.subcommand == "init"
    assert ns.path == Path("/tmp/loam-fbe1-test-ws")
    assert ns.canonical_source == "/Users/example/loam"
    assert ns.init_existing is True
    assert ns.persona_handle == "alice"
    assert callable(getattr(ns, "func", None)), (
        "leaf parser must set func via set_defaults so loam_cli.cli.main "
        "can dispatch via args.func(args)"
    )


def test_AC_FBE_1_3_persona_handle_default_is_primary() -> None:
    """Default persona handle mirrors workspace_bootstrap's `primary`."""
    ns = _build_loam_init_namespace(
        ["init", "/tmp/x", "--from", "/Users/example/loam"]
    )
    assert ns.persona_handle == "primary"
    assert ns.init_existing is False


def test_AC_FBE_1_3_canonical_source_optional() -> None:
    """Omitting `--from` parses as canonical_source=None.

    Per FBE.9 (AC.FBE.9.1): `--from` became optional in cli.py. The
    parser-side outcome is canonical_source=None; the `_cmd_init`
    action callable resolves the smart-default (cwd if it's a git
    tree, else exit 2). This test pins only the parser-side contract
    inversion (no SystemExit on omission); the action-side resolver
    is exercised by AC.FBE.1.5 tests.
    """
    ns = _build_loam_init_namespace(["init", "/tmp/x"])
    assert ns.canonical_source is None
    assert ns.path == Path("/tmp/x")


def test_AC_FBE_1_3_dispatch_calls_bootstrap_with_parsed_kwargs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Calling the dispatched func invokes bootstrap_new_workspace with the parsed kwargs."""
    captured: dict[str, Any] = {}

    class _StubScaffoldResult:
        reason = "first_run"

    class _StubResult:
        new_ws_path = Path("/tmp/loam-fbe1-test-ws")
        framework_dir = Path("/tmp/loam-fbe1-test-ws/framework")
        workspace_state_dir = Path("/tmp/loam-fbe1-test-ws/workspace")
        claude_dir = Path("/tmp/loam-fbe1-test-ws/.claude")
        sync_config_path = Path(
            "/tmp/loam-fbe1-test-ws/workspace/.pos/sync-config.yaml"
        )
        canonical_source = "/Users/example/loam"
        canonical_source_kind = "local"
        scaffold_result = _StubScaffoldResult()
        init_existing = False

    def _stub_bootstrap(**kwargs: Any) -> Any:
        captured.update(kwargs)
        return _StubResult()

    monkeypatch.setattr(
        "loam.workspace_bootstrap.new_workspace.bootstrap_new_workspace",
        _stub_bootstrap,
    )

    ns = _build_loam_init_namespace(
        [
            "init",
            "/tmp/loam-fbe1-test-ws",
            "--from",
            "/Users/example/loam",
            "--persona-handle",
            "alice",
        ]
    )
    rc = ns.func(ns)
    assert rc == 0, "success path returns exit code 0"
    assert captured == {
        "new_ws_path": Path("/tmp/loam-fbe1-test-ws"),
        "canonical_source": "/Users/example/loam",
        "init_existing": False,
        "persona_handle": "alice",
    }, "wrapper must forward exactly the four documented kwargs"

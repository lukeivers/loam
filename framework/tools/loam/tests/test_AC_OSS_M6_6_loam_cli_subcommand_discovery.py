"""AC.OSS-M6.6 — `loam_cli` discovers plugin-shipped subcommands via
the NEW entry-point group `loam.cli.subcommands`.

Per plan §10 D-build.M6.5: the unified `loam` CLI gains an
entry-point-group resolution path symmetric to workspace-bootstrap's
`loam.bootstrap.contributions` pattern. Each builder is invoked at
parser-build time with the parser's `_SubParsersAction` handle.

This test file covers the `loam_cli` side: the discovery function
returns registered entry-points; the parser invokes builders;
dispatch routes through `args.func` set on each leaf parser.

The plugin-side coverage (the dev-sdlc plugin's own subcommand)
lives at
`plugins/dev-sdlc/tests/test_AC_OSS_M6_6_loam_project_subcommand_registered.py`.
"""

from __future__ import annotations

import argparse

import loam_cli.cli as cli_mod


def test_discover_subcommand_builders_returns_list() -> None:
    """Discovery returns a list — empty when no plugin is installed
    contributing to the group, populated once dev-sdlc is editable-
    installed."""
    builders = cli_mod._discover_subcommand_builders()
    assert isinstance(builders, list)
    # When the plugin is editable-installed (its pyproject.toml ships
    # the entry-point), `project` MUST appear. The dispatch's
    # build-step installs the plugin via `pip install -e plugins/dev-sdlc/`
    # so this assertion holds at seal-time.
    names = {n for n, _ in builders}
    assert "project" in names, (
        "expected 'project' entry-point under "
        "'loam.cli.subcommands' group; ensure the plugin is "
        "editable-installed"
    )


def test_builder_invocation_attaches_subparser() -> None:
    """The discovered builder, when invoked with a `_SubParsersAction`,
    registers a named subparser. Smoke test against a synthetic
    parser."""
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="subcommand", required=True)
    for name, builder in cli_mod._discover_subcommand_builders():
        if name == "project":
            builder(sub)
            break
    sp_action = next(
        a
        for a in parser._actions
        if isinstance(a, argparse._SubParsersAction)
    )
    assert "project" in sp_action.choices


def test_main_dispatches_via_func_attribute(
    monkeypatch, tmp_path
) -> None:
    """Plugin-shipped subcommands set `args.func` on each leaf parser
    via `set_defaults`; `main()` dispatches via that callable."""
    captured: list[argparse.Namespace] = []

    def fake_builder(sub: argparse._SubParsersAction) -> None:
        p = sub.add_parser("dummy")
        p.add_argument("--value", default="x")

        def _cmd(args: argparse.Namespace) -> int:
            captured.append(args)
            return 0

        p.set_defaults(func=_cmd)

    monkeypatch.setattr(
        cli_mod,
        "_discover_subcommand_builders",
        lambda: [("dummy", fake_builder)],
    )
    rc = cli_mod.main(["dummy", "--value", "hello"])
    assert rc == 0
    assert len(captured) == 1
    assert captured[0].value == "hello"


def test_main_amend_path_preserved_after_extension(
    monkeypatch,
) -> None:
    """The pre-existing `loam amend` path remains intact — entry-point
    discovery is additive."""
    monkeypatch.setattr(
        cli_mod, "_discover_subcommand_builders", lambda: []
    )
    parser = cli_mod._build_parser()
    sp_action = next(
        a
        for a in parser._actions
        if isinstance(a, argparse._SubParsersAction)
    )
    assert "amend" in sp_action.choices


def test_discover_handles_load_failure_gracefully(
    monkeypatch,
) -> None:
    """A broken entry-point doesn't break discovery; the offending
    entry-point is skipped + a warning logged."""
    import importlib.metadata as md

    class _BrokenEP:
        name = "broken"

        def load(self):
            raise RuntimeError("cannot load")

    class _WorkingEP:
        name = "ok"

        def load(self):
            return lambda sub: None

    monkeypatch.setattr(
        md, "entry_points", lambda group=None: [_BrokenEP(), _WorkingEP()]
    )
    builders = cli_mod._discover_subcommand_builders()
    # Only the working one survives.
    names = {n for n, _ in builders}
    assert "ok" in names
    assert "broken" not in names

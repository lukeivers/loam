"""Command-line entry point for ``pos-amend``.

Subcommand surface: ``validate``, ``apply`` (with ``--dry-run``),
``seal``, ``template`` (``list`` / ``render`` / ``validate``).
See the plan doc for rationale on the minimal surface; ``template``
extends per ``docs/rebuild/plans/dispatch-prompt-template-extension.md``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pos_amend import __version__
from pos_amend.commands import apply as apply_cmd
from pos_amend.commands import seal as seal_cmd
from pos_amend.commands import template as template_cmd
from pos_amend.commands import validate as validate_cmd


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pos-amend",
        description="Amendment-dispatch tooling for pos-v2.",
    )
    parser.add_argument(
        "--version", action="version", version=f"pos-amend {__version__}"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="schema-lint a manifest")
    p_validate.add_argument("manifest", type=Path)

    p_apply = sub.add_parser(
        "apply", help="apply (or dry-run) a manifest to the tree"
    )
    p_apply.add_argument("manifest", type=Path)
    p_apply.add_argument(
        "--dry-run",
        action="store_true",
        help="simulate; report missing admissions without mutating",
    )

    p_seal = sub.add_parser(
        "seal",
        help=(
            "finalise an amendment cycle (advance sidecars + narrative, "
            "run touched + sweep tests, create deterministic seal commit, "
            "verify post-seal apply --dry-run)"
        ),
    )
    p_seal.add_argument("manifest", type=Path)
    p_seal.add_argument(
        "--no-finalize",
        action="store_true",
        help=(
            "preserve pre-extension behaviour: advance sidecars + "
            "append narrative only; do not stage, run tests, sweep, "
            "commit, or verify"
        ),
    )
    p_seal.add_argument(
        "--scoped-sweep",
        action="store_true",
        help=(
            "restrict cross-component sweep to manifest-listed "
            "components (default: sweep every sealed component in "
            "the workspace)"
        ),
    )
    p_seal.add_argument(
        "--plan-doc",
        type=Path,
        default=None,
        help=(
            "plan doc path; when set, append the deterministic "
            "`### Commit SHAs` subsection under §14 and create a "
            "`docs(plans): record amendment #N commit SHAs ...` "
            "follow-up commit (per AC.D-sa.7)"
        ),
    )

    # ``template`` subcommand family — markdown template engine for
    # high-repetition authored artefacts. Per
    # ``docs/rebuild/plans/dispatch-prompt-template-extension.md``
    # AC.D-tpl.1–AC.D-tpl.7. Purely additive: existing subcommands are
    # untouched (AC.D-tpl.6).
    p_template = sub.add_parser(
        "template",
        help="markdown template engine (list / render / validate)",
    )
    p_template.add_argument(
        "--templates-root",
        type=Path,
        default=None,
        help=(
            "alternate templates root (testing); defaults to the "
            "package's bundled templates/ directory"
        ),
    )
    template_sub = p_template.add_subparsers(dest="template_mode", required=True)

    template_sub.add_parser("list", help="enumerate registered templates")

    p_tpl_render = template_sub.add_parser(
        "render", help="render a template to stdout (or --out)"
    )
    p_tpl_render.add_argument(
        "spec", help="template id in '<family>/<id>' form"
    )
    p_tpl_render.add_argument(
        "--var",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="set a variable (repeatable; overrides --vars-file)",
    )
    p_tpl_render.add_argument(
        "--vars-file",
        type=Path,
        default=None,
        help="YAML mapping of variable_name -> value",
    )
    p_tpl_render.add_argument(
        "--out",
        type=Path,
        default=None,
        help="write rendered output to PATH (default: stdout)",
    )
    p_tpl_render.add_argument(
        "--force",
        action="store_true",
        help="overwrite an existing --out target",
    )

    p_tpl_validate = template_sub.add_parser(
        "validate", help="confirm a template parses and report its variables"
    )
    p_tpl_validate.add_argument(
        "spec", help="template id in '<family>/<id>' form"
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "validate":
        return validate_cmd.run(args.manifest)
    if args.command == "apply":
        return apply_cmd.run(args.manifest, dry_run=args.dry_run)
    if args.command == "seal":
        return seal_cmd.run(
            args.manifest,
            no_finalize=args.no_finalize,
            scoped_sweep=args.scoped_sweep,
            plan_doc=args.plan_doc,
        )
    if args.command == "template":
        templates_root = args.templates_root or template_cmd.DEFAULT_TEMPLATES_ROOT
        if args.template_mode == "list":
            return template_cmd.run("list", templates_root=templates_root)
        if args.template_mode == "validate":
            return template_cmd.run(
                "validate", templates_root=templates_root, spec=args.spec
            )
        if args.template_mode == "render":
            return template_cmd.run(
                "render",
                templates_root=templates_root,
                spec=args.spec,
                var_flags=args.var,
                vars_file=args.vars_file,
                out=args.out,
                force=args.force,
            )
        parser.error(f"unknown template mode: {args.template_mode}")
        return 2  # unreachable
    parser.error(f"unknown command: {args.command}")
    return 2  # unreachable

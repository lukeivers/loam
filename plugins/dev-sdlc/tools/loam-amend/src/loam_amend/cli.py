"""Command-line entry point for ``loam amend`` (the amendment-dispatch
subcommand of the unified ``loam`` top-level CLI; pre-M1g name was
``pos-amend``).

Subcommand surface: ``validate``, ``apply`` (with ``--dry-run``),
``seal``, ``template`` (``list`` / ``render`` / ``validate``),
``new-plan``. See the plan doc for rationale on the minimal surface;
``template`` extends per
``docs/rebuild/plans/dispatch-prompt-template-extension.md``;
``new-plan`` extends per
``docs/rebuild/plans/pos-amend-new-plan-orchestration.md``.

Per M1g (``docs/rebuild/plans/oss-v0-1-0-publish-rename-1g.md``): the
binary name + import paths rebrand from ``pos-amend`` /
``pos_amend.*`` to ``loam`` / ``loam_amend.*``; the public
behaviour is unchanged. This module exposes both
``attach_subparsers(parent)`` (for embedding under the top-level
``loam`` dispatcher) and ``main(argv)`` (for standalone
``python -m loam_cli.amend`` invocation).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from loam_cli import __version__
from loam_amend.commands import apply as apply_cmd
from loam_amend.commands import new_plan as new_plan_cmd
from loam_amend.commands import seal as seal_cmd
from loam_amend.commands import template as template_cmd
from loam_amend.commands import validate as validate_cmd


def attach_subparsers(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Attach the ``loam amend`` subcommand surface to ``parser``.

    ``parser`` is either:
      - a stand-alone parser created by ``_build_parser()`` for
        ``python -m loam_cli.amend ...`` invocation, OR
      - a subparser of the top-level ``loam`` CLI's parser created by
        ``loam_cli.cli._build_parser()``.

    Either way, the same ``validate / apply / seal / template /
    new-plan`` subparsers are registered on ``parser``.
    """
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
    p_seal.add_argument(
        "--allow-untracked-globs",
        action="append",
        default=[],
        metavar="PATTERN",
        help=(
            "admit dirty paths matching the named shell-style glob "
            "pattern when computing dirty-tree status (repeatable; "
            "patterns are anchored at the repo root and are NOT "
            "auto-staged or committed). Common case: "
            "`--allow-untracked-globs docs/rebuild/FUTURE_IDEAS_DRAFT.md` "
            "for in-flight capture state. Per AC.LAE.2."
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

    # ``new-plan`` subcommand — scaffold a vars-file (and optionally
    # render the plan-doc) for a new plan slug. Per
    # ``docs/rebuild/plans/pos-amend-new-plan-orchestration.md``
    # AC.D-np.1–AC.D-np.7. Purely additive; existing subcommands are
    # untouched (AC.D-np.6).
    p_new_plan = sub.add_parser(
        "new-plan",
        help=(
            "scaffold a vars-file for a new plan-doc at "
            "<repo>/docs/rebuild/plans/<slug>.vars.yaml; with --render "
            "also produce the plan-doc"
        ),
    )
    p_new_plan.add_argument("slug", help="plan filename slug, ^[a-z][a-z0-9-]*$")
    p_new_plan.add_argument(
        "--title",
        default=None,
        help="pre-fill the TITLE variable in the scaffolded vars-file",
    )
    p_new_plan.add_argument(
        "--ac-prefix",
        default=None,
        help="pre-fill the AC_PREFIX variable",
    )
    p_new_plan.add_argument(
        "--vars-out",
        type=Path,
        default=None,
        help=(
            "override the vars-file output path "
            "(default: <repo>/docs/rebuild/plans/<slug>.vars.yaml)"
        ),
    )
    p_new_plan.add_argument(
        "--plan-out",
        type=Path,
        default=None,
        help=(
            "override the plan-doc output path when --render is set "
            "(default: <repo>/docs/rebuild/plans/<slug>.md)"
        ),
    )
    p_new_plan.add_argument(
        "--render",
        action="store_true",
        help=(
            "after scaffolding the vars-file, render the plan-doc "
            "to --plan-out (delegates to `loam amend template render`)"
        ),
    )
    p_new_plan.add_argument(
        "--force",
        action="store_true",
        help="overwrite existing --vars-out / --plan-out (default: refuse)",
    )

    return parser


def _build_parser() -> argparse.ArgumentParser:
    """Build a stand-alone ``loam amend`` parser.

    Used by ``python -m loam_cli.amend ...`` invocation. The
    top-level ``loam`` CLI does NOT call this directly — it calls
    ``attach_subparsers(amend_subparser)`` on its own subparser.
    """
    parser = argparse.ArgumentParser(
        prog="loam amend",
        description="Amendment-dispatch tooling for loam.",
    )
    parser.add_argument(
        "--version", action="version", version=f"loam amend {__version__}"
    )
    return attach_subparsers(parser)


def dispatch(args: argparse.Namespace) -> int:
    """Run the matched subcommand from a parsed-args namespace.

    Used by the top-level ``loam`` dispatcher (``loam_cli.cli.main``)
    after argparse has parsed the full ``loam amend <subcommand> ...``
    surface. Mirrors the per-command dispatch from the legacy
    ``pos-amend`` CLI's ``main()``.
    """
    if args.command == "validate":
        return validate_cmd.run(args.manifest)
    if args.command == "apply":
        return apply_cmd.run(args.manifest, dry_run=args.dry_run)
    if args.command == "seal":
        # Normalise --plan-doc to an absolute path before any
        # downstream `Path.relative_to(repo_root)` walk. Relative
        # paths surfaced under a different cwd than the repo root
        # crash `relative_to` with ValueError; resolving here gives
        # the seal subcommand a path it can reliably reason about
        # regardless of caller cwd. (Surfaced by the #41 build:
        # operator passed `docs/rebuild/plans/...` as a relative
        # arg from inside the repo and the seal step crashed.)
        plan_doc = (
            args.plan_doc.resolve() if args.plan_doc is not None else None
        )
        return seal_cmd.run(
            args.manifest,
            no_finalize=args.no_finalize,
            scoped_sweep=args.scoped_sweep,
            plan_doc=plan_doc,
            allow_untracked_globs=tuple(args.allow_untracked_globs),
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
        # Unreachable because argparse declares template_mode required.
        return 2
    if args.command == "new-plan":
        return new_plan_cmd.run(
            args.slug,
            title=args.title,
            ac_prefix=args.ac_prefix,
            vars_out=args.vars_out,
            plan_out=args.plan_out,
            render=args.render,
            force=args.force,
        )
    return 2  # unreachable: argparse declares command required


def main(argv: list[str] | None = None) -> int:
    """Standalone entry point for ``python -m loam_cli.amend ...``.

    Most callers should invoke ``loam amend ...`` instead, which
    routes through ``loam_cli.cli.main`` and ends up here via
    ``dispatch(args)``.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)
    return dispatch(args)


# ---------------------------------------------------------------------------
# Plugin entry-point adapter (M6b.1)
#
# Per master plan AC.OSS-M6.15 + §10 D-build.M6.15 (loam amend MOVE alone
# with shadow-then-flip), the unified ``loam`` CLI's
# ``loam.cli.subcommands`` entry-point group (M6a-authored, see
# ``framework/tools/loam/src/loam_cli/cli.py:_discover_subcommand_builders``)
# resolves the ``amend`` subcommand to this adapter. The adapter shape
# follows the M6a builder contract: accept a ``_SubParsersAction`` +
# add a named subparser + set ``args.func`` on the leaf so the
# dispatcher's ``args.func`` dispatch path routes back here.
#
# Kept thin: ``attach_subparsers`` carries the full subcommand surface
# (validate/apply/seal/template/new-plan); the adapter just adds the
# top-level ``amend`` parser + wires dispatch.


def build_amend_subcommand(
    sub: argparse._SubParsersAction,
) -> None:
    """Register the ``amend`` subcommand on ``sub``.

    Entry-point declaration in
    ``plugins/dev-sdlc/tools/loam-amend/pyproject.toml``:

        [project.entry-points."loam.cli.subcommands"]
        amend = "loam_amend.cli:build_amend_subcommand"

    The unified ``loam`` CLI dispatcher discovers + invokes this at
    parser-build time. Calling ``attach_subparsers(amend_parser)``
    populates the ``loam amend`` subparser with the full
    ``validate / apply / seal / template / new-plan`` surface.
    ``set_defaults(func=dispatch)`` wires the M6a dispatcher's
    ``args.func`` path back to ``dispatch(args)``.
    """
    amend_parser = sub.add_parser(
        "amend",
        help=(
            "amendment-dispatch tooling: validate / apply / seal / "
            "template / new-plan"
        ),
        add_help=True,
    )
    attach_subparsers(amend_parser)
    amend_parser.set_defaults(func=dispatch)

"""``loam amend template`` — markdown template engine for high-repetition
authored artefacts (dispatch prompts, plan-doc skeletons, ...).

Surface (per ``docs/rebuild/plans/dispatch-prompt-template-extension.md``):

- ``loam amend template list`` — enumerate registered templates by family.
- ``loam amend template render <family>/<id> [--var KEY=VALUE]... [--vars-file PATH] [--out PATH] [--force]``
- ``loam amend template validate <family>/<id>``

Templates live under ``tools/loam/templates/<family>/<id>.md`` by
default; tests inject an alternate root via ``--templates-root``.

Exit code mapping (existing loam amend taxonomy, no new codes — AC.D-tpl.5):

- 0 — success.
- 2 — template/vars contract failure (unknown id, malformed template,
  missing required variable, unrecognised variable, malformed
  ``--var`` flag, malformed ``--vars-file``).
- 3 — IO error (``--out`` overwrite refusal, write failure).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

import yaml

from loam_cli.amend.template_engine import (
    ParsedTemplate,
    TemplateError,
    TemplateNotFound,
    TemplateMalformed,
    discover_templates,
    parse_template,
    render,
)


# Default templates root, relative to this package's source tree.
# Path arithmetic: this file is at
#   framework/tools/loam/src/loam_cli/amend/commands/template.py
# parents[0]=commands/, [1]=amend/, [2]=loam_cli/, [3]=src/,
# [4]=loam/, [5]=tools/, [6]=framework/, [7]=<workspace>.
#
# Post-M6b.0 (D-build.M6b0.3 / F2 mechanism mirror): the dispatch +
# plan templates MOVED from framework/tools/loam/templates/ to
# plugins/dev-sdlc/templates/. The unified loam CLI's resolver now
# probes for plugin-side templates first, falling back to the
# canonical-side templates directory if the plugin tree is not
# present. Mirror of amendment #67's ``_resolve_corpus_path``
# probe-and-prefer pattern. ``DEFAULT_TEMPLATES_ROOT`` resolves
# (per workspace) to whichever exists; tests asserting against the
# default path now hit the plugin-side location post-M6b.0.
_PKG_ROOT = Path(__file__).resolve().parents[4]
_WORKSPACE_ROOT = Path(__file__).resolve().parents[7]
_PLUGIN_TEMPLATES_ROOT = (
    _WORKSPACE_ROOT
    / "plugins"
    / "dev-sdlc"
    / "templates"
)
_CANONICAL_TEMPLATES_ROOT = _PKG_ROOT / "templates"


def _resolve_default_templates_root() -> Path:
    """Probe-and-prefer for the default templates root.

    Prefer the Dev/SDLC plugin's templates tree; fall back to the
    canonical-side templates directory if the plugin tree is not
    present. Defensive only — ``_PLUGIN_TEMPLATES_ROOT`` is the
    expected location post-M6b.0.
    """
    if _PLUGIN_TEMPLATES_ROOT.exists():
        return _PLUGIN_TEMPLATES_ROOT
    return _CANONICAL_TEMPLATES_ROOT


DEFAULT_TEMPLATES_ROOT = _resolve_default_templates_root()


def _emit_diagnostic(exc: TemplateError) -> None:
    """Emit a structured diagnostic to stderr (AC.D-tpl.5).

    Note: per AC.D-tpl.5 (existing test
    ``test_AC_D_tpl_5_no_partial_stdout_on_render_failure``) the
    template-render halt path must NOT write to stdout — it would
    contaminate the stdout stream that callers redirect with `>`
    when capturing rendered template output. Halt visibility for
    template halts is provided via stderr only; the seal + new-plan
    halts (where stdout-redirection is not a concern) carry the
    ``HALT:`` stdout prefix per
    ``docs/rebuild/plans/pos-amend-halt-visibility.md``.
    """
    print(f"template error [{exc.failure_class}]: {exc}", file=sys.stderr)


def _resolve_template_path(
    templates_root: Path, family: str, template_id: str
) -> Path:
    return templates_root / family / f"{template_id}.md"


def _parse_id(spec: str) -> tuple[str, str]:
    if "/" not in spec:
        raise TemplateMalformed(
            f"template id '{spec}' must be in '<family>/<id>' form"
        )
    family, _, template_id = spec.partition("/")
    if not family or not template_id or "/" in template_id:
        raise TemplateMalformed(
            f"template id '{spec}' must be in '<family>/<id>' form"
        )
    return family, template_id


def _parse_var_flags(var_flags: Iterable[str]) -> dict[str, str]:
    """``--var KEY=VALUE`` → dict. Raises TemplateMalformed on bad shape."""
    out: dict[str, str] = {}
    for flag in var_flags:
        if "=" not in flag:
            raise TemplateMalformed(
                f"--var '{flag}' must be in KEY=VALUE form"
            )
        key, _, value = flag.partition("=")
        if not key:
            raise TemplateMalformed(
                f"--var '{flag}' has empty key"
            )
        out[key] = value
    return out


def _load_vars_file(path: Path) -> dict[str, str]:
    """Load a YAML mapping; coerce values to strings (templates substitute text)."""
    if not path.is_file():
        raise TemplateMalformed(f"--vars-file '{path}' does not exist")
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise TemplateMalformed(
            f"--vars-file '{path}' YAML parse error: {exc}"
        ) from exc
    if not isinstance(loaded, dict):
        raise TemplateMalformed(
            f"--vars-file '{path}' must be a YAML mapping (got "
            f"{type(loaded).__name__})"
        )
    out: dict[str, str] = {}
    for key, val in loaded.items():
        if not isinstance(key, str):
            raise TemplateMalformed(
                f"--vars-file '{path}' has non-string key {key!r}"
            )
        out[key] = "" if val is None else str(val)
    return out


# ---------------------------------------------------------------------------
# `list` mode


def run_list(templates_root: Path) -> int:
    entries = discover_templates(templates_root)
    if not entries:
        print(f"(no templates registered under {templates_root})")
        return 0
    current_family: str | None = None
    for family, template_id, path in entries:
        if family != current_family:
            print(f"{family}/")
            current_family = family
        try:
            tpl = parse_template(path, family=family, template_id=template_id)
            desc = tpl.description or "(no description)"
        except TemplateError as exc:
            desc = f"<malformed: {exc.failure_class}>"
        print(f"  {template_id} — {desc}")
    return 0


# ---------------------------------------------------------------------------
# `validate` mode


def run_validate(templates_root: Path, spec: str) -> int:
    try:
        family, template_id = _parse_id(spec)
        path = _resolve_template_path(templates_root, family, template_id)
        tpl = parse_template(path, family=family, template_id=template_id)
    except TemplateError as exc:
        _emit_diagnostic(exc)
        return 2
    print(
        f"ok: template '{family}/{template_id}' "
        f"({tpl.description or 'no description'})"
    )
    print(f"  required: {list(tpl.required)}")
    print(f"  optional: {dict(tpl.optional_defaults)}")
    print(f"  placeholders: {list(tpl.placeholders)}")
    return 0


# ---------------------------------------------------------------------------
# `render` mode


def run_render(
    templates_root: Path,
    spec: str,
    var_flags: list[str],
    vars_file: Path | None,
    out: Path | None,
    force: bool,
) -> int:
    # Parse id + collect variables, surfacing every contract failure as
    # exit 2 with a structured diagnostic (AC.D-tpl.5).
    try:
        family, template_id = _parse_id(spec)
        path = _resolve_template_path(templates_root, family, template_id)
        tpl = parse_template(path, family=family, template_id=template_id)
        variables: dict[str, str] = {}
        if vars_file is not None:
            variables.update(_load_vars_file(vars_file))
        # --var flags override --vars-file (caller-wins, last-wins inside flags).
        variables.update(_parse_var_flags(var_flags))
    except TemplateError as exc:
        _emit_diagnostic(exc)
        return 2

    try:
        rendered = render(tpl, variables)
    except TemplateError as exc:
        _emit_diagnostic(exc)
        return 2

    # --out shape (AC.D-tpl.3): refuse to overwrite without --force.
    # Per AC.D-tpl.5 the render halt path must not contaminate stdout
    # (callers redirect stdout with `>` to capture rendered output).
    if out is not None:
        if out.exists() and not force:
            print(
                f"refuse-overwrite: '{out}' exists; pass --force to overwrite",
                file=sys.stderr,
            )
            return 3
        try:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(rendered, encoding="utf-8")
        except OSError as exc:
            print(f"io error: {exc}", file=sys.stderr)
            return 3
        return 0

    sys.stdout.write(rendered)
    return 0


# ---------------------------------------------------------------------------
# Top-level dispatcher (called by cli.py)


def run(
    mode: str,
    *,
    templates_root: Path,
    spec: str | None = None,
    var_flags: list[str] | None = None,
    vars_file: Path | None = None,
    out: Path | None = None,
    force: bool = False,
) -> int:
    if mode == "list":
        return run_list(templates_root)
    if mode == "validate":
        assert spec is not None
        return run_validate(templates_root, spec)
    if mode == "render":
        assert spec is not None
        return run_render(
            templates_root, spec, var_flags or [], vars_file, out, force
        )
    raise AssertionError(f"unknown template mode: {mode}")  # unreachable via CLI


__all__ = [
    "DEFAULT_TEMPLATES_ROOT",
    "run",
    "run_list",
    "run_render",
    "run_validate",
]

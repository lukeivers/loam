"""``loam amend new-plan <slug>`` — scaffold a vars-file for a new plan-doc.

Surface (per ``docs/rebuild/plans/pos-amend-new-plan-orchestration.md`` — historical):

- ``loam amend new-plan <slug>`` — write a YAML vars-file at
  ``<repo>/docs/rebuild/plans/<slug>.vars.yaml`` pre-stubbed with the
  plan-doc skeleton's contract (16 required + 6 optional vars). Plan
  author edits the vars-file and runs
  ``loam amend template render plan/dev-discipline --vars-file <…>``
  to produce the rendered plan-doc.
- ``--title`` / ``--ac-prefix`` pre-fill the corresponding vars.
- ``--render`` produces the rendered plan-doc end-to-end (delegates
  to ``loam_cli.amend.commands.template.run("render", ...)``).
- ``--vars-out`` / ``--plan-out`` override default paths.
- ``--force`` overwrites existing files; default is refuse-overwrite.

Exit-code mapping (existing loam amend taxonomy — AC.D-np.4):

- 0 — success.
- 2 — invalid slug, malformed flag value, template-render contract failure.
- 3 — IO error (refuse-overwrite without ``--force``, write failure).
"""

from __future__ import annotations

import datetime
import re
import sys
import subprocess
from pathlib import Path

from loam_cli.amend.commands import template as template_cmd


# ---------------------------------------------------------------------------
# Errors


class NewPlanError(Exception):
    """Base class for new-plan failures."""

    failure_class: str = "new-plan-error"


class InvalidSlug(NewPlanError):
    failure_class = "invalid-slug"


class RefuseOverwrite(NewPlanError):
    failure_class = "refuse-overwrite"


class IOFailure(NewPlanError):
    failure_class = "io-failure"


# ---------------------------------------------------------------------------
# Slug validation (locked D-6: ^[a-z][a-z0-9-]*$)


_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]*$")


def _validate_slug(slug: str) -> None:
    if not slug:
        raise InvalidSlug("slug must not be empty")
    if "/" in slug:
        raise InvalidSlug(
            f"slug '{slug}' must not contain '/' (no subdirectories)"
        )
    if not _SLUG_RE.match(slug):
        raise InvalidSlug(
            f"slug '{slug}' must match ^[a-z][a-z0-9-]*$ "
            "(lowercase, hyphens, leading letter)"
        )


# ---------------------------------------------------------------------------
# Repo-root resolution


def _resolve_repo_root(repo_root: Path | None) -> Path:
    if repo_root is not None:
        return repo_root
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise NewPlanError(
            f"could not resolve repo-root (not in a git tree?): {exc}"
        ) from exc
    return Path(result.stdout.strip())


# ---------------------------------------------------------------------------
# Vars-file scaffold


def _vars_file_content(slug: str, title: str, ac_prefix: str) -> str:
    """Produce the scaffolded YAML vars-file for ``slug``.

    Pre-stubs HARD_CONSTRAINTS / IMPLEMENTATION_ORDER / HALT_TRIGGERS
    (locked D-4) and the three Lens-1/2/3 subsection headings (locked D-3).
    Pre-fills RESEARCH_PATH (slug-derived), STATUS_LINE (current ISO date),
    and WORKING_DIRECTORY (the standard repo path).
    """
    iso_date = datetime.date.today().isoformat()
    return f"""# loam amend new-plan scaffold for {slug}
# Edit this file, then render with:
#   loam amend template render plan/dev-discipline --vars-file <this-file> --out docs/rebuild/plans/{slug}.md --force

# --- Required vars (16) ---

TITLE: {_yaml_string(title)}
TLDR: |
  (empty — plan author fills §1 body)
AC_PREFIX: {_yaml_string(ac_prefix)}
SPEC_PLACEMENT: |
  (empty — §2 body; cite CLAUDE.md §2.5 framing)
LENS_ANALYSIS: |
  ### Lens 1 — Claude leverage

  (plan-author fills)

  ### Lens 2 — Harness + primary-persona value

  (plan-author fills; trace each AC to AC.PO.1 + AC.PO.2)

  ### Lens 3 — ODD authoring

  (plan-author fills)
ACCEPTANCE_CRITERIA: |
  (empty — §4 body; one AC per behaviour, outcome-shaped, no method-in-AC)
BEHAVIOUR_COUNT: |
  | # | Declared behaviour | AC |
  |---|--------------------|-----|
  | 1 | (declared behaviour) | (ac-id) |
HARD_CONSTRAINTS: |
  1. **No `--amend`.** Corrective new commits only.
  2. **Scope fence.** (plan-author edits — name the path(s) the work is fenced to).
  3. **Plan-before-code.** This plan exists; builder writes a builder-plan before code.
  4. **No new third-party dependency.** Stdlib + existing deps only.
  5. **Backward-compat preserved unconditionally.**
  6. **CDC adherence.** (plan-author extends per the work's specifics).
OUT_OF_SCOPE: |
  - (plan-author lists explicit out-of-scope items per ODD §2.5)
IMPLEMENTATION_ORDER: |
  1. Read session-start corpus per CLAUDE.md.
  2. Read this plan + research doc + companions.
  3. Write builder-plan to `docs/rebuild/plans/{slug}.builder-plan.md`.
  4. Land code per plan + builder-plan.
  5. Run tests (narrow scope first; full suite before commit).
  6. Conventional commits land the change. No `--amend`.
SECTION_9_HEADING: "Impact / motivation"
SECTION_9_BODY: |
  (plan-author fills; for sealed-component plans, replace the heading with
  "Bookkeeping surface" and include a `loam amend` manifest YAML stub)
HALT_TRIGGERS: |
  1. Cross-component scope expansion beyond the scope fence. Halt.
  2. Backward-compat cannot be preserved. Halt.
  3. ODD-violating shape becomes strongly required. Halt; owner rules.
  4. A new third-party dependency becomes required. Halt.
  5. Wall-time exceeds 90 minutes. Halt with current state.
  6. ODD violation observed in surrounding code/docs (per `feedback_subagent_odd_violation_halt`). Halt; do NOT extend a violating surface.
DECISIONS_DETAIL: |
  (no genuinely uncertain decisions — confirm or replace with D-1, D-2, … entries)
DECISIONS_SUMMARY: |
  | Decision | Recommendation | Why it matters |
  |---|---|---|
  | (placeholder) | | |
HALT_FINDINGS: |
  Per `feedback_subagent_odd_violation_halt`: halt and surface any
  ODD violation observed in surrounding code/docs.

  **(none observed during plan authoring.)**

# --- Optional vars (6) — uncomment + override the template's defaults ---

# COMPANIONS: ""
# ANCESTOR_RECORD: ""
# REFERENCES: |
#   (override the standard refs stub if needed)
STATUS_LINE: "plan (pre-dispatch). {iso_date}."
RESEARCH_PATH: "docs/rebuild/plans/research/{slug}-research.md"
# WORKING_DIRECTORY: "/Users/lukeivers/ivers-corp-pos-v2/"
"""


def _yaml_string(value: str) -> str:
    """Render a YAML-safe scalar string. Empty → empty quotes; else
    double-quoted with embedded double-quotes escaped.
    """
    if value == "":
        return '""'
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


# ---------------------------------------------------------------------------
# Diagnostic emission


def _emit_diagnostic(exc: NewPlanError) -> None:
    # Emit on stdout AND stderr. Stdout carries the scannable HALT
    # line for stderr-dropped contexts (e.g. some Bash-tool eval-
    # wrapper invocations); stderr carries the existing detail
    # for back-compat with prior assertions. Per AC.PA-hv.1 /
    # AC.PA-hv.2 of `docs/rebuild/plans/pos-amend-halt-visibility.md`.
    print(f"HALT: {exc.failure_class}: {exc}")
    print(f"new-plan error [{exc.failure_class}]: {exc}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Entry point


def run(
    slug: str,
    *,
    title: str | None = None,
    ac_prefix: str | None = None,
    vars_out: Path | None = None,
    plan_out: Path | None = None,
    render: bool = False,
    force: bool = False,
    repo_root: Path | None = None,
) -> int:
    """Scaffold a vars-file (and optionally render the plan-doc).

    Parameters
    ----------
    slug
        Plan filename slug; matches ``^[a-z][a-z0-9-]*$``.
    title, ac_prefix
        Pre-fill the corresponding vars; empty when ``None``.
    vars_out
        Output path for the vars-file. Default:
        ``<repo>/docs/rebuild/plans/<slug>.vars.yaml``.
    plan_out
        Output path for the rendered plan-doc when ``--render``. Default:
        ``<repo>/docs/rebuild/plans/<slug>.md``.
    render
        When True, also render the plan-doc (delegates to
        ``loam_cli.amend.commands.template.run("render", ...)``).
    force
        Overwrite existing files. Default is refuse-overwrite.
    repo_root
        Override repo-root resolution (testing hook). Default: query git.
    """
    # Slug validation first — invalid slug never touches disk.
    try:
        _validate_slug(slug)
    except NewPlanError as exc:
        _emit_diagnostic(exc)
        return 2

    try:
        root = _resolve_repo_root(repo_root)
    except NewPlanError as exc:
        _emit_diagnostic(exc)
        return 2

    if vars_out is None:
        vars_out = root / "docs" / "rebuild" / "plans" / f"{slug}.vars.yaml"
    if plan_out is None:
        plan_out = root / "docs" / "rebuild" / "plans" / f"{slug}.md"

    # Refuse-overwrite check BEFORE writing anything (no partial output
    # — AC.D-np.4).
    if vars_out.exists() and not force:
        exc = RefuseOverwrite(
            f"'{vars_out}' exists; pass --force to overwrite"
        )
        _emit_diagnostic(exc)
        return 3
    if render and plan_out.exists() and not force:
        exc = RefuseOverwrite(
            f"'{plan_out}' exists; pass --force to overwrite"
        )
        _emit_diagnostic(exc)
        return 3

    # Materialise the scaffold.
    content = _vars_file_content(
        slug,
        title=title or "",
        ac_prefix=ac_prefix or "",
    )

    try:
        vars_out.parent.mkdir(parents=True, exist_ok=True)
        vars_out.write_text(content, encoding="utf-8")
    except OSError as exc:
        _emit_diagnostic(IOFailure(f"writing '{vars_out}': {exc}"))
        return 3

    # Optional render — delegate to the template engine, no duplication.
    if render:
        rc = template_cmd.run(
            "render",
            templates_root=template_cmd.DEFAULT_TEMPLATES_ROOT,
            spec="plan/dev-discipline",
            var_flags=[],
            vars_file=vars_out,
            out=plan_out,
            force=force,
        )
        if rc != 0:
            # Template-render failure: the vars-file was written but
            # the plan-doc render failed. Surface as exit 2 (contract
            # failure) per AC.D-np.4 mapping; the underlying template
            # diagnostic was already emitted by template_cmd.
            return rc

    print(f"scaffolded vars-file: {vars_out}")
    if render:
        print(f"rendered plan-doc:   {plan_out}")
    return 0


__all__ = [
    "InvalidSlug",
    "IOFailure",
    "NewPlanError",
    "RefuseOverwrite",
    "run",
]

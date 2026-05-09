"""``loam amend new-memory <slug>`` — scaffold a vars-file for a new memory-doc.

Surface (per ``docs/plans/v0-7-0-non-tech-user-surface.md`` AC.NTU.4):

- ``loam amend new-memory <slug>`` — write a YAML vars-file at the
  project's memory directory pre-stubbed with the memory-doc
  skeleton's contract (4 required + 7 optional vars). Author edits
  the vars-file and runs
  ``loam amend template render memory-doc/SKELETON --vars-file <…>``
  to produce the rendered memory-doc.
- ``--name`` pre-fills the NAME variable.
- ``--description`` pre-fills the DESCRIPTION variable.
- ``--render`` produces the rendered memory-doc end-to-end (delegates
  to ``loam_amend.commands.template.run("render", ...)``).
- ``--vars-out`` / ``--memory-out`` override default paths.
- ``--memory-dir`` overrides the default memory-doc destination directory
  (default: ``<repo>/docs/memory/``).
- ``--force`` overwrites existing files; default is refuse-overwrite.

The default memory-doc destination is ``<repo>/docs/memory/feedback_<slug>.md``
— mirroring the long-standing ``feedback_*.md`` filename shape that the
existing memory corpus uses (per the procedural rule in
``feedback_principle_conflict_resolution_multi_signal``). Tests
exercise this path; production callers typically point ``--memory-dir`` at
``~/.claude/projects/<project>/memory/`` to land in the live retrieval
surface.

Exit-code mapping (existing loam amend taxonomy — mirrors AC.D-np.4):

- 0 — success.
- 2 — invalid slug, malformed flag value, template-render contract failure.
- 3 — IO error (refuse-overwrite without ``--force``, write failure).

Parallel structure to ``new_plan.py`` per D-NTU.4 ruling: parallelism is
load-bearing — same template engine, same scaffolding pattern, same
validation surface; only the template family + default destination
differ.
"""

from __future__ import annotations

import datetime
import re
import subprocess
import sys
from pathlib import Path

from loam_amend.commands import template as template_cmd


# ---------------------------------------------------------------------------
# Errors


class NewMemoryError(Exception):
    """Base class for new-memory failures."""

    failure_class: str = "new-memory-error"


class InvalidSlug(NewMemoryError):
    failure_class = "invalid-slug"


class RefuseOverwrite(NewMemoryError):
    failure_class = "refuse-overwrite"


class IOFailure(NewMemoryError):
    failure_class = "io-failure"


# ---------------------------------------------------------------------------
# Slug validation (mirrors new_plan: ^[a-z][a-z0-9_]*$ — underscores
# allowed because the canonical memory filenames use snake_case
# (feedback_no_amend_in_agent_dispatches, etc.))


_SLUG_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def _validate_slug(slug: str) -> None:
    if not slug:
        raise InvalidSlug("slug must not be empty")
    if "/" in slug:
        raise InvalidSlug(
            f"slug '{slug}' must not contain '/' (no subdirectories)"
        )
    if not _SLUG_RE.match(slug):
        raise InvalidSlug(
            f"slug '{slug}' must match ^[a-z][a-z0-9_]*$ "
            "(lowercase, snake_case, leading letter)"
        )


# ---------------------------------------------------------------------------
# Repo-root resolution (mirrors new_plan)


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
        raise NewMemoryError(
            f"could not resolve repo-root (not in a git tree?): {exc}"
        ) from exc
    return Path(result.stdout.strip())


# ---------------------------------------------------------------------------
# Vars-file scaffold


def _vars_file_content(slug: str, name: str, description: str) -> str:
    """Produce the scaffolded YAML vars-file for ``slug``.

    Pre-stubs DEFINITION_BODY / HOW_TO_APPLY_BODY (the 2 required body
    vars; NAME + DESCRIPTION pre-filled from flags). Pre-fills
    CAPTURED_DATE (current ISO date) + COMPOSES_WITH placeholder
    reminding the author of the M5 derivation/relationship procedural
    rule from feedback_principle_conflict_resolution_multi_signal.
    """
    iso_date = datetime.date.today().isoformat()
    return f"""# loam amend new-memory scaffold for {slug}
# Edit this file, then render with:
#   loam amend template render memory-doc/SKELETON --vars-file <this-file> --out docs/memory/feedback_{slug}.md --force

# --- Required vars (4) ---

NAME: {_yaml_string(name)}
DESCRIPTION: {_yaml_string(description)}
DEFINITION_BODY: |
  (author fills — one to three paragraphs naming the rule + the
  failure mode it prevents. Be concrete: name the situation, the
  observed failure, the corrective behaviour.)
HOW_TO_APPLY_BODY: |
  1. (author fills — numbered list of how to apply this rule in
     practice; what to do, what to check, when to halt-and-surface.)

# --- Optional vars (7) — uncomment + override the template's defaults ---

TYPE: "feedback"
CAPTURED_DATE: "{iso_date}"
# ORIGIN_SESSION_ID: ""
COMPOSES_WITH: |
  derivation/relationship: composes with / derives from / independent
  of [named principles] because [one-line justification per the M5
  procedural rule in feedback_principle_conflict_resolution_multi_signal].
STATUS: "active"
SOURCE: |
  (citation: telegram message id / build report path / commit SHA / equivalent)
WHY_BODY: |
  (author fills — one to three paragraphs naming the failure mode this
  rule prevents and the underlying mechanism. The "why" exists so a
  reader who encounters the rule out of context understands what
  problem it is solving, not just the corrective behaviour.)
"""


def _yaml_string(value: str) -> str:
    """Render a YAML-safe scalar string. Empty → empty quotes; else
    double-quoted with embedded double-quotes escaped.

    Mirrors ``new_plan._yaml_string``.
    """
    if value == "":
        return '""'
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


# ---------------------------------------------------------------------------
# Diagnostic emission (mirrors new_plan._emit_diagnostic)


def _emit_diagnostic(exc: NewMemoryError) -> None:
    # Emit on stdout AND stderr per AC.PA-hv.* halt-visibility pattern;
    # mirrors new_plan._emit_diagnostic.
    print(f"HALT: {exc.failure_class}: {exc}")
    print(f"new-memory error [{exc.failure_class}]: {exc}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Entry point


def run(
    slug: str,
    *,
    name: str | None = None,
    description: str | None = None,
    vars_out: Path | None = None,
    memory_out: Path | None = None,
    memory_dir: Path | None = None,
    render: bool = False,
    force: bool = False,
    repo_root: Path | None = None,
) -> int:
    """Scaffold a vars-file (and optionally render the memory-doc).

    Parameters
    ----------
    slug
        Memory-doc filename slug; matches ``^[a-z][a-z0-9_]*$``. The
        rendered file lands at ``<memory_dir>/feedback_<slug>.md``.
    name, description
        Pre-fill the corresponding vars; empty when ``None``.
    vars_out
        Output path for the vars-file. Default:
        ``<repo>/docs/memory/feedback_<slug>.vars.yaml``.
    memory_out
        Output path for the rendered memory-doc when ``--render``. Default:
        ``<memory_dir>/feedback_<slug>.md``.
    memory_dir
        Default destination directory for the memory-doc. Default:
        ``<repo>/docs/memory/``. Production callers typically point
        this at ``~/.claude/projects/<project>/memory/``.
    render
        When True, also render the memory-doc (delegates to
        ``loam_amend.commands.template.run("render", ...)``).
    force
        Overwrite existing files. Default is refuse-overwrite.
    repo_root
        Override repo-root resolution (testing hook). Default: query git.
    """
    # Slug validation first — invalid slug never touches disk.
    try:
        _validate_slug(slug)
    except NewMemoryError as exc:
        _emit_diagnostic(exc)
        return 2

    try:
        root = _resolve_repo_root(repo_root)
    except NewMemoryError as exc:
        _emit_diagnostic(exc)
        return 2

    if memory_dir is None:
        memory_dir = root / "docs" / "memory"
    if vars_out is None:
        vars_out = memory_dir / f"feedback_{slug}.vars.yaml"
    if memory_out is None:
        memory_out = memory_dir / f"feedback_{slug}.md"

    # Refuse-overwrite check BEFORE writing anything (no partial output).
    if vars_out.exists() and not force:
        exc = RefuseOverwrite(
            f"'{vars_out}' exists; pass --force to overwrite"
        )
        _emit_diagnostic(exc)
        return 3
    if render and memory_out.exists() and not force:
        exc = RefuseOverwrite(
            f"'{memory_out}' exists; pass --force to overwrite"
        )
        _emit_diagnostic(exc)
        return 3

    # Materialise the scaffold.
    content = _vars_file_content(
        slug,
        name=name or "",
        description=description or "",
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
            spec="memory-doc/SKELETON",
            var_flags=[],
            vars_file=vars_out,
            out=memory_out,
            force=force,
        )
        if rc != 0:
            # Template-render failure: vars-file written, memory-doc
            # render failed. Surface as exit 2 (contract failure)
            # mirroring AC.D-np.4 mapping; underlying diagnostic
            # already emitted by template_cmd.
            return rc

    print(f"scaffolded vars-file: {vars_out}")
    if render:
        print(f"rendered memory-doc: {memory_out}")
    return 0


__all__ = [
    "InvalidSlug",
    "IOFailure",
    "NewMemoryError",
    "RefuseOverwrite",
    "run",
]

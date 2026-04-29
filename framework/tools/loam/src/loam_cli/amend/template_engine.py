"""Markdown template engine for ``loam amend template`` (v1).

Templates are plain UTF-8 markdown files with an optional YAML
frontmatter block declaring required + optional variables. The body
substitutes ``{{KEY}}`` placeholders with values supplied at render
time. ``\\{{`` and ``\\}}`` escape to literal ``{{`` / ``}}`` after
substitution so a template can contain literal double-brace text.

This module is purely additive to loam amend (AC.D-tpl.6): no existing
subcommand reads from it; no existing function imports it. Stdlib +
``PyYAML`` only — no new third-party dependency.

ACs covered (per ``docs/rebuild/plans/dispatch-prompt-template-extension.md``):

- AC.D-tpl.1 — deterministic ``{{KEY}}`` substitution.
- AC.D-tpl.2 — frontmatter ``required`` / ``optional`` contract.
- AC.D-tpl.4 — ``parse_template`` exposes the contract for introspection.
- AC.D-tpl.5 — failure modes raise ``TemplateError`` subclasses with
  structured ``failure_class`` + identifier; never silent-render.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import yaml


# ---------------------------------------------------------------------------
# Errors


class TemplateError(Exception):
    """Base class for template engine failures.

    Carries a ``failure_class`` string for structured diagnostics so the
    CLI layer can map any TemplateError to a stable exit-code without a
    type-by-type dispatch.
    """

    failure_class: str = "template-error"


class TemplateNotFound(TemplateError):
    failure_class = "template-not-found"


class TemplateMalformed(TemplateError):
    """Frontmatter parse error or unmatched ``{{`` placeholder in body."""

    failure_class = "template-malformed"


class MissingRequiredVariable(TemplateError):
    failure_class = "missing-required-variable"


class UnrecognisedVariable(TemplateError):
    failure_class = "unrecognised-variable"


# ---------------------------------------------------------------------------
# Parsed template + helpers


_FRONTMATTER_RE = re.compile(
    r"\A---\s*\n(?P<fm>.*?)\n---\s*\n(?P<body>.*)\Z",
    re.DOTALL,
)
# Matches an opening or closing brace pair that is NOT preceded by a
# backslash. Used (a) to find ``{{KEY}}`` placeholders and (b) to detect
# unmatched delimiters in a malformed template. The placeholder regex
# captures the variable name; the unmatched-delimiter regex looks for
# any unescaped ``{{`` or ``}}`` left after substitution.
_PLACEHOLDER_RE = re.compile(r"(?<!\\)\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")
_UNMATCHED_OPEN_RE = re.compile(r"(?<!\\)\{\{")
_UNMATCHED_CLOSE_RE = re.compile(r"(?<!\\)\}\}")


@dataclass(frozen=True)
class ParsedTemplate:
    """A template parsed from disk: frontmatter contract + raw body."""

    family: str
    template_id: str
    description: str
    required: tuple[str, ...]
    optional_defaults: Mapping[str, str]
    body: str
    placeholders: tuple[str, ...]
    """Every ``{{NAME}}`` referenced in the body (deduped, in source order).

    AC.D-tpl.4 — ``validate`` reports the template's variables; AC.D-tpl.2 —
    rendering checks every placeholder against the contract.
    """


def _deduped(seq: list[str]) -> tuple[str, ...]:
    seen: dict[str, None] = {}
    for item in seq:
        if item not in seen:
            seen[item] = None
    return tuple(seen)


def _extract_placeholders(body: str) -> tuple[str, ...]:
    return _deduped([m.group(1) for m in _PLACEHOLDER_RE.finditer(body)])


def parse_template_text(text: str, *, family: str, template_id: str) -> ParsedTemplate:
    """Parse a template's source text into a ``ParsedTemplate``.

    Raises ``TemplateMalformed`` when the frontmatter block is missing,
    the YAML is malformed, ``required`` / ``optional`` shape is wrong,
    or the body contains unmatched ``{{``/``}}`` outside of recognised
    ``{{NAME}}`` placeholders (AC.D-tpl.4 / AC.D-tpl.5).
    """
    match = _FRONTMATTER_RE.match(text)
    if match is None:
        raise TemplateMalformed(
            f"template '{family}/{template_id}': missing or malformed YAML "
            "frontmatter (expected '---\\n<yaml>\\n---\\n' at file start)"
        )
    fm_text = match.group("fm")
    body = match.group("body")

    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as exc:
        raise TemplateMalformed(
            f"template '{family}/{template_id}': frontmatter YAML parse "
            f"error: {exc}"
        ) from exc

    if not isinstance(fm, dict):
        raise TemplateMalformed(
            f"template '{family}/{template_id}': frontmatter must be a "
            f"mapping (got {type(fm).__name__})"
        )

    description = fm.get("description", "")
    if not isinstance(description, str):
        raise TemplateMalformed(
            f"template '{family}/{template_id}': 'description' must be a "
            "string"
        )

    required_raw = fm.get("required", []) or []
    if not isinstance(required_raw, list) or not all(
        isinstance(x, str) for x in required_raw
    ):
        raise TemplateMalformed(
            f"template '{family}/{template_id}': 'required' must be a list "
            "of variable names"
        )
    required = tuple(required_raw)

    optional_raw = fm.get("optional", {}) or {}
    if not isinstance(optional_raw, dict):
        raise TemplateMalformed(
            f"template '{family}/{template_id}': 'optional' must be a "
            "mapping of variable_name -> default_value"
        )
    optional_defaults: dict[str, str] = {}
    for key, val in optional_raw.items():
        if not isinstance(key, str):
            raise TemplateMalformed(
                f"template '{family}/{template_id}': 'optional' keys must "
                "be strings"
            )
        optional_defaults[key] = "" if val is None else str(val)

    overlap = set(required) & set(optional_defaults)
    if overlap:
        raise TemplateMalformed(
            f"template '{family}/{template_id}': variables declared in "
            f"both 'required' and 'optional': {sorted(overlap)}"
        )

    placeholders = _extract_placeholders(body)

    # AC.D-tpl.5(d): unmatched ``{{`` / ``}}`` in body that do not pair
    # into a ``{{NAME}}`` placeholder are a malformed-template failure.
    # Strip recognised placeholders, then scan for stragglers.
    stripped = _PLACEHOLDER_RE.sub("", body)
    if _UNMATCHED_OPEN_RE.search(stripped) or _UNMATCHED_CLOSE_RE.search(stripped):
        raise TemplateMalformed(
            f"template '{family}/{template_id}': body contains unmatched "
            "'{{' or '}}' delimiters outside of recognised {{NAME}} "
            "placeholders (use \\{{ / \\}} to escape literal braces)"
        )

    return ParsedTemplate(
        family=family,
        template_id=template_id,
        description=description,
        required=required,
        optional_defaults=optional_defaults,
        body=body,
        placeholders=placeholders,
    )


def parse_template(path: Path, *, family: str, template_id: str) -> ParsedTemplate:
    """Parse a template at ``path``. Raises ``TemplateNotFound`` if absent."""
    if not path.is_file():
        raise TemplateNotFound(
            f"template '{family}/{template_id}' not found at {path}"
        )
    text = path.read_text(encoding="utf-8")
    return parse_template_text(text, family=family, template_id=template_id)


# ---------------------------------------------------------------------------
# Rendering


def render(template: ParsedTemplate, variables: Mapping[str, str]) -> str:
    """Render ``template`` with ``variables``.

    Raises ``MissingRequiredVariable`` if a required variable is absent
    (AC.D-tpl.2 / AC.D-tpl.5(b)). Raises ``UnrecognisedVariable`` if the
    caller supplies a variable not declared in the contract
    (AC.D-tpl.2 / AC.D-tpl.5(c)).
    """
    declared = set(template.required) | set(template.optional_defaults)
    extra = set(variables) - declared
    if extra:
        raise UnrecognisedVariable(
            f"template '{template.family}/{template.template_id}': "
            f"unrecognised variable(s) {sorted(extra)}; declared: "
            f"required={list(template.required)}, "
            f"optional={list(template.optional_defaults)}"
        )

    missing = [name for name in template.required if name not in variables]
    if missing:
        raise MissingRequiredVariable(
            f"template '{template.family}/{template.template_id}': "
            f"missing required variable(s) {missing}"
        )

    resolved: dict[str, str] = dict(template.optional_defaults)
    resolved.update({k: str(v) for k, v in variables.items()})

    def _sub(match: "re.Match[str]") -> str:
        name = match.group(1)
        # Defensive: every placeholder name appears in declared vars
        # (template parsing did not enforce that — by design, since a
        # placeholder for a declared optional var without explicit
        # defaulting is allowed). Resolve via ``resolved`` falling back
        # to empty string for any optional var without a default.
        if name in resolved:
            return resolved[name]
        if name in template.optional_defaults:
            return template.optional_defaults[name]
        # AC.D-tpl.5: a placeholder referencing a name absent from the
        # contract should have been caught at parse-time-against-contract,
        # but defensively raise here too. This path indicates a template
        # whose body references a variable not declared in either
        # ``required`` or ``optional`` — treat as malformed.
        raise TemplateMalformed(
            f"template '{template.family}/{template.template_id}': body "
            f"references {{{{ {name} }}}} which is not declared in "
            "frontmatter 'required' or 'optional'"
        )

    rendered = _PLACEHOLDER_RE.sub(_sub, template.body)
    # Decode escape sequences to literal braces. AC.D-tpl.1 design note.
    rendered = rendered.replace("\\{{", "{{").replace("\\}}", "}}")
    return rendered


# ---------------------------------------------------------------------------
# Registry discovery


def discover_templates(root: Path) -> list[tuple[str, str, Path]]:
    """Walk a templates root and return ``(family, template_id, path)`` for
    every ``<family>/<id>.md`` file.

    Used by ``loam amend template list`` (AC.D-tpl.4). Sort order is
    deterministic: family ascending, template_id ascending.
    """
    if not root.is_dir():
        return []
    entries: list[tuple[str, str, Path]] = []
    for family_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        family = family_dir.name
        for tpl_path in sorted(family_dir.glob("*.md")):
            template_id = tpl_path.stem
            entries.append((family, template_id, tpl_path))
    return entries

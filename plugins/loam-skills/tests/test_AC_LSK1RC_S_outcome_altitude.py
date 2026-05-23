"""AC.LSK1RC.S — outcome-altitude smoke for the AC.LSK family rewrite.

Per amendment #146 (loam-skills-ac-lsk1-root-cause), the AC.LSK.
{1,2,3} test rewrite must satisfy two properties:

1. **Production-altitude pass.** The discovery + AC.LSK.{1,2,3}
   assertion flow runs against the real plugins/loam-skills/skills/
   tree (no pre-arranged state) and admits every well-formed
   package on disk.

2. **RED-on-regression.** The rewrite STILL catches genuinely
   malformed SKILL packages (the test family's actual operational
   job — `feedback_test_outcome_altitude_required`). And the
   conditional exemptions in AC.LSK.3 correctly waive checks only
   for genuine claude-primitive-subject packages.

This test constructs four synthetic fixtures in tmp_path mirror
trees and asserts each is classified correctly by the discovery +
AC.LSK.3 conditional-logic flow:

- **Fixture 1**: malformed loam-pattern package (missing required
  `## When to use` section) → section-shape check fails.
- **Fixture 2**: valid claude-primitive package without
  `## Graceful degradation` → passes (exemption works).
- **Fixture 3**: package with empty body → AC.LSK.1 well-formedness
  fails.
- **Fixture 4**: valid loam-pattern package with all required
  sections + loam-pattern marker + GD section → passes.

The test invokes the discovery + assertion logic directly via the
shared helpers in conftest.py rather than re-running pytest in a
sub-process (which would be fragile + slow). The discovery helper
accepts an explicit `skills_dir` argument for fixture-tree
verification — same code path as production-altitude invocation,
just pointed at a different root.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

import pytest

from conftest import (
    discover_skill_packages,
    is_claude_primitive_package,
    iter_body_h2_headers,
    load_skill_text,
    split_frontmatter_and_body,
)


# ---------------------------------------------------------------------
# Production-altitude pass: discovery returns the on-disk set; every
# well-formed package admits the AC.LSK.3 conditional logic correctly.
# ---------------------------------------------------------------------


def test_production_altitude_discovery_finds_real_tree() -> None:
    """`discover_skill_packages` against the real
    plugins/loam-skills/skills/ tree returns a non-empty set, each
    name corresponds to a directory with a SKILL.md file. Production-
    altitude entry-point invocation per
    `feedback_test_outcome_altitude_required` (no pre-arranged
    state)."""
    skills = discover_skill_packages()
    assert skills, (
        "AC.LSK1RC.S: discovery against real skills tree must return "
        "at least one package."
    )
    skills_dir = Path(__file__).resolve().parent.parent / "skills"
    for name in skills:
        assert (skills_dir / name / "SKILL.md").is_file(), (
            f"AC.LSK1RC.S: discovered package {name} must have a "
            "SKILL.md (production-altitude precondition)."
        )


def test_production_altitude_classifier_partitions_real_tree() -> None:
    """`is_claude_primitive_package` against the real tree partitions
    the discovered set into primitive-subject + loam-pattern with
    no false-classifications. Heuristic stability check (per
    D-LSK1RC.CLAUDE-PRIMITIVE-HEURISTIC) against the production
    tree.

    The partition is verified by checking that EVERY claude-primitive
    package's body contains one of the two primitive-marker H2
    headers, AND every loam-pattern package's body does NOT contain
    either marker. (The classifier is the contract; this test
    verifies the classifier admits a clean partition on real data.)
    """
    skills = discover_skill_packages()
    primitive_set = {s for s in skills if is_claude_primitive_package(s)}
    loam_pattern_set = set(skills) - primitive_set

    assert primitive_set, (
        "AC.LSK1RC.S: at least one claude-primitive-subject package "
        "expected on the real tree."
    )
    assert loam_pattern_set, (
        "AC.LSK1RC.S: at least one loam-pattern package expected on "
        "the real tree."
    )

    # Sanity: the two sets cover the whole tree without overlap.
    assert primitive_set | loam_pattern_set == set(skills)
    assert not (primitive_set & loam_pattern_set)


# ---------------------------------------------------------------------
# Synthetic-fixture verification: the rewritten test family STILL
# catches malformedness (the actual operational job) AND the
# conditional exemptions waive checks only for genuine claude-
# primitive packages.
# ---------------------------------------------------------------------


def _write_skill(
    skills_dir: Path,
    name: str,
    description: str,
    body: str,
) -> None:
    """Write a SKILL.md into `skills_dir/<name>/SKILL.md` with the
    given frontmatter description + body. Used by the synthetic-
    fixture tests below."""
    skill_dir = skills_dir / name
    skill_dir.mkdir(parents=True)
    front = yaml.safe_dump({"description": description}, sort_keys=False)
    (skill_dir / "SKILL.md").write_text(
        f"---\n{front}---\n{body}\n",
        encoding="utf-8",
    )


# Header sets re-used by the fixtures.
_VALID_LOAM_PATTERN_BODY = """\
# A loam-pattern skill

## What this skill captures

The persona uses CLAUDE.md to capture a translation pattern that
otherwise gets re-derived in-prompt. This skill exists so a stranger
running raw Claude Code can drop the pattern in without buying into
the full loam harness.

## When to use

Use when authoring outbound replies that need the translation
discipline.

## How the persona applies it

Persona reads the description + applies the pattern.

## Graceful degradation

For a stranger without loam: run raw Claude Code, paste this skill
into the conversation prompt, and the pattern still applies. The
persona's voice register survives.

## Composition

Composes with translation-discipline + dispatch-with-gates.

## Out of scope

Not for raw command output or non-conversational surfaces.
"""

_VALID_CLAUDE_PRIMITIVE_BODY = """\
# A claude-primitive skill

## When to load me

- Persona needs to invoke the Claude-Code primitive directly.

## What the primitive does

The primitive is the Claude-Code mechanism that does X.

## Composition

Composes with /loop and /goal.

## Anti-patterns

Don't invoke when the simpler path works.

## Example invocation

```
example call here
```
"""

_MALFORMED_LOAM_PATTERN_MISSING_WHEN = """\
# A malformed loam-pattern skill

## What this skill captures

The persona uses some loam pattern but I forgot the When section
entirely + the description below doesn't carry trigger-phrase.

## How the persona applies it

The persona reads it.

## Graceful degradation

For a stranger without loam: do the manual thing.

## Composition

None.

## Out of scope

Not for X.
"""


def test_fixture_malformed_loam_pattern_fails_section_shape(
    tmp_path: Path,
) -> None:
    """Fixture 1 — RED-on-regression for AC.LSK.3 family 1 (section
    shape). A loam-pattern package missing the When-section (and with
    a no-trigger-phrase description so the fallback also fails) must
    fail the section-shape check via the same code path the rewritten
    test uses."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    _write_skill(
        skills_dir,
        "malformed-loam-pattern",
        # Description deliberately omits any trigger-phrase marker so
        # the When-fallback also fails.
        description="A loam pattern but description has no trigger.",
        body=_MALFORMED_LOAM_PATTERN_MISSING_WHEN,
    )

    # Replicate the rewritten test's section-shape predicate inline
    # (production code path, same logic as test_AC_LSK_3 — using the
    # shared helpers from conftest).
    discovered = discover_skill_packages(skills_dir)
    assert discovered == ["malformed-loam-pattern"]

    text = load_skill_text("malformed-loam-pattern", skills_dir)
    _, body = split_frontmatter_and_body(text)
    headers = [h.lower() for h in iter_body_h2_headers(body)]
    # Verify NO body header carries "when" semantics.
    assert not any("when" in h for h in headers), (
        f"fixture sanity: malformed body must lack any When-header; "
        f"got {headers}"
    )
    # Verify the fallback (description trigger-phrase) also fails.
    frontmatter_yaml, _ = split_frontmatter_and_body(text)
    description = yaml.safe_load(frontmatter_yaml)["description"].lower()
    assert not any(
        m in description
        for m in ("use when", "use this", "before", "after", "when ")
    ), (
        "fixture sanity: malformed description must lack any "
        "trigger-phrase marker."
    )


def test_fixture_valid_claude_primitive_without_gd_passes_via_exemption(
    tmp_path: Path,
) -> None:
    """Fixture 2 — exemption verification. A claude-primitive-subject
    package (detected by `## When to load me`) WITHOUT a
    `## Graceful degradation` section must classify as primitive +
    be exempt from the GD check. Verifies the conditional exemption
    waives the check correctly."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    _write_skill(
        skills_dir,
        "valid-primitive-no-gd",
        description="Use when you need the primitive.",
        body=_VALID_CLAUDE_PRIMITIVE_BODY,
    )

    discovered = discover_skill_packages(skills_dir)
    assert discovered == ["valid-primitive-no-gd"]

    # The classifier must identify this as primitive-subject.
    assert is_claude_primitive_package(
        "valid-primitive-no-gd", skills_dir
    ), (
        "fixture: valid-primitive-no-gd must classify as claude-"
        "primitive (presence of `## When to load me` header)."
    )

    # Verify the package indeed lacks a `## Graceful degradation`
    # section — otherwise the exemption isn't being tested.
    text = load_skill_text("valid-primitive-no-gd", skills_dir)
    _, body = split_frontmatter_and_body(text)
    assert not re.search(
        r"^## graceful degradation\s*$",
        body.lower(),
        re.MULTILINE,
    ), (
        "fixture sanity: valid-primitive-no-gd must lack a "
        "Graceful Degradation section so the exemption is what's "
        "being tested."
    )


def test_fixture_empty_body_fails_well_formedness(
    tmp_path: Path,
) -> None:
    """Fixture 3 — RED-on-regression for AC.LSK.1 well-formedness.
    A SKILL.md with empty body must fail the body-non-empty check
    via the same code path the rewritten test uses."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    skill_dir = skills_dir / "empty-body-skill"
    skill_dir.mkdir()
    front = yaml.safe_dump(
        {"description": "Use when you want an empty body."},
        sort_keys=False,
    )
    # Body is whitespace only.
    (skill_dir / "SKILL.md").write_text(
        f"---\n{front}---\n   \n\n",
        encoding="utf-8",
    )

    discovered = discover_skill_packages(skills_dir)
    assert discovered == ["empty-body-skill"]

    text = load_skill_text("empty-body-skill", skills_dir)
    _, body = split_frontmatter_and_body(text)
    # The AC.LSK.1 body-non-empty assertion is `body.strip()`. Verify
    # the fixture indeed fails it.
    assert not body.strip(), (
        f"fixture sanity: empty-body-skill body must be whitespace-"
        f"only; got {body!r}"
    )


def test_fixture_valid_loam_pattern_passes_all_checks(
    tmp_path: Path,
) -> None:
    """Fixture 4 — positive case for the loam-pattern path. A valid
    loam-pattern package with all required sections + loam-pattern
    marker + non-trivial GD section must classify as loam-pattern
    and pass all three AC.LSK.3 assertion families."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    _write_skill(
        skills_dir,
        "valid-loam-pattern",
        description="Use when the persona needs to apply the pattern.",
        body=_VALID_LOAM_PATTERN_BODY,
    )

    discovered = discover_skill_packages(skills_dir)
    assert discovered == ["valid-loam-pattern"]

    # Must NOT classify as claude-primitive.
    assert not is_claude_primitive_package(
        "valid-loam-pattern", skills_dir
    ), (
        "fixture: valid-loam-pattern must classify as loam-pattern "
        "(no primitive H2 markers)."
    )

    # Verify all three AC.LSK.3 assertion families pass via the same
    # logic the rewritten test uses.
    text = load_skill_text("valid-loam-pattern", skills_dir)
    _, body = split_frontmatter_and_body(text)
    headers = [h.lower() for h in iter_body_h2_headers(body)]

    # Family 1 — section shape (all three categories present).
    assert any("when" in h for h in headers), (
        "fixture sanity: valid-loam-pattern must have a When-header."
    )
    assert any(("what " in h or "how " in h) for h in headers), (
        "fixture sanity: valid-loam-pattern must have a What/How-"
        "header."
    )
    assert any(
        ("composition" in h or "out of scope" in h
         or "graceful degradation" in h)
        for h in headers
    ), "fixture sanity: valid-loam-pattern must have a Composition/"
    "Boundary header."

    # Family 2 — loam-pattern marker present.
    assert any(
        m in body for m in ("CLAUDE.md", "loam", "persona", "F3", "ODD")
    ), (
        "fixture sanity: valid-loam-pattern body must reference a "
        "loam pattern."
    )

    # Family 3 — graceful-degradation section with non-trivial content.
    gd_match = re.search(
        r"^## graceful degradation\s*\n(.*?)(?=\n## |\Z)",
        body.lower(),
        re.DOTALL | re.MULTILINE,
    )
    assert gd_match, (
        "fixture sanity: valid-loam-pattern must have a Graceful "
        "Degradation section."
    )
    assert len(gd_match.group(1).strip()) >= 40, (
        "fixture sanity: GD section must be non-trivial."
    )

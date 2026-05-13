"""AC.SDPD.{1,2,3} — `loam release --plan-doc <path>` flag.

Per `feedback_version_numbers_at_release_time` (2026-05-13) plan-doc
filenames are now scope-descriptive (no version pre-baked); version
derives at release-time. The v0.8.2 PATCH adds the ``--plan-doc``
flag to ``loam release`` so the gates that previously inferred their
input paths from the version slug can read explicit paths instead.

This module covers the three new ACs:

- **AC.SDPD.1** — flag accepted by argparse with helpful help text.
- **AC.SDPD.2** — `check_acs_verified` reads the named plan-doc when
  the flag is set; RED with corrective hint on missing-explicit-path.
- **AC.SDPD.3** — `check_hard_smoke` reads
  `docs/experiments/<plan-doc-stem>-hard-smoke.md` when the flag is
  set; RED with corrective hint on missing stem-derived path.

Backward-compat (flag-absent behaviour preserved) is verified by the
existing `test_AC_V060_2_pre_publish_gates.py` suite continuing to
pass unmodified.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

import loam_cli.cli as cli_mod
from loam_cli.release import gates
from loam_cli.release.cli import build_release_subcommand


# --------------------------------------------------------------------
# AC.SDPD.1 — argparse flag accepted
# --------------------------------------------------------------------


def test_release_parser_accepts_plan_doc_flag() -> None:
    """The release subparser accepts `--plan-doc <path>` and exposes
    the value at `args.plan_doc` as a Path. Default value when the
    flag is omitted is None (per D-SDPD.1.b backward-compat ruling).
    """
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="subcommand", required=True)
    build_release_subcommand(sub)
    args = parser.parse_args(
        ["release", "v0.8.2", "--plan-doc", "/tmp/x.md"]
    )
    assert args.plan_doc == Path("/tmp/x.md")
    args2 = parser.parse_args(["release", "v0.8.2"])
    assert args2.plan_doc is None


def test_release_help_mentions_plan_doc_and_scope_descriptive() -> None:
    """`loam release --help` output references the flag + the
    scope-descriptive use case so an operator reading the help
    understands when to use it."""
    parser = cli_mod._build_parser()
    sp = next(
        a for a in parser._actions
        if isinstance(a, argparse._SubParsersAction)
    )
    release_parser = sp.choices["release"]
    help_text = release_parser.format_help()
    assert "--plan-doc" in help_text
    assert "scope-descriptive" in help_text


# --------------------------------------------------------------------
# AC.SDPD.2 — check_acs_verified reads explicit plan-doc
# --------------------------------------------------------------------


def _author_scope_descriptive_plan_doc(
    repo_root: Path,
    slug: str,
    ac_id: str = "AC.FOO.1",
) -> Path:
    """Author a minimal scope-descriptive plan-doc at
    ``docs/plans/<slug>.md`` with a §4 heading naming *ac_id* + a
    §13 §status section marking it GREEN. Returns the absolute path.
    """
    plan_path = repo_root / "docs" / "plans" / f"{slug}.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        f"# {slug}\n\n"
        "## §4 Acceptance criteria\n\n"
        f"### {ac_id} — Trivial\n\nWhat: does the thing.\n\n"
        "## §13 §status\n\n"
        f"| AC | Verdict | Evidence |\n"
        f"|---|---|---|\n"
        f"| {ac_id} | GREEN | works. |\n",
        encoding="utf-8",
    )
    return plan_path


def test_acs_verified_reads_named_plan_doc_when_flag_provided(
    staged_repo: Path,
) -> None:
    """When `plan_doc` is set, the gate reads the named plan-doc and
    skips the version-slug glob entirely. The fixture's existing
    `v0-6-0-release-process.md` is ignored; the explicit
    scope-descriptive plan-doc is read."""
    scope_descriptive = _author_scope_descriptive_plan_doc(
        staged_repo, "scope-descriptive-feature-slug"
    )
    # Use a version that has NO matching version-slug plan-doc so the
    # glob fallback would RED — verifies the explicit path is what
    # gets read.
    r = gates.check_acs_verified(
        staged_repo, "v9.9.9", plan_doc=scope_descriptive
    )
    assert r.ok is True, r.message
    assert "GREEN" in r.message
    # The success message names the explicit plan-doc (repo-relative).
    assert "scope-descriptive-feature-slug" in r.message


def test_acs_verified_red_with_hint_when_provided_plan_doc_missing(
    staged_repo: Path,
) -> None:
    """When `plan_doc` is set but the path doesn't exist, the gate
    returns RED with a corrective hint naming the missing path + the
    `--plan-doc` flag."""
    missing = Path("docs/plans/does-not-exist-anywhere.md")
    r = gates.check_acs_verified(
        staged_repo, "v9.9.9", plan_doc=missing
    )
    assert r.ok is False
    assert "does-not-exist-anywhere.md" in r.message
    assert "--plan-doc" in r.message


def test_acs_verified_accepts_relative_plan_doc_path(
    staged_repo: Path,
) -> None:
    """A relative `plan_doc` path is resolved against `repo_root`.
    Verifies D-SDPD.1.a + D-SDPD.1.b semantics together: an operator
    passing `--plan-doc docs/plans/foo.md` from the repo root works
    the same as passing the absolute path."""
    _author_scope_descriptive_plan_doc(
        staged_repo, "another-descriptive-slug"
    )
    relative = Path("docs/plans/another-descriptive-slug.md")
    r = gates.check_acs_verified(
        staged_repo, "v9.9.9", plan_doc=relative
    )
    assert r.ok is True, r.message


# --------------------------------------------------------------------
# AC.SDPD.3 — check_hard_smoke reads stem-derived path
# --------------------------------------------------------------------


def test_hard_smoke_reads_stem_derived_path_when_flag_provided(
    staged_repo: Path,
) -> None:
    """When `plan_doc` is set, the gate constructs
    `docs/experiments/<plan-doc-stem>-hard-smoke.md` and reads it.
    `Path.stem` strips the trailing `.md` extension."""
    stem = "scope-descriptive-feature-slug"
    smoke_path = (
        staged_repo / "docs" / "experiments" / f"{stem}-hard-smoke.md"
    )
    smoke_path.parent.mkdir(parents=True, exist_ok=True)
    smoke_path.write_text(
        f"# {stem} HARD smoke\n\nVerdict: GREEN.\n", encoding="utf-8"
    )
    # The plan-doc path doesn't need to exist on disk for the stem
    # extraction; check_hard_smoke only uses .stem (not .read_text).
    plan_doc = Path("docs/plans/scope-descriptive-feature-slug.md")
    r = gates.check_hard_smoke(
        staged_repo, "v9.9.9", plan_doc=plan_doc
    )
    assert r.ok is True, r.message
    assert "GREEN" in r.message
    assert stem in r.message


def test_hard_smoke_red_when_stem_derived_path_missing(
    staged_repo: Path,
) -> None:
    """When `plan_doc` is set but the stem-derived hard-smoke writeup
    is missing, the gate returns RED with a hint naming the
    expected path."""
    plan_doc = Path("docs/plans/nonexistent-feature-slug.md")
    r = gates.check_hard_smoke(
        staged_repo, "v9.9.9", plan_doc=plan_doc
    )
    assert r.ok is False
    assert "nonexistent-feature-slug-hard-smoke.md" in r.message


def test_hard_smoke_uses_plan_doc_stem_not_version_slug_when_both_paths_exist(
    staged_repo: Path,
) -> None:
    """When `plan_doc` is set AND the version-slug hard-smoke writeup
    also exists (the fixture's `v0-6-0-hard-smoke.md`), the gate
    reads the stem-derived path. Verifies the explicit-flag path
    takes precedence; the version-slug inference is fully bypassed.

    Sanity-check evidence: the version-slug writeup says ``GREEN``
    but the stem-derived writeup says ``RED`` so the verdict is
    distinguishable.
    """
    stem = "other-descriptive-slug"
    smoke_path = (
        staged_repo / "docs" / "experiments" / f"{stem}-hard-smoke.md"
    )
    smoke_path.parent.mkdir(parents=True, exist_ok=True)
    # Deliberately omit GREEN so the gate would RED-with-hint if it
    # reads this file. The version-slug writeup at v0-6-0-hard-smoke.md
    # already exists and contains GREEN (fixture default).
    smoke_path.write_text(
        f"# {stem}\n\nVerdict: RED.\n", encoding="utf-8"
    )
    plan_doc = Path(f"docs/plans/{stem}.md")
    r = gates.check_hard_smoke(
        staged_repo, "v0.6.0", plan_doc=plan_doc
    )
    # Stem-derived writeup was read (and RED'd) — NOT the version-
    # slug-derived one (which has GREEN).
    assert r.ok is False
    assert "GREEN verdict token" in r.message


# --------------------------------------------------------------------
# Backward-compat sanity — flag-absent behaviour preserved
# --------------------------------------------------------------------


def test_acs_verified_falls_back_to_version_glob_when_flag_absent(
    staged_repo: Path, fixture_version: str
) -> None:
    """Confirms backward-compat. Existing test in
    `test_AC_V060_2_pre_publish_gates.py` covers this with deeper
    asserts; this is a sanity-check that the new optional parameter
    didn't shift the default code path."""
    r = gates.check_acs_verified(staged_repo, fixture_version)
    assert r.ok is True


def test_hard_smoke_falls_back_to_version_slug_when_flag_absent(
    staged_repo: Path, fixture_version: str
) -> None:
    """Backward-compat sanity-check for `check_hard_smoke`."""
    r = gates.check_hard_smoke(staged_repo, fixture_version)
    assert r.ok is True


def test_run_all_forwards_plan_doc_to_relevant_gates(
    staged_repo: Path,
) -> None:
    """`run_all(..., plan_doc=...)` threads the parameter to
    `check_hard_smoke` + `check_acs_verified`; the other four gates
    ignore it (their behaviour unchanged). Verifies D-SDPD.6."""
    stem = "yet-another-descriptive-slug"
    _author_scope_descriptive_plan_doc(staged_repo, stem)
    (
        staged_repo / "docs" / "experiments" / f"{stem}-hard-smoke.md"
    ).write_text(
        f"# {stem}\n\nVerdict: GREEN.\n", encoding="utf-8"
    )
    results = gates.run_all(
        staged_repo,
        "v9.9.9",  # no version-slug match; explicit plan-doc carries
        plan_doc=Path(f"docs/plans/{stem}.md"),
    )
    by_name = {r.name: r for r in results}
    assert by_name["acs-verified"].ok is True, (
        by_name["acs-verified"].message
    )
    assert by_name["hard-smoke"].ok is True, (
        by_name["hard-smoke"].message
    )
    # The other gates may RED for unrelated reasons (state-shipped
    # checks for v9.9.9 in STATE.md, seal-reachable checks the
    # roadmap row for v9.9.9, etc.) — those failures are expected
    # and don't tell us anything about the plan_doc forwarding. The
    # only thing the test asserts is that the two flag-honoring
    # gates return GREEN, which is the AC behaviour.

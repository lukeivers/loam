"""Per-gate pre-publish verification (AC.V060.2 + AC.MIG-GATE.*).

Seven structural gates, each returning a :class:`GateResult` carrying
a verdict + a corrective hint on RED. The orchestrator
(:mod:`loam_cli.release.runner`) runs every gate (does NOT short-
circuit on first RED) so the operator sees the full state in one
report rather than chasing one failure at a time. Per AC.V060.2
spec each gate has its own corrective hint (not a generic error).

Default Path A per D-V060.2: single module, per-gate functions, no
plugin registry. Each ``check_*`` function takes ``(repo_root,
version)`` plus any extra context and returns ``GateResult``.

Gates:
  1. ``check_hard_smoke`` — ``docs/experiments/<version>-hard-smoke.md``
     exists + contains the literal ``GREEN`` token.
  2. ``check_acs_verified`` — ``docs/plans/<version-slug>.md`` plan-doc
     §status / §verdict-matrix marks each AC GREEN.
  3. ``check_state_shipped`` — ``docs/STATE.md`` mentions the version
     followed by ``SHIPPED``.
  4. ``check_clean_tree`` — ``git status --porcelain`` returns empty.
  5. ``check_branch_main`` — ``git branch --show-current`` returns
     ``main`` (revised from ``pos-v2`` per the plan-doc revision).
  6. ``check_seal_commit_reachable`` — the seal SHA from
     ``docs/release-roadmap.md`` §2 row is reachable from HEAD.
  7. ``check_migration_declared`` — ``docs/state-migrations/`` declares a
     user-state migration for the version (a ``no-op`` declaration is valid).
     HARD-BLOCK, no override (the load-bearing migration release-gate, P1.3).
  8. ``check_substrate_audit`` — no shipping doc carries a structured
     status claim that DIVERGES from the STATE-OF-LOAM record derived
     fresh from ground truth (refs + live config + real probes). HARD-
     BLOCK (AC.SOL-GATE.*, N2): a stale "dark"-for-live status claim
     shipping in a release is the exact failure this gate exists to
     stop. Composes on the SAME comparator the ``loam audit`` verb uses.

Each gate is independently testable; per-gate test pairs (one passing,
one failing) live in
``framework/tools/loam/tests/test_AC_V060_2_*.py``.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GateResult:
    """Verdict for a single pre-publish gate.

    ``ok`` carries the boolean verdict; ``message`` carries either a
    one-line success summary or a multi-line corrective hint on
    failure. ``name`` is the short gate identifier used in report
    headers (``hard-smoke`` / ``acs-verified`` / ``state-shipped`` /
    ``clean-tree`` / ``branch-main`` / ``seal-reachable``).
    """

    name: str
    ok: bool
    message: str


# --------------------------------------------------------------------
# Gate 1 — HARD smoke GREEN (AC.V060.2 #1)
# --------------------------------------------------------------------


def _version_to_slug(version: str) -> str:
    """``v0.6.0`` → ``v0-6-0``; preserves any 4-digit hot-patch form
    such as ``v0.2.5.1`` → ``v0-2-5-1``.
    """
    return version.replace(".", "-")


def _display_path(path: Path, repo_root: Path) -> str:
    """Return a repo-relative display string for *path* when it lives
    under *repo_root*; otherwise the absolute path.

    Used in corrective-hint messages. Falls back gracefully when an
    explicit ``--plan-doc`` argument points outside the repo root
    (rare but legal — ``relative_to`` would raise ValueError there).
    """
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def check_hard_smoke(
    repo_root: Path,
    version: str,
    *,
    plan_doc: Path | None = None,
) -> GateResult:
    """Verify ``docs/experiments/<version-slug>-hard-smoke.md`` exists
    + contains the literal ``GREEN`` verdict token.

    Pattern matches the established v0.4.x hard-smoke writeups (see
    ``docs/experiments/v0-4-3-hard-smoke.md`` for the canonical
    template; the file's first heading + verdict line carry ``GREEN``).

    Per AC.SDPD.3 (v0.8.2): when *plan_doc* is provided, the
    experiments-path is derived from the plan-doc's stem instead of
    the version slug (``docs/experiments/<plan-doc-stem>-hard-smoke.md``).
    This supports scope-descriptive plan-doc slugs per
    ``feedback_version_numbers_at_release_time`` (2026-05-13).
    """
    if plan_doc is not None:
        # Per D-SDPD.3.a: Path.stem strips the trailing ``.md`` (and
        # any subdirectory prefix); the experiments directory is fixed.
        stem = plan_doc.stem
        path = repo_root / "docs" / "experiments" / f"{stem}-hard-smoke.md"
    else:
        slug = _version_to_slug(version)
        path = repo_root / "docs" / "experiments" / f"{slug}-hard-smoke.md"
    if not path.exists():
        return GateResult(
            name="hard-smoke",
            ok=False,
            message=(
                f"missing HARD smoke writeup at {path.relative_to(repo_root)}; "
                f"per `feedback_hard_smoke_per_minor_before_publish` every "
                f"minor's last cycle runs HARD smoke against rd-automation "
                f"BEFORE publish gate. Author the writeup + record the "
                f"verdict; re-run `loam release {version}` once GREEN."
            ),
        )
    body = path.read_text(encoding="utf-8")
    # Look for the verdict token. Existing writeups carry "Verdict:
    # GREEN" or "GREEN." in the opening line; either matches the
    # token-presence check.
    if "GREEN" not in body:
        return GateResult(
            name="hard-smoke",
            ok=False,
            message=(
                f"HARD smoke writeup at {path.relative_to(repo_root)} does "
                f"not contain the GREEN verdict token. Re-run the smoke "
                f"against rd-automation; record the verdict line "
                f"(`Verdict: GREEN.`); re-run `loam release {version}` once "
                f"GREEN."
            ),
        )
    return GateResult(
        name="hard-smoke",
        ok=True,
        message=f"HARD smoke GREEN at {path.relative_to(repo_root)}",
    )


# --------------------------------------------------------------------
# Gate 2 — ACs verified per plan-doc (AC.V060.2 #2)
# --------------------------------------------------------------------


def _find_plan_doc(
    repo_root: Path,
    version: str,
    *,
    plan_doc: Path | None = None,
) -> Path | None:
    """Locate the plan-doc for *version*.

    Two paths:

    1. **Explicit (AC.SDPD.2, v0.8.2):** when *plan_doc* is provided,
       resolve it (relative paths joined to *repo_root*) and return
       it iff the file exists. The version-slug glob is skipped
       entirely. Caller is responsible for the corrective hint on
       missing-explicit-path.
    2. **Implicit (default, v0.6.0 — v0.8.1):** glob
       ``docs/plans/<version-slug>*.md`` for the named version.
       Plan-doc filenames vary slightly:
       ``v0-6-0-release-process.md`` /
       ``v0-5-0-subagent-personas-routing-and-priming.md``. The lookup
       uses the version's slug as a prefix glob so the filename's
       descriptive tail is permitted.

    Per ``feedback_version_numbers_at_release_time`` (2026-05-13)
    scope-descriptive plan-doc slugs are the new convention; the
    explicit path is how that convention reaches the gates.
    """
    if plan_doc is not None:
        # Resolve relative paths against repo_root for caller
        # convenience. Absolute paths pass through.
        resolved = (
            plan_doc
            if plan_doc.is_absolute()
            else (repo_root / plan_doc)
        )
        return resolved if resolved.is_file() else None
    slug = _version_to_slug(version)
    # Amendment #143 Scope B (D-T1RS.GLOB-UPDATE + D-T1RS.GLOB-PRIORITY):
    # walk BOTH docs/plans/ and docs/plans/sealed/ via the shared
    # ``find_plan_doc_by_slug_glob`` helper. Sealed-first when both
    # versions exist (canonical archive wins during transition window).
    # Local import so the dependency is at call-time (release gates
    # are dev-mode-only callers; loam-amend may not be installed in
    # non-dev modes).
    from loam_amend.plan_locator import find_plan_doc_by_slug_glob

    return find_plan_doc_by_slug_glob(repo_root, slug)


def _extract_section_4_body(body: str) -> str | None:
    """Slice the plan-doc body to its `## §4 — Acceptance criteria`
    section.

    Returns the substring between the §4 heading and the next
    ``## §<n>`` boundary (or end-of-doc if §4 is the final section).
    Returns ``None`` if no §4 heading is found.

    Heading-recognition is permissive across the three observed
    forms in the existing plan-doc corpus (verified at v0.7.2
    plan-time across 88 plan-docs):
      - ``## §4 — Acceptance criteria`` (em-dash separator; v0.6.0+)
      - ``## §4. Acceptance criteria`` (period separator; older shape)
      - ``## §4 Acceptance criteria`` (space separator; conftest fixture)

    Per AC.READYP.1: the AC-ID scan is restricted to this slice, so
    cross-reference AC IDs in §6 (out-of-scope), §8 (dependencies),
    §11 (authority chain), §13 (§status), etc. are not flagged as
    in-scope ACs requiring §status verdicts.
    """
    # Match `## §4` followed by an optional separator (em-dash, hyphen,
    # period, or whitespace) and then any heading text. Case-insensitive
    # so a future ``Acceptance Criteria`` capitalisation still resolves.
    heading_match = re.search(
        r"(?im)^##\s*§4\b[^\n]*$",
        body,
    )
    if heading_match is None:
        return None
    section_start = heading_match.end()
    # Next `## §<n>` heading (any digit) bounds the section. End-of-doc
    # is the implicit terminator if §4 is the final ``## §`` block.
    next_section = re.search(
        r"(?m)^##\s*§\d+\b",
        body[section_start:],
    )
    if next_section is None:
        return body[section_start:]
    return body[section_start : section_start + next_section.start()]


def check_acs_verified(
    repo_root: Path,
    version: str,
    *,
    plan_doc: Path | None = None,
) -> GateResult:
    """Verify the plan-doc's §status / §verdict-matrix marks each AC
    declared in §4 GREEN.

    Per AC.SDPD.2 (v0.8.2): when *plan_doc* is provided, the gate
    reads the named plan-doc directly instead of inferring the path
    from the version-slug glob. On missing-explicit-path the corrective
    hint names the path + the ``--plan-doc`` flag.

    Per AC.READYP.1 (v0.7.2 fix): the AC-ID scan is restricted to
    the plan-doc's ``## §4 — Acceptance criteria`` section body
    (between the §4 heading and the next ``## §<n>`` boundary).
    AC IDs appearing in any other section (§1 prime-objective ladder,
    §6 out-of-scope, §8 dependencies, §11 authority chain, §13
    §status, etc.) are NOT treated as in-scope ACs requiring
    §status verdicts. This fixes the v0.7.1 publish-time defect
    where cross-reference AC IDs in §6 + §8 were flagged as missing-
    from-§status.

    A plan-doc passes the gate when the §status / §13 section names
    each §4-declared AC ID alongside a recognised non-failure verdict
    (within 240 chars on the same logical span — accommodates table
    rows + prose verdicts). Two non-failure verdicts are recognised:

      - ``GREEN`` — the v0.6.0 default; the AC shipped as planned.
      - ``REMOVED`` — added in v0.8.3 per AC.RVG.1. The AC was
        legitimately struck at build-time per ODD §4 re-extension
        (`feedback_locked_design_not_license_for_bad_outcomes`).
        Plan-doc author + reviewer enforce the discipline that the
        REMOVED row also names the build-time decision that struck
        the AC (e.g., `D-<plan-id>.<n>`); the gate verifies only the
        verdict token, not the justification (D-RVG.2.b).

    Missing-verdict (no GREEN AND no REMOVED token within 240 chars
    of the AC ID in §status) still returns RED — the REMOVED extension
    is narrowly defined and doesn't open the gate to silently-skipped
    ACs.

    For the dogfood self-publish (this very plan-doc), the §status
    backfill is appended at end-of-build; the gate runs against the
    backfilled doc.
    """
    resolved_plan_doc = _find_plan_doc(
        repo_root, version, plan_doc=plan_doc
    )
    if resolved_plan_doc is None:
        if plan_doc is not None:
            # AC.SDPD.2 RED-with-hint: name the explicit path the
            # caller asked for + the --plan-doc flag's role.
            return GateResult(
                name="acs-verified",
                ok=False,
                message=(
                    f"plan-doc not found at {plan_doc} (resolved via "
                    f"`--plan-doc` flag). Verify the path exists relative "
                    f"to the repo root; re-run with a corrected "
                    f"`--plan-doc` argument."
                ),
            )
        return GateResult(
            name="acs-verified",
            ok=False,
            message=(
                f"no plan-doc found at docs/plans/{_version_to_slug(version)}-*.md "
                f"or {_version_to_slug(version)}.md. Plan-before-code per "
                f"`feedback_plan_before_code` requires the plan-doc as the "
                f"AC source-of-truth; author it, backfill §status with each "
                f"AC verdict, then re-run. Alternatively, pass "
                f"`--plan-doc <path>` for a scope-descriptive plan-doc "
                f"that doesn't follow the version-slug glob convention."
            ),
        )
    body = resolved_plan_doc.read_text(encoding="utf-8")
    # Per AC.READYP.1 (v0.7.2): scope the AC-ID scan to §4 only.
    # Cross-references in §6 / §8 / §11 / §13 are NOT in-scope ACs.
    section_4 = _extract_section_4_body(body)
    plan_doc_display = _display_path(resolved_plan_doc, repo_root)
    if section_4 is None:
        return GateResult(
            name="acs-verified",
            ok=False,
            message=(
                f"plan-doc at {plan_doc_display} has no "
                f"`## §4 — Acceptance criteria` heading; the `acs-verified` "
                f"gate scopes the AC-ID scan to §4 per the plan-doc "
                f"convention. Add the heading + author the in-scope ACs "
                f"there; re-run."
            ),
        )
    # Per AC.READYP.1 (v0.7.2): in-scope ACs are those declared as
    # `### AC.<...>` headings (the canonical ODD shape — verified at
    # 519 instances across the plan-doc corpus). AC IDs appearing only
    # in §4 *prose* (e.g., AC.READYP.2's description naming the
    # AC.NTU.6 + AC.V060.7 cross-references it reverts) are NOT
    # in-scope; only heading-form declarations are.
    #
    # Heading shapes accepted (verified across the corpus):
    #   - `### AC.<scope>.<id>` (canonical; 519 instances)
    #   - `#### AC.<scope>.<id>` (sub-heading; v0.2.3 + ABC family)
    #   - `## AC.<scope>.<id>` (rare; allowed for completeness)
    ac_id_re = re.compile(
        r"^#{2,4}\s+(AC\.[A-Z][A-Z0-9_-]*\.[A-Za-z0-9_-]+)\b",
        re.MULTILINE,
    )
    ac_ids = sorted(set(ac_id_re.findall(section_4)))
    if not ac_ids:
        return GateResult(
            name="acs-verified",
            ok=False,
            message=(
                f"plan-doc at {plan_doc_display} declares no "
                f"AC IDs in §4 (looked for `### AC.<scope>.<n>` heading "
                f"declarations). Verify the doc is the right shape (§4 "
                f"Acceptance criteria block per ODD §2.5)."
            ),
        )
    # Locate the §status / §13 section (the post-build backfill block).
    status_match = re.search(
        r"(?ms)^##\s*§(?:13|status)\b.*?(?=^##\s|\Z)",
        body,
    )
    status_body = status_match.group(0) if status_match else ""
    missing: list[str] = []
    for ac in ac_ids:
        # An AC counts as verified when the status section names it
        # alongside a recognised non-failure verdict on the same
        # logical span (within 240 chars — accommodates table rows +
        # prose verdicts). Two verdicts are recognised:
        #   - GREEN (the v0.6.0 default; the AC shipped as planned).
        #   - REMOVED (per AC.RVG.1; the AC was struck mid-build via
        #     ODD §4 re-extension; plan-doc author + reviewer enforce
        #     that the REMOVED row also names the build-time decision
        #     that struck the AC).
        if not status_body:
            missing.append(ac)
            continue
        # Per D-RVG.1.a: try GREEN first (the most common case);
        # fall through to REMOVED if GREEN doesn't match. Per
        # D-RVG.2.a, only these two pass tokens are recognised —
        # missing-verdict (no GREEN AND no REMOVED) still RED.
        green_pattern = re.compile(
            re.escape(ac) + r".{0,240}?GREEN", re.DOTALL
        )
        if green_pattern.search(status_body):
            continue
        removed_pattern = re.compile(
            re.escape(ac) + r".{0,240}?REMOVED", re.DOTALL
        )
        if removed_pattern.search(status_body):
            continue
        missing.append(ac)
    if missing:
        return GateResult(
            name="acs-verified",
            ok=False,
            message=(
                f"plan-doc {plan_doc_display} §status does "
                f"not mark these ACs GREEN: {', '.join(missing)}. Backfill "
                f"§status (or §13) with the verdict matrix; each AC must "
                f"appear with a GREEN marker (or REMOVED if struck "
                f"build-time per ODD §4 re-extension). Re-run once "
                f"backfilled."
            ),
        )
    return GateResult(
        name="acs-verified",
        ok=True,
        message=(
            f"all {len(ac_ids)} AC(s) verified (GREEN or REMOVED) in "
            f"{plan_doc_display} §status"
        ),
    )


# --------------------------------------------------------------------
# Gate 3 — STATE.md SHIPPED (AC.V060.2 #3)
# --------------------------------------------------------------------


def check_state_shipped(repo_root: Path, version: str) -> GateResult:
    """Verify ``docs/STATE.md`` mentions the version followed by
    ``SHIPPED``.

    Pattern matches existing STATE.md rollup phrasing — entries take
    the shape ``v0.4.3 SHIPPED 2026-05-09`` / ``v0.5.0 SHIPPED LOCAL``
    / similar. The gate accepts any ``<version> ... SHIPPED`` proximity
    (within 120 chars to allow ``SHIPPED LOCAL`` vs ``SHIPPED PUBLIC``
    qualifiers).
    """
    path = repo_root / "docs" / "STATE.md"
    if not path.exists():
        return GateResult(
            name="state-shipped",
            ok=False,
            message=(
                f"missing {path.relative_to(repo_root)}; canonical "
                f"shipped-state record. Author or restore."
            ),
        )
    body = path.read_text(encoding="utf-8")
    pattern = re.compile(
        re.escape(version) + r"\b.{0,120}?SHIPPED", re.DOTALL
    )
    if not pattern.search(body):
        return GateResult(
            name="state-shipped",
            ok=False,
            message=(
                f"docs/STATE.md does not mark {version} as SHIPPED. Append "
                f"the version's rollup to STATE.md (objective sentence + "
                f"seal SHA + cycle anchors) so future operators find it. "
                f"Re-run once the rollup line is present."
            ),
        )
    return GateResult(
        name="state-shipped",
        ok=True,
        message=f"{version} marked SHIPPED in docs/STATE.md",
    )


# --------------------------------------------------------------------
# Gate 4 — clean tree (AC.V060.2 #4)
# --------------------------------------------------------------------


def check_clean_tree(repo_root: Path, version: str) -> GateResult:
    """Verify ``git status --porcelain`` returns empty at *repo_root*.

    Defensive against half-committed work landing in a publish window.
    """
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    out = proc.stdout.strip()
    if out:
        return GateResult(
            name="clean-tree",
            ok=False,
            message=(
                "uncommitted changes in canonical tree:\n"
                + "\n".join(f"  {line}" for line in out.splitlines())
                + "\nCommit, stash, or revert; re-run."
            ),
        )
    return GateResult(
        name="clean-tree",
        ok=True,
        message="working tree clean",
    )


# --------------------------------------------------------------------
# Gate 5 — branch == main (AC.V060.2 #5)
# --------------------------------------------------------------------


_EXPECTED_BRANCH = "main"


def check_branch_main(repo_root: Path, version: str) -> GateResult:
    """Verify ``git branch --show-current`` returns ``main``.

    The split-worktrees move (2026-05-09) retired the prior
    ``pos-v2`` branch name; canonical post-split is ``main``.
    """
    proc = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    branch = proc.stdout.strip()
    if branch != _EXPECTED_BRANCH:
        return GateResult(
            name="branch-main",
            ok=False,
            message=(
                f"current branch is {branch!r}, expected {_EXPECTED_BRANCH!r}. "
                f"Publish flows from {_EXPECTED_BRANCH} only (the split-"
                f"worktrees move retired the pos-v2 branch). Switch with "
                f"`git switch {_EXPECTED_BRANCH}`; re-run."
            ),
        )
    return GateResult(
        name="branch-main",
        ok=True,
        message=f"on branch {_EXPECTED_BRANCH}",
    )


# --------------------------------------------------------------------
# Gate 6 — seal commit reachable (AC.V060.2 #6)
# --------------------------------------------------------------------


def _extract_seal_sha(roadmap_body: str, version: str) -> str | None:
    """Pull the seal SHA from the §2-shipped table row for *version*.

    §2 rows take the shape::

        | v0.4.3 | <objective sentence> | Single-cycle PATCH: ...
          seal `7bff3817`; ... |

    The seal is a 7+ hex-char token following ``seal``. Prefer the
    last seal in the row when multiple exist (the most-recent
    cycle's seal anchors the version's HEAD).
    """
    # Find the row whose first cell starts with the version.
    row_pattern = re.compile(
        r"^\|\s*" + re.escape(version) + r"\s*\|.*$",
        re.MULTILINE,
    )
    match = row_pattern.search(roadmap_body)
    if match is None:
        return None
    row = match.group(0)
    # All seal tokens in the row.
    seals = re.findall(r"seal[s]?\s*[`']?([0-9a-f]{7,40})", row)
    if not seals:
        return None
    return seals[-1]


def check_seal_commit_reachable(
    repo_root: Path, version: str
) -> GateResult:
    """Verify ``docs/release-roadmap.md`` §2 row carries a seal SHA
    for *version* + that SHA is reachable from HEAD.

    Reachability means ``git merge-base --is-ancestor <seal> HEAD``
    succeeds (rc=0). On RED, surface the seal SHA + the commit it
    anchors so the operator can resolve.
    """
    path = repo_root / "docs" / "release-roadmap.md"
    if not path.exists():
        return GateResult(
            name="seal-reachable",
            ok=False,
            message=(
                f"missing {path.relative_to(repo_root)}; canonical "
                f"forward-looking roadmap. Restore."
            ),
        )
    body = path.read_text(encoding="utf-8")
    seal = _extract_seal_sha(body, version)
    if seal is None:
        return GateResult(
            name="seal-reachable",
            ok=False,
            message=(
                f"docs/release-roadmap.md §2 row for {version} carries no "
                f"seal SHA. Append the seal anchor to the row (cycle SHA "
                f"after `seal `) and re-run."
            ),
        )
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", seal, "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return GateResult(
            name="seal-reachable",
            ok=False,
            message=(
                f"seal commit {seal} declared for {version} in "
                f"docs/release-roadmap.md is NOT reachable from HEAD. "
                f"Either checkout the branch containing the seal, or "
                f"correct the roadmap row to point at the actual seal "
                f"SHA on HEAD's history."
            ),
        )
    return GateResult(
        name="seal-reachable",
        ok=True,
        message=f"seal {seal} reachable from HEAD",
    )


# --------------------------------------------------------------------
# Gate 7 — declared user-state migration present (AC.MIG-GATE.*)
# --------------------------------------------------------------------


def _migration_matches_version(
    migrations_dir: Path,
    version: str,
    *,
    plan_doc: Path | None = None,
) -> Path | None:
    """Locate the declared migration file for *version* in *migrations_dir*.

    Two resolution paths, mirroring how ``check_acs_verified`` /
    ``check_hard_smoke`` resolve plan-docs:

    1. **Release-version stamp (D1):** a ``*.migration.yaml`` whose body
       declares ``version: <version>`` (the stamp the release-gate writes at
       release time). This is the primary key once a migration is released.
    2. **Scope-descriptive plan-doc slug (dogfood / pre-release):** when
       *plan_doc* is provided, the migration file whose slug stem matches the
       plan-doc stem (``<slug>.migration.yaml`` vs ``<slug>.md`` /
       ``<slug>-slice-plan.md``). This supports versions whose plan-doc is
       scope-descriptive rather than version-named
       (``feedback_version_numbers_at_release_time``).

    Returns the matched file path, or ``None`` when no declared migration
    matches.
    """
    if not migrations_dir.is_dir():
        return None
    files = sorted(migrations_dir.glob("*.migration.yaml"))

    # Path 1 — release-version stamp.
    version_re = re.compile(
        r"(?m)^\s*version\s*:\s*['\"]?" + re.escape(version) + r"['\"]?\s*$"
    )
    for f in files:
        if version_re.search(f.read_text(encoding="utf-8")):
            return f

    # Path 2 — scope-descriptive plan-doc slug match.
    if plan_doc is not None:
        stem = plan_doc.stem
        # Strip the conventional plan-doc tail so a `<slug>-slice-plan` doc
        # resolves to `<slug>.migration.yaml` / `<slug>-slice.migration.yaml`.
        candidates = {
            stem,
            stem.removesuffix("-plan"),
            stem.removesuffix("-slice-plan"),
            stem.removesuffix("-slice-plan") + "-slice",
        }
        for f in files:
            mig_stem = f.name.removesuffix(".migration.yaml")
            if mig_stem in candidates:
                return f

    return None


def check_migration_declared(
    repo_root: Path,
    version: str,
    *,
    plan_doc: Path | None = None,
) -> GateResult:
    """Verify the version declares a user-state migration (AC.MIG-GATE.*).

    HARD-BLOCK, no override (D3): a version that declares no migration file in
    ``docs/state-migrations/`` returns RED and publish cannot proceed. A
    declared ``operation: no-op`` migration PASSES (AC.MIG-GATE.2) -- the gate
    forces a DECLARATION + a moment's thought, not a non-trivial migration;
    declaring a no-op is the ~30-second valid answer, so the gate never blocks
    legitimate work.

    Runs in the SAME ``loam release`` gate pass as the other gates
    (AC.MIG-GATE.3) -- one report, no parallel CI.
    """
    migrations_dir = repo_root / "docs" / "state-migrations"
    matched = _migration_matches_version(
        migrations_dir, version, plan_doc=plan_doc
    )
    if matched is None:
        hint_path = (
            f"docs/state-migrations/<slug>.migration.yaml declaring "
            f"`version: {version}`"
        )
        if plan_doc is not None:
            hint_path += (
                f" (or a slug matching the plan-doc stem "
                f"`{plan_doc.stem}`)"
            )
        return GateResult(
            name="migration-declared",
            ok=False,
            message=(
                f"{version} declares NO user-state migration. Every release "
                f"must declare what it changes in a user's .loam/ state so "
                f"the migration engine can carry that state forward (the "
                f"load-bearing release-gate, P1.3). Author {hint_path}; a "
                f"code-only release declares `operation: no-op` (a valid "
                f"~30-second declaration). Re-run once present."
            ),
        )
    return GateResult(
        name="migration-declared",
        ok=True,
        message=(
            f"{version} declares a user-state migration at "
            f"{matched.relative_to(repo_root)}"
        ),
    )


# --------------------------------------------------------------------
# Gate 8 — substrate audit: no shipping status claim diverges from the
#          ground-truth-derived STATE-OF-LOAM record (AC.SOL-GATE.*)
# --------------------------------------------------------------------


# The canonical status docs the release-gate audits for divergence. A
# release that ships a stale "dark"-for-live status claim in one of
# these is the exact failure N2 prevents. Bounded set (D4 = structured
# status fields only; NOT free-prose scanning).
_AUDITED_STATUS_DOCS = (
    "docs/STATE.md",
    "docs/release-roadmap.md",
)


def check_substrate_audit(
    repo_root: Path,
    version: str,
    *,
    audited_docs: tuple[str, ...] | None = None,
    settings_path: Path | None = None,
) -> GateResult:
    """Verify no shipping doc carries a structured status claim that
    DIVERGES from the STATE-OF-LOAM record derived fresh from ground
    truth (AC.SOL-GATE.{1,3}).

    HARD-BLOCK (D3): a divergence returns RED and publish cannot
    proceed until the stale claim is corrected — mirroring the six
    structural siblings. Agreement passes clean (AC.SOL-GATE.2 — low
    false-positive). Composes on the SAME comparator the ``loam audit``
    verb uses (AC.SOL-GATE.3 — one mechanism, two entry points; no
    parallel CI).

    Fail-safe (plan principle): the audit must NEVER crash the release
    path. Any error generating the record or reading a doc degrades to a
    clear GREEN-with-caveat ("could not determine"), never a false RED
    that would block a legitimate publish on the audit's own failure.
    Indeterminate ground truth (an UNKNOWN derived class) yields no
    divergence by construction in the comparator.
    """
    docs = audited_docs if audited_docs is not None else _AUDITED_STATUS_DOCS
    try:
        # Local import: the audit package is a sibling subcommand; keep
        # the dependency at call time so the release gates load even if
        # the audit module is mid-refactor.
        from loam_cli.audit.comparator import (
            compare_claims,
            extract_claims_from_doc,
        )
        from loam_cli.audit.loam_state import default_state_record

        record = default_state_record(
            repo_root, settings_path=settings_path
        )
    except Exception as exc:  # pragma: no cover — fail-safe path
        return GateResult(
            name="substrate-audit",
            ok=True,
            message=(
                f"substrate audit could not derive the STATE-OF-LOAM "
                f"record ({type(exc).__name__}: {exc}); degraded to "
                f"pass-with-caveat (fail-safe — the audit never blocks a "
                f"publish on its own failure). Run `loam audit` manually "
                f"to investigate."
            ),
        )

    covered = frozenset(r.name for r in record.components)
    divergences = []
    for rel in docs:
        path = repo_root / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:  # pragma: no cover — fail-safe path
            continue
        claims = extract_claims_from_doc(
            text, source=rel, components=covered
        )
        divergences.extend(compare_claims(claims, record))

    if divergences:
        lines = "\n".join(
            f"    {d.source}: {d.detail}" for d in divergences
        )
        return GateResult(
            name="substrate-audit",
            ok=False,
            message=(
                f"{len(divergences)} doc status claim(s) DIVERGE from the "
                f"ground-truth STATE-OF-LOAM record:\n{lines}\n  A shipping "
                f"doc claims a status that contradicts ground truth (refs + "
                f"live config + real probe). Correct the stale claim(s); "
                f"re-run `loam release {version}` once the audit is clean. "
                f"(`loam audit --doc <path>` reproduces the finding.)"
            ),
        )
    return GateResult(
        name="substrate-audit",
        ok=True,
        message=(
            "no shipping status claim diverges from the derived "
            "STATE-OF-LOAM record (ground truth agrees)"
        ),
    )


# --------------------------------------------------------------------
# Aggregation
# --------------------------------------------------------------------


ALL_GATES = (
    check_hard_smoke,
    check_acs_verified,
    check_state_shipped,
    check_clean_tree,
    check_branch_main,
    check_seal_commit_reachable,
    check_migration_declared,
    check_substrate_audit,
)


def run_all(
    repo_root: Path,
    version: str,
    *,
    plan_doc: Path | None = None,
) -> list[GateResult]:
    """Run every gate; return the verdict list in declaration order.

    Does NOT short-circuit on first RED — the operator sees every
    failure in one pass.

    Per AC.SDPD.{2,3} (v0.8.2): when *plan_doc* is provided, it is
    forwarded to ``check_hard_smoke`` and ``check_acs_verified``
    (the two gates whose path inference uses the version slug). The
    other four gates ignore the parameter — they read fixed paths
    (``docs/STATE.md``, ``docs/release-roadmap.md``) or invoke
    ``git`` directly. Per D-SDPD.6 the ``ALL_GATES`` tuple keeps its
    uniform ``(repo_root, version)`` signature for backward-compat;
    the per-gate calls below thread the new parameter explicitly.
    """
    return [
        check_hard_smoke(repo_root, version, plan_doc=plan_doc),
        check_acs_verified(repo_root, version, plan_doc=plan_doc),
        check_state_shipped(repo_root, version),
        check_clean_tree(repo_root, version),
        check_branch_main(repo_root, version),
        check_seal_commit_reachable(repo_root, version),
        check_migration_declared(repo_root, version, plan_doc=plan_doc),
        check_substrate_audit(repo_root, version),
    ]


def format_report(results: list[GateResult]) -> str:
    """Pretty-print a list of GateResults for terminal display."""
    lines: list[str] = []
    for r in results:
        marker = "GREEN" if r.ok else "RED"
        lines.append(f"  [{marker}] {r.name}: {r.message}")
    return "\n".join(lines)

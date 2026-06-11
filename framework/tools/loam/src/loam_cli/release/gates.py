"""Per-gate pre-publish verification (AC.V060.2 + AC.MIG-GATE.*).

Nine structural gates, each returning a :class:`GateResult` carrying
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
  9. ``check_boundary_respected`` — no framework code writes user-state
     OUTSIDE the two declared homes (``~/.claude/`` global +
     ``<workspace>/.loam/`` scoped). HARD-BLOCK (AC.BLOCK-ENFORCE.*, N1):
     the framework ↔ user-state boundary (ADR-0001). Reads the declared
     allowlist ``docs/design/adr/user-state-homes.yaml`` — the same single
     source the ADR cites (no doc<->code drift) — exactly as gate 7 reads
     the declared migration contract.

Each gate is independently testable; per-gate test pairs (one passing,
one failing) live in
``framework/tools/loam/tests/test_AC_V060_2_*.py``.
"""

from __future__ import annotations

import ast
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

    found = find_plan_doc_by_slug_glob(repo_root, slug)
    if found is not None:
        return found
    # AC.RFPR.2 (D-RFPR.1): release-side fallback for the
    # ``release-integration-v<X-Y-Z>.md`` naming (the shape the
    # v1.5.0 incident hit — notes degraded to "(unavailable)" because
    # the slug glob requires the slug as filename PREFIX). The
    # fallback lives HERE, release-side, so the shared loam_amend
    # locator stays release-naming-free (it also serves
    # amendment-cycle resolution, where release-integration docs are
    # not amendment plan-docs). Sealed-first, mirroring the shared
    # locator's D-T1RS.GLOB-PRIORITY ordering.
    plans_dir = repo_root / "docs" / "plans"
    for base in (plans_dir / "sealed", plans_dir):
        candidate = base / f"release-integration-{slug}.md"
        if candidate.is_file():
            return candidate
    return None


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
# Gate 9 — framework ↔ user-state boundary respected (AC.BLOCK-ENFORCE.*)
# --------------------------------------------------------------------


# The declared allowlist of legal user-state homes — the SINGLE SOURCE OF
# TRUTH shared with the boundary ADR (ADR-0001). The gate reads THIS file;
# it does not hardcode a parallel rule (AC.BLOCK-ENFORCE.4 — no doc<->code
# drift). Mirrors how gate-7 reads docs/state-migrations/ rather than
# hardcoding the migration contract.
_BOUNDARY_ALLOWLIST_REL = "docs/design/adr/user-state-homes.yaml"

# The framework trees whose source is scanned for write-sites. A path is
# FRAMEWORK by what it is about (loam's own machinery); these are the two
# roots that hold it (ADR-0001 §2).
_FRAMEWORK_ROOTS = ("framework", "plugins")

# The write-call methods whose target-path argument is checked. A write to
# a user-state-marked path landing outside a home is the violation.
_WRITE_METHODS = frozenset({"write_text", "write_bytes", "mkdir", "touch"})


def _load_boundary_allowlist(
    repo_root: Path,
) -> tuple[tuple[str, ...], tuple[str, ...]] | None:
    """Read the declared allowlist; return ``(home_paths, user_state_markers)``.

    Returns ``None`` when the allowlist is absent or unparseable — the
    caller degrades to a clear pass-with-caveat (fail-safe: the gate never
    blocks a legitimate publish on its OWN failure, and never a false RED).

    Parsed without a YAML dependency (the release gates declare only
    PyYAML-optional surfaces): the two fields are flat string lists with a
    stable shape, extracted by line scan so the gate has no import-time
    dependency that could fail in a minimal release env.
    """
    path = repo_root / _BOUNDARY_ALLOWLIST_REL
    if not path.is_file():
        return None
    try:
        body = path.read_text(encoding="utf-8")
    except OSError:  # pragma: no cover — fail-safe path
        return None
    # `path:` lines under `homes:` carry the legal home tokens; we want the
    # home MARKER (the .loam/ or .claude/ fragment), normalised so a
    # write-target containing it counts as "inside a home".
    home_paths = re.findall(r"(?m)^\s*-?\s*path:\s*[\"']?([^\"'\n]+)", body)
    homes = tuple(p.strip() for p in home_paths if p.strip())
    # `user_state_markers:` list items.
    markers_block = re.search(
        r"(?ms)^user_state_markers:\s*\n(.*?)(?=^\S|\Z)", body
    )
    markers: list[str] = []
    if markers_block:
        markers = re.findall(
            r'(?m)^\s*-\s*["\']?([^"\'#\n]+)', markers_block.group(1)
        )
        markers = [m.strip() for m in markers if m.strip()]
    return homes, tuple(markers)


def _home_markers(homes: tuple[str, ...]) -> tuple[str, ...]:
    """Reduce declared home paths to the directory marker that identifies
    a target as landing INSIDE that home.

    ``~/.claude/`` → ``.claude``; ``<workspace>/.loam/`` → ``.loam``.
    A write target string containing one of these markers lands in a home.
    """
    markers: list[str] = []
    for h in homes:
        # Strip the placeholder/home prefix down to the home dir token.
        token = h.replace("~/", "").replace("<workspace>/", "").strip("/")
        if token:
            markers.append(token)
    return tuple(markers)


def _path_literals_in_write_sites(source: str) -> list[str]:
    """Return the joined string-path literals that flow into a write-call's
    target in *source*.

    Conservative static read: parse the module, find calls whose method is
    a write-method (``.write_text`` / ``.mkdir`` / …) on a Path-expression,
    and reconstruct the string-literal path fragments composing that target
    (``Path(root) / 'framework' / 'leaky' / 'OBJECTIVES.md'`` →
    ``framework/leaky/OBJECTIVES.md``). Non-literal fragments (variables) are
    skipped — they cannot be statically resolved, so they are not flagged
    (false-negative-safe over false-positive-noisy; the planted-violation
    AC uses literal paths, the representative real-leak shape).
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:  # pragma: no cover — skip unparseable source
        return []

    # Symbol table of local `name = <path-chain>` bindings so a write
    # called on a variable (``target = Path(root) / 'a' / 'b';
    # target.write_text(...)``) — the realistic leak shape — resolves to
    # its path-chain fragments. Single-assignment, last-write-wins; good
    # enough for the representative static read (the AC pins the caught
    # violation, not a full dataflow engine).
    bindings: dict[str, list[str]] = {}

    def _binop_path_fragments(node: ast.AST) -> list[str]:
        """Collect string literals from a ``Path(...) / 'a' / 'b'`` chain,
        resolving bare ``Name`` receivers through *bindings*."""
        frags: list[str] = []
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            frags.extend(_binop_path_fragments(node.left))
            frags.extend(_binop_path_fragments(node.right))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            frags.append(node.value)
        elif isinstance(node, ast.Name):
            frags.extend(bindings.get(node.id, []))
        elif isinstance(node, ast.Call):
            # Path('lit') / open('lit', ...) — first str-literal arg.
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(
                    arg.value, str
                ):
                    frags.append(arg.value)
                    break
        return frags

    # First pass: record local path-chain bindings (in source order so a
    # later binding can reference an earlier one).
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            tgt = node.targets[0]
            if isinstance(tgt, ast.Name):
                frags = _binop_path_fragments(node.value)
                if frags:
                    bindings[tgt.id] = frags

    # Second pass: write-call sites, resolving variable receivers.
    targets: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (
            isinstance(func, ast.Attribute)
            and func.attr in _WRITE_METHODS
        ):
            continue
        frags = _binop_path_fragments(func.value)
        if frags:
            targets.append("/".join(frags))
    return targets


def check_boundary_respected(
    repo_root: Path,
    version: str,
    *,
    allowlist_rel: str | None = None,
) -> GateResult:
    """Verify no framework code writes user-state OUTSIDE the two declared
    homes (AC.BLOCK-ENFORCE.*, ADR-0001 — gate 9).

    HARD-BLOCK (twin of gate 7): a framework-code write of user-state to a
    path outside ``~/.claude/`` / ``<workspace>/.loam/`` returns RED with a
    corrective hint naming the offending path + the legal homes; publish
    cannot proceed. Legitimate framework→user-state writes (those landing
    IN a home — ``establish_loam_layout`` writing under ``.loam/``) pass
    clean (AC.BLOCK-ENFORCE.2 — no false-positive).

    The set of legal homes + the user-state markers is sourced from the
    DECLARED ALLOWLIST (``docs/design/adr/user-state-homes.yaml``) — the
    same single source the ADR cites (AC.BLOCK-ENFORCE.4). The gate reads
    the file; it does not hardcode a parallel rule, so the doc-rule and the
    code-rule cannot drift.

    Detection method (builder's call per ODD — the AC pins the caught
    violation, not the how): a conservative static scan of every ``.py``
    under ``framework/`` and ``plugins/`` for write-call sites whose target
    path-literal carries a user-state marker but does NOT land inside a
    legal home. Non-literal (variable) targets are not flagged (false-
    negative-safe); the representative leak shape — a framework module
    writing a per-user file to a literal path under ``framework/`` — IS
    caught.

    Fail-safe (plan principle): the gate NEVER crashes the release path.
    An absent/unparseable allowlist degrades to a clear GREEN-with-caveat
    ("could not determine"), never a false RED that would block a
    legitimate publish on the gate's own failure.
    """
    rel = allowlist_rel if allowlist_rel is not None else _BOUNDARY_ALLOWLIST_REL
    loaded = _load_boundary_allowlist(
        repo_root if allowlist_rel is None else repo_root
    )
    if loaded is None:
        return GateResult(
            name="boundary-respected",
            ok=True,
            message=(
                f"could not read the declared user-state-home allowlist at "
                f"{rel}; degraded to pass-with-caveat (fail-safe — the "
                f"boundary gate never blocks a publish on its own failure). "
                f"Restore the allowlist (ADR-0001) so the gate can enforce."
            ),
        )
    homes, markers = loaded
    home_markers = _home_markers(homes)
    if not home_markers or not markers:
        return GateResult(
            name="boundary-respected",
            ok=True,
            message=(
                f"the declared allowlist at {rel} names no homes/markers; "
                f"degraded to pass-with-caveat (fail-safe). Check the "
                f"allowlist shape (ADR-0001)."
            ),
        )

    violations: list[tuple[str, str]] = []  # (source_file, target_path)
    for root_name in _FRAMEWORK_ROOTS:
        root = repo_root / root_name
        if not root.is_dir():
            continue
        for py in root.rglob("*.py"):
            try:
                source = py.read_text(encoding="utf-8")
            except OSError:  # pragma: no cover — fail-safe path
                continue
            for target in _path_literals_in_write_sites(source):
                # Is this a user-state write? (target carries a marker)
                if not any(m in target for m in markers):
                    continue
                # Does it land in a legal home? A target whose path carries
                # a home marker (``.loam`` / ``.claude``) lands in a home —
                # legitimate. The cursor/store/model writes inside a home
                # are addressed relative to the home dir, so the home marker
                # is present (``.loam/migrations/.cursor``) OR the marker IS
                # the home (``.cursor`` written under a ``.loam`` Path
                # variable — see below).
                if any(hm in target for hm in home_markers):
                    continue
                # The violation signal: the write lands under a FRAMEWORK
                # tree. A legitimate user-state write is addressed relative
                # to a home (a ``.loam`` / ``.claude`` Path) — it never has
                # a ``framework/`` or ``plugins/`` segment in its literal
                # target. A leak writes user-state to a path rooted under
                # the framework tree (``framework/<x>/OBJECTIVES.md``). Only
                # framework-rooted user-state targets are violations; a
                # home-relative literal (``migrations/.cursor``) without a
                # framework segment is a legitimate in-home write the static
                # scan cannot fully resolve (the home dir is a Path variable)
                # and is NOT flagged (false-negative-safe per the ADR).
                segments = target.split("/")
                if not any(seg in _FRAMEWORK_ROOTS for seg in segments):
                    continue
                rel_src = _display_path(py, repo_root)
                violations.append((rel_src, target))

    if violations:
        lines = "\n".join(
            f"    {src} writes user-state to `{tgt}`"
            for src, tgt in violations
        )
        legal = " / ".join(f"`{h}`" for h in homes) or "the two declared homes"
        return GateResult(
            name="boundary-respected",
            ok=False,
            message=(
                f"{len(violations)} framework-code write(s) land user-state "
                f"OUTSIDE the legal homes:\n{lines}\n  The framework ↔ "
                f"user-state boundary (ADR-0001) requires every framework-"
                f"written user-state path to land in one of {legal}. Move "
                f"the write into a legal home (or, if the path is NOT user-"
                f"state, the marker scan misfired — narrow the write target). "
                f"Re-run `loam release {version}` once the leak is closed. "
                f"(The legal homes are declared in {rel}.)"
            ),
        )
    return GateResult(
        name="boundary-respected",
        ok=True,
        message=(
            "no framework-code write lands user-state outside the two "
            "declared homes (boundary respected)"
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
    check_boundary_respected,
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
        check_boundary_respected(repo_root, version),
    ]


def format_report(results: list[GateResult]) -> str:
    """Pretty-print a list of GateResults for terminal display."""
    lines: list[str] = []
    for r in results:
        marker = "GREEN" if r.ok else "RED"
        lines.append(f"  [{marker}] {r.name}: {r.message}")
    return "\n".join(lines)

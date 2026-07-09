"""Auto-generate GitHub Release notes (AC.V060.4).

Per D-V060.4 default, notes assemble from three sources:

1. **Plan-doc §1 outcome shape** — the "why" sentence + supporting
   prose (up to the next ``## §`` heading).
2. **Plan-doc §13 / §status** — the per-AC verdict matrix.
3. **Commit log** — ``git log --oneline <prev-seal>..<this-seal>``,
   filtered to feat/fix/docs/chore prefixes when the raw log is
   noisy (per D-V060.4 fallback rule).

The function returns a single string ready to feed to
``gh release create --notes <markdown>``. Invocation is mocked in
tests; the live invocation lives in :mod:`loam_cli.release.runner`.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from loam_cli.release import gates
from loam_cli.release.gates import _find_plan_doc


_NOISY_PREFIX_PATTERN = re.compile(
    r"^([0-9a-f]{7,40})\s+"
    r"(?:chore\(amend\):|chore\(seals\):|chore\(rebrand\):)"
)


def _extract_section(body: str, section_marker: str) -> str | None:
    """Return the body of the ``## §<marker>`` section (without the
    heading itself) up to the next ``## §`` heading or EOF.

    ``section_marker`` is the post-``§`` token — ``"1"`` for §1,
    ``"status"`` for §status, etc.
    """
    pattern = re.compile(
        r"(?ms)^##\s*§"
        + re.escape(section_marker)
        + r"\b[^\n]*\n(.*?)(?=^##\s|\Z)",
    )
    m = pattern.search(body)
    if m is None:
        return None
    return m.group(1).strip()


def _previous_seal(
    repo_root: Path, roadmap_body: str, version: str
) -> str | None:
    """Find the tag target (dominating seal) for the version *immediately
    preceding* *version* in §2's shipped table — the lower bound of the
    ``git log <prev>..<this>`` commit range in the notes.

    Walks the table top-to-bottom; the row matching *version* is the
    target; the previous row's tag target is resolved via the DOMINATING
    seal resolver (AC.DOM.6 — no last-in-row text-parse straggler). When *version*
    is the first row (no predecessor), returns ``None`` and the notes
    omit the commit-log section.
    """
    # Parse all rows of the shipped table. Each row starts with
    # ``| v0.X.Y |`` so the first capture is the version.
    row_pattern = re.compile(
        r"^\|\s*(v[0-9][0-9.]*)\s*\|.*$",
        re.MULTILINE,
    )
    versions = [m.group(1) for m in row_pattern.finditer(roadmap_body)]
    for idx, v in enumerate(versions):
        if v == version and idx > 0:
            return gates.resolve_tag_target(
                repo_root, roadmap_body, versions[idx - 1]
            ).sha
    return None


def _commit_log(
    repo_root: Path, prev_seal: str | None, this_seal: str
) -> list[str]:
    """Return ``git log --oneline <prev-seal>..<this-seal>`` lines.

    When *prev_seal* is ``None``, the range becomes ``<this-seal>``
    alone (which yields the full history; rare — only happens for the
    very first version's notes).
    """
    range_spec = (
        f"{prev_seal}..{this_seal}" if prev_seal else this_seal
    )
    proc = subprocess.run(
        ["git", "log", "--oneline", "--no-decorate", range_spec],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        # Non-fatal — surface a placeholder line; the rest of the
        # notes still render.
        return [f"(commit log unavailable: {proc.stderr.strip()})"]
    return [line for line in proc.stdout.splitlines() if line.strip()]


def _filter_noise(lines: list[str]) -> list[str]:
    """Per D-V060.4 fallback: filter out chore(amend) / chore(seals) /
    chore(rebrand) prefixes when the raw log is noisy.

    Threshold: when noise lines exceed half of the log, drop them;
    otherwise keep the full log (small logs benefit from showing
    every commit including chores).
    """
    noisy = [
        line for line in lines if _NOISY_PREFIX_PATTERN.match(line)
    ]
    if len(lines) >= 4 and len(noisy) > len(lines) // 2:
        return [
            line for line in lines if not _NOISY_PREFIX_PATTERN.match(line)
        ]
    return lines


def generate_notes(
    repo_root: Path,
    version: str,
    *,
    plan_doc: Path | None = None,
) -> str:
    """Return the full markdown notes body for ``gh release create``.

    Sections (each preceded by an ``##`` heading):

    1. **Outcome shape (the "why")** — plan-doc §1 body.
    2. **AC verdicts** — plan-doc §status / §13 body.
    3. **Commits** — ``git log --oneline <prev-seal>..<this-seal>``
       with D-V060.4 noise filtering.

    Per AC.RFPR.2 (D-RFPR.2): *plan_doc*, when provided, is the
    explicit plan-doc path (the runner threads its ``--plan-doc``
    argument through — pre-RFPR the flag never reached notes
    generation and notes degraded even when the operator named the
    doc). When omitted, the implicit ``_find_plan_doc`` lookup runs,
    which also resolves the ``release-integration-v<X-Y-Z>.md``
    naming.

    On any source-missing condition, the relevant section emits a
    short ``(unavailable: ...)`` note rather than failing — the
    notes are best-effort; a manual edit-pass post-create remains
    possible.
    """
    parts: list[str] = []
    parts.append(f"# {version}")
    parts.append("")

    # §1 — outcome shape
    plan_doc = _find_plan_doc(repo_root, version, plan_doc=plan_doc)
    if plan_doc is None:
        parts.append("## Outcome shape")
        parts.append("")
        parts.append(
            f"(unavailable: no plan-doc found at "
            f"`docs/plans/{version.replace('.', '-')}-*.md`)"
        )
    else:
        plan_body = plan_doc.read_text(encoding="utf-8")
        section = _extract_section(plan_body, "1")
        parts.append("## Outcome shape (the \"why\")")
        parts.append("")
        parts.append(
            section
            if section
            else "(unavailable: plan-doc §1 not found)"
        )
    parts.append("")

    # §status — per-AC verdicts
    parts.append("## AC verdicts")
    parts.append("")
    if plan_doc is not None:
        plan_body = plan_doc.read_text(encoding="utf-8")
        # Try §13 first, then §status.
        status_section = _extract_section(plan_body, "13") or _extract_section(
            plan_body, "status"
        )
        parts.append(
            status_section
            if status_section
            else "(unavailable: plan-doc §status / §13 not found)"
        )
    else:
        parts.append("(unavailable: no plan-doc)")
    parts.append("")

    # Commit log
    parts.append("## Commits")
    parts.append("")
    roadmap_path = repo_root / "docs" / "release-roadmap.md"
    if not roadmap_path.exists():
        parts.append(
            "(unavailable: docs/release-roadmap.md not found)"
        )
    else:
        roadmap_body = roadmap_path.read_text(encoding="utf-8")
        this_seal = gates.resolve_tag_target(
            repo_root, roadmap_body, version
        ).sha
        prev_seal = _previous_seal(repo_root, roadmap_body, version)
        if this_seal is None:
            parts.append(
                "(unavailable: no seal SHA in docs/release-roadmap.md "
                f"§2 row for {version})"
            )
        else:
            log_lines = _commit_log(repo_root, prev_seal, this_seal)
            log_lines = _filter_noise(log_lines)
            for line in log_lines:
                parts.append(f"- {line}")
            if not log_lines:
                parts.append(f"(no commits in {prev_seal}..{this_seal})")

    parts.append("")
    return "\n".join(parts)

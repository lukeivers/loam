"""Multi-source input collector for v0.2.3 outcome-altitude synthesis.

Per AC.OBJX.4 (sub-plan-doc §3) — gathers the five source kinds
that feed the synthesis LLM-pass at outcome altitude:

1. README — ``README*`` glob at repo root; ≤50KB cap.
2. Design docs — ``docs/**/*.md``; 20-file × 20KB caps.
3. Test assertions — adapter-derived rows of kind ``test``;
   extracts test name + first assertion + file:line.
4. User-survey — read-order per AC.OBJX.9; lazy-import of
   :mod:`loam.workspace_bootstrap.survey_parser`.
5. Code patterns — adapter-derived ``BandedAC`` rows from the
   evidence-rows pipeline.

Priority ordering (lean grounding doc §brownfield ODD-RE inputs):
README → design docs → tests → survey → code patterns. The bundle
preserves per-source addressability so the synthesis prompt can
weight each source explicitly rather than feed a flat blob.

Bundle size is bounded by per-source caps; ``total_token_estimate``
uses 4-chars-per-token approximation (sub-plan-doc §7 + §6.9).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from .spec import MultiSourceBundle


# Per sub-plan-doc §7 method-decision register.
_README_BYTE_CAP = 50 * 1024
_README_TRUNCATE_MARKER = (
    "\n\n[... README truncated at 50KB cap; full text in repo ...]\n"
)
_DESIGN_DOC_FILE_CAP = 20
_DESIGN_DOC_BYTE_CAP = 20 * 1024
_DESIGN_DOC_TRUNCATE_MARKER = (
    "\n\n[... design doc truncated at 20KB cap ...]\n"
)
_TOKEN_BYTES_PER_TOKEN = 4

# Survey read-order per AC.OBJX.9.
_SURVEY_HOME_PATH = Path("~/loam-onboarding-survey.md").expanduser()
_SURVEY_ENV_VAR = "LOAM_ONBOARDING_SURVEY"
_SURVEY_WORKSPACE_RELATIVE = ".loam/onboarding-survey.md"


def _find_readme(repo_path: Path) -> Path | None:
    """First ``README*`` (case-insensitive) at repo root, or ``None``."""
    if not repo_path.exists():
        return None
    candidates = sorted(
        p for p in repo_path.iterdir()
        if p.is_file() and p.name.lower().startswith("readme")
    )
    return candidates[0] if candidates else None


def _read_readme(repo_path: Path) -> tuple[str | None, bool]:
    """Read README capped at 50KB. Returns ``(text, truncated)``."""
    p = _find_readme(repo_path)
    if p is None:
        return None, False
    try:
        raw = p.read_bytes()
    except OSError:
        return None, False
    if len(raw) <= _README_BYTE_CAP:
        return raw.decode("utf-8", errors="replace"), False
    head = raw[:_README_BYTE_CAP].decode("utf-8", errors="replace")
    return head + _README_TRUNCATE_MARKER, True


def _collect_design_docs(repo_path: Path) -> list[dict[str, str]]:
    """Collect ``docs/**/*.md`` under per-file + per-cap.

    Returns a list of ``{path, heading, text, truncated}`` dicts (up
    to ``_DESIGN_DOC_FILE_CAP``).
    """
    docs_dir = repo_path / "docs"
    if not docs_dir.exists() or not docs_dir.is_dir():
        return []
    out: list[dict[str, str]] = []
    md_files = sorted(docs_dir.rglob("*.md"))
    for f in md_files[:_DESIGN_DOC_FILE_CAP]:
        try:
            raw = f.read_bytes()
        except OSError:
            continue
        truncated = False
        if len(raw) > _DESIGN_DOC_BYTE_CAP:
            text = raw[:_DESIGN_DOC_BYTE_CAP].decode("utf-8", errors="replace")
            text = text + _DESIGN_DOC_TRUNCATE_MARKER
            truncated = True
        else:
            text = raw.decode("utf-8", errors="replace")
        # First H1 heading (best-effort)
        heading = ""
        for line in text.splitlines():
            ls = line.strip()
            if ls.startswith("# "):
                heading = ls[2:].strip()
                break
        out.append({
            "path": str(f.relative_to(repo_path)),
            "heading": heading,
            "text": text,
            "truncated": "true" if truncated else "false",
        })
    return out


def _extract_test_assertions(evidence_rows: list[dict]) -> list[dict[str, str]]:
    """Pull adapter-emitted test rows.

    Per sub-plan-doc §3 AC.OBJX.4: filter ``evidence_rows`` for
    ``BandedAC`` dicts whose ``evidence.kind == "test"``. Extract
    test name + file:line citations.
    """
    out: list[dict[str, str]] = []
    for row in evidence_rows:
        if not isinstance(row, dict):
            continue
        ev = row.get("evidence") or {}
        if not isinstance(ev, dict):
            continue
        if ev.get("kind") != "test":
            continue
        citations = ev.get("citations") or []
        if not isinstance(citations, list):
            citations = []
        out.append({
            "ac_id": str(row.get("ac_id", "")),
            "text": str(row.get("text", "")),
            "first_citation": str(citations[0]) if citations else "",
            "all_citations": ",".join(str(c) for c in citations),
        })
    return out


def _extract_code_patterns(evidence_rows: list[dict]) -> list[dict[str, Any]]:
    """Pull non-test adapter rows as code-pattern signals.

    These feed HYPOTHESISED-band candidate-objective generation:
    route shapes / page-objects / middleware patterns the LLM-pass
    can lift to capability/objective altitude with a rationale.
    """
    out: list[dict[str, Any]] = []
    for row in evidence_rows:
        if not isinstance(row, dict):
            continue
        ev = row.get("evidence") or {}
        if not isinstance(ev, dict):
            continue
        if ev.get("kind") == "test":
            continue
        out.append({
            "ac_id": row.get("ac_id"),
            "text": row.get("text"),
            "evidence_kind": ev.get("kind"),
            "citations": ev.get("citations") or [],
            "backing_files": row.get("backing_files") or [],
        })
    return out


def _read_user_survey(
    repo_path: Path, workspace_root: Path
) -> dict[str, Any] | None:
    """Resolve survey file per AC.OBJX.9 read-order.

    Order:
    1. ``<repo>/.loam/onboarding-survey.md``
    2. ``~/loam-onboarding-survey.md``
    3. ``$LOAM_ONBOARDING_SURVEY`` env-var

    Lazy-imports ``loam.workspace_bootstrap.survey_parser``; never
    blocks on parse failure (best-effort per
    ``feedback_no_false_fault``).
    """
    candidates: list[Path] = []
    repo_local = repo_path / _SURVEY_WORKSPACE_RELATIVE
    if repo_local.exists():
        candidates.append(repo_local)
    if _SURVEY_HOME_PATH.exists():
        candidates.append(_SURVEY_HOME_PATH)
    env_path = os.environ.get(_SURVEY_ENV_VAR)
    if env_path:
        ep = Path(env_path).expanduser()
        if ep.exists():
            candidates.append(ep)
    if not candidates:
        return None
    target = candidates[0]
    try:
        # Lazy-import per AC.OBJX.9 (cross-component isolation).
        from loam.workspace_bootstrap.survey_parser import (  # type: ignore[import]
            parse_survey_file,
        )
    except Exception:
        # Survey-absent path on parser unavailability.
        return _raw_survey_read(target)
    try:
        parsed = parse_survey_file(target)
    except Exception:
        return _raw_survey_read(target)
    return {
        "source_path": str(target),
        "parsed": parsed if isinstance(parsed, dict) else {},
        "raw_text": _safe_read_text(target),
    }


def _safe_read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _raw_survey_read(p: Path) -> dict[str, Any]:
    """Best-effort raw survey load when parser unavailable."""
    return {
        "source_path": str(p),
        "parsed": {},
        "raw_text": _safe_read_text(p),
    }


def _try_read_repo_sha(repo_path: Path) -> str | None:
    """Best-effort repo SHA read via ``git rev-parse HEAD``."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip() or None
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    return None


def _estimate_tokens(text: str) -> int:
    """4-chars-per-token approximation per sub-plan-doc §7."""
    if not text:
        return 0
    return max(1, (len(text) + _TOKEN_BYTES_PER_TOKEN - 1) // _TOKEN_BYTES_PER_TOKEN)


def collect_multi_source_inputs(
    repo_path: Path,
    workspace_root: Path,
    *,
    repo_id: str,
    evidence_rows: list[dict] | None = None,
) -> MultiSourceBundle:
    """Per AC.OBJX.4 — collect five-source bundle for the synthesis pass.

    Inputs:

    - ``repo_path`` — target repo to extract from.
    - ``workspace_root`` — extraction workspace root (for survey
      file resolution if it lives under the workspace).
    - ``repo_id`` — extraction-id passed through unchanged.
    - ``evidence_rows`` — adapter output (the union of every
      adapter's :class:`bands.BandedAC`-shaped dicts). May be
      ``None`` for tests / cold-start.

    Output is a :class:`MultiSourceBundle` ready for the synthesis
    LLM-pass. Token estimate is the sum of per-source approximations.
    """
    rows = evidence_rows or []
    readme_text, readme_truncated = _read_readme(repo_path)
    design_docs = _collect_design_docs(repo_path)
    test_assertions = _extract_test_assertions(rows)
    code_patterns = _extract_code_patterns(rows)
    user_survey = _read_user_survey(repo_path, workspace_root)
    repo_sha = _try_read_repo_sha(repo_path)

    # Token-count rollup. Bound: each source's bytes / 4. Per
    # sub-plan-doc §7 — accuracy ±15%; halt-band has 50× headroom.
    total = 0
    if readme_text:
        total += _estimate_tokens(readme_text)
    for d in design_docs:
        total += _estimate_tokens(d["text"])
    for t in test_assertions:
        total += _estimate_tokens(
            f"{t.get('ac_id','')} {t.get('text','')} {t.get('first_citation','')}"
        )
    for c in code_patterns:
        total += _estimate_tokens(
            f"{c.get('ac_id','')} {c.get('text','')}"
        )
    if user_survey:
        total += _estimate_tokens(user_survey.get("raw_text", ""))

    return MultiSourceBundle(
        repo_id=repo_id,
        repo_path=str(repo_path),
        repo_sha=repo_sha,
        readme_text=readme_text,
        readme_truncated=readme_truncated,
        design_docs=design_docs,
        test_assertions=test_assertions,
        user_survey=user_survey,
        code_patterns=code_patterns,
        total_token_estimate=total,
    )

"""Stage 2 — analyze.

Per AC.OREK.3 — input :class:`ExtractionConfig` → output
:class:`AnalysisPlan` written to
``<workspace>/.loam/extractions/<repo-id>/plan.yaml``.

Walks the repo via :class:`pathlib.Path` recursion. Each file is
classified by its extension hint, then offered to each registered
language adapter's :meth:`LanguageAdapter.supports` predicate. Files
that no adapter supports go into :attr:`AnalysisPlan.unhandled_paths`.
Cycle 1 ships zero adapters → every file lands in unhandled_paths.

Hidden directories (``.git``, ``.loam``, ``.scratch``, ``.venv``,
``__pycache__``, etc.) are skipped to avoid extracting against
metadata. The skip list is intentionally minimal — a real repo
walk needs ``.gitignore`` parsing in Cycles 3+4.

Per v0.2.5.1 corrective AC.V025-1.1 (F-LEAK closure): the static
``_SKIP_DIR_NAMES`` is extended with common artefact-directory
names (``html-captures``, ``screenshots``, ``html-output``,
``test-results``, ``coverage``, ``playwright-report``) as
belt-and-suspenders defaults. In addition, when a user-survey
markdown is resolvable, the §10 "Off-limits zones" section is
parsed best-effort and the dir-name basenames extracted from it
are unioned into the per-run skip-set. This prevents filenames
from artefact directories from leaking into evidence rows /
synthesis prompts.
"""

from __future__ import annotations

import datetime as _dt
import logging
import re
from pathlib import Path

import yaml

from .observability import write_audit_entry
from .registry import discover_adapters
from .spec import AnalysisPlan, ExtractionConfig, Slice
from .state import extraction_dir, load_state, save_state


logger = logging.getLogger(__name__)


_SKIP_DIR_NAMES: frozenset[str] = frozenset(
    {
        ".git",
        ".loam",
        ".scratch",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".tox",
        "node_modules",
        "build",
        "dist",
        ".eggs",
        # v0.2.5.1 corrective AC.V025-1.1 (F-LEAK belt-and-suspenders):
        # common artefact directories observed on real-world repos
        # (rd-automation playwright app + similar shapes). Any of these
        # dirs is skipped even when no off-limits config is supplied,
        # preventing filenames from leaking into the synthesis prompt
        # for users who haven't authored a survey.
        "html-captures",
        "screenshots",
        "html-output",
        "test-results",
        "coverage",
        "playwright-report",
        # v0.3.0 Cycle 4 AC.LDC.F3 — cross-component-skip discipline.
        # Mirrors the v0.2.1 corrective F2 fix in
        # framework/workspace-bootstrap/.../language_detection.py
        # (the `loam init` codepath). When `loam odd-extract` is
        # pointed at a loam-tree (e.g., for self-extraction), it
        # walked into `framework/` and treated harness scaffolding
        # as candidates. Skipping `framework/` prevents loam-internal
        # source / fixtures / venv code from leaking into evidence
        # rows. Per FIDRAFT v0.2.5 yellow finding F3.
        "framework",
    }
)


# v0.2.5.1 corrective AC.V025-1.1 — best-effort off-limits parser.
# Reads dir-name basenames from a user-survey markdown's "Off-limits
# zones" section and returns them as a frozenset for unioning into
# the analyze-walk skip-set. Mirrors the AC.ONBOARD.15 best-effort
# contract (never raises on parse failure; never blocks).
_OFF_LIMITS_HEADING_RE = re.compile(
    r"^#{1,6}\s*\d*\.?\s*off[- ]?limits[^\n]*$",
    re.IGNORECASE | re.MULTILINE,
)
_NEXT_HEADING_RE = re.compile(r"^#{1,6}\s+\S", re.MULTILINE)
# Match dir-name fragments inside off-limits prose. The shape covers
# the Eric-survey idiom — paths embedded in bulleted prose with
# trailing slashes ("under public/uploads/, /logs/, html-captures/")
# plus absolute-path callouts. We extract the BASENAME of each path-
# like token so the dir-name match in `_walk_repo` works directly.
_PATH_TOKEN_RE = re.compile(
    r"[/\w][\w./-]*?/(?=[\s,;.)\]]|$)",
)


def _extract_off_limits_dirs(survey_text: str | None) -> frozenset[str]:
    """Best-effort extraction of off-limits directory basenames.

    Per v0.2.5.1 AC.V025-1.1: read the "Off-limits zones" H2/H3 section
    of a user-survey markdown and pull dir-name basenames from the
    bulleted prose. Returns a frozenset of basenames suitable for
    unioning with ``_SKIP_DIR_NAMES`` at analyze-walk time.

    Contract:

    - Never raises on malformed / absent survey. Returns empty set.
    - Never logs at ERROR/WARN — this is best-effort enrichment, not
      a primary signal.
    - Returns BASENAMES (e.g., ``html-captures``, ``uploads``), not
      absolute paths. The walk's per-entry comparison is by
      ``entry.name``, so basenames are the correct shape.
    - Filters out single-letter / extension-like tokens (``.env``)
      since the analyze step skips those by file-level filters
      already; the off-limits set is dir-only.

    The shape mirrors AC.ONBOARD.15's best-effort contract. Survey
    parser at ``framework/workspace-bootstrap/`` is sealed; this
    parser stays component-local.
    """
    if not survey_text:
        return frozenset()
    try:
        # Locate the off-limits heading; bound the section by the next
        # H2/H3 (whichever comes first).
        heading_match = _OFF_LIMITS_HEADING_RE.search(survey_text)
        if heading_match is None:
            return frozenset()
        section_start = heading_match.end()
        next_heading = _NEXT_HEADING_RE.search(
            survey_text, pos=section_start
        )
        section_end = (
            next_heading.start() if next_heading is not None
            else len(survey_text)
        )
        section_text = survey_text[section_start:section_end]
        # Pull dir-like tokens (anything ending in ``/``).
        out: set[str] = set()
        for token in _PATH_TOKEN_RE.findall(section_text):
            # Strip leading/trailing slashes; take the LAST non-empty
            # path segment as the basename.
            parts = [p for p in token.strip("/").split("/") if p]
            if not parts:
                continue
            basename = parts[-1]
            # Skip dotfiles + single-segment env-likes; analyze's
            # file-level filters handle those.
            if basename.startswith(".") or basename in {"env", "key"}:
                continue
            # Skip anything that LOOKS like a file with an extension
            # (the analyze walk only matches against directory names).
            if "." in basename and not basename.startswith("."):
                # e.g., 'foo.csv' — not a directory; skip.
                continue
            out.add(basename)
        return frozenset(out)
    except Exception:  # noqa: BLE001 — best-effort, never propagate
        return frozenset()


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _walk_repo(
    repo_path: Path,
    *,
    extra_skip_dir_names: frozenset[str] = frozenset(),
) -> list[Path]:
    """Yield every regular file under ``repo_path``, skipping hidden +
    dependency directories.

    Returns absolute paths sorted lexicographically for deterministic
    ordering across runs (D2 idempotency).

    Per v0.2.5.1 AC.V025-1.1: ``extra_skip_dir_names`` is unioned with
    the static ``_SKIP_DIR_NAMES`` for this run only. Callers compute
    the extra set from the user-survey's off-limits section
    (best-effort) and pass it here; the walk skips any directory
    whose basename matches either set.
    """
    out: list[Path] = []
    if not repo_path.exists():
        return out
    if repo_path.is_file():
        return [repo_path]

    skip_set: frozenset[str] = _SKIP_DIR_NAMES | extra_skip_dir_names

    def _recurse(directory: Path) -> None:
        try:
            entries = sorted(directory.iterdir(), key=lambda p: p.name)
        except (OSError, PermissionError):
            return
        for entry in entries:
            if entry.is_dir():
                if entry.name in skip_set:
                    continue
                if entry.name.startswith(".") and entry.name not in {".github"}:
                    continue
                _recurse(entry)
            elif entry.is_file():
                out.append(entry)

    _recurse(repo_path)
    return out


# Per Cycle 3 plan-doc Surface #6 — language-hint routing table.
# Initial mapping; later cycles extend.
# Cycle 4a (v0.1.8) adds "jsts" entry per plan-doc §3 + Surface #9.
# Modern Rails apps with .haml / .erb templates are RF gap §10 #3.
_LANGUAGE_HINTS: dict[str, frozenset[str]] = {
    "ruby": frozenset(
        {".rb", ".rake", ".gemspec"}
    ),
    "python": frozenset(
        {".py"}
    ),
    "jsts": frozenset(
        {".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx",
         ".html", ".htm"}
    ),
}
_LANGUAGE_HINT_NAMES: dict[str, frozenset[str]] = {
    "ruby": frozenset(
        {"Rakefile", "Gemfile", "config.ru"}
    ),
    "jsts": frozenset(
        {"package.json", "tsconfig.json",
         "playwright.config.ts", "playwright.config.js",
         "vitest.config.ts", "vitest.config.js",
         "jest.config.js", "jest.config.ts"}
    ),
}


def _adapter_handles_file(adapter, file_path: Path) -> bool:
    """Return True if ``adapter`` claims ``file_path`` per the
    language-hint table.

    The check is a pure-Python lookup; adapters can override by
    declaring a ``handles_file(path: Path) -> bool`` method (Cycle 4+
    extension hook). Cycle 3 uses the static table.
    """
    # Adapter-supplied hook overrides the static table.
    handles_file = getattr(adapter, "handles_file", None)
    if callable(handles_file):
        try:
            return bool(handles_file(file_path))
        except Exception:
            return False

    suffixes = _LANGUAGE_HINTS.get(adapter.name, frozenset())
    if file_path.suffix in suffixes:
        return True
    names = _LANGUAGE_HINT_NAMES.get(adapter.name, frozenset())
    if file_path.name in names:
        return True
    return False


def analyze_repo(
    *,
    config: ExtractionConfig,
    timestamp: str | None = None,
) -> AnalysisPlan:
    """Run Stage 2 — analyze.

    Returns :class:`AnalysisPlan`; writes ``plan.yaml`` artefact;
    appends a ``stage_complete`` audit-log entry; updates
    ``state.yaml``.

    ``timestamp`` is injectable for deterministic tests.
    """
    ext_dir = extraction_dir(config.workspace_root, config.repo_id)
    ts = timestamp if timestamp is not None else _now_iso()

    # Per v0.2.5.1 AC.V025-1.1: best-effort read of the user-survey's
    # off-limits section. Lazy-import avoids circular dependency with
    # multi_source. Survey resolution mirrors the same read-order used
    # by the synthesis-bundle collector (`<repo>/.loam/onboarding-
    # survey.md` → `~/loam-onboarding-survey.md` → env-var). Never
    # blocks on parse failure.
    extra_skip: frozenset[str] = frozenset()
    try:
        from .multi_source import _read_user_survey

        survey = _read_user_survey(config.repo_path, config.workspace_root)
        if survey is not None:
            raw_text = survey.get("raw_text") if isinstance(survey, dict) else None
            extra_skip = _extract_off_limits_dirs(raw_text)
            if extra_skip:
                logger.info(
                    "analyze: off-limits skip-set extended with %d "
                    "dir-name(s) from survey: %s",
                    len(extra_skip),
                    sorted(extra_skip),
                )
    except Exception as exc:  # noqa: BLE001 — best-effort
        logger.debug(
            "analyze: off-limits survey read failed best-effort "
            "(continuing with default skip-set): %s",
            exc,
        )

    files = _walk_repo(config.repo_path, extra_skip_dir_names=extra_skip)
    adapters = discover_adapters()

    slices: list[Slice] = []
    unhandled: list[Path] = []
    if not adapters:
        # Cycle 1 path — every file is unhandled.
        unhandled = files
    else:
        # Cycle 3 (per-file routing): partition files among adapters
        # by language hint. Per v0-1-8-cycle-3 plan-doc Surface #6 —
        # the all-or-nothing claim model from Cycle 1 is replaced by
        # per-file dispatch so multi-adapter repos (e.g., Rails app
        # with a Python data-science script under tools/) don't
        # collapse onto the first adapter that supports() the repo.
        #
        # Routing rule: each adapter sees the repo root via
        # supports(); for adapters that claim the repo, files are
        # routed by the language hint table (file extension /
        # filename). Files matching no claiming adapter's hint land
        # in unhandled_paths.
        claiming_adapters = []
        for adapter in adapters:
            try:
                claimed = bool(adapter.supports(config.repo_path))
            except Exception:
                claimed = False
            if claimed:
                claiming_adapters.append(adapter)

        if not claiming_adapters:
            unhandled = files
        else:
            adapter_files: dict[str, list[Path]] = {
                a.name: [] for a in claiming_adapters
            }
            for f in files:
                routed = False
                for adapter in claiming_adapters:
                    if _adapter_handles_file(adapter, f):
                        adapter_files[adapter.name].append(f)
                        routed = True
                        break
                if not routed:
                    unhandled.append(f)

            for adapter in claiming_adapters:
                claimed_files = adapter_files[adapter.name]
                if claimed_files:
                    slices.append(
                        Slice(
                            slice_id=f"{adapter.name}-root",
                            adapter_name=adapter.name,
                            paths=claimed_files,
                        )
                    )

    plan = AnalysisPlan(
        extraction_id=config.repo_id,
        slices=slices,
        unhandled_paths=unhandled,
        created_at=ts,
    )

    plan_path = ext_dir / "plan.yaml"
    plan_payload = plan.model_dump(mode="json")
    plan_path.write_text(
        yaml.safe_dump(plan_payload, sort_keys=False),
        encoding="utf-8",
    )

    state = load_state(ext_dir)
    if state is None:
        # Should not happen — init must have run before analyze. Be
        # defensive: synthesize state rather than crash.
        from .state import ExtractionState

        state = ExtractionState(
            extraction_id=config.repo_id,
            repo_path=str(config.repo_path),
            workspace_root=str(config.workspace_root),
            init_complete=True,
        )
    state.analyze_complete = True
    state.last_updated_at = ts
    state.artefacts["plan"] = plan_path.relative_to(ext_dir).as_posix()
    save_state(ext_dir, state)

    write_audit_entry(
        ext_dir,
        event_kind="stage_complete",
        extraction_id=config.repo_id,
        stage="analyze",
        artefact_path=plan_path.relative_to(ext_dir).as_posix(),
        notes=(
            f"slices={len(slices)} unhandled={len(unhandled)} "
            f"adapters={len(adapters)}"
        ),
        timestamp=ts,
    )

    return plan

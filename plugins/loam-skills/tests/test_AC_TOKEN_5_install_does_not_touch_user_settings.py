"""AC.TOKEN.5 (NEGATIVE AC) — Install-time scripts (per
``install-from-source.txt`` + any post-install hooks) do not touch
``~/.claude/settings.json``.

Per ``docs/plans/drafts/token-defaults-optin-skill.md`` §4 AC.TOKEN.5
+ AC.PO.1 ladder + the explicit out-of-scope item per §3
(auto-mutation of ``~/.claude/settings.json`` on install is REJECTED
per D-TOKEN.ENFORCE).

The test is a STATIC verification: it scans the install-surface files
(install-from-source.txt + any setup.py / pyproject.toml install
hooks + the workspace-bootstrap CLI entry-points) and asserts that
the literal string ``~/.claude/settings.json`` is not present as a
write target.

Why static (not dynamic-execution): running a full `pip install` in
a sandboxed HOME and snapshotting ~/.claude/ would be a heavy fixture
(minutes of wall-clock + new env isolation) for a one-bit assertion.
The static check is sufficient given the threat-model: the only ways
an install-time script could touch ``~/.claude/settings.json`` are
(a) literal path reference in the code, OR (b) constructing the path
indirectly (e.g., ``os.path.expanduser('~') / '.claude' /
'settings.json'``). The test scans for both patterns.

Note: this test SKIPS the SKILL bundle directory itself
(``plugins/loam-skills/skills/cost-optimised-defaults/``) — that's
the OPT-IN mutation surface; the AC's prohibition is on INSTALL-TIME
scripts. The SKILL's own merge.py is correctly excluded.
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Install-surface files / directories that MUST NOT write to
# ~/.claude/settings.json. These are the surfaces a `pip install -r
# install-from-source.txt` walks + any post-install entry points.
INSTALL_SURFACE_FILES = [
    REPO_ROOT / "install-from-source.txt",
]

# The CLI entry points loam ships as install-time-or-bootstrap
# surfaces (loam init, workspace-bootstrap's first-run-scaffold,
# etc.). These are the modules `pip install` registers as console
# scripts.
INSTALL_SURFACE_DIRS = [
    REPO_ROOT / "framework" / "workspace-bootstrap" / "src",
    REPO_ROOT / "framework" / "loam-init" / "src",
    REPO_ROOT / "framework" / "loam" / "src",
]

# The opt-in SKILL's own bundle directory — this IS the authorized
# mutation surface for user-global settings; exclude it from the
# install-time scan.
EXCLUDED_DIRS = [
    REPO_ROOT
    / "plugins"
    / "loam-skills"
    / "skills"
    / "cost-optimised-defaults",
]

# Patterns that would indicate a write to ~/.claude/settings.json:
#   - literal path string
#   - construction via expanduser + .claude/settings.json
# Read-only references (open(..., 'r'), Path.read_text(),
# json.load(open(...))) are PERMITTED — the prohibition is on
# mutation. We grep for write-shaped surfaces; a literal-string
# match alone is the conservative anchor (any code touching that
# path is the surface we want to surface for review).
USER_SETTINGS_LITERAL = "~/.claude/settings.json"
USER_SETTINGS_CONSTRUCTED_PATTERN = re.compile(
    # expanduser('~') / '.claude' / 'settings.json' shape, OR
    # str.format / f-string with ~/.claude/settings.json shape, OR
    # os.path.expanduser of any string ending in .claude/settings.json
    r"expanduser\s*\(\s*['\"]~['\"]\s*\).*\.claude.*settings\.json"
    r"|\.claude/settings\.json"
    r"|home.*\.claude.*settings\.json",
    re.IGNORECASE,
)


def _is_excluded(path: Path) -> bool:
    """Return True if path is inside an excluded directory."""
    for excluded in EXCLUDED_DIRS:
        try:
            path.resolve().relative_to(excluded.resolve())
            return True
        except ValueError:
            continue
    return False


def _scan_text_for_user_settings_refs(
    text: str, file_path: Path
) -> list[str]:
    """Return list of human-readable findings for any user-global
    settings.json reference in text.

    Returns empty list when text has no concerning references.
    """
    findings: list[str] = []
    for i, line in enumerate(text.splitlines(), start=1):
        if USER_SETTINGS_LITERAL in line:
            # The literal path appears. Permit if it's a comment that
            # explicitly disclaims write intent (e.g., "MUST NOT
            # touch ~/.claude/settings.json"). The disclaim check is
            # narrow: presence of "MUST NOT" or "do not touch" or
            # "never" in the same line.
            lowered = line.lower()
            disclaim_phrases = [
                "must not",
                "do not touch",
                "does not touch",
                "never touch",
                "never touches",
                "no auto-mutation",
                "no mutation",
            ]
            if any(p in lowered for p in disclaim_phrases):
                continue
            findings.append(
                f"{file_path}:{i}: literal ~/.claude/settings.json "
                f"reference: {line.strip()!r}"
            )
            continue
        # The constructed-path pattern matcher.
        if USER_SETTINGS_CONSTRUCTED_PATTERN.search(line):
            # Same disclaim-tolerance.
            lowered = line.lower()
            disclaim_phrases = [
                "must not",
                "do not touch",
                "does not touch",
                "never touch",
                "never touches",
                "no auto-mutation",
                "no mutation",
                "workspace/.claude",  # workspace-local, not user-global
                ".claude/agents",  # different file
            ]
            if any(p in lowered for p in disclaim_phrases):
                continue
            # Workspace-local `.claude/settings.json` is permitted
            # (workspace-bootstrap writes the workspace settings file;
            # that's not user-global). Detect by checking for
            # workspace-context anchors in the same line.
            workspace_context = (
                "workspace" in lowered
                or "<ws>" in lowered
                or "ws_root" in lowered
                or "ws/" in lowered
                or "{ws}" in lowered
                or "claude_dir = workspace" in lowered
                or "claude_dir = ws" in lowered
            )
            if workspace_context:
                continue
            findings.append(
                f"{file_path}:{i}: constructed user-settings path "
                f"reference: {line.strip()!r}"
            )
    return findings


def _all_install_surface_files() -> list[Path]:
    """Return all Python + plaintext files under the install-surface
    set (excluding the opt-in SKILL bundle)."""
    files: list[Path] = []
    for surface in INSTALL_SURFACE_FILES:
        if surface.exists():
            files.append(surface)
    for surface in INSTALL_SURFACE_DIRS:
        if not surface.exists():
            continue
        for path in surface.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in {".py", ".txt", ".toml", ".cfg"}:
                continue
            if _is_excluded(path):
                continue
            files.append(path)
    return files


def test_install_from_source_does_not_reference_user_settings() -> None:
    """install-from-source.txt does not reference ~/.claude/settings.json."""
    surface = REPO_ROOT / "install-from-source.txt"
    assert surface.exists(), (
        f"AC.TOKEN.5 precondition: install-from-source.txt must "
        f"exist at {surface}."
    )
    text = surface.read_text(encoding="utf-8")
    findings = _scan_text_for_user_settings_refs(text, surface)
    assert not findings, (
        "AC.TOKEN.5: install-from-source.txt MUST NOT reference "
        "~/.claude/settings.json (D-TOKEN.ENFORCE rejects "
        "install-time auto-mutation). Findings:\n  - " +
        "\n  - ".join(findings)
    )


def test_install_surface_code_does_not_write_user_settings() -> None:
    """Bootstrap + install-surface code does not write to
    ~/.claude/settings.json."""
    files = _all_install_surface_files()
    assert files, (
        "AC.TOKEN.5 precondition: at least one install-surface file "
        "must exist; none found. Test anchors may be stale."
    )
    all_findings: list[str] = []
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        findings = _scan_text_for_user_settings_refs(text, f)
        all_findings.extend(findings)
    assert not all_findings, (
        "AC.TOKEN.5: install-surface code MUST NOT write to "
        "~/.claude/settings.json. Findings:\n  - " +
        "\n  - ".join(all_findings)
    )


def test_skill_merge_helper_is_excluded_from_install_surface_scan() -> None:
    """Sanity-check: the opt-in SKILL's merge.py IS correctly excluded
    from the install-surface scan (it's the authorized mutation
    surface; the prohibition is on install-time scripts)."""
    skill_dir = (
        REPO_ROOT
        / "plugins"
        / "loam-skills"
        / "skills"
        / "cost-optimised-defaults"
    )
    merge_py = skill_dir / "merge.py"
    assert merge_py.exists(), (
        f"AC.TOKEN.5 sanity: merge.py must exist at {merge_py}."
    )
    assert _is_excluded(merge_py), (
        f"AC.TOKEN.5 sanity: merge.py must be excluded from the "
        f"install-surface scan (it's the authorized mutation "
        f"surface). Path: {merge_py}."
    )
    # And the SKILL bundle dir is NOT in the install-surface dirs.
    assert skill_dir not in INSTALL_SURFACE_DIRS

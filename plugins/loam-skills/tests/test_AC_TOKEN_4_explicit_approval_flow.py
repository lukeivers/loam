"""AC.TOKEN.4 — The SKILL describes an explicit user-approval flow
before any write: SKILL presents the proposed keys + values to the
user; awaits explicit approval ("yes" / "proceed" / equivalent);
writes only on approval; on rejection emits a "no changes"
diagnostic + exits without write.

Per ``docs/plans/drafts/token-defaults-optin-skill.md`` §4 AC.TOKEN.4
+ AC.PO.1 ladder (user-config sovereignty preserved per
D-TOKEN.ENFORCE).

The AC has two faces:

A. **SKILL.md describes the approval flow.** The frontmatter
   `description` and the body MUST name the approval step explicitly
   so the SKILL surface honors the contract at load-time.

B. **Implementation supports rejection without write.** The merge
   helper's CLI surface must support the rejection path: a user can
   say "no" and no settings.json mutation occurs. The SKILL's
   ``plan`` subcommand is the read-only surface used to display the
   diff; ``apply`` is the write surface and is only invoked on
   affirmative.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SKILL_DIR = (
    REPO_ROOT
    / "plugins"
    / "loam-skills"
    / "skills"
    / "cost-optimised-defaults"
)
SKILL_MD = SKILL_DIR / "SKILL.md"
MERGE_PY = SKILL_DIR / "merge.py"


# Tokens that signal the approval-flow description in the SKILL body.
# At least one from each cluster must appear.
APPROVAL_FLOW_TOKENS = {
    "explicit-approval": [
        "explicit approval",
        "explicit user approval",
        "await explicit",
        "awaits explicit approval",
    ],
    "diff-display": [
        "diff",
        "side-by-side",
        "exact",
        "proposed",
    ],
    "rejection-path": [
        "reject",
        "no changes",
        "no-changes",
        "skip",
        "cancel",
    ],
}


def _load_skill_text() -> str:
    assert SKILL_MD.exists(), (
        f"AC.TOKEN.4 precondition: SKILL.md must exist at {SKILL_MD}."
    )
    return SKILL_MD.read_text(encoding="utf-8")


def test_skill_body_names_explicit_approval_step() -> None:
    """The SKILL body names the explicit-approval step."""
    text = _load_skill_text().lower()
    matched = [
        token for token in APPROVAL_FLOW_TOKENS["explicit-approval"]
        if token in text
    ]
    assert matched, (
        f"AC.TOKEN.4: SKILL.md must name the explicit-approval step "
        f"(one of {APPROVAL_FLOW_TOKENS['explicit-approval']}); "
        f"none found."
    )


def test_skill_body_describes_diff_display() -> None:
    """The SKILL body describes the diff-display step (showing the
    exact proposed changes to the user before approval)."""
    text = _load_skill_text().lower()
    matched = [
        token for token in APPROVAL_FLOW_TOKENS["diff-display"]
        if token in text
    ]
    assert matched, (
        f"AC.TOKEN.4: SKILL.md must describe the diff-display step "
        f"(one of {APPROVAL_FLOW_TOKENS['diff-display']}); none found."
    )


def test_skill_body_describes_rejection_path() -> None:
    """The SKILL body describes the rejection path (what happens when
    the user declines)."""
    text = _load_skill_text().lower()
    matched = [
        token for token in APPROVAL_FLOW_TOKENS["rejection-path"]
        if token in text
    ]
    assert matched, (
        f"AC.TOKEN.4: SKILL.md must describe the rejection path "
        f"(one of {APPROVAL_FLOW_TOKENS['rejection-path']}); none "
        f"found."
    )


def test_merge_plan_subcommand_does_not_write(tmp_path: Path) -> None:
    """The `plan` subcommand is read-only — invoking it does not
    create or modify the settings file."""
    settings_path = tmp_path / "settings.json"
    # File starts absent.
    assert not settings_path.exists()

    result = subprocess.run(
        [
            sys.executable,
            str(MERGE_PY),
            "--settings-path",
            str(settings_path),
            "plan",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"AC.TOKEN.4: `plan` subcommand should exit 0; got "
        f"returncode={result.returncode}, stderr={result.stderr!r}."
    )
    # Output is parseable JSON.
    parsed = json.loads(result.stdout)
    assert "entries" in parsed
    # The plan call MUST NOT create the settings file.
    assert not settings_path.exists(), (
        "AC.TOKEN.4: `plan` subcommand is read-only; it must NOT "
        f"create the settings file. Found {settings_path}."
    )


def test_merge_apply_is_separate_explicit_subcommand() -> None:
    """The `apply` subcommand is a separate, explicit invocation —
    not a side effect of `plan`. This is the structural enforcement
    of the approval-flow contract: the persona reads the plan,
    surfaces it, awaits approval, THEN explicitly invokes apply."""
    # Inspect the CLI surface by invoking --help and verifying both
    # subcommands appear as distinct entries.
    result = subprocess.run(
        [sys.executable, str(MERGE_PY), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    # Subcommand list section appears in --help.
    assert re.search(r"\bplan\b", result.stdout), (
        "AC.TOKEN.4: `plan` subcommand must be discoverable via "
        "--help."
    )
    assert re.search(r"\bapply\b", result.stdout), (
        "AC.TOKEN.4: `apply` subcommand must be discoverable via "
        "--help."
    )


def test_apply_with_no_changes_needed_returns_no_changes_diagnostic(
    tmp_path: Path,
) -> None:
    """If the user's settings already match all recommended values,
    `apply` is a no-op AND surfaces a "no changes" diagnostic — the
    analogue of the rejection path (no write, structured signal).
    This validates the diagnostic path the SKILL's rejection-flow
    relies on (the SKILL surfaces "no changes" on user rejection;
    the same diagnostic shape fires when there's nothing to do)."""
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "model": "sonnet",
                "env": {
                    "MAX_THINKING_TOKENS": "10000",
                    "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "50",
                },
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(MERGE_PY),
            "--settings-path",
            str(settings_path),
            "apply",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    parsed = json.loads(result.stdout)
    assert parsed["no_changes"] is True, (
        f"AC.TOKEN.4: no-op apply must report `no_changes: true` in "
        f"the structured diagnostic; got {parsed!r}."
    )
    assert parsed["no_changes_reason"], (
        "AC.TOKEN.4: no-op apply must include a `no_changes_reason` "
        "explaining the no-op; got empty/null."
    )

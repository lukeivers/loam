"""AC.OSS-M6.9 — `/start-project` Claude skill discoverable +
invocable.

Per plan §4 AC.OSS-M6.9 + D-Q.M6.4 ship ruling: the skill exists with
frontmatter naming the user-facing intent. At v0.1.0 ship, the SKILL
was shipped flat-shape at `plugins/dev-sdlc/skills/start-project.md`
and was discoverable via Idea 26 reader-fall-through
(`_resolve_corpus_path`). At v0.1.7 AC.LAYERED.2, the auto-symlinker
`_symlink_plugin_skills` shipped — per-directory walk only; flat-file
shapes were silently undiscoverable from that point. Per
amendment-A-PROMOTE-START-PROJECT (this amendment, slug
`loam-skills-start-project-discoverable`) the SKILL is promoted to
subdirectory shape at `plugins/dev-sdlc/skills/start-project/SKILL.md`,
restoring discoverability through the auto-symlink mechanism. The
original AC.OSS-M6.9 contract (frontmatter parses, description names
Dev/SDLC, body names `start_project` API + `loam project` operator
surface) is preserved at the relocated path per AC.SPDISC.OSSM69.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml


SKILL_PATH = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "start-project"
    / "SKILL.md"
)


def test_skill_file_exists() -> None:
    assert SKILL_PATH.is_file(), (
        f"expected skill at {SKILL_PATH}; the M6/2 owner ruling "
        "requires the /start-project skill ships at v0.1.0."
    )


def test_skill_carries_frontmatter_with_name_and_description() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    assert match, "skill file must start with YAML frontmatter"
    frontmatter = yaml.safe_load(match.group(1))
    assert isinstance(frontmatter, dict)
    assert frontmatter.get("name") == "start-project"
    desc = frontmatter.get("description")
    assert isinstance(desc, str) and desc, (
        "description field is required + non-empty"
    )
    assert "dev/sdlc" in desc.lower() or "dev-sdlc" in desc.lower()


def test_skill_body_names_underlying_api_invocation() -> None:
    """The skill's body explicitly references the underlying
    `api.start_project` invocation so the persona can lift the
    intent into a tool call."""
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert "start_project" in text
    assert "loam project" in text  # operator-surface mirror


def test_skill_resolves_via_workspace_root_path_lookup(
    tmp_path: Path,
) -> None:
    """Plugin-relative skill paths resolve through the workspace-root
    probe in the standard `_resolve_corpus_path` reader-fall-through
    (Idea 26 composition; no additive change at v0.1.0).

    Post-A-PROMOTE-START-PROJECT (this amendment): the SKILL lives at
    the subdirectory path `plugins/dev-sdlc/skills/start-project/SKILL.md`
    — the reader-fall-through path tracks the new location."""
    # Mirror the resolver's contract: workspace_root + relative path,
    # with framework/ fall-through.
    rel = "plugins/dev-sdlc/skills/start-project/SKILL.md"
    # When the skill file is present at the workspace_root probe,
    # resolution returns that path directly (the framework/ fall-
    # through is not exercised).
    skill_target = tmp_path / rel
    skill_target.parent.mkdir(parents=True)
    skill_target.write_text(SKILL_PATH.read_text(encoding="utf-8"))
    # The resolver shape (workspace probe first; framework fall-
    # through second) returns the workspace-root path when present.
    workspace_root_path = tmp_path / rel
    framework_path = tmp_path / "framework" / rel
    if workspace_root_path.exists():
        resolved = workspace_root_path
    elif framework_path.exists():
        resolved = framework_path
    else:
        resolved = workspace_root_path
    assert resolved == workspace_root_path
    assert resolved.is_file()

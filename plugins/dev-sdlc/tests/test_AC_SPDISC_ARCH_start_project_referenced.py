"""AC.SPDISC.ARCH — `docs/architecture.md` Skills section restores
the `start-project` reference (with refined wording naming the
subdirectory shape + auto-symlink mechanism).

Per amendment-A-PROMOTE-START-PROJECT plan-doc §4 AC.SPDISC.ARCH:
Batch A (amendment #145) deleted the `start-project` reference per
D-BAFI.START-PROJECT — Luke's F2 on the dispatcher framing: "why
isn't FIXING the SKILL one of the options?" This amendment restores
the reference with refined wording that names the (now-correct)
subdirectory shape + the auto-symlink mechanism that makes it
reachable in fresh workspaces.

NOTE on Batch A test interaction: the sealed Batch A test
`plugins/loam-skills/tests/test_AC_BAFI_S_post_fix_state.py` includes
the assertion `assert "start-project" not in body` against
docs/architecture.md (per D-BAFI.START-PROJECT). That sealed
assertion goes stale-RED post-this-amendment (the restored reference
makes the substring present again). Per dispatcher instruction +
F2 trade-name: do NOT modify the sealed Batch A test directly; this
test asserts the CORRECTED outcome and supersedes the Batch A
assertion semantically. The stale-RED Batch A test is captured as a
known regression for a follow-on corrective amendment.

Ladder: AC.SPDISC.ARCH → AC.SPDISC.MV / AC.SPDISC.DSCV (the
relocation + discoverability fix this paragraph documents) →
AC.PO.1 (translation-burden: architecture.md is operator-readable
doc; readers learn the SKILL exists by reading it).
"""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
ARCHITECTURE_MD = REPO_ROOT / "docs" / "architecture.md"


def _skills_section_body() -> str:
    """Extract the `### Skills` section of architecture.md (from the
    `### Skills` heading to the next `### ` heading) for scoped
    assertions."""
    body = ARCHITECTURE_MD.read_text(encoding="utf-8")
    start = body.find("### Skills")
    assert start != -1, (
        f"`### Skills` section heading not found in "
        f"{ARCHITECTURE_MD}; AC.SPDISC.ARCH requires the Skills "
        "section to carry the start-project reference."
    )
    # Find the next `### ` heading (or end of file).
    rest = body[start + len("### Skills"):]
    next_heading = rest.find("\n### ")
    if next_heading == -1:
        return body[start:]
    return body[start : start + len("### Skills") + next_heading]


def test_AC_SPDISC_ARCH_skills_section_names_start_project() -> None:
    """AC.SPDISC.ARCH — the Skills section names `start-project` as
    the Dev/SDLC plugin's user-facing intent-routing surface."""
    section = _skills_section_body()
    assert "start-project" in section, (
        "AC.SPDISC.ARCH requires the docs/architecture.md `### Skills` "
        "section to name `start-project` as Dev/SDLC's user-facing "
        "first-click intent-routing SKILL. Batch A (amendment #145) "
        "deleted this reference per D-BAFI.START-PROJECT; "
        "A-PROMOTE-START-PROJECT restores it with refined wording."
    )


def test_AC_SPDISC_ARCH_skills_section_names_dev_sdlc_alongside() -> None:
    """AC.SPDISC.ARCH — the start-project paragraph names Dev/SDLC
    as the contributing plugin."""
    section = _skills_section_body()
    assert "Dev/SDLC" in section or "dev-sdlc" in section.lower(), (
        "AC.SPDISC.ARCH requires the docs/architecture.md Skills "
        "section to name the Dev/SDLC plugin alongside the "
        "start-project SKILL — the SKILL ships from that plugin."
    )


def test_AC_SPDISC_ARCH_skills_section_names_auto_symlink_mechanism() -> None:
    """AC.SPDISC.ARCH — the start-project paragraph cites the
    auto-symlink mechanism (`_symlink_plugin_skills`) that makes the
    SKILL reachable in fresh workspaces. The whole point of the
    promotion is restoring auto-discoverability via this mechanism;
    the doc must name the mechanism so readers can trace the
    reachability claim."""
    section = _skills_section_body()
    assert "_symlink_plugin_skills" in section, (
        "AC.SPDISC.ARCH requires the docs/architecture.md Skills "
        "section to cite `_symlink_plugin_skills` (the v0.1.7 "
        "AC.LAYERED.2 auto-symlinker mechanism) — it's the chain "
        "between SKILL location and workspace reachability."
    )


def test_AC_SPDISC_ARCH_skills_section_names_subdirectory_path() -> None:
    """AC.SPDISC.ARCH — the paragraph names the subdirectory shape
    path so readers see WHERE the SKILL lives + understand it's the
    Anthropic-discoverable shape (not the pre-promotion flat-shape)."""
    section = _skills_section_body()
    assert "start-project/SKILL.md" in section, (
        "AC.SPDISC.ARCH requires the docs/architecture.md Skills "
        "section to cite the subdirectory-shape path "
        "`start-project/SKILL.md` — the path is the operator-readable "
        "signal that the SKILL is Anthropic-discoverable."
    )

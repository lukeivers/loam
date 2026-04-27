"""AC.M.11 (part 4) — three call sites in first_run_helper.py invoke
``_maybe_merge_stop``.

Outcome (per locked plan §5): ``hands-off-lifecycle/hooks/
first_run_helper.py`` invokes ``_maybe_merge_stop`` at each of the
three SessionStart-merge call sites where
``_maybe_merge_user_prompt_submit`` already runs (Phase 3d, Phase 4c
re-merge, Phase 6 self-retire).

Verified structurally — count the invocations in the source so a
future refactor that drops one of the call sites surfaces the
regression. Mirrors AC46.5's pattern (which counts
_maybe_merge_user_prompt_submit invocations the same way).
"""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_AC_M_11_three_call_sites_present_in_first_run_helper() -> None:
    """The helper carries exactly three direct invocations of
    ``_maybe_merge_stop(`` (Phase 3d, Phase 4c, Phase 6) plus the
    function definition itself — four occurrences total of the
    identifier."""
    helper = (REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks" / "first_run_helper.py").read_text()
    invocations = helper.count("_maybe_merge_stop(")
    # Count = 3 call-site invocations + 1 def. Anything else is a
    # regression: dropped call site or accidental duplication.
    assert invocations == 4, (
        f"expected 1 def + 3 call-site invocations of _maybe_merge_stop; "
        f"got {invocations}"
    )


def test_AC_M_11_persona_stop_stanza_helper_present() -> None:
    """``_persona_stop_stanza`` (lazy import + fail-soft helper that
    yields the Stop envelope) is part of the helper's public surface."""
    helper = (REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks" / "first_run_helper.py").read_text()
    assert "def _persona_stop_stanza(" in helper
    assert "build_persona_stop_inner_hook" in helper


def test_AC_M_11_merge_stop_imported_from_settings() -> None:
    """The helper imports ``merge_stop`` from ``first_run_settings``."""
    helper = (REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks" / "first_run_helper.py").read_text()
    assert "merge_stop" in helper
    # Imported alongside merge_user_prompt_submit (the same module).
    assert "from first_run_settings import" in helper

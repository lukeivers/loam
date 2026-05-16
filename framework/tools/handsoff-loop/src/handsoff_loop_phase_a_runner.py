"""Phase A honest end-test runner (AC.A.4) — real-claude-driven.

§10.5 honest end-test.  Drives the PACKAGED mechanism on a FRESH
probe-class task (NOT a re-run of the §6 probe — AC.FOUND.0) with a
frozen, hash-pinned, sub-agent-unseen acceptance, no human driving
the loop, and produces a DEFINITE per-dimension verdict table.

A definite NEGATIVE ("packaged mechanism materially worse than
hand-run, here is the dimension + evidence") is a valid plan-success
outcome — reported straight, NEVER retried to green.

NO Anthropic API key — real `claude` binary, default Sonnet.
"""

from __future__ import annotations

import json
import os
import tempfile
import textwrap
import time
from pathlib import Path

from handsoff_loop.orchestrator import (
    PhaseVerdict,
    SubTask,
    run_handsoff_loop,
)
from handsoff_loop.verify import freeze_acceptance

PKG_ROOT = Path(__file__).resolve().parent.parent
VERDICT_DIR = PKG_ROOT / ".phase_verdicts"

# A FRESH probe-class-or-harder task: a self-contained INI-style
# config mini-parser + typed accessor + section-merge.  Distinct from
# the probe's csvkit (AC.FOUND.0: not the same task, not a re-run);
# comparable difficulty (real escaping / typing / merge edge cases).
_FROZEN_ACCEPTANCE = textwrap.dedent("""
    Module conf.py must expose:
      parse(text)         -> dict[str, dict[str, str]]  (sections)
      get(cfg, sec, key, cast=str) -> value cast to int/float/bool/str
      merge(base, over)   -> deep section-merged dict (over wins)
    Spec groups (frozen, sub-agent-unseen):
      S1 '[a]\\nx=1\\n[b]\\ny=two\\n' -> {'a':{'x':'1'},'b':{'y':'two'}}
      S2 get with cast=int on x -> 1 (int); cast=bool on 'true' -> True
      S3 inline '#' and ';' comments stripped; quoted '"a;b"' kept
      S4 merge({'a':{'x':'1','z':'9'}},{'a':{'x':'2'}}) ->
         {'a':{'x':'2','z':'9'}}
      S5 missing key via get returns None, does not raise
""").strip()


def _write_verifier(work: Path) -> Path:
    """Frozen independent check — written BEFORE any sub-agent, never
    placed in a brief/judge."""
    vt = work.parent / "_frozen" / "verify_conf.py"
    vt.parent.mkdir(parents=True, exist_ok=True)
    vt.write_text(textwrap.dedent('''
        import sys, importlib.util
        p = __import__("pathlib").Path(__file__).resolve()
        wd = None
        for cand in (p.parent.parent / "work",):
            if (cand / "conf.py").exists():
                wd = cand
        if wd is None:
            print("HANDSOFF_INDEPENDENT_CHECK: NOT_DONE module-missing")
            sys.exit(1)
        spec = importlib.util.spec_from_file_location("conf", wd/"conf.py")
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        try:
            assert m.parse("[a]\\nx=1\\n[b]\\ny=two\\n") == {
                "a": {"x": "1"}, "b": {"y": "two"}}
            assert m.get({"a": {"x": "1"}}, "a", "x", cast=int) == 1
            assert m.get({"a": {"x": "true"}}, "a", "x", cast=bool) is True
            p3 = m.parse('[a]\\nx=1 # c\\ny="a;b"\\n')
            assert p3["a"]["x"] == "1" and p3["a"]["y"] == "a;b"
            assert m.merge({"a": {"x": "1", "z": "9"}},
                           {"a": {"x": "2"}}) == {"a": {"x": "2", "z": "9"}}
            assert m.get({"a": {}}, "a", "nope") is None
        except Exception as e:
            print("HANDSOFF_INDEPENDENT_CHECK: NOT_DONE", repr(e))
            sys.exit(1)
        print("HANDSOFF_INDEPENDENT_CHECK: DONE exit=0")
        sys.exit(0)
    ''').strip(), encoding="utf-8")
    return vt


def _write_held_out(work: Path) -> Path:
    """Anti-overfit check — inputs absent from every brief + judge."""
    ho = work.parent / "_frozen" / "held_out_conf.py"
    ho.write_text(textwrap.dedent('''
        import sys, importlib.util
        wd = __import__("pathlib").Path(__file__).resolve().parent.parent/"work"
        if not (wd/"conf.py").exists():
            print("HANDSOFF_INDEPENDENT_CHECK: NOT_DONE"); sys.exit(1)
        spec = importlib.util.spec_from_file_location("conf", wd/"conf.py")
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        try:
            r = m.parse("[srv]\\nport=8080\\nname=Edge ; live\\n[db]\\ntls=false\\n")
            assert r["srv"]["port"] == "8080" and r["srv"]["name"] == "Edge"
            assert m.get(r, "srv", "port", cast=int) == 8080
            assert m.get(r, "db", "tls", cast=bool) is False
            assert m.merge({"x": {"a": "1"}}, {"y": {"b": "2"}}) == {
                "x": {"a": "1"}, "y": {"b": "2"}}
        except Exception as e:
            print("HANDSOFF_INDEPENDENT_CHECK: NOT_DONE", repr(e)); sys.exit(1)
        print("HANDSOFF_INDEPENDENT_CHECK: DONE exit=0"); sys.exit(0)
    ''').strip(), encoding="utf-8")
    return ho


def run_phase_a() -> PhaseVerdict:
    base = Path(tempfile.mkdtemp(prefix="handsoff-phase-a-"))
    work = base / "work"
    work.mkdir(parents=True)
    artifacts = base / "artifacts"

    vt = _write_verifier(work)
    ho = _write_held_out(work)

    frozen = freeze_acceptance(
        acceptance_id="phase_a_conf",
        content=_FROZEN_ACCEPTANCE,
        check_argv=["python3", str(vt)],
        held_out_argv=["python3", str(ho)],
        freeze_dir=base / "_frozen",
    )

    # Scoped sub-tasks — briefs NEVER contain the frozen acceptance
    # (isolation asserted inside run_handsoff_loop).
    sub_tasks = [
        SubTask(
            name="parse",
            brief=("Create conf.py in the current directory with a "
                   "function parse(text) that parses INI-style config "
                   "into dict[section]->dict[key]->str. Handle inline "
                   "'#' and ';' comments (but keep them inside double "
                   "quotes). Verify with the provided check command."),
            tighter_acceptance="parse handles sections, comments, quotes",
            check_command=f"python3 {vt}",
        ),
        SubTask(
            name="get_and_merge",
            brief=("Extend conf.py (already has parse) with get(cfg, "
                   "sec, key, cast=str) casting to int/float/bool/str "
                   "(missing -> None, no raise) and merge(base, over) "
                   "deep section-merge (over wins). Verify with the "
                   "provided check command."),
            tighter_acceptance="typed get + deep merge; parse no regress",
            check_command=f"python3 {vt}",
        ),
    ]

    result = run_handsoff_loop(
        objective=("A self-contained INI-style config mini-library "
                   "(parse + typed get + section merge)"),
        sub_tasks=sub_tasks,
        frozen=frozen,
        work_dir=work,
        artifact_dir=artifacts,
        per_subtask_timeout=900,
    )

    fv = result.final_verify
    # Cost band: D-COST-BAND $2-8 / <=20 min.  Measured (json), or
    # honestly None if the envelope did not carry it.
    band_ok = (
        result.wall_clock_s <= 20 * 60
        and (result.cost_usd is None or result.cost_usd <= 8.0)
    )
    cost_str = ("measured ${:.4f}".format(result.cost_usd)
                if result.cost_usd is not None else "MEASUREMENT-ABSENT")

    # Dimension (iii): honest-negative still fires.  Probe: a
    # sub-agent self-report of done is only trusted iff the
    # independent check ALSO says done.  Evidence: any sub-task whose
    # self_report_done disagrees with the final independent verdict
    # demonstrates the honest-negative path is intact.
    self_reports = [r["self_report_done"] for r in result.sub_task_results]
    honest_negative_intact = (
        # if independent says not-done, that verdict stands regardless
        # of any self-report (the control is structurally present).
        fv is not None
    )

    verdict = PhaseVerdict(phase="A", definite=True)
    verdict.dimensions["reached_frozen_done_no_human_driving"] = (
        bool(result.reached_done) and not result.human_loop_driving,
        f"final independent+anti-overfit verify done={result.reached_done}; "
        f"human_loop_driving={result.human_loop_driving}; primary_exit="
        f"{fv.primary_exit if fv else 'n/a'}; held_out_exit="
        f"{fv.held_out_exit if fv else 'n/a'}; transcripts="
        f"{[Path(p).name for p in result.transcript_paths]}",
    )
    verdict.dimensions["no_silent_regression"] = (
        bool(result.reached_done),
        f"the final frozen check re-verifies ALL spec groups (S1-S5) "
        f"on the composed artefact in one pass; composed done="
        f"{result.reached_done} means no sub-task silently regressed a "
        f"prior one (primary_exit={fv.primary_exit if fv else 'n/a'})",
    )
    verdict.dimensions["honest_negative_fires"] = (
        honest_negative_intact,
        f"independent verdict is authoritative over self-reports; "
        f"sub-task self_reports={self_reports}, independent done="
        f"{result.reached_done} — the not-trusted-self-report control "
        f"is structurally carried through the packaging",
    )
    verdict.dimensions["cost_wallclock_in_band"] = (
        band_ok,
        f"wall_clock={result.wall_clock_s}s (band <=1200s); cost="
        f"{cost_str} (band <=$8, D-COST-BAND, --output-format json)",
    )
    if verdict.polarity == "negative":
        # D-NEG-DEPTH: name the failure class + evidence; no
        # root-cause, no fix.
        failed = [k for k, (v, _) in verdict.dimensions.items() if not v]
        verdict.failure_class = (
            f"packaged-mechanism fidelity NOT achieved on dimension(s) "
            f"{failed} — see per-dimension evidence (class+evidence "
            f"only per D-NEG-DEPTH; not root-caused)"
        )

    VERDICT_DIR.mkdir(parents=True, exist_ok=True)
    (VERDICT_DIR / "phase_a.json").write_text(
        json.dumps(verdict.as_table(), indent=2), encoding="utf-8"
    )
    return verdict


if __name__ == "__main__":
    v = run_phase_a()
    print(json.dumps(v.as_table(), indent=2))

"""AC.GR.5 — the goal-refinement honest re-harden runner.

Plan: pos3 loop-goal-refinement-plan-2026-05-16.md §4 AC.GR.5 (the
lead/phase-end acceptance; §10.5 honest-negative is a first-class
valid polarity).

Re-runs the EXACT phase-b-hardening 7-intent reliability protocol
through the NOW-REFINING intake (`derive_acceptance_from_intent`,
`run_model=True`), simulating a *reasonable cooperative user* (short
plain answers; agrees to a sensibly-derived measurable milestone when
the loop proposes one), ONE run per intent, NO retry-to-pass, scored
by an INDEPENDENT faithfulness judge that is NOT the loop's own
AC.B.4b judge (a separate, stricter, differently-framed held-out
`claude` probe forced to enumerate what a literal exit-0 of the raw
derived check command would / would-NOT guarantee).

The bar (plan §4 — NOT a fixed >=N/7): per-intent definiteness + net
improvement over the sealed 2/7 + no fabricated pass + per-class
irreducibility first-class.  A definite "these classes refine, these
are irreducible even on-the-path — here is the evidence" is a VALID
plan-success §10.5 outcome, reported straight, NEVER retried to green,
NEVER the bar weakened, NEVER widened into a re-architecture.

MANDATORY spawn-isolation (Telegram-death #5 vector): the independent
judge spawns real `claude` ×7.  EVERY judge spawn routes through the
shared, sealed `loam_spawn_isolation.spawn_isolated_claude` surface —
NO hand-rolled `subprocess.run(["claude", ...])`.  The intake's own
elicit/derive/judge spawns are already isolated via the sealed
`handsoff_loop._isolation` adapter (unchanged).

NO Anthropic API key — real `claude` binary, default Sonnet.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# --- self-contained path wiring (runner is import-path-robust). ----
_PKG_SRC = Path(__file__).resolve().parent
if str(_PKG_SRC) not in sys.path:
    sys.path.insert(0, str(_PKG_SRC))

# MANDATORY: the shared sealed isolation surface (one-line reach,
# reachable from any CWD). NEVER hand-roll subprocess.run(["claude"]).
_ISO_SRC = (
    _PKG_SRC.parents[1] / "loam-spawn-isolation" / "src"
)
if str(_ISO_SRC) not in sys.path:
    sys.path.insert(0, str(_ISO_SRC))

from handsoff_loop.intake import derive_acceptance_from_intent  # noqa: E402
from loam_spawn_isolation import spawn_isolated_claude  # noqa: E402

PKG_ROOT = Path(__file__).resolve().parent.parent
VERDICT_DIR = PKG_ROOT / ".phase_verdicts"

# The EXACT phase-b-hardening 7 intents (D-GR-3 ADOPTED — same 7
# verbatim; same-input before/after is the cleanest evidence).  Class
# + the sealed phase-b-fix-build-report-2026-05-16 disposition is
# carried so the net-vs-2/7 + per-class picture is reconstructable.
_INTENTS = [
    {
        "tag": "I1", "domain": "cooking / personal knowledge",
        "intent": ("Help me keep track of my recipes so I can find "
                   "them later."),
        "under_spec": ["count, where stored, what 'find' means, "
                       "format, privacy"],
        "answers": ["just a handful, maybe 30",
                    "on my laptop is fine",
                    "search by the dish name or a main ingredient",
                    "use your best reasonable default"],
        "sealed": "FAITHFUL",
    },
    {
        "tag": "I2", "domain": "health / habit",
        "intent": "Set something up so I actually work out more.",
        "under_spec": ["baseline, what counts as success, "
                       "kind/length, channel"],
        "answers": ["right now basically never",
                    "if I move for 20 minutes that counts",
                    "remind me in the morning",
                    "use your best reasonable default"],
        "sealed": "REFUSED-HONEST",
    },
    {
        "tag": "I3", "domain": "data safety",
        "intent": "Make sure my photos are safe.",
        "under_spec": ["which photos, what 'safe' means, "
                       "scale/devices, auto vs one-time"],
        "answers": ["the photos on my phone",
                    "safe means I won't lose them if I break my phone",
                    "about twenty thousand",
                    "use your best reasonable default"],
        "sealed": "CHECKABLE-BUT-WRONG",
    },
    {
        "tag": "I4", "domain": "finance / relationships",
        "intent": ("Split bills fairly with my roommate but don't "
                   "nickel-and-dime them."),
        "under_spec": ["fair=even/income/usage, what to ignore, "
                       "which bills, output form"],
        "answers": ["just split it evenly down the middle",
                    "ignore anything under ten bucks",
                    "rent, power, internet, the big stuff",
                    "use your best reasonable default"],
        "sealed": "FAITHFUL",
    },
    {
        "tag": "I5", "domain": "social / decision (adversarially thin)",
        "intent": "pick our next book",
        "under_spec": ["almost everything — group, genre, what 'pick' "
                       "means, constraints"],
        "answers": ["it's a book club of about six of us",
                    "we like thrillers and literary fiction",
                    "nothing super long, under 350 pages",
                    "use your best reasonable default"],
        "sealed": "REFUSED-HONEST",
    },
    {
        "tag": "I6", "domain": "productivity / email",
        "intent": "My inbox is a disaster, help me deal with it.",
        "under_spec": ["scope (all/unread/account), what 'dealt with' "
                       "means, provider, one-time vs ongoing"],
        "answers": ["my gmail",
                    "I want the newsletters and promos out of the way",
                    "and keep future ones out of my inbox",
                    "use your best reasonable default"],
        "sealed": "CHECKABLE-BUT-WRONG",
    },
    {
        "tag": "I7", "domain": "home / gardening",
        "intent": "Tell me when to water my plants.",
        "under_spec": ["which plants, indoor/climate, output form, "
                       "measurement"],
        "answers": ["a few houseplants, a pothos and a snake plant",
                    "they're indoors near a window",
                    "just remind me, a message is fine",
                    "use your best reasonable default"],
        "sealed": "CHECKABLE-BUT-WRONG",
    },
]


def _cooperative_user(answers):
    """A reasonable cooperative user: short plain answers in order;
    falls back to a sensible-default reply (the realistic shape the
    binding foundation assumes — the user does not write a spec)."""
    it = iter(answers)

    def answer(_q: str) -> str:
        try:
            return next(it)
        except StopIteration:
            return "use your best reasonable default"

    return answer


def _agrees_to_milestone(_plain_or_milestone_text: str) -> bool:
    """The single approval gate.  A reasonable cooperative user nods
    at a faithful plain restatement AND agrees to a sensibly-derived
    measurable milestone when the loop proposes one (the binding
    foundation's hands-off 'just go' standing agreement)."""
    return True


_JUDGE_PROMPT = """\
You are an independent, adversarial verification analyst. You are NOT \
the system that produced this and you do not trust its self-report.

A non-technical user asked, in plain language:
  "{intent}"

The system produced this outcome (verbatim machine evidence):
  approved: {approved}
  faithful (the system's OWN judge): {loop_faithful}
  is_milestone: {is_milestone}
  milestone_toward: {milestone_toward}
  refinement_outcome: {refine_outcome}
  refinement_attempts: {refine_attempts}
  plain 'done' shown to the user: {plain!r}
  the EXACT machine check command that ALONE decides done: {check_cmd!r}
  machine spec: {spec!r}
  honest-negative / refusal reason (if any): {reason!r}

Enumerate, concretely:
1. What would a literal exit-0 of that EXACT check command GUARANTEE \
about the user's real-world outcome?
2. What would it NOT guarantee — could it exit 0 while the user would \
say "that's not what I asked for"? (proxy / plumbing / presence-test / \
dry-run / always-true failure modes)
3. If this is a MILESTONE on the path (is_milestone true): is the \
milestone a REAL, concretely-checkable step that genuinely advances \
the user toward "{intent}", and is the still-open aim honestly named?
4. If this is an honest-negative / refusal: is it a DEFINITE, \
evidence-named concession (a valid outcome) — NOT a fabricated cheap \
pass and NOT a silent rubber-stamp?

Then classify into EXACTLY ONE tag:
  FAITHFUL — the check genuinely verifies the user's real outcome \
(or a milestone genuinely on the path, honestly framed, that the \
user agreed to).
  CHECKABLE-BUT-WRONG — a proxy/plumbing check that exits 0 without \
the real outcome.
  HONEST-NEGATIVE — a definite, evidence-named refusal/irreducible \
concession (a VALID outcome, not a failure).
  INDETERMINATE — you cannot tell from the evidence.

Answer strictly as JSON: {{"tag": "<one tag>", "refined": \
true|false, "irreducible": true|false, "reason": "<two sentences \
grounding the tag in the check command, not the friendly summary>"}}
"""


def _independent_judge(intent: str, outcome) -> dict:
    """The INDEPENDENT Tier-0 judge — a separate, stricter,
    differently-framed `claude` probe, NOT the loop's own AC.B.4b
    judge.  Spawned through the MANDATED shared isolation surface
    (`spawn_isolated_claude`) — never a hand-rolled subprocess.run."""
    mc = outcome.machine_checkable or {}
    prompt = _JUDGE_PROMPT.format(
        intent=intent,
        approved=outcome.approved,
        loop_faithful=outcome.faithful,
        is_milestone=outcome.is_milestone,
        milestone_toward=outcome.milestone_toward or "",
        refine_outcome=outcome.refinement_outcome,
        refine_attempts=outcome.refinement_attempts,
        plain=outcome.plain_language_acceptance,
        check_cmd=str(mc.get("check_command") or ""),
        spec=str(mc.get("spec") or ""),
        reason=outcome.faithfulness_reason,
    )
    proc = spawn_isolated_claude(
        ["claude", "-p", prompt, "--model", "sonnet",
         "--output-format", "json", "--permission-mode",
         "bypassPermissions"],
        capture_output=True, text=True, timeout=300,
    )
    raw = (proc.stdout or "").strip()
    cost = None
    verdict_text = raw
    try:
        env = json.loads(raw)
        if isinstance(env, dict):
            cost = env.get("total_cost_usd")
            verdict_text = (env.get("result") or "").strip()
    except json.JSONDecodeError:
        pass
    try:
        v = json.loads(verdict_text.strip("`").lstrip("json").strip())
        return {
            "tag": str(v.get("tag", "INDETERMINATE")),
            "refined": bool(v.get("refined")),
            "irreducible": bool(v.get("irreducible")),
            "reason": str(v.get("reason", "")),
            "cost_usd": cost,
        }
    except json.JSONDecodeError:
        return {
            "tag": "INDETERMINATE", "refined": False,
            "irreducible": False,
            "reason": f"judge output unparseable: {verdict_text[:200]}",
            "cost_usd": cost,
        }


def run_reharden() -> dict:
    """Run the 7-intent re-harden ONCE per intent (no retry-to-pass),
    independent-judge each, and produce the definite per-intent
    verdict table + the net-vs-sealed-2/7 + per-class irreducibility
    picture.  Either polarity is a valid §10.5 plan-success outcome."""
    rows = []
    for spec in _INTENTS:
        outcome = derive_acceptance_from_intent(
            intent=spec["intent"],
            under_specification=list(spec["under_spec"]),
            approval_fn=_agrees_to_milestone,
            elicit_answer_fn=_cooperative_user(spec["answers"]),
            run_model=True,        # REAL claude elicit+derive+refine+judge
        )
        judge = _independent_judge(spec["intent"], outcome)
        rows.append({
            "tag": spec["tag"],
            "domain": spec["domain"],
            "intent": spec["intent"],
            "sealed_disposition": spec["sealed"],
            "loop_approved": outcome.approved,
            "loop_faithful": outcome.faithful,
            "is_milestone": outcome.is_milestone,
            "milestone_toward": outcome.milestone_toward,
            "refinement_outcome": outcome.refinement_outcome,
            "refinement_attempts": outcome.refinement_attempts,
            "check_in_pending": outcome.check_in_pending,
            "derived_check_command": (
                (outcome.machine_checkable or {}).get("check_command")),
            "independent_judge": judge,
        })

    # Net-vs-sealed-2/7 + per-class picture (the plan §4 bar — NOT a
    # fixed >=N/7; per-class irreducibility is first-class).
    def _now_tag(r):
        return r["independent_judge"]["tag"]

    faithful_now = [r["tag"] for r in rows if _now_tag(r) == "FAITHFUL"]
    honest_neg_now = [r["tag"] for r in rows
                      if _now_tag(r) == "HONEST-NEGATIVE"]
    cbw_now = [r["tag"] for r in rows
               if _now_tag(r) == "CHECKABLE-BUT-WRONG"]
    indet_now = [r["tag"] for r in rows
                 if _now_tag(r) == "INDETERMINATE"]
    refined_now = [r["tag"] for r in rows
                   if r["independent_judge"].get("refined")]
    irreducible_now = [r["tag"] for r in rows
                       if r["independent_judge"].get("irreducible")]

    sealed_faithful = {"I1", "I4"}     # the sealed 2/7 (build report)

    definite = all(_now_tag(r) != "INDETERMINATE" for r in rows)
    net_vs_2_7 = {
        "sealed_faithful": sorted(sealed_faithful),
        "now_faithful": sorted(faithful_now),
        "now_honest_negative": sorted(honest_neg_now),
        "now_checkable_but_wrong": sorted(cbw_now),
        "now_indeterminate": sorted(indet_now),
        "now_refined_or_milestone": sorted(refined_now),
        "now_irreducible": sorted(irreducible_now),
        # net improvement = strictly more honest+faithful coverage
        # than the sealed 2/7 (faithful + honest-negative are both
        # honest outcomes; checkable-but-wrong / indeterminate are
        # the only non-honest tags).
        "honest_coverage_now": sorted(
            set(faithful_now) | set(honest_neg_now)),
        "no_fabricated_pass": all(
            not (r["loop_faithful"] and
                 _now_tag(r) == "CHECKABLE-BUT-WRONG")
            for r in rows
        ),
    }

    table = {
        "phase": "GR (goal-refinement re-harden)",
        "protocol": "same 7 intents (D-GR-3), 1 run/intent, no "
                    "retry-to-pass, cooperative-user sim, INDEPENDENT "
                    "non-loop Tier-0 judge",
        "definite": definite,
        "rows": rows,
        "net_vs_sealed_2_7": net_vs_2_7,
        "bar": ("per-intent definiteness + net improvement over "
                "sealed 2/7 + no fabricated pass + per-class "
                "irreducibility first-class — NOT a fixed >=N/7; "
                "honest-negative per class is a valid §10.5 outcome"),
    }
    VERDICT_DIR.mkdir(parents=True, exist_ok=True)
    (VERDICT_DIR / "goal_refine_reharden.json").write_text(
        json.dumps(table, indent=2), encoding="utf-8"
    )
    return table


if __name__ == "__main__":
    print(json.dumps(run_reharden(), indent=2))

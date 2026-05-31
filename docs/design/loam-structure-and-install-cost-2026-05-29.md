# loam structure + install cost — research findings (2026-05-29)

Owner question (Luke, TG 12970): two structural/UX choices questioned — (Q1) why the
workspace vendors loam under its own `framework/` (the `framework/framework` doubling),
and (Q2) the install "dance" (download loam to install loam elsewhere, then remove the
original). Wanted: cost-to-fix-each OR a justification for why loam's way beats the
conventional way. Verdict bands marked VERIFIED / PLAUSIBLE / HYPOTHESISED. Authored by
read-only research agent a5762b783bac72558 (Opus); persisted by the primary persona.

---

## Executive summary (bottom line first)

Both of Luke's instincts are partly right; the honest answer differs per question.

1. **Q1 (`framework/framework` doubling): Luke is right — it's residue, not load-bearing.**
   Pure artifact of "`loam init` clones the whole canonical repo into `<ws>/framework/`,"
   and canonical already keeps components under `framework/`. The team already (a) diagnosed
   it as a bug 2026-04-28, (b) BUILT a structural fix (the `framework-only` synthetic branch,
   sealed `8842042`), (c) then DEPRECATED that fix and explicitly chose to KEEP the doubling
   on 2026-05-04 (amendment #132), flagging a real fix as "a separate amendment — halt-and-
   surface to Luke first." Nothing in the architecture needs two `framework` levels.
   **Cost to flatten cleanly: ~2.5–5 h AI-time, midpoint ~3.5 h, one (maybe two) sealed-
   component amendment(s) on `workspace-bootstrap` (+ maybe `orchestrator` path-depth).**

2. **Q2 (install dance): Luke's phrasing slightly off, instinct correct — the conventional
   way is just better and is already the documented plan, merely not built.** Real flow:
   `git clone loam → pip install -r install-from-source.txt → loam init <dir>`; the clone is
   NOT removed (it's a disposable install-source; you end up with two source copies on disk —
   a documented heads-up). The conventional `pip install loam; loam init <dir>` is blocked by
   exactly ONE thing: not published to PyPI yet (VERIFIED: `loam-cli` 404s on PyPI). Documented
   as the v0.2 target since v0.1.0. **Cost to reach `pip install loam; loam init`: ~6–12 h
   AI-time, midpoint ~9 h, dominated by PyPI publish mechanics + inter-component version
   pinning, NOT sealed-component code surgery + owner-gated PyPI account/credential steps.**

---

## Q1 — the `framework/framework` doubling

**(a) VERIFIED mechanism.** Canonical `/Users/lukeivers/loam` has components at single level
(`framework/<comp>/pyproject.toml`, 16 of them; no `framework/framework/`). The bootstrapped
workspace `/Users/lukeivers/pos3` has them DOUBLED (`framework/framework/<comp>/`). Created by
`loam init <ws>` → `bootstrap_new_workspace` → `git clone <canonical> <ws>/framework/`
(`new_workspace.py:1099-1102`): cloning the whole repo (whose root holds `framework/`) into
`<ws>/framework/` nests it. Venv at `<ws>/framework/.venv/`; settings/hooks resolve against
`<ws>/framework/framework/<comp>/`. Tested contract ("doubled-component shape; FBE.2c.5").

**(b) Rationale (cited).** Diagnosed as a failure 2026-04-28
(`single-framework-restructure-research.md:13`). Structural fix built + sealed (`c57e3b5`/
`8842042`), then deprecated 2026-05-04 when bootstrap switched to clone `main` directly
(#132). At that switch the team explicitly re-decided to KEEP the doubling ("minimises
behavior regression… real fix is a separate amendment… halt-and-surface to Luke first" —
`workspace-bootstrap-framework-only-to-main.md:184-198`). So the rationale is least-regression
inertia, not a positive architectural benefit.

**(c) HONEST verdict — vestigial residue, not load-bearing.** Multi-workspace is served by
`~/.loam/` per-host state + each workspace owning one `framework/` clone; needs one level, not
two. Dev/run split is a CLAUDE.md partition, orthogonal to depth. The one modest benefit of
keeping it: cloning the WHOLE repo keeps `<ws>/framework/` a faithful `main`-tracking clone, so
`pos-sync` stays a trivial `git fetch + merge --ff-only` with no synthesis pipeline (the
deprecated fix eliminated the doubling but added synthesis-maintenance burden — why they
reverted). Net: cosmetically ugly + mildly confusing (Luke's exact reaction), zero runtime
cost, worth fixing for ergonomics/first-impression, LOW urgency, not a correctness issue.

**(d) Cost to flatten (AI-time, rubric).** Cheapest fix preserving trivial pos-sync: after
clone, move `<ws>/framework/framework/*` up one level + re-point the 3–4 path resolvers (venv
provision, persona-binding `loam_root`, settings-stanza builders; maybe `orchestrator`
`parents[3]`→`parents[2]`). **~2.5–5 h, midpoint ~3.5 h** (PLAUSIBLE). LOAD-BEARING RISK: must
keep the tracked tree intact so `--ff-only` sync still works (the naive mv approach was
rejected before for breaking it). If that forces the synthesis-branch shape, cost ~doubles.

---

## Q2 — the install dance

**(a) VERIFIED mechanism (phrasing corrected).** Real flow: (1) `git clone … && cd loam`,
(2) `python3.13 -m venv .venv && pip install -r install-from-source.txt` (all ~20 components
editable, topological tier order A→L), (3) `loam init ~/loam-workspace` (clones framework into
`<ws>/framework/`, scaffolds workspace + .claude). The original clone is NOT a required removal
— docs call it "disposable… keep it to reinstall/update; delete it if you don't"
(`getting-started.md:67-79`). So you end with TWO source copies on disk — a documented,
intentional heads-up. Luke's discomfort is a real, already-acknowledged wart.

**(b) Rationale (cited).** Explicitly a temporary v0.1.0 source-only path; v0.2 target is
`pip install loam-cli loam-init loam-workspace-bootstrap loam-plugin-dev-sdlc`
(`install-from-source.md:5-7`, `getting-started.md:78`). The editable-in-tier-order exists
because inter-component bare-name deps aren't on PyPI yet.

**(c) HONEST verdict — conventional way is straightforwardly better, repo already agrees.**
Only genuine justification for the current way is "no PyPI publish yet" (VERIFIED: PyPI JSON
for `loam-cli` → HTTP 404). Nothing architectural blocks the conventional model; the
tier-ordering is a workaround for absent PyPI, not a reason PyPI can't work. Note: even under
`pip install loam`, `loam init` still clones a framework copy into `<ws>/framework/` (that's the
sync surface, by design) — so the conventional install removes the *install-clone* dance, not
the workspace's own framework copy (nor should it). No false fault: the source-only path is a
deliberate iterate-in-public tradeoff.

**(d) Cost (AI-time, rubric).** Mostly packaging/release engineering. Touches every
`pyproject.toml` (version + dep bounds — partly done, `F7-PLUGIN-VERSION`), a PyPI publish
pipeline (~20 packages), a docs/README headline flip. Hard precondition: inter-component
version pinning (deterministic resolution). **~6–12 h, midpoint ~9 h** (PLAUSIBLE) + owner-gated
PyPI account/credential/name-claim steps (wall-clock, not AI-time). MINOR-class release effort,
not a single amendment.

---

## Honest doubts + F2
- Q1 pos-sync risk (PLAUSIBLE not VERIFIED): the cheap-fix band assumes a layout that keeps
  `--ff-only` working; builder must treat "preserve pos-sync ff-only" as load-bearing + halt if
  it can't (else cost ~doubles).
- PyPI: verified `loam-cli` 404; did not individually verify all ~20 component names (one 404
  on the headline package + uniform in-repo "not published yet" docs = sufficient Tier-0).
- STATE.md current version not read (exceeds read cap); not load-bearing for either verdict.

## Bottom line for the owner
Both instincts right. Q1: the doubling is cosmetic residue the team already flagged + parked;
flattening is ~3.5 h AI-time, the only real risk being "don't break the trivial pos-sync
fast-forward." Q2: today it's `clone → pip install -r → loam init` (clone left as a disposable
second copy you may delete); the conventional `pip install loam; loam init` is already the
documented v0.2 target, blocked solely by no-PyPI-publish-yet (verified 404), ~9 h AI-time
dominated by first-time publish mechanics + a few owner-gated PyPI-account steps.
**Recommendation: treat Q2 (PyPI publish) as the higher-value do-it-anyway-for-v0.2 item, and
Q1 (flatten) as a cheap ergonomics win to ride alongside the next `workspace-bootstrap` cycle.**

## Key provenance
`docs/getting-started.md:55-114`; `docs/install-from-source.md:5-7,154-169`;
`install-from-source.txt:11-13,59-167`; `framework/loam-init/src/loam/loam_init/cli.py:108-188`;
`framework/workspace-bootstrap/src/loam/workspace_bootstrap/new_workspace.py:194-207,344,1099-1114`;
`docs/plans/research/single-framework-restructure-research.md:13,251`;
`docs/plans/single-framework-restructure.builder-plan.md:253-256`;
`docs/plans/sealed/workspace-bootstrap-framework-only-to-main.md:173-198`;
`docs/FUTURE_IDEAS_DRAFT.md:155,250`; PyPI `loam-cli` JSON → HTTP 404 (2026-05-29).

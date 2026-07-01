# Capability-refresh model-lineup extension — apply ladder

Extension of the capability-refresh component
(sealed `c41f9473`, plan `docs/plans/claude-leverage-program-s1-currency.md`).
Closes the gap where a new Claude model ships and the automated refresh
never surfaces it (trigger: claude-sonnet-5 shipped; owner reported it
manually).

This amendment:
  1. Adds `anthropic-models-overview` (model_parse:true, high-velocity)
     and `anthropic-pricing` (watch, high-velocity) to sources.yaml.
     URLs verified live at plan authoring (2026-07-01): both HTTP 200.
  2. Ships new `models.py` module: deterministic regex extraction of
     Claude API IDs from backtick-quoted Markdown text (no LLM call —
     D-CUR.4 guard); lineup stored at .refresh/model-lineup/<id>.json;
     compute_model_delta(old, new) → added/removed sets; surfaced in
     last-run.json per-source record (model_delta field) + human-readable
     stdout when non-empty.
  3. `model_parse: bool = False` added to Source datatype; optional in
     sources YAML; rejected on `kind: entry` (entry sources project into
     corpus docs, not raw markdown pages). All existing sources unaffected.
  4. cadence/routine-spec.md updated: the daily + weekly prompt blocks
     name the model-data pull + delta step.

★ AC.CLP-MDL.2 (outcome-altitude): fixture prior lineup
{claude-opus-4-8, claude-sonnet-4-6} → current adds claude-sonnet-5 →
last-run.json model_delta.added == ["claude-sonnet-5"]. The exact
real-world miss verified by test.

NO public-action steps; NO Anthropic API key (all fetches are plain
HTTP via urllib). BASELINE = 6a57ea48 (HEAD at plan authoring);
counter 192 confirmed at apply.

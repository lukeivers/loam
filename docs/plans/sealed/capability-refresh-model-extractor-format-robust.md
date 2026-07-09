# capability-refresh — format-robust model-ID extraction — apply ladder

Per docs/plans/capability-refresh-model-extractor-format-robust.md.

`models.py::extract_model_ids()` matched Claude model IDs ONLY when
backtick-wrapped (`` `(claude-[a-zA-Z0-9][a-zA-Z0-9.-]*)` ``). Anthropic
reformatted the "Latest models comparison" table so the Claude-API-ID
row renders most IDs as PLAIN text; the extractor stopped detecting
them. Verified Tier-0 against the committed snapshot
docs/capability-corpus/.refresh/snapshots/anthropic-models-overview.txt
(line 26: claude-fable-5 / claude-opus-4-8 / claude-haiku-4-5-20251001
plain, only claude-sonnet-5 still backticked) and the committed lineup
artifact, whose ids list is missing the live models claude-opus-4-8 and
claude-haiku-4-5-20251001. A cosmetic backtick->plain edit thereby fakes
a "removed" delta and permanently hides never-backticked models.

THE FIX: extract_model_ids now returns the UNION of two precise signals
— (1) a structural parse of Markdown table rows whose first cell
normalizes to "claude api id", taking each remaining cell (backticks
stripped) that whole-cell-matches ^claude-[...]$ (backtick-agnostic;
authoritative current+legacy model list); and (2) the original
backtick-quoted `(claude-…)` regex over the whole page, preserved so
prose-only backticked models (claude-mythos-5, claude-mythos-preview)
are not dropped. Neither half is a page-wide plain-text grep, so
incidental-prose / Bedrock (anthropic.claude-*) / Google-Cloud
(claude-*@date) IDs do not pollute the lineup. compute_model_delta,
load/save_model_lineup, and run_refresh are UNCHANGED — the fix is
localized to the one extraction function plus a private table-row helper.

ACs: AC.CLP-MDLR.1 ★ outcome-altitude (production extract on the REAL
committed snapshot detects claude-fable-5 + claude-opus-4-8 +
claude-sonnet-5 + claude-haiku-4-5-20251001 regardless of backticks),
AC.CLP-MDLR.2 (no phantom delta across a pure backtick->plain formatting
change, through production run_refresh), AC.CLP-MDLR.3 (a genuinely
removed model is still named in model_delta.removed — the real signal
survives), AC.CLP-MDLR.4 (no over-capture: incidental-prose / Bedrock /
Google-Cloud IDs excluded), AC.CLP-MDLR.5 (prose-only backticked model
preserved — no false removal). Existing AC.CLP-MDL.1-4 stay green (the
union is a strict superset of old behavior on those fixtures).

Fence: capability-refresh (source + tests only). The committed lineup
JSON is intentionally NOT hand-edited (runtime machine state with a
run_ts stamp); the next real refresh recomputes it and emits a one-time
TRUE "added" delta for the previously-hidden live models.

Predecessor: a1166b8d (memory-redesign S4 STATE change-log backfill).

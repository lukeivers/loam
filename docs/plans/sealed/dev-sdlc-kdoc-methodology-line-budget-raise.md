# dev-sdlc — methodology-spec line-budget raise (KDOC 360 -> 380) — apply ladder

Per docs/plans/dev-sdlc-kdoc-methodology-line-budget-raise.md.

The v1.11.0 recall-volume reshape (AC.RVL.8) adds a required cap-bias
checklist (§7.6 + reviewer item 15) to plugins/dev-sdlc/docs/odd-methodology.md,
growing it 360 -> 373 lines. dev-sdlc's test_AC_KDOC_1 asserted the doc
<= 360 lines (a keel-adoption leanness guard). The two sealed constraints
collide. Per feedback_loose_AC_text_fix_AC_not_implementation the numeric
bound is the too-tight AC, not the content: raise it 360 -> 380 (the sole
dependent on the number), credit the AC.RVL.8 §7.6 checklist in a comment,
and add AC.MSLB.1's own test so the raise is ODD §2.5-traceable. No
production source changes; odd-methodology.md itself is unchanged by this
amendment. F-SEAL-PLUGINS-TESTS-SKIPPED: dev-sdlc suite run manually pre-seal.

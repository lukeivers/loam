# frame-kernel — SubagentStart envelope cwd-fallback

Single-purpose corrective to slice 1a's envelope contract. Sealed
local; rides the next release after v1.4.0 (publish owner-gated).

THE BUG (Tier-0, pos3 watched activation, 2026-06-10):
`bundle.py::parse_envelope` resolved workspace_root ONLY from
`envelope["workspace"]["project_dir"]`. Real Claude Code
SubagentStart envelopes carry the standard hook common-input `cwd`
field, not that shape. Result: on every REAL dispatch
workspace_root=None and ALL THREE bundle tiers (microkernel /
workstream / memory) degraded to structured placeholders — verified
by a probe agent reading its own injected context (marker present,
all tiers `[... unavailable ...]`), while a synthetic
workspace.project_dir envelope produced the full 6.3KB bundle. The
injection plumbing + AC.SACH.4 fail-soft contracts worked exactly
as sealed; the envelope contract was wrong.

THE FIX: parse_envelope gains the cwd fallback — priority order
`workspace.project_dir` when present, else `cwd` — mirroring the
pattern slice 1b already shipped in-fence at
`frame_judge.py` (workspace-root resolution with the cwd
common-input fallback). 1a and 1b now agree on the envelope
contract.

AC.EWR.1 — an envelope carrying ONLY `cwd` (the real observed
shape) resolves workspace_root; the composed bundle is identical to
the project_dir-envelope bundle for the same root; a both-present
envelope prefers workspace.project_dir.

AC.EWR.S (outcome-altitude) — the REAL envelope shape (cwd-only)
driven end-to-end through the production hook entry-point
(`subagent_start_context.py` subprocess, the AC.SACH.S pattern)
yields an injected additionalContext whose microkernel tier is
NON-degraded against the real on-disk `kernel/loam-microkernel.md`.
This is the regression test the original AC.SACH.S probe missed —
that probe's synthetic envelope used the project_dir shape, which
is why the contract gap shipped unobserved.

Unchanged: fail-soft exit-0 (AC.SACH.4) — an envelope with NEITHER
field still degrades exactly as before; task-text handling;
frame_judge.py; the hook script; all existing AC.SACH.* /
AC.DMP.* / AC.SSFC.* tests pass untouched.

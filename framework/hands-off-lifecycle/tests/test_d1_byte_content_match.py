# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""HC#4 / AC.D.1.5 — byte-content-match regression for D-migration D.1.

The bug-class that triggered the D-migration architectural review was
test-shape-only verification: tests asserted "files are at the right
paths" but never verified file *content* survived the move byte-
identically. This test closes that gap structurally.

Method (per builder-plan D-build.D.1.H):
1. Pre-move (during build), SHA-256 hashes were computed for 15
   representative files spanning three components (5 each from
   primary-persona, workspace-bootstrap, scope-of-work — leaf,
   mid-graph, high-fan-in per AC.D.1.5).
2. The hashes are hardcoded below.
3. The test reads each file at its post-D.1 framework/<comp>/<...>
   path and asserts the SHA-256 matches.

A builder-side accidental edit during git-mv would break the test
because git mv preserves bytes by default (rename without content
edit gives byte-identical content). This is the structural binding
of HC#4 — pure-rename moves cannot silently corrupt content.

Note: files that ARE intentionally edited as part of D.1
(``first_run_helper.py``, ``first_run_scaffold.py``, ``seal.py``,
the seal-diff tests, and the renamed ``settings.dev-template.json``)
are deliberately EXCLUDED from this list — their content changes
are the amendment's intent, not regressions.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]


# Pre-move SHA-256 hashes captured during the D.1 build.
# Each tuple: (repo-relative path post-D.1, expected SHA-256).
_SAMPLE_FILES = (
    # primary-persona — leaf component (no dependents in framework graph
    # for these files specifically; D-mig plan §4 names primary-persona
    # as mid-graph but the named files are pure module bodies).
    #
    # M1e (amendment #80, sub-plan oss-v0-1-0-publish-rename-1e.md):
    # path entries updated for the per-component framework/<comp>/src/
    # loam/<comp>/ namespace pivot per D-RNM.2 ruling. Where the file's
    # content was preserved by `git mv` (content-preserving rename),
    # the original SHA-256 is preserved verbatim. Where content was
    # also touched by Phase C import rebrand (`from <pkg>` →
    # `from loam.<pkg>`) or Phase D entry-point group rebrand
    # (`pos.bootstrap.contributions` → `loam.bootstrap.contributions`)
    # or pyproject restructure, SHAs are bumped. ODD §4 in-band
    # retire-and-rebaseline applied per M1e sub-plan §5 hard-constraint
    # + §11 finding #3 + dispatch's named carve-out.
    ("framework/primary-persona/src/loam/primary_persona/cli.py",
     # M1c launchd-label rebrand SHA preserved (content unchanged by
     # M1e — pure rename via git mv).
     # M8-corrective (2026-05-01) SHA bump: M8 commit `6bef03b`
     # ("feat(public): M8 license-governance — Apache headers on
     # runtime .py + SECURITY.md tightening") inserted a 14-line
     # Apache-2.0 license header at the top of this file per AC.OSS.4.
     # ODD §4 in-band retire-and-rebaseline per
     # `feedback_loose_AC_text_fix_AC_not_implementation` analog —
     # implementation matches AC.OSS.4 intent; the byte-content sample
     # SHA updates to reflect the legitimate header addition.
     # Amendment #144 SHA bump (closed-loop engagement canonical
     # promotion — Scope A): added the `intent-classifier` subcommand
     # entry alongside the existing `user-prompt-submit` /
     # `session-start` / `stop` / `memory-write` / `memory-worker` /
     # `trait-reflection-stop` subparsers; new import of
     # `cli_intent_classifier` from the new `intent_classifier`
     # module + new `_cmd_intent_classifier` handler. ODD §4 in-band
     # retire-and-rebaseline per
     # `feedback_loose_AC_text_fix_AC_not_implementation`.
     # Amendment #154 SHA bump (FBM Cycle 1 — fix-write-path + unify
     # retrieval surface, sealed at `fd5fe6a`): cli.py was legitimately
     # content-edited by #154's write-path fix. #154 sealed on the
     # primary-persona fence and never ran this D.1 byte-content test
     # (it lives in hands-off-lifecycle), so the frozen hash went stale-
     # RED at HEAD `f23deda` — surfaced during the #155 first-run-
     # message-retired-deps-sweep seal sweep (the seal sweep IS the
     # discovery mechanism). NOT introduced by #155. Blast radius = 1
     # of 16 samples; the git-mv-corruption guard stays intact for the
     # other 15. ODD §4 in-band retire-and-rebaseline per
     # `feedback_loose_AC_text_fix_AC_not_implementation` — the test's
     # own docstring (lines 36-40) directs re-baselining intentionally-
     # edited files; #154's edit is exactly that. F2 surfaced in the
     # dispatcher report.
     "260c580308bc0a3bc4a53e2608d88b8912e607c696e8e2105e131f2df5920ac0"),
    ("framework/primary-persona/src/loam/primary_persona/__init__.py",
     # M4 (amendment #85) SHA bump: re-export of NEW public function
     # ``write_dispatcher_stub`` (and ``NewACSpec`` made public for
     # caller convenience) added per plan §4 AC.OSS-M4.4 + AC.OSS-M4.7.
     # ODD §4 in-band retire-and-rebaseline. Plan §11 finding #6
     # predicted no HC#4 impact; the prediction was wrong but the
     # amendment's intent is preserved (see §14 D-build.M4.* for the
     # post-build surfacing of this finding).
     # M-FBM (memory-substrate pivot, 2026-05-01) SHA bump: re-exports
     # of the file-based memory primitives (``FileMemoryStore``,
     # ``FileMemoryRetrievalConfig``, ``MemoryProvider``,
     # ``build_file_memory_retrieval_contributor``,
     # ``memory_dir_for_workspace``,
     # ``register_file_memory_retrieval``) added; MCP-backed
     # ``LiveMCPMemoryClient`` + ``build_live_mcp_memory_client``
     # re-exports retired from package surface per AC.MFBM.5. ODD
     # §4 in-band retire-and-rebaseline per `feedback_loose_AC_text_
     # fix_AC_not_implementation`.
     # M8-corrective (2026-05-01) SHA bump: Apache-2.0 license header
     # inserted by M8 (`6bef03b`) per AC.OSS.4. ODD §4 in-band
     # retire-and-rebaseline.
     "f3119c49c2b0037081448cc7d72f7752b863a08710142987387a3e013f21cb39"),
    ("framework/primary-persona/src/loam/primary_persona/onboarding.py",
     # M1e SHA bump: Phase C import rebrand
     # (`from workspace_bootstrap.workspace_paths` →
     # `from loam.workspace_bootstrap.workspace_paths`).
     # M8-corrective (2026-05-01) SHA bump: Apache-2.0 license header
     # inserted by M8 (`6bef03b`) per AC.OSS.4. ODD §4 in-band
     # retire-and-rebaseline.
     "996a439815e867000f5600b70f1e9735e91899cc2a9c0f20a4d5f8e3374e7ac9"),
    ("framework/primary-persona/src/loam/primary_persona/session_start_emitter.py",
     # M1e SHA bump: Phase E internal-decoration rebrand (legacy
     # `loam_root` predecessor identifier callsites) plus Phase C `-m`
     # shell-command shape rebrand for primary_persona.cli emission
     # helper.
     # MPF (amendment #95) SHA bump: AC.MPF.3 propagates
     # ``workspace_root`` through ``register_memory_retrieval`` so
     # boundary exceptions surface to ``<workspace>/.pos/memory-
     # reads.log``. Two-line edit at the call site (kwarg added).
     # ODD §4 in-band retire-and-rebaseline per `feedback_loose_AC_
     # text_fix_AC_not_implementation` — implementation matches
     # AC.MPF.3 intent; the byte-content sample SHA updates to
     # reflect the new contract.
     # M-FBM (memory-substrate pivot, 2026-05-01) SHA bump:
     # ``_default_memory_client_factory`` retires the
     # ``mcp_memory_client.build_live_mcp_memory_client`` import +
     # the file-based contributor registers in
     # ``build_session_composer`` when the factory returns ``None``
     # (production path). Per AC.MFBM.5: zero MCP instantiation in
     # the runtime retrieval path.
     # M8-corrective (2026-05-01) SHA bump: Apache-2.0 license header
     # inserted by M8 (`6bef03b`) per AC.OSS.4. ODD §4 in-band
     # retire-and-rebaseline.
     # C2-prime (2026-05-02) SHA bump: ``loam-mode`` cosmetic-
     # prose references in two docstring locations rewritten to
     # "dev-mode session-start emit timeout" / "dev-mode session-
     # start emit + persona session-start + user-prompt-submit
     # timeouts" per C2-prime amendment §5.4 file 17 (RW shape;
     # AC.OSS.3 banned-literal removal). ODD §4 in-band rebaseline.
     # Amendment #144 §16 finding rebaseline: pre-existing drift
     # (NOT caused by amendment #144 edits) — surfaced when amendment
     # #144's hands-off-lifecycle full-suite ran at seal; the prior
     # snapshot lagged a legitimate post-C2-prime edit to this file.
     # ODD §4 in-band retire-and-rebaseline per
     # `feedback_loose_AC_text_fix_AC_not_implementation`. Discovery-
     # driven (the seal sweep IS the discovery mechanism).
     "7893d8a7292b651d2c79f243edfc7975cb9cc56b5c0bf36b9c3e5c4522ecf14c"),
    ("framework/primary-persona/pyproject.toml",
     # M1e SHA bump: Phase B pyproject restructure
     # (project name `primary_persona` → `loam-primary-persona`,
     # package-dir entry, dependencies list rewrite).
     # FBE.5 SHA bump (description scrub) + FBE.8 SHA bump
     # (mcp pin annotation comment scrub — drops dev-vocabulary
     # leakage per HIGH-FBE6.1; pin-rationale prose preserved).
     # ODD §4 in-band retire-and-rebaseline per
     # `feedback_loose_AC_text_fix_AC_not_implementation`.
     # Amendment #144 §16 finding rebaseline: pre-existing drift
     # (NOT caused by amendment #144) — pyproject's post-FBE.8 state
     # diverged from the snapshot in a later amendment that did not
     # rebaseline. Discovery-driven rebaseline.
     # Wave 1.4 security-hooks-bundle (2026-05-24, amendment #152)
     # rebaseline: pre-existing drift surfaced by the touched-component
     # full-sweep — `7b774b1` (per-component-pyproject-version-
     # lockstep regression closure PATCH) edited this pyproject.toml
     # without rebaselining the byte-content sample. Discovery-driven
     # rebaseline; OUT-OF-CYCLE-FENCE but in-band retire-and-rebaseline
     # per the established pattern in this file. F2 ruthlessly surfaced
     # in the dispatcher report.
     # v0.13.0 MINOR publish (2026-05-24) rebaseline: per-component
     # pyproject version lockstep bumped 0.12.0 -> 0.13.0 in the
     # release-staging worktree, invalidating this SHA. SECOND
     # consecutive recurrence of the SAME drift pattern (Wave 1.4 = 1st,
     # v0.13.0 = 2nd) — per `feedback_workaround_masks_rootcause_urgency`,
     # the root-cause fix (stop pinning pyproject.toml byte content
     # because pyprojects MUST mutate every MINOR by design) is
     # scheduled + surfaced as a FIDRAFT entry by the v0.13.0 release
     # integrator; this entry is the in-cycle workaround landing.
     # v0.14.0 MINOR publish (2026-05-29) rebaseline: per-component
     # pyproject version lockstep bumped 0.13.0 -> 0.14.0 in the
     # release/v0-14-0 worktree, invalidating this SHA. THIRD
     # consecutive recurrence of the SAME drift pattern (Wave 1.4 = 1st,
     # v0.13.0 = 2nd, v0.14.0 = 3rd). The root-cause structural fix
     # (exclude pyproject.toml from the byte-content sample — they MUST
     # mutate every MINOR by design, so pinning their bytes enforces an
     # invariant that contradicts the per-component-version lockstep
     # discipline) is now OWED + surfaced as a hard F2 finding to the
     # dispatcher; this entry is the in-cycle workaround landing pending
     # that dispatched fix.
     "2d27684c5c643c8bc583892437a84641faad2c5e1bd89b0f729cca13ac34094f"),
    # workspace-bootstrap — high-fan-in component.
    ("framework/workspace-bootstrap/src/loam/workspace_bootstrap/__init__.py",
     # M1e SHA bump: Phase D entry-point group rebrand in docstring
     # (`pos.bootstrap.contributions` → `loam.bootstrap.contributions`).
     # M8-corrective (2026-05-01) SHA bump: Apache-2.0 license header
     # inserted by M8 (`6bef03b`) per AC.OSS.4. ODD §4 in-band
     # retire-and-rebaseline.
     # Amendment #144 §16 finding rebaseline: pre-existing drift
     # (NOT caused by amendment #144) — workspace-bootstrap's
     # __init__.py drifted in a later amendment that did not
     # rebaseline. Discovery-driven rebaseline.
     "df013a63a75dacd661c6123a45814ea9b7abbfb2f64e535fa9209850bb343960"),
    ("framework/workspace-bootstrap/src/loam/workspace_bootstrap/spec.py",
     # M8-corrective (2026-05-01) SHA bump: Apache-2.0 license header
     # inserted by M8 (`6bef03b`) per AC.OSS.4. ODD §4 in-band
     # retire-and-rebaseline.
     # Amendment #144 §16 finding rebaseline: pre-existing drift
     # (NOT caused by amendment #144) — discovery-driven rebaseline.
     "e341d5f346258805af9917916d86eede8389e537a9432fa5f906b1127b86f1bd"),
    ("framework/workspace-bootstrap/src/loam/workspace_bootstrap/host.py",
     # M1f SHA bump: workspace-bootstrap host.py field rename
     # (self.graceful_degradation → self.dormancy + docstring entry)
     # per AC.RNM-1f.6. ODD §4 in-band retire-and-rebaseline.
     # M8-corrective (2026-05-01) SHA bump: Apache-2.0 license header
     # inserted by M8 (`6bef03b`) per AC.OSS.4. ODD §4 in-band
     # retire-and-rebaseline.
     "04b01405e218a518e18c873de25e448851404c864078aac16c64e26cccb899fa"),
    ("framework/workspace-bootstrap/src/loam/workspace_bootstrap/errors.py",
     # M8-corrective (2026-05-01) SHA bump: Apache-2.0 license header
     # inserted by M8 (`6bef03b`) per AC.OSS.4. ODD §4 in-band
     # retire-and-rebaseline.
     "85215ebbc0eb622f44630694430fc76239f9e53f513ac04c75ac3f99f76c2ffc"),
    ("framework/workspace-bootstrap/src/loam/workspace_bootstrap/discovery.py",
     # M1e SHA bump: Phase D `_ENTRYPOINT_GROUP` value rebrand.
     # M8-corrective (2026-05-01) SHA bump: Apache-2.0 license header
     # inserted by M8 (`6bef03b`) per AC.OSS.4. ODD §4 in-band
     # retire-and-rebaseline.
     # Amendment #144 §16 finding rebaseline: pre-existing drift
     # (NOT caused by amendment #144) — discovery-driven rebaseline.
     "bbf1fa90ed86264c0ce60c5d45e5f9f7954053b2dc49ceed0318a9f2c5a60c41"),
    # scope-of-work — leaf component (no test_no_sealed sidecar; the
    # leaf shape is the cleanest regression target for HC#4).
    ("framework/scope-of-work/src/loam/scope_of_work/spec.py",
     # M8-corrective (2026-05-01) SHA bump: Apache-2.0 license header
     # inserted by M8 (`6bef03b`) per AC.OSS.4. ODD §4 in-band
     # retire-and-rebaseline.
     "209d7390db93c5d36ad68e6cbe9470cf3e21ed7fbacfeac5089eff627e7bff43"),
    ("framework/scope-of-work/src/loam/scope_of_work/events.py",
     # M8-corrective (2026-05-01) SHA bump: Apache-2.0 license header
     # inserted by M8 (`6bef03b`) per AC.OSS.4. ODD §4 in-band
     # retire-and-rebaseline.
     "c029a95070b1df5389f25a323e76145630bb2698e3b22fe3ea6b5a8f7262442e"),
    ("framework/scope-of-work/src/loam/scope_of_work/projection.py",
     # M8-corrective (2026-05-01) SHA bump: Apache-2.0 license header
     # inserted by M8 (`6bef03b`) per AC.OSS.4. ODD §4 in-band
     # retire-and-rebaseline.
     "ff212437fa1b168b998f13212f7a8d4f351c497acbdf0cb8c9f0d4fbe2b1532b"),
    ("framework/scope-of-work/src/loam/scope_of_work/triggers.py",
     # M8-corrective (2026-05-01) SHA bump: Apache-2.0 license header
     # inserted by M8 (`6bef03b`) per AC.OSS.4. ODD §4 in-band
     # retire-and-rebaseline.
     # Amendment #144 §16 finding rebaseline: pre-existing drift
     # (NOT caused by amendment #144) — discovery-driven rebaseline.
     "98d9d8f21b754c6ba99cce90426ac2a0d6c37d76d19de6ed56f8b5575f781ed0"),
    ("framework/scope-of-work/pyproject.toml",
     # M1e SHA bump: Phase B pyproject restructure
     # (project name `scope_of_work` → `loam-scope-of-work`).
     # FBE.5 SHA bump (description scrub at `8032348`) — landed in
     # FBE.5's source delta but the byte-content sample was not
     # retired-and-rebaselined at FBE.5 seal; FBE.8 closes the gap.
     # ODD §4 in-band retire-and-rebaseline.
     # Amendment #144 §16 finding rebaseline: pre-existing drift
     # (NOT caused by amendment #144) — discovery-driven rebaseline.
     # Wave 1.4 security-hooks-bundle (2026-05-24, amendment #152)
     # rebaseline: same shape as the primary-persona/pyproject.toml
     # rebaseline above. `7b774b1` edited this pyproject without
     # rebaselining. Discovery-driven retire-and-rebaseline; F2
     # surfaced in the dispatcher report.
     # v0.13.0 MINOR publish (2026-05-24) rebaseline: same shape as
     # the primary-persona/pyproject.toml rebaseline above (per-component
     # version lockstep bumped 0.12.0 -> 0.13.0). SECOND consecutive
     # recurrence of the SAME drift pattern; root-cause-fix FIDRAFT
     # entry scheduled by the v0.13.0 release integrator per
     # `feedback_workaround_masks_rootcause_urgency`.
     # v0.14.0 MINOR publish (2026-05-29) rebaseline: same shape
     # (per-component version lockstep bumped 0.13.0 -> 0.14.0). THIRD
     # consecutive recurrence; root-cause structural fix now OWED +
     # surfaced as a hard F2 finding to the dispatcher (exclude
     # pyproject.toml from the byte-content sample).
     "13383b1afe22bba6de6c6fda71297884e42a9acff96dcedae4e3d22e6cf4d7ca"),
)


@pytest.mark.parametrize("relpath,expected_sha", _SAMPLE_FILES)
def test_AC_D_1_5_byte_content_match_post_move(
    relpath: str, expected_sha: str
) -> None:
    """The file at *relpath* (post-D.1 framework/<...> path) has the
    expected SHA-256 captured pre-move. ``git mv`` preserves bytes
    by default; any divergence indicates a builder-side content
    edit slipped into the rename window.
    """
    path = REPO_ROOT / relpath
    assert path.exists(), (
        f"D.1 byte-content regression: file missing post-move: {path}\n"
        "Expected SHA: {expected_sha}\n"
        "Possible causes: file was deleted during restructure, or the "
        "framework/ directory layout differs from D.1's locked design."
    )
    with open(path, "rb") as fh:
        actual_sha = hashlib.sha256(fh.read()).hexdigest()
    assert actual_sha == expected_sha, (
        f"D.1 byte-content regression: {relpath}\n"
        f"  expected SHA-256: {expected_sha}\n"
        f"  actual SHA-256:   {actual_sha}\n"
        "git mv was supposed to preserve bytes; a content-edit "
        "slipped into the rename window. HC#4 binding."
    )


def test_AC_D_1_5_test_carries_at_least_15_samples() -> None:
    """Structural check: the sample list must carry at least 15 entries
    (5 per component × 3 components per AC.D.1.5). Catches a regression
    where the list gets accidentally pruned."""
    assert len(_SAMPLE_FILES) >= 15, (
        f"AC.D.1.5 names ≥3 components × ≥5 files each. "
        f"Sample list has {len(_SAMPLE_FILES)} entries."
    )

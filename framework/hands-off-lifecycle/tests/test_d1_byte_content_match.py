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

"""HC#4 / AC.D.1.5 — module-survival regression for the D-migration D.1.

The bug-class that triggered the D-migration architectural review was
test-shape-only verification: tests asserted "files are at the right paths"
but never verified file *content* survived the move. This test closes that
gap for a representative sample spanning three components (5 each from
primary-persona, workspace-bootstrap, scope-of-work — leaf, mid-graph,
high-fan-in per AC.D.1.5).

Converted, amendment #197 / AC.BVG.2 (2026-07-09, Class E of the 2026-07-08
release-seal near-miss audit). The original guard pinned a whole-file SHA-256
per sample. That was a brittle exact-value pin: ``git mv`` preserves bytes,
but every LEGITIMATE later edit — an Apache license header, an import rebrand,
a new re-export, an added kwarg — changed the bytes and forced a manual
"rebaseline the hash to match reality" every cycle (STATE.md logs 6+ such
recurrences with "root-cause fix OWED"; the pyproject sub-instance was already
root-caused 2026-06-11). A whole-file hash cannot tell a git-mv corruption from
a legitimate edit, so as a corruption guard it was already toothless — each
rebaseline blessed whatever the current bytes were.

The intent — "the moved file survived as the right, uncorrupted module" — is
now asserted structurally, following the proven STATE.md L143 "stable
module-body replacements" pattern: each sample must (1) still exist, (2) parse
as valid Python (``ast.parse`` — catches truncation / mangling / a rename
window that corrupted the file), and (3) carry its expected stable public
top-level surface (the module's characteristic def / class / re-export names —
catches a wrong-file swap or a public-surface deletion). This survives
legitimate edits (headers, kwargs, new re-exports) and REDs on the corruption
the guard exists to catch.

Honest limit (D-EG.SIGLIMIT): the surface signature does NOT catch a surgical
edit buried inside a function body that leaves the public surface intact — the
same residual as the STATE.md L143 fix it follows. Behavioral regressions in a
module body are caught by that module's own tests, not by this migration guard.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]


def _module_surface(src: str) -> set[str]:
    """The module's public top-level surface: names of top-level functions,
    classes, ``from x import`` aliases, plain ``import`` bindings, and
    module-level ``NAME = ...`` assignments. Raises ``SyntaxError`` if *src*
    is not valid Python (the truncation / corruption signal)."""
    tree = ast.parse(src)
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
    return names


def _module_survived(src: str, expected: tuple[str, ...]) -> bool:
    """True iff *src* is valid Python whose public top-level surface contains
    every name in *expected*. False on a SyntaxError (truncation / corruption)
    or a missing expected symbol (wrong-file swap / surface deletion)."""
    try:
        surface = _module_surface(src)
    except SyntaxError:
        return False
    return set(expected).issubset(surface)


# Each tuple: (repo-relative path post-D.1, expected stable public surface).
# The expected surface is a small set of characteristic top-level names per
# file. Code modules use their def/class names; the two ``__init__.py``
# re-export modules use their re-exported public aliases.
_SAMPLE_FILES: tuple[tuple[str, tuple[str, ...]], ...] = (
    # primary-persona — 5 samples.
    (
        "framework/primary-persona/src/loam/primary_persona/cli.py",
        ("_cmd_session_start", "_cmd_stop", "_cmd_memory_write"),
    ),
    (
        "framework/primary-persona/src/loam/primary_persona/__init__.py",
        ("PersonaContract", "PersonaTier", "load_contract", "PersonaLoader"),
    ),
    (
        "framework/primary-persona/src/loam/primary_persona/onboarding.py",
        (
            "OnboardingGroundingError",
            "GroundingCapture",
            "build_starter_pending_contributor",
            "persist_grounding",
        ),
    ),
    (
        "framework/primary-persona/src/loam/primary_persona/session_start_emitter.py",
        (
            "build_session_composer",
            "emit_session_start_context",
            "emit_user_prompt_submit_context",
        ),
    ),
    (
        "framework/primary-persona/src/loam/primary_persona/contract.py",
        (
            "PersonaContract",
            "PersonaTier",
            "EscalationTaxonomy",
            "AuthorityBoundary",
        ),
    ),
    # workspace-bootstrap — 5 samples (high-fan-in component).
    (
        "framework/workspace-bootstrap/src/loam/workspace_bootstrap/__init__.py",
        ("read_metadata", "resolve_ref", "BootstrapError", "ContributionNotFoundError"),
    ),
    (
        "framework/workspace-bootstrap/src/loam/workspace_bootstrap/spec.py",
        ("Contribution", "BaseContribution", "BootstrapHostProtocol", "Phase"),
    ),
    (
        "framework/workspace-bootstrap/src/loam/workspace_bootstrap/host.py",
        ("BootstrapHost", "HostAttributeNotYetAvailable"),
    ),
    (
        "framework/workspace-bootstrap/src/loam/workspace_bootstrap/errors.py",
        (
            "BootstrapError",
            "MissingConfigError",
            "NameCollisionError",
            "UnknownReferenceError",
        ),
    ),
    (
        "framework/workspace-bootstrap/src/loam/workspace_bootstrap/discovery.py",
        ("resolve_ref", "read_metadata"),
    ),
    # scope-of-work — 5 samples (leaf component).
    (
        "framework/scope-of-work/src/loam/scope_of_work/store.py",
        ("EventStore", "AppendedEvent", "rehydrate_events"),
    ),
    (
        "framework/scope-of-work/src/loam/scope_of_work/spec.py",
        ("ScopeState", "Budget", "SuccessCriterion", "Observer"),
    ),
    (
        "framework/scope-of-work/src/loam/scope_of_work/events.py",
        ("ScopeCreated", "StateTransitioned", "BudgetDebited", "ObserverAdded"),
    ),
    (
        "framework/scope-of-work/src/loam/scope_of_work/projection.py",
        ("apply_event", "project", "BudgetLedger"),
    ),
    (
        "framework/scope-of-work/src/loam/scope_of_work/triggers.py",
        ("evaluate_trigger", "is_stuck", "remaining_for_axis"),
    ),
)


@pytest.mark.parametrize(
    "relpath,expected", _SAMPLE_FILES, ids=[s[0] for s in _SAMPLE_FILES]
)
def test_AC_D_1_5_module_surface_survived_move(
    relpath: str, expected: tuple[str, ...]
) -> None:
    """The file at *relpath* (post-D.1 framework/<...> path) survived the move
    as a valid, correctly-surfaced module: it exists, parses as Python, and
    carries its expected stable public top-level surface. Catches a rename
    window that deleted / truncated / corrupted / swapped the file; tolerates
    legitimate later edits (license headers, kwargs, new re-exports)."""
    path = REPO_ROOT / relpath
    assert path.exists(), (
        f"D.1 module-survival regression: file missing post-move: {path}\n"
        f"Expected surface: {expected}\n"
        "Possible causes: file deleted during restructure, or the framework/ "
        "layout differs from D.1's locked design."
    )
    src = path.read_text(encoding="utf-8")
    assert _module_survived(src, expected), (
        f"D.1 module-survival regression: {relpath}\n"
        f"  expected public surface (subset): {expected}\n"
        f"  actual public surface: {sorted(_module_surface(src)) if _valid(src) else 'INVALID PYTHON (parse failed)'}\n"
        "The moved file is not valid Python or lost its expected public "
        "surface — a corruption / wrong-file swap slipped into the move window. "
        "HC#4 binding."
    )


def _valid(src: str) -> bool:
    try:
        ast.parse(src)
        return True
    except SyntaxError:
        return False


def test_AC_D_1_5_test_carries_at_least_15_samples() -> None:
    """Structural check: the sample list must carry at least 15 entries
    (5 per component × 3 components per AC.D.1.5). Catches a regression
    where the list gets accidentally pruned."""
    assert len(_SAMPLE_FILES) >= 15, (
        f"AC.D.1.5 names ≥3 components × ≥5 files each. "
        f"Sample list has {len(_SAMPLE_FILES)} entries."
    )


# --- AC.BVG.S — outcome-altitude for the byte-hash conversion ---------------
# outcome-altitude: true. Exercises the converted signature check on real-shaped
# inputs with no pre-set state: a legitimately-edited module that must PASS and
# corrupted / wrong-surface modules that must RED. This is the proof the guard
# now tracks its intent (the file survived as the right module) rather than a
# whole-file byte hash that fired on every legitimate edit.

_FIXTURE_EXPECTED = (
    "PersonaContract",
    "PersonaTier",
    "EscalationTaxonomy",
    "AuthorityBoundary",
)
_LICENSE_HEADER = (
    "# Copyright 2026 Luke Ivers and contributors\n"
    "# Licensed under the Apache License, Version 2.0\n"
)


def _fixture_base_src() -> str:
    return (
        REPO_ROOT
        / "framework/primary-persona/src/loam/primary_persona/contract.py"
    ).read_text(encoding="utf-8")


def test_AC_BVG_S_signature_passes_legitimate_edit() -> None:
    """A legitimately-edited module — real source + an inserted Apache license
    header + an appended top-level helper (the exact edit shapes that forced
    past rebaselines) — PASSES the converted signature check. The old whole-file
    hash would have false-RED'd here."""
    edited = _LICENSE_HEADER + _fixture_base_src() + "\n\ndef _new_helper(x, *, flag=False):\n    return x\n"
    assert _module_survived(edited, _FIXTURE_EXPECTED)


def test_AC_BVG_S_signature_reds_on_corruption() -> None:
    """A corrupted (truncated mid-statement → invalid Python) module and a
    valid-but-wrong-surface module both RED the converted signature check —
    the corruption the guard exists to catch."""
    truncated = "class PersonaContract:\n    def __init__(self, "  # syntactically broken
    assert not _module_survived(truncated, _FIXTURE_EXPECTED)
    wrong_surface = "x = 1\n"  # parses, but none of the expected symbols
    assert not _module_survived(wrong_surface, _FIXTURE_EXPECTED)

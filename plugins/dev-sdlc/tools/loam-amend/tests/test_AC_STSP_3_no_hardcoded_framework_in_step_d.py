"""AC.STSP.3 — step (d) in ``_finalize`` derives its pytest target
purely from the manifest's ``seal_test:`` field; no hardcoded
``framework/`` prefix appears in the step (d) body.

Per plan-doc ``amendment-138-loam-amend-seal-tool-hygiene-pair.md``
§4 (Scope A: F-SEAL-PLUGINS-TESTS-SKIPPED).

Source-level verification — the regression-guard against re-
introducing the hardcoded path. AC.STSP.1 + AC.STSP.2 verify the
positive behavior; AC.STSP.3 prevents drift.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

from loam_amend.commands import seal as seal_mod


def _step_d_source() -> str:
    """Return the source of ``_finalize`` step (d) — the touched-
    component pytest loop. The plan-doc names this as the lone
    site where the hardcoded path must be gone."""
    src = inspect.getsource(seal_mod._finalize)
    # Step (d) is the loop iterating manifest.components that calls
    # _run_pytest with the per-component tests target. Locate it by
    # the "# (d)" comment marker.
    match = re.search(
        r"# \(d\).*?(?=# \(e\)|\Z)",
        src,
        flags=re.DOTALL,
    )
    assert match is not None, (
        "step (d) marker not found in _finalize source; the source "
        "marker convention used by AC.STSP.3 may have drifted"
    )
    return match.group(0)


def test_AC_STSP_3_step_d_has_no_hardcoded_framework_path():
    """The step (d) body must contain no literal ``"framework"`` token
    inside a path-building expression. The schema-driven
    ``Path(seal_test).parent`` shape is the canonical resolution."""
    step_d = _step_d_source()
    # The descriptive comment above step (d) intentionally references
    # ``framework/<comp>/tests/`` to explain what the OLD code did;
    # we strip comments before searching.
    code_only_lines = [
        line for line in step_d.splitlines()
        if not line.lstrip().startswith("#")
    ]
    code_only = "\n".join(code_only_lines)
    assert '"framework"' not in code_only, (
        f"step (d) must not carry a hardcoded \"framework\" path token; "
        f"step (d) code-only body:\n{code_only}"
    )
    assert "framework/" not in code_only, (
        f"step (d) must not carry a hardcoded \"framework/\" path "
        f"prefix; step (d) code-only body:\n{code_only}"
    )


def test_AC_STSP_3_step_d_reads_seal_test_from_manifest():
    """The step (d) body must reference ``comp.seal_test`` (the
    schema-driven manifest field). Affirmatively-shaped check —
    AC.STSP.3 is about ``no hardcoded path``; AC.STSP.1 + AC.STSP.2
    verify the positive behavior end-to-end; this assertion guards
    the source-shape invariant the mechanism relies on."""
    step_d = _step_d_source()
    assert "comp.seal_test" in step_d, (
        f"step (d) must reference ``comp.seal_test`` (the schema-"
        f"driven canonical lookup); step (d) body:\n{step_d}"
    )

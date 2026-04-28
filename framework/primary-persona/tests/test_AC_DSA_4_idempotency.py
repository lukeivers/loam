"""AC.DSA.4 — idempotency.

For each artefact (sentinel, manifest row, stub file), repeated
dispatcher invocations with the same dispatch shape do not corrupt
existing on-disk content. Specifically: a re-dispatch with the same
``new_acs`` finds existing artefacts and either no-ops on byte-equal
content (sentinel, stub) or no-ops on duplicate row (manifest). When
a stub file already contains a function whose body is NOT the
dispatcher's skip-with-reason (i.e., the build agent already authored
the real test), the dispatcher does NOT overwrite — it logs a
structured diagnostic and proceeds.
"""

from __future__ import annotations

from pathlib import Path

from primary_persona.dispatch_wrapper import NewACSpec
from primary_persona.dispatch_wrapper import (
    _is_dispatcher_authored_stub,
    _render_stub_body,
    _write_stub_idempotent,
)


def _spec(component="c", ac_id="AC.X.1", glob="framework/c/src/y.py"):
    return NewACSpec(
        component=component, ac_id=ac_id, source_path_glob=glob
    )


def test_AC_DSA_4_first_write_outcome_written(tmp_path) -> None:
    """The first write authors the file fresh; outcome is 'written'."""
    spec = _spec()
    out = _write_stub_idempotent(
        tmp_path, spec, scope_id="s1", plan_path="p1"
    )
    assert out["outcome"] == "written"
    p = Path(out["path"])
    assert p.exists()


def test_AC_DSA_4_second_write_byte_equal_skips(tmp_path) -> None:
    """Re-invocation with identical scope_id / plan_path returns
    'skipped-identical' and leaves the file unchanged."""
    spec = _spec()
    out1 = _write_stub_idempotent(
        tmp_path, spec, scope_id="s1", plan_path="p1"
    )
    p = Path(out1["path"])
    mtime_before = p.stat().st_mtime_ns
    out2 = _write_stub_idempotent(
        tmp_path, spec, scope_id="s1", plan_path="p1"
    )
    assert out2["outcome"] == "skipped-identical"
    assert p.stat().st_mtime_ns == mtime_before


def test_AC_DSA_4_re_dispatch_with_drift_skips_existing_dispatcher_stub(
    tmp_path,
) -> None:
    """A re-dispatch with a different scope_id / plan_path doesn't
    overwrite the dispatcher's existing stub (the function name +
    skip reason markers are sufficient to identify it)."""
    spec = _spec()
    _write_stub_idempotent(
        tmp_path, spec, scope_id="s1", plan_path="p1"
    )
    out = _write_stub_idempotent(
        tmp_path, spec, scope_id="s2", plan_path="p2"
    )
    assert out["outcome"] == "skipped-identical"


def test_AC_DSA_4_agent_authored_content_not_overwritten(tmp_path) -> None:
    """When a stub file exists with content that does NOT match the
    dispatcher's skip-with-reason body, the dispatcher does NOT
    overwrite — outcome is 'skipped-agent-authored'."""
    spec = _spec()
    target = (
        tmp_path
        / "framework"
        / "c"
        / "tests"
        / "test_AC_X_1_placeholder.py"
    )
    target.parent.mkdir(parents=True)
    target.write_text(
        "def test_AC_X_1_real():\n    assert 1 + 1 == 2\n",
        encoding="utf-8",
    )
    out = _write_stub_idempotent(
        tmp_path, spec, scope_id="s", plan_path="p"
    )
    assert out["outcome"] == "skipped-agent-authored"
    # Agent-authored content is preserved verbatim.
    assert (
        target.read_text(encoding="utf-8")
        == "def test_AC_X_1_real():\n    assert 1 + 1 == 2\n"
    )


def test_AC_DSA_4_dispatcher_stub_recogniser_positive() -> None:
    """The dispatcher recognises its own stub body."""
    body = _render_stub_body(
        component="c", ac_id="AC.X.1", scope_id="s", plan_path="p"
    )
    assert _is_dispatcher_authored_stub(
        body, component="c", ac_id="AC.X.1"
    )


def test_AC_DSA_4_dispatcher_stub_recogniser_negative_real_test() -> None:
    """A genuinely agent-authored test does NOT register as a
    dispatcher stub."""
    real = (
        '"""real test for AC.X.1"""\n\n'
        "import pytest\n\n\n"
        "def test_AC_X_1_happy_path():\n"
        "    assert 1 + 1 == 2\n"
    )
    assert not _is_dispatcher_authored_stub(
        real, component="c", ac_id="AC.X.1"
    )


def test_AC_DSA_4_dispatcher_stub_recogniser_negative_unrelated_skip() -> None:
    """A skip-call without the dispatcher's skip-reason marker does
    NOT register as a dispatcher stub."""
    not_ours = (
        "import pytest\n\n\n"
        "def test_AC_X_1_placeholder():\n"
        '    pytest.skip("manual placeholder, not the dispatcher")\n'
    )
    assert not _is_dispatcher_authored_stub(
        not_ours, component="c", ac_id="AC.X.1"
    )

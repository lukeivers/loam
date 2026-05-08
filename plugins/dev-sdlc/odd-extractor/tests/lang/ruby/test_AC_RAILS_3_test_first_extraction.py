"""AC.RAILS.3 — Test-first extraction (RSpec + Minitest → VERIFIED).

Verifies:

- Each ``it`` block in an RSpec spec → 1 VERIFIED BandedAC with
  ``evidence.kind="test"``, non-null ``repo_sha``, citations matching
  ``<file>:<line>:rspec:<describe>#<it>``.
- Each ``test '...'`` block + each ``def test_<name>`` in a Minitest
  file → 1 VERIFIED BandedAC.
- Non-git repos downgrade VERIFIED → PLAUSIBLE (per AC.BANDS.2).
- Non-spec / non-test files return ``[]``.
"""

from __future__ import annotations

from pathlib import Path

from loam_odd_extractor.bands import ConfidenceBand
from loam_odd_extractor.lang.ruby.parser import parse_file
from loam_odd_extractor.lang.ruby.recognizers import (
    recognize_minitest_tests,
    recognize_rspec_tests,
)


def test_rspec_recognizer_emits_verified_for_each_it_block(
    synthetic_rails_repo: Path,
) -> None:
    spec = (
        synthetic_rails_repo / "spec" / "models" / "payment_spec.rb"
    )
    tree, src = parse_file(spec)
    out = recognize_rspec_tests(
        tree, src, spec, synthetic_rails_repo, "deadbeef" * 5
    )
    # 3 it blocks in the fixture.
    assert len(out) == 3
    for ac in out:
        assert ac.confidence is ConfidenceBand.VERIFIED
        assert ac.evidence.kind == "test"
        assert ac.evidence.repo_sha == "deadbeef" * 5
        # Citations: <file>:<line>:rspec:<describe>#<it>
        assert any(":rspec:" in c for c in ac.evidence.citations)


def test_rspec_recognizer_downgrades_when_no_repo_sha(
    synthetic_rails_repo: Path,
) -> None:
    """No repo_sha → downgrade VERIFIED → PLAUSIBLE per AC.BANDS.2."""
    spec = (
        synthetic_rails_repo / "spec" / "models" / "payment_spec.rb"
    )
    tree, src = parse_file(spec)
    out = recognize_rspec_tests(
        tree, src, spec, synthetic_rails_repo, None
    )
    assert len(out) == 3
    for ac in out:
        assert ac.confidence is ConfidenceBand.PLAUSIBLE
        assert ac.evidence.kind == "source"
        assert ac.evidence.repo_sha is None


def test_minitest_recognizer_emits_verified_for_test_block(
    synthetic_rails_repo: Path,
) -> None:
    test_file = (
        synthetic_rails_repo
        / "test"
        / "integration"
        / "payment_flow_test.rb"
    )
    tree, src = parse_file(test_file)
    out = recognize_minitest_tests(
        tree, src, test_file, synthetic_rails_repo, "deadbeef" * 5
    )
    assert len(out) >= 1
    for ac in out:
        assert ac.confidence is ConfidenceBand.VERIFIED
        assert ac.evidence.kind == "test"
        assert any(":minitest:" in c for c in ac.evidence.citations)


def test_minitest_recognizer_def_form() -> None:
    """``def test_<name>`` form recognised."""
    src = b"""
class FooTest < Minitest::Test
  def test_one
    assert true
  end
  def test_two
    assert false
  end
end
"""
    from loam_odd_extractor.lang.ruby.parser import parse_source

    tree = parse_source(src)
    file_path = Path("foo_test.rb")
    out = recognize_minitest_tests(
        tree, src, file_path, Path("/"), "deadbeef" * 5
    )
    # 2 def test_ methods.
    def_acs = [a for a in out if "def test_" in a.text]
    assert len(def_acs) == 2


def test_rspec_skips_non_spec_files(tmp_path: Path) -> None:
    """A `.rb` file outside ``spec/`` and not ending with ``_spec.rb``
    is not treated as a spec file.
    """
    rb = tmp_path / "regular.rb"
    rb.write_text("describe 'x' do; it 'y' do; end; end\n", encoding="utf-8")
    tree, src = parse_file(rb)
    out = recognize_rspec_tests(
        tree, src, rb, tmp_path, "deadbeef" * 5
    )
    assert out == []


def test_minitest_skips_non_test_files(tmp_path: Path) -> None:
    rb = tmp_path / "regular.rb"
    rb.write_text("test 'x' do\nend\n", encoding="utf-8")
    tree, src = parse_file(rb)
    out = recognize_minitest_tests(
        tree, src, rb, tmp_path, "deadbeef" * 5
    )
    assert out == []


def test_rspec_includes_describe_in_text(
    synthetic_rails_repo: Path,
) -> None:
    """The AC text includes the describe target prefix."""
    spec = (
        synthetic_rails_repo / "spec" / "models" / "payment_spec.rb"
    )
    tree, src = parse_file(spec)
    out = recognize_rspec_tests(
        tree, src, spec, synthetic_rails_repo, "deadbeef" * 5
    )
    texts = [ac.text for ac in out]
    # All texts begin with "RSpec — "
    assert all(t.startswith("RSpec — ") for t in texts)

"""AC.DRY.3 (v0.1.8 Cycle 4b) — ``_common/heuristic_helpers.py``
exposes ``make_inferred_banded_ac()`` constructor.

Both per-language ``heuristic_inferences.py`` modules (Ruby + JsTs)
were refactored in Cycle 4b to call this helper instead of
hand-rolling ``BandedAC(... evidence=Evidence(kind="inference",
...))``.
"""

from __future__ import annotations

from pathlib import Path

from loam_odd_extractor.bands import BandedAC, ConfidenceBand, Evidence
from loam_odd_extractor.lang._common.heuristic_helpers import (
    make_inferred_banded_ac,
)


def _make_source_plausible_ac() -> BandedAC:
    """Helper — a synthetic PLAUSIBLE BandedAC for use as
    ``source_ac`` in ``make_inferred_banded_ac()``.
    """
    return BandedAC(
        ac_id="AC.RAILS.active_record.payment.app_models_payment_rb",
        text="Payment is an ActiveRecord model",
        confidence=ConfidenceBand.PLAUSIBLE,
        evidence=Evidence(
            kind="source",
            citations=["app/models/payment.rb:1"],
        ),
        backing_files=["app/models/payment.rb"],
    )


def test_make_inferred_banded_ac_constructs_hypothesised_band() -> None:
    """The helper returns a HYPOTHESISED-band BandedAC."""
    src = _make_source_plausible_ac()

    inferred = make_inferred_banded_ac(
        ac_id="AC.RAILS.inferred.test.dummy",
        text="Inferred: dummy thing",
        rationale="heuristic: dummy → infers dummy. Source AC: " + src.ac_id,
        source_ac=src,
    )

    assert inferred.confidence is ConfidenceBand.HYPOTHESISED
    assert inferred.ac_id == "AC.RAILS.inferred.test.dummy"
    assert inferred.text == "Inferred: dummy thing"
    assert inferred.evidence is not None
    assert inferred.evidence.kind == "inference"
    assert inferred.evidence.rationale is not None
    assert "Source AC: " in inferred.evidence.rationale


def test_make_inferred_banded_ac_forwards_citations() -> None:
    """Citations from the source AC propagate to the inferred AC."""
    src = _make_source_plausible_ac()

    inferred = make_inferred_banded_ac(
        ac_id="AC.RAILS.inferred.test.cite",
        text="text",
        rationale="reason",
        source_ac=src,
    )

    assert list(inferred.evidence.citations) == ["app/models/payment.rb:1"]


def test_make_inferred_banded_ac_forwards_backing_files_by_default() -> None:
    """``backing_files`` defaults to ``source_ac.backing_files``."""
    src = _make_source_plausible_ac()

    inferred = make_inferred_banded_ac(
        ac_id="AC.RAILS.inferred.test.back",
        text="text",
        rationale="reason",
        source_ac=src,
    )

    assert list(inferred.backing_files) == ["app/models/payment.rb"]


def test_make_inferred_banded_ac_accepts_explicit_backing_files() -> None:
    """Caller can override backing_files explicitly."""
    src = _make_source_plausible_ac()

    inferred = make_inferred_banded_ac(
        ac_id="AC.RAILS.inferred.test.explicit",
        text="text",
        rationale="reason",
        source_ac=src,
        backing_files=["app/models/customer.rb"],
    )

    assert list(inferred.backing_files) == ["app/models/customer.rb"]


def test_ruby_heuristics_use_make_inferred_banded_ac() -> None:
    """Ruby's ``heuristic_inferences.py`` imports
    ``make_inferred_banded_ac`` from the canonical location.
    """
    import loam_odd_extractor

    pkg_root = Path(loam_odd_extractor.__file__).parent
    text = (
        pkg_root / "lang" / "ruby" / "heuristic_inferences.py"
    ).read_text()

    assert (
        "from .._common.heuristic_helpers import make_inferred_banded_ac"
        in text
    ), "Ruby heuristic_inferences.py does not import the canonical helper"

    # Sanity: the file no longer hand-rolls Evidence(kind="inference", ...).
    # Strip the module docstring before checking — the docstring
    # describes the helper using ``kind="inference"`` as descriptive
    # prose; only code-level occurrences are violations.
    import ast as _ast
    tree = _ast.parse(text)
    # Drop module-level docstring + any function/class docstrings.
    for node in _ast.walk(tree):
        if isinstance(
            node, (_ast.Module, _ast.FunctionDef, _ast.AsyncFunctionDef, _ast.ClassDef)
        ):
            if (
                node.body
                and isinstance(node.body[0], _ast.Expr)
                and isinstance(node.body[0].value, _ast.Constant)
                and isinstance(node.body[0].value.value, str)
            ):
                node.body = node.body[1:] or [_ast.Pass()]
    code_only = _ast.unparse(tree)
    assert (
        "kind=\"inference\"" not in code_only
        and "kind='inference'" not in code_only
    ), (
        "Ruby heuristic_inferences.py still hand-rolls Evidence("
        "kind=\"inference\", ...) — should call make_inferred_banded_ac()"
    )


def test_jsts_heuristics_use_make_inferred_banded_ac() -> None:
    """JsTs's ``heuristic_inferences.py`` imports
    ``make_inferred_banded_ac`` from the canonical location.
    """
    import loam_odd_extractor

    pkg_root = Path(loam_odd_extractor.__file__).parent
    text = (
        pkg_root / "lang" / "jsts" / "heuristic_inferences.py"
    ).read_text()

    assert (
        "from .._common.heuristic_helpers import make_inferred_banded_ac"
        in text
    ), "JsTs heuristic_inferences.py does not import the canonical helper"

    # Strip the module docstring before checking — the docstring
    # describes the helper using ``kind="inference"`` as descriptive
    # prose; only code-level occurrences are violations.
    import ast as _ast
    tree = _ast.parse(text)
    # Drop module-level docstring + any function/class docstrings.
    for node in _ast.walk(tree):
        if isinstance(
            node, (_ast.Module, _ast.FunctionDef, _ast.AsyncFunctionDef, _ast.ClassDef)
        ):
            if (
                node.body
                and isinstance(node.body[0], _ast.Expr)
                and isinstance(node.body[0].value, _ast.Constant)
                and isinstance(node.body[0].value.value, str)
            ):
                node.body = node.body[1:] or [_ast.Pass()]
    code_only = _ast.unparse(tree)
    assert (
        "kind=\"inference\"" not in code_only
        and "kind='inference'" not in code_only
    ), (
        "JsTs heuristic_inferences.py still hand-rolls Evidence("
        "kind=\"inference\", ...) — should call make_inferred_banded_ac()"
    )


def test_per_language_heuristic_inference_still_produces_hypothesised() -> None:
    """End-to-end: Ruby's ``infer_domain_rules`` still produces
    HYPOTHESISED ACs after the refactor (behaviour preservation).
    """
    from loam_odd_extractor.lang.ruby.heuristic_inferences import (
        infer_domain_rules,
    )

    src = BandedAC(
        ac_id="AC.RAILS.active_record.customer.email_uniq",
        text="Customer declares validates :email, uniqueness: true",
        confidence=ConfidenceBand.PLAUSIBLE,
        evidence=Evidence(
            kind="source",
            citations=["app/models/customer.rb:5"],
        ),
        backing_files=["app/models/customer.rb"],
    )

    out = infer_domain_rules([src])

    assert len(out) >= 1
    assert all(
        ac.confidence is ConfidenceBand.HYPOTHESISED for ac in out
    )
    assert all(ac.evidence.kind == "inference" for ac in out)
    assert all(ac.evidence.rationale for ac in out)

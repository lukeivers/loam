"""D1 — persona contract + template.

Acceptance (brief D1):
- Directory layout (contract.yaml mandatory, prompt.md mandatory,
  voice.md optional, home/ optional).
- Contract mandatory fields declared + validated.
- Pydantic rejects missing mandatory fields with errors that name each
  missing field.
- Template directory exists as a copy-to-workspace starter.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from src.contract import (
    AuthorityBoundary,
    ContractFileError,
    EscalationTaxonomy,
    PersonaContract,
    Responsibilities,
    SeverityVocabulary,
    TierAction,
    load_contract,
)


# ---- mandatory-field rejection ---------------------------------------


def test_missing_handle_names_field():
    with pytest.raises(ValidationError) as exc:
        PersonaContract(  # type: ignore[call-arg]
            given_name="Eve",
            responsibilities=Responsibilities(
                single_point_of_contact="a",
                context_holder="b",
                escalation_judge="c",
            ),
            authority_boundary=AuthorityBoundary(
                tier_a=TierAction.defer,
                tier_b=TierAction.defer,
                tier_c=TierAction.execute,
                tier_d=TierAction.execute,
            ),
            escalation_taxonomy=EscalationTaxonomy(categories=("x",)),
            severity_vocabulary=SeverityVocabulary(labels=("x", "y")),
        )
    assert "handle" in str(exc.value)


def test_missing_responsibilities_names_field():
    with pytest.raises(ValidationError) as exc:
        PersonaContract(  # type: ignore[call-arg]
            handle="eve",
            given_name="Eve",
            authority_boundary=AuthorityBoundary(
                tier_a=TierAction.defer,
                tier_b=TierAction.defer,
                tier_c=TierAction.execute,
                tier_d=TierAction.execute,
            ),
            escalation_taxonomy=EscalationTaxonomy(categories=("x",)),
            severity_vocabulary=SeverityVocabulary(labels=("x", "y")),
        )
    assert "responsibilities" in str(exc.value)


def test_missing_authority_boundary_names_field():
    with pytest.raises(ValidationError) as exc:
        PersonaContract(  # type: ignore[call-arg]
            handle="eve",
            given_name="Eve",
            responsibilities=Responsibilities(
                single_point_of_contact="a",
                context_holder="b",
                escalation_judge="c",
            ),
            escalation_taxonomy=EscalationTaxonomy(categories=("x",)),
            severity_vocabulary=SeverityVocabulary(labels=("x", "y")),
        )
    assert "authority_boundary" in str(exc.value)


def test_authority_boundary_rejects_missing_tier():
    with pytest.raises(ValidationError) as exc:
        AuthorityBoundary(  # type: ignore[call-arg]
            tier_a=TierAction.defer,
            tier_b=TierAction.defer,
            tier_c=TierAction.execute,
            # tier_d missing
        )
    assert "tier_d" in str(exc.value)


def test_escalation_taxonomy_requires_at_least_one_category():
    with pytest.raises(ValidationError):
        EscalationTaxonomy(categories=())


def test_severity_vocabulary_requires_at_least_two_labels():
    with pytest.raises(ValidationError):
        SeverityVocabulary(labels=("only-one",))


def test_handle_must_match_pattern():
    with pytest.raises(ValidationError) as exc:
        PersonaContract(
            handle="Eve!",  # uppercase + punctuation
            given_name="Eve",
            responsibilities=Responsibilities(
                single_point_of_contact="a",
                context_holder="b",
                escalation_judge="c",
            ),
            authority_boundary=AuthorityBoundary(
                tier_a=TierAction.defer,
                tier_b=TierAction.defer,
                tier_c=TierAction.execute,
                tier_d=TierAction.execute,
            ),
            escalation_taxonomy=EscalationTaxonomy(categories=("x",)),
            severity_vocabulary=SeverityVocabulary(labels=("x", "y")),
        )
    assert "handle" in str(exc.value)


def test_contract_version_must_be_semver():
    with pytest.raises(ValidationError):
        PersonaContract(
            handle="eve",
            given_name="Eve",
            contract_version="not-a-semver",
            responsibilities=Responsibilities(
                single_point_of_contact="a",
                context_holder="b",
                escalation_judge="c",
            ),
            authority_boundary=AuthorityBoundary(
                tier_a=TierAction.defer,
                tier_b=TierAction.defer,
                tier_c=TierAction.execute,
                tier_d=TierAction.execute,
            ),
            escalation_taxonomy=EscalationTaxonomy(categories=("x",)),
            severity_vocabulary=SeverityVocabulary(labels=("x", "y")),
        )


def test_extra_field_rejected():
    with pytest.raises(ValidationError):
        PersonaContract(  # type: ignore[call-arg]
            handle="eve",
            given_name="Eve",
            responsibilities=Responsibilities(
                single_point_of_contact="a",
                context_holder="b",
                escalation_judge="c",
            ),
            authority_boundary=AuthorityBoundary(
                tier_a=TierAction.defer,
                tier_b=TierAction.defer,
                tier_c=TierAction.execute,
                tier_d=TierAction.execute,
            ),
            escalation_taxonomy=EscalationTaxonomy(categories=("x",)),
            severity_vocabulary=SeverityVocabulary(labels=("x", "y")),
            unknown_field="nope",
        )


# ---- valid construction ----------------------------------------------


def test_valid_contract_constructs_and_serialises():
    c = PersonaContract(
        handle="eve",
        given_name="Eve",
        responsibilities=Responsibilities(
            single_point_of_contact="a",
            context_holder="b",
            escalation_judge="c",
        ),
        authority_boundary=AuthorityBoundary(
            tier_a=TierAction.defer,
            tier_b=TierAction.defer,
            tier_c=TierAction.execute,
            tier_d=TierAction.execute,
        ),
        escalation_taxonomy=EscalationTaxonomy(categories=("external-funds",)),
        severity_vocabulary=SeverityVocabulary(
            labels=("crisis", "urgent", "material", "advisory")
        ),
    )
    s = c.to_yaml()
    # Round-trip: what we dumped loads back identically.
    reloaded = PersonaContract.model_validate(yaml.safe_load(s))
    assert reloaded.handle == "eve"
    assert reloaded.authority_boundary.tier_c == TierAction.execute


def test_load_contract_from_yaml(tmp_path: Path, workspace_with_primary: Path):
    contract_path = workspace_with_primary / "personas" / "eve" / "contract.yaml"
    c = load_contract(contract_path)
    assert c.handle == "eve"
    assert c.is_primary is True


def test_load_contract_nonexistent_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_contract(tmp_path / "nope.yaml")


def test_load_contract_invalid_yaml_raises(tmp_path: Path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("not: valid: yaml: [unclosed")
    with pytest.raises(ContractFileError):
        load_contract(bad)


def test_load_contract_wrong_root_type_raises(tmp_path: Path):
    bad = tmp_path / "listroot.yaml"
    bad.write_text("- item1\n- item2\n")
    with pytest.raises(ContractFileError):
        load_contract(bad)


# ---- template exists -------------------------------------------------


def test_template_directory_exists_and_validates():
    # Template lives alongside src/ at primary-persona/templates/.
    tmpl_dir = Path(__file__).resolve().parent.parent / "templates" / "persona-template"
    assert tmpl_dir.exists()
    assert (tmpl_dir / "contract.yaml").exists()
    assert (tmpl_dir / "prompt.md").exists()
    # The template contract parses and validates cleanly.
    c = load_contract(tmpl_dir / "contract.yaml")
    assert c.handle == "example-persona"

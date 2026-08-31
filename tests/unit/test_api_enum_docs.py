from pathlib import Path

import pytest

from genlayer_py.types import ExecutionResult, VoteType

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "relative_path",
    (
        "docs/api-references/api.md",
        "docs/api-references/genlayer-py.md",
    ),
)
@pytest.mark.parametrize(
    ("enum_name", "enum_type"),
    (("ExecutionResult", ExecutionResult), ("VoteType", VoteType)),
)
def test_public_enum_docs_are_generated_from_the_complete_train_enum(
    relative_path, enum_name, enum_type
):
    docs = (PROJECT_ROOT / relative_path).read_text()

    for member in enum_type:
        assert f'{enum_name}.{member.name} = "{member.value}"' in docs


@pytest.mark.parametrize(
    "relative_path",
    (
        "docs/api-references/api.md",
        "docs/api-references/genlayer-py.md",
    ),
)
def test_advanced_lifecycle_enums_are_not_documented_as_primary_types(relative_path):
    docs = (PROJECT_ROOT / relative_path).read_text()

    assert "### TransactionStatus" not in docs
    assert "### ResolutionAction" not in docs


@pytest.mark.parametrize(
    "relative_path",
    (
        "README.md",
        "docs/api-references/api.md",
        "docs/api-references/genlayer-py.md",
        "docs/api-references/index.md",
    ),
)
def test_public_lifecycle_docs_use_state_as_the_discriminator(relative_path):
    docs = (PROJECT_ROOT / relative_path).read_text()

    assert "state" in docs
    assert '{"status": "processing"' not in docs
    assert '{"status": "decided"' not in docs
    assert 'lifecycle"]["status' not in docs

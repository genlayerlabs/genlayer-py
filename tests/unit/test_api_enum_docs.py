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

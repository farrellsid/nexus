"""A small executable boundary rule for the domain modules."""

import ast
from pathlib import Path

import pytest

DOMAIN_IMPORTS = {
    "evidence": set(),
    "knowledge": {"evidence"},
    "geography": {"knowledge"},
    "investigation": {"geography", "knowledge"},
    "review": {"evidence", "knowledge"},
    "normalisation/digest": set(),
    "normalisation/measurements": set(),
    "normalisation/vocabulary": {"knowledge", "normalisation.digest"},
    "normalisation/release": {
        "investigation",
        "knowledge",
        "normalisation.digest",
        "normalisation.vocabulary",
    },
}


def violations(module: str, source: str) -> list[str]:
    invalid = []
    for node in ast.walk(ast.parse(source)):
        names = []
        if isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
            if node.level:
                invalid.append("Use explicit public imports")
        elif isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        for name in names:
            if name.split(".")[0] in {"fastapi", "sqlalchemy", "uvicorn", "psycopg"}:
                invalid.append(name)
            if name == "app" or name.startswith("app."):
                if name not in {f"app.{allowed}" for allowed in DOMAIN_IMPORTS[module]}:
                    invalid.append(name)
    return invalid


@pytest.mark.parametrize("module", DOMAIN_IMPORTS)
def test_domain_dependencies_point_inward(module):
    source = (Path(__file__).parents[1] / "app" / f"{module}.py").read_text("utf-8")
    assert violations(module, source) == []


@pytest.mark.parametrize(
    "source", ["from app.main import app", "import fastapi", "from . import main"]
)
def test_checker_rejects_representative_forbidden_imports(source):
    assert violations("evidence", source)

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
    "evaluation/figures": set(),
    "evaluation/cases": {"knowledge"},
    "evaluation/corpus": {"investigation", "knowledge", "normalisation.release"},
    "evaluation/retrieval": {"evaluation.cases", "evaluation.corpus", "knowledge"},
    "evaluation/oracle": {
        "evaluation.cases",
        "evaluation.corpus",
        "evaluation.figures",
    },
    "evaluation/answers": {
        "evaluation.cases",
        "evaluation.corpus",
        "evaluation.figures",
        "evaluation.retrieval",
        "knowledge",
    },
    "acquisition/policy": set(),
    "acquisition/fetch": {"acquisition.policy", "knowledge"},
    "acquisition/snapshots": {"acquisition.policy", "knowledge"},
    "acquisition/extraction": {"knowledge"},
    "acquisition/verification": {"acquisition.extraction", "knowledge"},
    "acquisition/proposals": {"acquisition.extraction", "evaluation.figures", "knowledge"},
    "acquisition/providers/observation": {"knowledge"},
    "acquisition/providers/eia": {"acquisition.providers.observation", "knowledge"},
    "acquisition/providers/jodi": {"acquisition.providers.observation"},
    "acquisition/providers/compare": {"knowledge"},
    "acquisition/providers/statcan": {"acquisition.providers.observation"},
    "acquisition/providers/sodir": {"acquisition.providers.observation"},
    "acquisition/providers/gdelt": {"knowledge"},
    "acquisition/providers/crosscheck": {
        "acquisition.providers.compare",
        "acquisition.providers.observation",
        "knowledge",
    },
    "comparability/model": {"knowledge"},
    "comparability/display": {"comparability.model", "knowledge"},
    "comparability/reports": {
        "comparability.model",
        "investigation",
        "normalisation.release",
        "normalisation.vocabulary",
    },
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

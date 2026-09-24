"""Closed, versioned Nexus vocabularies. A code that is not listed here does not exist."""

from pathlib import Path

from pydantic import model_validator

from app.knowledge import Record
from app.normalisation.digest import fingerprint


class Predicate(Record):
    definition: str


class Unit(Record):
    symbol: str
    dimension: str
    scale: str  # exact decimal text; "million" is 1000000, "percent" is 0.01


class Measure(Record):
    name: str
    unit: str
    statistic: str
    material_basis: str


class Vocabulary(Record):
    version: str
    predicates: dict[str, Predicate]
    epistemic_statuses: list[str]
    content_types: list[str]
    modalities: list[str]
    publisher_classes: list[str]
    document_classes: list[str]
    release_statuses: list[str]
    units: dict[str, Unit]
    measures: dict[str, Measure]
    statistics: list[str]
    precisions: list[str]
    valid_kinds: list[str]
    entity_categories: dict[str, list[str]]

    @model_validator(mode="after")
    def codes_are_unique_and_measures_use_known_units(self) -> "Vocabulary":
        for name in (
            "epistemic_statuses",
            "content_types",
            "modalities",
            "publisher_classes",
            "document_classes",
            "release_statuses",
            "statistics",
            "precisions",
            "valid_kinds",
        ):
            codes = getattr(self, name)
            if len(codes) != len(set(codes)):
                raise ValueError(f"duplicate code in {name}")
        for code, measure in self.measures.items():
            if measure.unit not in self.units:
                raise ValueError(f"measure {code} uses unknown unit {measure.unit}")
            if measure.statistic not in self.statistics:
                raise ValueError(f"measure {code} uses unknown statistic {measure.statistic}")
        return self

    def content_hash(self) -> str:
        return fingerprint(self.model_dump(mode="json"))


def load_vocabulary(path: Path) -> Vocabulary:
    return Vocabulary.model_validate_json(path.read_text("utf-8"))

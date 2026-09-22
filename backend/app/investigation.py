"""Fixture adapter and curated reading prompts; no model calls or factual inference."""

import json
from pathlib import Path

from app.geography import GuidedGeography
from app.knowledge import EvidencePack, Record


class ReadingPrompt(Record):
    id: str
    question: str
    expected_answer: str
    claim_ids: list[str]
    status: str


class Investigation(Record):
    pack: EvidencePack
    questions: list[ReadingPrompt]
    geography: GuidedGeography | None = None
    answer_mode: str = "curated_reading_guide"


def load_investigation(directory: Path) -> Investigation:
    pack = EvidencePack.model_validate_json((directory / "evidence-pack.json").read_text("utf-8"))
    questions = [
        ReadingPrompt.model_validate(record)
        for record in json.loads((directory / "acceptance-cases.json").read_text("utf-8"))
    ]
    claim_ids = {claim.id for claim in pack.claims}
    if any(not set(question.claim_ids) <= claim_ids for question in questions):
        raise ValueError("Reading guide references an unknown claim")
    if len({question.id for question in questions}) != len(questions):
        raise ValueError("Duplicate reading guide IDs")
    geography_path = directory / "geography.json"
    geography = (
        GuidedGeography.model_validate_json(geography_path.read_text("utf-8"))
        if geography_path.exists()
        else None
    )
    if geography:
        entity_ids = {entity.id for entity in pack.entities}
        stop_ids = [stop.id for stop in geography.stops]
        if len(stop_ids) != len(set(stop_ids)):
            raise ValueError("Duplicate geography stop IDs")
        if any(stop.entity_id not in entity_ids for stop in geography.stops):
            raise ValueError("Geography references an unknown entity")
    return Investigation(pack=pack, questions=questions, geography=geography)


def load_investigations(root: Path) -> list[Investigation]:
    investigations = [
        load_investigation(directory)
        for directory in sorted(root.iterdir())
        if directory.is_dir()
        and (directory / "evidence-pack.json").exists()
        and (directory / "acceptance-cases.json").exists()
    ]
    case_ids = [item.pack.case_id for item in investigations]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("Duplicate investigation case IDs")
    if not investigations:
        raise ValueError("No investigations found")
    return investigations

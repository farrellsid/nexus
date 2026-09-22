"""Retained source metadata. This module has no knowledge or rendering dependencies."""

from datetime import date

from pydantic import BaseModel, ConfigDict, HttpUrl


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    title: str
    publisher: str
    published_on: date | None
    language: str
    url: HttpUrl
    locator: str
    excerpt: str
    format: str
    origin_group: str
    checked_on: date
    review_status: str
    rights: str
    independence: str


def validate_references(references: list[str], sources: list[Source]) -> None:
    available = {source.id for source in sources}
    if not references or not set(references) <= available:
        raise ValueError(f"Missing or unresolved evidence references: {references}")

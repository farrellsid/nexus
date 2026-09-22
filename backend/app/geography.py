"""Sourced map anchors for guided reading; points never imply full feature geometry."""

from datetime import date

from pydantic import HttpUrl

from app.knowledge import Record


class GeoStop(Record):
    id: str
    entity_id: str
    label: str
    latitude: float
    longitude: float
    precision: str
    role: str
    why_it_matters: str
    caveat: str
    source_title: str
    source_url: HttpUrl
    checked_on: date


class GuidedGeography(Record):
    title: str
    framing: str
    stops: list[GeoStop]

"""Sourced map anchors for guided reading; points never imply full feature geometry."""

from datetime import date

from pydantic import HttpUrl, field_validator

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


class GeoPoint(Record):
    """One ordered vertex of a route/corridor line. Not itself a separately sourced record."""

    latitude: float
    longitude: float


class GeoRoute(Record):
    """A sourced illustrative line between anchor points.

    Unlike GeoStop, a route never claims to be an exact centerline, vessel
    track or as-built path unless the caveat says so explicitly. Where a
    source only describes a corridor in prose, the points are built from
    separately sourced anchor coordinates (strait mouths, ports, reused
    stops) and the caveat must say the line is an approximation.
    """

    id: str
    entity_id: str
    label: str
    points: list[GeoPoint]
    precision: str
    role: str
    why_it_matters: str
    caveat: str
    source_title: str
    source_url: HttpUrl
    checked_on: date

    @field_validator("points")
    @classmethod
    def _at_least_two_points(cls, points: list[GeoPoint]) -> list[GeoPoint]:
        if len(points) < 2:
            raise ValueError("A route needs at least two points to draw a line")
        return points


class GuidedGeography(Record):
    title: str
    framing: str
    stops: list[GeoStop]
    routes: list[GeoRoute] = []

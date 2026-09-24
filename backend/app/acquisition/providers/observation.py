"""One provider observation, kept close to what the provider actually said."""

from app.knowledge import Record


class Observation(Record):
    provider: str  # "eia" or "jodi"
    series: dict[str, str]  # the provider's own identifiers (series id, area, product, flow, ...)
    period: str  # the provider's period label, unchanged
    value_text: str | None  # original decimal text; None when the provider gave no number
    unit: str  # the provider's unit code, unchanged
    flag: (
        str | None
    )  # a provider symbol that stands in for a missing number, for example "-" or "x"
    source_url: str  # already redacted; safe to store

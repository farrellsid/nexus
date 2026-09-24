"""Match one pack value to a provider observation and say what the comparison shows.

A cross-check is not a verdict on the pack. `equal_at_pack_precision` means the provider's own
number, scaled exactly and rounded to the pack's precision, equals the pack's. It does not show the
pack cited that provider, and `differs` may be a different definition, month or vintage.
"""

from typing import Literal

from app.acquisition.providers.compare import UnitError, compare
from app.acquisition.providers.observation import Observation
from app.knowledge import Record

Status = Literal[
    "equal_at_pack_precision", "differs", "not_comparable", "no_observation", "unit_error"
]


class CrossCheckRow(Record):
    measurement_id: str
    label: str
    pack_value: str
    status: Status
    provider_period: str | None
    provider_value: str | None  # the provider's value scaled to the pack's unit, unrounded
    provider_raw: str | None  # the provider's original text and unit
    note: str


def cross_check(
    measurement_id: str,
    label: str,
    pack_value: str,
    nexus_unit: str,
    observations: list[Observation],
    series: dict[str, str],
    period: str,
    provider_unit: str,
) -> CrossCheckRow:
    candidates = [
        o
        for o in observations
        if all(o.series.get(k) == v for k, v in series.items()) and o.unit == provider_unit
    ]
    found = next((o for o in candidates if o.period == period), None)
    if found is None:
        have = sorted({o.period for o in candidates})
        listed = (
            ", ".join(have[:3] + (["..."] if len(have) > 6 else []) + have[-3:]) if have else "none"
        )
        return CrossCheckRow(
            measurement_id=measurement_id,
            label=label,
            pack_value=pack_value,
            status="no_observation",
            provider_period=None,
            provider_value=None,
            provider_raw=None,
            note=f"the provider has no observation for {period}; it has: {listed}",
        )
    raw = f"{found.value_text if found.value_text is not None else found.flag} {found.unit}"
    try:
        result = compare(pack_value, found.value_text, provider_unit, nexus_unit)
    except UnitError as error:
        return CrossCheckRow(
            measurement_id=measurement_id,
            label=label,
            pack_value=pack_value,
            status="unit_error",
            provider_period=found.period,
            provider_value=None,
            provider_raw=raw,
            note=str(error),
        )
    note = (
        result.note
        if found.value_text is not None
        else (f"the provider gave no number (symbol {found.flag!r})")
    )
    return CrossCheckRow(
        measurement_id=measurement_id,
        label=label,
        pack_value=pack_value,
        status=result.status,
        provider_period=found.period,
        provider_value=result.provider_value,
        provider_raw=raw,
        note=note,
    )

"""Compare a provider value with a pack value using exact scale changes only.

There is no mass-to-volume conversion and no unit guessing: a pair of units that is not listed
here raises `UnitError`. A pack value is rounded-to, not rounded-from: the provider's value is
rounded half-up to the pack's own decimal places before comparing, and both are shown.
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from app.knowledge import Record

# (provider unit, Nexus unit code) -> exact multiplier. Nexus codes come from vocabulary-v1.json.
SCALES: dict[tuple[str, str], Decimal] = {
    ("MBBL", "million_barrel_petroleum"): Decimal("0.001"),
    ("%", "percent"): Decimal("1"),
    ("B/CD", "million_barrel_petroleum_per_calendar_day"): Decimal("0.000001"),
    ("KBD", "million_barrel_petroleum_per_day"): Decimal("0.001"),
    ("TBPD", "million_barrel_petroleum_per_day"): Decimal("0.001"),
}


class UnitError(ValueError):
    """The two units cannot be compared by an exact scale change."""


class Comparison(Record):
    status: Literal["equal_at_pack_precision", "differs", "not_comparable"]
    pack_value: str
    provider_value: str | None  # the provider's value scaled to the pack's unit, unrounded
    note: str


def scale(value: Decimal, provider_unit: str, nexus_unit: str) -> Decimal:
    try:
        return value * SCALES[(provider_unit, nexus_unit)]
    except KeyError:
        raise UnitError(f"no exact scale from {provider_unit} to {nexus_unit}") from None


def compare(
    pack_text: str, provider_text: str | None, provider_unit: str, nexus_unit: str
) -> Comparison:
    if provider_text is None:
        return Comparison(
            status="not_comparable",
            pack_value=pack_text,
            provider_value=None,
            note="the provider gave no number for this period",
        )
    scaled = scale(Decimal(provider_text), provider_unit, nexus_unit)
    pack = Decimal(pack_text)
    places = max(0, -pack.as_tuple().exponent)
    rounded = scaled.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    equal = rounded == pack
    return Comparison(
        status="equal_at_pack_precision" if equal else "differs",
        pack_value=pack_text,
        provider_value=str(scaled),
        note=f"provider rounded to {places} decimal place(s) is {rounded}",
    )

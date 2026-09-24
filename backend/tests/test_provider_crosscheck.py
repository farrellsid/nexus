"""The cross-check matches a pack value to a provider observation. Synthetic test data."""

from app.acquisition.providers.crosscheck import cross_check
from app.acquisition.providers.observation import Observation


def obs(period, value, unit="MBBL", **series):
    return Observation(
        provider="eia",
        series={"series": "WCESTUS1", **series},
        period=period,
        value_text=value,
        unit=unit,
        flag=None,
        source_url="https://api.eia.gov/v2/x?api_key=REDACTED",
    )


OBSERVATIONS = [
    obs("2026-06-19", "412134"),
    obs("2026-07-17", "411675"),
    obs("2026-09-11", "423429"),
]
UNIT = "million_barrel_petroleum"


def check(period, pack, **overrides):
    args = {
        "measurement_id": "m1",
        "label": "week ending",
        "pack_value": pack,
        "nexus_unit": UNIT,
        "observations": OBSERVATIONS,
        "series": {"series": "WCESTUS1"},
        "period": period,
        "provider_unit": "MBBL",
    }
    return cross_check(**{**args, **overrides})


def test_a_matching_observation_is_compared_at_the_pack_precision():
    row = check("2026-06-19", "412.1")
    assert row.status == "equal_at_pack_precision"
    assert (row.provider_period, row.provider_value) == ("2026-06-19", "412.134")


def test_a_differing_observation_is_reported_as_differs():
    row = check("2026-09-11", "999.9")
    assert row.status == "differs" and row.provider_value == "423.429"


def test_a_missing_period_says_which_periods_the_provider_does_have():
    row = check("2026-08-01", "1.0")
    assert row.status == "no_observation"
    assert "2026-06-19" in row.note and "2026-09-11" in row.note


def test_series_filters_must_match():
    row = check("2026-06-19", "412.1", series={"series": "OTHER"})
    assert row.status == "no_observation"


def test_a_provider_with_no_number_is_not_comparable():
    silent = Observation(
        provider="jodi",
        series={"area": "IQ"},
        period="2026-07",
        value_text=None,
        unit="KBD",
        flag="-",
        source_url="u",
    )
    row = cross_check(
        "m2",
        "Iraq",
        "3.86",
        "million_barrel_petroleum_per_day",
        [silent],
        {"area": "IQ"},
        "2026-07",
        "KBD",
    )
    assert row.status == "not_comparable" and "-" in row.note


def test_an_unlisted_unit_pair_is_reported_not_converted():
    row = check("2026-06-19", "412.1", nexus_unit="million_tonne_metric")
    assert row.status == "unit_error"

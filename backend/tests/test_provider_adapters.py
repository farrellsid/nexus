"""Provider parsers and the cross-check comparison. Fixtures mirror real response shapes but are
synthetic; the key below is a made-up value, never a real credential."""

import json
from decimal import Decimal

import pytest

from app.acquisition.providers.compare import UnitError, compare, scale
from app.acquisition.providers.eia import EiaQuery, build_url, parse_page
from app.acquisition.providers.jodi import parse_csv, select

KEY = "SYNTHETIC-KEY"

EIA_PAGE = json.dumps(
    {
        "response": {
            "total": "2",
            "dateFormat": "YYYY-MM-DD",
            "frequency": "weekly",
            "data": [
                {
                    "period": "2026-06-19",
                    "duoarea": "NUS",
                    "area-name": "U.S.",
                    "product": "EPC0",
                    "process": "SAX",
                    "series": "WCESTUS1",
                    "series-description": "U.S. Ending Stocks excluding SPR of Crude Oil",
                    "value": "412134",
                    "units": "MBBL",
                },
                {
                    "period": "2026-06-26",
                    "duoarea": "NUS",
                    "area-name": "U.S.",
                    "product": "EPC0",
                    "process": "SAX",
                    "series": "WCESTUS1",
                    "series-description": "U.S. Ending Stocks excluding SPR of Crude Oil",
                    "value": "408359",
                    "units": "MBBL",
                },
            ],
        },
        "request": {"command": "/v2/petroleum/stoc/wstk/data/", "params": {}},
        "apiVersion": "2.1.11",
    }
).encode()


class TestEia:
    def test_the_url_carries_the_key_and_the_query_but_only_the_key_is_secret(self):
        query = EiaQuery(
            route="petroleum/stoc/wstk",
            frequency="weekly",
            facets={"series": ["WCESTUS1"]},
            start="2026-06-15",
            end="2026-09-15",
        )
        url = build_url(query, KEY, offset=0, length=5000)
        assert url.startswith("https://api.eia.gov/v2/petroleum/stoc/wstk/data/?")
        assert "frequency=weekly" in url and "facets%5Bseries%5D%5B%5D=WCESTUS1" in url
        assert "start=2026-06-15" in url and "length=5000" in url
        assert url.endswith(f"api_key={KEY}")

    def test_a_page_parses_into_observations_with_the_original_value_text(self):
        page = parse_page(EIA_PAGE, "https://api.eia.gov/v2/x?api_key=REDACTED")
        assert page.total == 2 and page.warnings == []
        first = page.observations[0]
        assert (first.provider, first.period, first.value_text, first.unit) == (
            "eia",
            "2026-06-19",
            "412134",
            "MBBL",
        )
        assert first.series["series"] == "WCESTUS1" and first.series["duoarea"] == "NUS"
        assert "value" not in first.series and "period" not in first.series

    def test_a_truncation_warning_is_surfaced_not_swallowed(self):
        body = json.loads(EIA_PAGE)
        body["warnings"] = [{"warning": "parameter out of range", "description": "max 5,000 rows"}]
        page = parse_page(json.dumps(body).encode(), "u")
        assert page.warnings == ["parameter out of range: max 5,000 rows"]

    def test_an_error_body_is_an_error_not_an_empty_result(self):
        with pytest.raises(ValueError, match="API_KEY_MISSING"):
            parse_page(b'{"error": {"code": "API_KEY_MISSING", "message": "No key"}}', "u")

    def test_a_null_value_stays_null(self):
        body = json.loads(EIA_PAGE)
        body["response"]["data"][0]["value"] = None
        page = parse_page(json.dumps(body).encode(), "u")
        assert page.observations[0].value_text is None


JODI = (
    "REF_AREA,TIME_PERIOD,ENERGY_PRODUCT,FLOW_BREAKDOWN,UNIT_MEASURE,OBS_VALUE,ASSESSMENT_CODE\n"
    "SA,2026-07,CRUDEOIL,INDPROD,KBD,8135.0968,1\n"
    "SA,2026-07,CRUDEOIL,INDPROD,KBBL,-,1\n"
    "IQ,2026-07,CRUDEOIL,INDPROD,KBD,-,3\n"
    "US,2026-06,CRUDEOIL,INDPROD,KBD,13791.9333,1\n"
    "AE,2026-01,CRUDEOIL,CLOSTLV,KBD,x,3\n"
)


class TestJodi:
    def test_rows_parse_with_original_text_and_the_assessment_code(self):
        observations = parse_csv(JODI, "https://example.org/jodi.csv")
        assert len(observations) == 5
        first = observations[0]
        assert (first.provider, first.period, first.value_text, first.unit) == (
            "jodi",
            "2026-07",
            "8135.0968",
            "KBD",
        )
        assert first.series == {
            "area": "SA",
            "product": "CRUDEOIL",
            "flow": "INDPROD",
            "assessment": "1",
        }

    def test_dash_and_x_are_not_numbers_and_keep_their_symbol_as_the_flag(self):
        observations = parse_csv(JODI, "u")
        by = {(o.series["area"], o.unit, o.period): o for o in observations}
        dash = by[("SA", "KBBL", "2026-07")]
        assert (dash.value_text, dash.flag) == (None, "-")
        cross = by[("AE", "KBD", "2026-01")]
        assert (cross.value_text, cross.flag) == (None, "x")

    def test_selection_filters_by_area_product_flow_and_unit(self):
        chosen = select(
            parse_csv(JODI, "u"), areas=["SA", "US"], product="CRUDEOIL", flow="INDPROD", unit="KBD"
        )
        assert [(o.series["area"], o.value_text) for o in chosen] == [
            ("SA", "8135.0968"),
            ("US", "13791.9333"),
        ]

    def test_a_missing_header_is_an_error(self):
        with pytest.raises(ValueError, match="REF_AREA"):
            parse_csv("A,B\n1,2\n", "u")


class TestCompare:
    def test_exact_scale_changes_only(self):
        assert scale(Decimal("412134"), "MBBL", "million_barrel_petroleum") == Decimal("412.134")
        assert scale(Decimal("96.1"), "%", "percent") == Decimal("96.1")
        assert scale(Decimal("8135"), "KBD", "million_barrel_petroleum_per_day") == Decimal("8.135")
        assert scale(
            Decimal("18331493"), "B/CD", "million_barrel_petroleum_per_calendar_day"
        ) == Decimal("18.331493")

    def test_a_cross_dimension_conversion_is_refused(self):
        with pytest.raises(UnitError):
            scale(Decimal("100"), "MBBL", "million_tonne_metric")
        with pytest.raises(UnitError):
            scale(Decimal("100"), "KBD", "million_barrel_petroleum")

    def test_equal_at_the_pack_precision_after_rounding_half_up(self):
        result = compare("412.1", "412134", "MBBL", "million_barrel_petroleum")
        assert result.status == "equal_at_pack_precision" and result.provider_value == "412.134"
        assert (
            compare("411.7", "411675", "MBBL", "million_barrel_petroleum").status
            == "equal_at_pack_precision"
        )

    def test_a_real_difference_is_reported_with_both_values(self):
        result = compare("423.4", "424410", "MBBL", "million_barrel_petroleum")
        assert result.status == "differs"
        assert (result.pack_value, result.provider_value) == ("423.4", "424.410")

    def test_a_provider_value_that_is_not_a_number_is_not_comparable(self):
        result = compare("5.97", None, "KBD", "million_barrel_petroleum_per_day")
        assert result.status == "not_comparable"

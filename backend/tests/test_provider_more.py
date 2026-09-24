"""StatCan, Sodir and GDELT parsers. Fixtures mirror real shapes; the values are invented."""

import io
import json
import zipfile

import pytest

from app.acquisition.providers.gdelt import Article, build_query_url, parse_articles
from app.acquisition.providers.sodir import parse_csv as parse_sodir
from app.acquisition.providers.statcan import parse_zip, select

STATCAN_CSV = (
    "REF_DATE,GEO,DGUID,Supply and disposition,Products,Unit of measure,UOM,UOM_ID,"
    "SCALAR_FACTOR,SCALAR_ID,VECTOR,COORDINATE,VALUE,STATUS,SYMBOL,TERMINATED,DECIMALS\n"
    '2026-06,Alberta,2016A000248,"Exports, disposition",Asphalt,Cubic metres,Cubic metres,'
    "301,units,0,v1,1.1.1,1234.5,,,,1\n"
    '2026-06,Nunavut,2016A000262,"Exports, disposition",Asphalt,Cubic metres,Cubic metres,'
    "301,units,0,v2,2.1.1,,..,,,1\n"
    '2026-05,Alberta,2016A000248,"Exports, disposition",Butane,Cubic metres,Cubic metres,'
    "301,units,0,v3,1.2.1,99,E,,,0\n"
)


def zipped(csv_text):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("25100081.csv", csv_text)
        archive.writestr("25100081_MetaData.csv", "metadata,ignored\n")
    return buffer.getvalue()


class TestStatCan:
    def test_the_data_member_is_parsed_and_the_metadata_member_is_ignored(self):
        observations = parse_zip(zipped(STATCAN_CSV), "https://example.org/25100081-eng.zip")
        assert len(observations) == 3
        first = observations[0]
        assert (first.provider, first.period, first.value_text, first.unit) == (
            "statcan",
            "2026-06",
            "1234.5",
            "Cubic metres",
        )
        assert first.series == {
            "geo": "Alberta",
            "products": "Asphalt",
            "disposition": "Exports, disposition",
            "scalar": "units",
        }

    def test_a_missing_value_keeps_its_symbol_and_an_estimate_flag_is_kept(self):
        by = {(o.series["geo"], o.period): o for o in parse_zip(zipped(STATCAN_CSV), "u")}
        missing = by[("Nunavut", "2026-06")]
        assert (missing.value_text, missing.flag) == (None, "..")
        estimated = by[("Alberta", "2026-05")]
        assert (estimated.value_text, estimated.flag) == ("99", "E")

    def test_selection_by_geography_product_and_disposition(self):
        chosen = select(
            parse_zip(zipped(STATCAN_CSV), "u"),
            geo="Alberta",
            products="Asphalt",
            disposition="Exports, disposition",
        )
        assert [o.period for o in chosen] == ["2026-06"]

    def test_a_zip_without_the_expected_columns_is_an_error(self):
        with pytest.raises(ValueError, match="REF_DATE"):
            parse_zip(zipped("A,B\n1,2\n"), "u")


SODIR = (
    "prfInformationCarrier,prfYear,prfMonth,prfPrdOilNetMillSm3,prfPrdGasNetBillSm3,"
    "prfPrdNGLNetMillSm3,prfPrdCondensateNetMillSm3,prfPrdOeNetMillSm3,"
    "prfPrdProducedWaterInFieldMillSm3,prfNpdidInformationCarrier\n"
    "EKOFISK,2026,7,0.31234,0.05,0.001,0.0,0.36,0.5,43506\n"
    "EKOFISK,2026,12,0.30000,0.04,0.002,0.0,0.34,0.4,43506\n"
)


class TestSodir:
    def test_each_measure_becomes_an_observation_with_its_own_unit(self):
        observations = parse_sodir("﻿" + SODIR, "https://example.org/sodir.csv")
        oil = [o for o in observations if o.series["measure"] == "oil"]
        assert [(o.series["field"], o.period, o.value_text, o.unit) for o in oil] == [
            ("EKOFISK", "2026-07", "0.31234", "MillSm3"),
            ("EKOFISK", "2026-12", "0.30000", "MillSm3"),
        ]
        gas = next(o for o in observations if o.series["measure"] == "gas")
        assert gas.unit == "BillSm3"
        assert {o.series["measure"] for o in observations} == {
            "oil",
            "gas",
            "ngl",
            "condensate",
            "oil_equivalent",
            "produced_water",
        }

    def test_oil_gas_ngl_and_condensate_stay_separate_measures(self):
        observations = parse_sodir(SODIR, "u")
        assert len({o.series["measure"] for o in observations if o.period == "2026-07"}) == 6

    def test_a_missing_header_is_an_error(self):
        with pytest.raises(ValueError, match="prfYear"):
            parse_sodir("a,b\n1,2\n", "u")


GDELT = json.dumps(
    {
        "articles": [
            {
                "url": "https://example.org/a",
                "url_mobile": "",
                "title": "Tanker traffic falls",
                "seendate": "20260924T061500Z",
                "socialimage": "https://example.org/i.jpg",
                "domain": "example.org",
                "language": "English",
                "sourcecountry": "United States",
            }
        ]
    }
)


class TestGdelt:
    def test_the_query_url_is_a_bounded_document_search(self):
        url = build_query_url('"Strait of Hormuz" sourcelang:eng', timespan="7d", maxrecords=25)
        assert url.startswith("https://api.gdeltproject.org/api/v2/doc/doc?")
        assert "mode=artlist" in url and "format=json" in url
        assert "maxrecords=25" in url and "timespan=7d" in url
        assert "%22Strait+of+Hormuz%22" in url

    def test_a_result_larger_than_the_hard_cap_is_refused(self):
        with pytest.raises(ValueError, match="maxrecords"):
            build_query_url("x", timespan="7d", maxrecords=500)

    def test_articles_are_leads_with_a_machine_coded_label(self):
        [article] = parse_articles(GDELT)
        assert isinstance(article, Article)
        assert (article.url, article.title, article.domain) == (
            "https://example.org/a",
            "Tanker traffic falls",
            "example.org",
        )
        assert article.seen_at == "2026-09-24T06:15:00Z"
        assert article.provenance == "gdelt-machine-coded"

    def test_an_empty_or_non_json_reply_is_no_articles_not_an_error(self):
        assert parse_articles("{}") == []
        assert parse_articles("") == []
        assert parse_articles("Timespan is too short.") == []


SODIR_TOTAL = (
    "prfYear,prfMonth,prfPrdOilNetMillSm3,prfPrdGasNetBillSm3,prfPrdNGLNetMillSm3,"
    "prfPrdCondensateNetMillSm3,prfPrdOeNetMillSm3,prfPrdProducedWaterInFieldMillSm3\n"
    "2026,7,6.1,10.2,0.4,0.3,17.0,12.0\n"
)


def test_the_national_total_export_has_no_field_column_and_is_labelled_as_a_total():
    observations = parse_sodir(SODIR_TOTAL, "u")
    assert {o.series["field"] for o in observations} == {"NCS total"}
    oil = next(o for o in observations if o.series["measure"] == "oil")
    assert (oil.period, oil.value_text, oil.unit) == ("2026-07", "6.1", "MillSm3")

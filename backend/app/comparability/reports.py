"""Build comparison reports from accepted measurements and the packs' source metadata.

Source binding is group-level: a metric group's sources back every point in it, until point-level
passages exist. Scope metadata (geography, population, methodology, seasonal adjustment) is not in
the packs yet, so every report starts with those gaps listed.
"""

from app.comparability.model import Period, Report
from app.investigation import Investigation
from app.normalisation.release import MeasurementRecord
from app.normalisation.vocabulary import Vocabulary


def build_reports(
    measurements: list[MeasurementRecord],
    investigations: list[Investigation],
    vocabulary: Vocabulary,
) -> list[Report]:
    groups = {}
    origins = {}
    for investigation in investigations:
        pack = investigation.pack
        origins.update({(pack.case_id, s.id): s.origin_group for s in pack.sources})
        for metric in pack.briefing.metrics if pack.briefing else []:
            groups[(pack.case_id, metric.id)] = metric.source_ids
    reports = []
    for measurement in measurements:
        definition = vocabulary.measures[measurement.measure]
        source_ids = list(groups[(measurement.case_id, measurement.metric_id)])
        source_ids += [
            b.source_id for b in measurement.bound_sources if b.source_id not in source_ids
        ]
        temporal = measurement.temporal
        reports.append(
            Report(
                id=measurement.id,
                entity=measurement.entity,
                measure=measurement.measure,
                statistic=definition.statistic,
                unit_symbol=vocabulary.units[definition.unit].symbol,
                period=Period(
                    kind=temporal.valid_kind,
                    start=temporal.valid_start,
                    end_exclusive=temporal.valid_end_exclusive,
                    at=temporal.valid_at,
                ),
                value_text=measurement.value_text,
                epistemic_status=measurement.epistemic_status,
                release_status=measurement.release_status,
                source_ids=list(source_ids),
                origin_groups=sorted({origins[(measurement.case_id, s)] for s in source_ids}),
            )
        )
    return reports

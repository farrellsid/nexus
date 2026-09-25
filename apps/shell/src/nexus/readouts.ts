// The static corner readouts: what the shown data is, how fresh it is, what the map leaves out, and
// how precise the selected record is. All of it comes from the generated pack summary and the
// records themselves, so a readout cannot claim more than the evidence pack says.
import { OIL_GEOGRAPHY, OIL_PACK } from './oilStops.ts';

const STOPS_PREFIX = 'nexus-oil-stops:';
const CORRIDORS_PREFIX = 'nexus-oil-corridors:';

const anchoredEntityIds = new Set(
  [...OIL_GEOGRAPHY.stops, ...OIL_GEOGRAPHY.routes].map(
    (record) => record.entityId,
  ),
);

/** Three lines: the as-of date, the pack and its schema, and how many pack entities the map places. */
export function packReadoutLines(): string[] {
  const onMap = OIL_PACK.entities.filter((entity) =>
    anchoredEntityIds.has(entity.id),
  ).length;
  const total = OIL_PACK.entities.length;
  return [
    `AS OF ${OIL_PACK.checkedOn}`,
    `PACK ${OIL_PACK.caseId} · SCHEMA ${OIL_PACK.schemaVersion.split('-')[0]}`,
    `${onMap} OF ${total} ENTITIES ON MAP · ${total - onMap} NOT ON MAP`,
  ];
}

const precisionLabel = (precision: string): string =>
  precision.replaceAll('_', ' ').toUpperCase();

/** The precision line for a selected entity id, or a plain statement when there is none to give. */
export function selectionReadout(entityId: string | undefined): string {
  if (!entityId) return 'SELECTED: NONE';
  const record = entityId.startsWith(STOPS_PREFIX)
    ? OIL_GEOGRAPHY.stops.find(
        (stop) => stop.id === entityId.slice(STOPS_PREFIX.length),
      )
    : entityId.startsWith(CORRIDORS_PREFIX)
      ? OIL_GEOGRAPHY.routes.find(
          (route) => route.id === entityId.slice(CORRIDORS_PREFIX.length),
        )
      : undefined;
  return record
    ? `SELECTED: ${record.label} · ${precisionLabel(record.precision)}`
    : 'SELECTED: NO STATED PRECISION';
}

/** What the HUD needs to show the readouts; it knows nothing about the pack. */
export const NEXUS_READOUTS = {
  staticLines: packReadoutLines,
  selectionLine: selectionReadout,
};

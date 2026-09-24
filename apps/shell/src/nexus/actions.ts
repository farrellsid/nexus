// The action layer: the small set of things anything driving the shell may ask it to do.
//
// The mouse, the scene director and (later) a chat box all go through `run`. Each verb checks its
// arguments, refuses anything it does not recognise, and can only reach the shell through
// `ShellControls`, which offers camera, layer and tour operations and nothing else. There is no
// network access here and no way to write evidence: a verb cannot do what the controls do not offer.

/** What a verb may do to the shell. Deliberately has no way to fetch data or change evidence. */
export interface ShellControls {
  /** Fly to a place. Returns false when the destination or place does not exist. */
  flyToPlace(destinationId: string, placeIndex: number): boolean;
  setLayerVisible(layerId: string, visible: boolean): Promise<void>;
  /** Start the guided tour. Returns false when it could not start (for example, one is running). */
  playTour(): Promise<boolean>;
  stopTour(): void;
  enterGlobalContext(): Promise<void>;
  exitGlobalContext(): Promise<void>;
  resetView(): void;
}

/** The ids a verb may name. Anything else is refused before it reaches the controls. */
export interface ActionCatalogue {
  /** Destination id to the number of places in it. */
  readonly places: Readonly<Record<string, number>>;
  readonly layerIds: readonly string[];
}

export type ActionResult =
  { readonly ok: true } | { readonly ok: false; readonly error: string };

export interface VerbDescription {
  readonly name: string;
  readonly summary: string;
  /** The arguments, as a reader would write them: `layer: string, visible: boolean`. */
  readonly arguments: string;
}

type Args = Readonly<Record<string, unknown>>;

type Parsed<T> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly error: string };

interface Verb<T> extends VerbDescription {
  parse(args: Args, catalogue: ActionCatalogue): Parsed<T>;
  run(controls: ShellControls, value: T): Promise<ActionResult>;
}

const fail = (error: string): { ok: false; error: string } => ({
  ok: false,
  error,
});
const done: ActionResult = { ok: true };

/** Reject any argument the verb does not declare, so a typo or an injected field is an error, not ignored. */
function unexpectedArgument(
  args: Args,
  known: readonly string[],
): string | null {
  const extra = Object.keys(args).find((key) => !known.includes(key));
  return extra === undefined ? null : `Unexpected argument "${extra}"`;
}

function readName(args: Args, key: string): Parsed<string> {
  const value = Object.hasOwn(args, key) ? args[key] : undefined;
  return typeof value === 'string' && value.length > 0 && value.length <= 80
    ? { ok: true, value }
    : fail(`"${key}" must be a non-empty string`);
}

function readBoolean(args: Args, key: string): Parsed<boolean> {
  const value = Object.hasOwn(args, key) ? args[key] : undefined;
  return typeof value === 'boolean'
    ? { ok: true, value }
    : fail(`"${key}" must be true or false`);
}

function noArguments(args: Args): Parsed<null> {
  const extra = unexpectedArgument(args, []);
  return extra ? fail(extra) : { ok: true, value: null };
}

/** Keep each verb's argument type checked where it is written, then store them all as one kind. */
const verb = <T>(definition: Verb<T>): Verb<unknown> =>
  definition as Verb<unknown>;

const VERBS: readonly Verb<unknown>[] = [
  verb<{ destination: string; place: number }>({
    name: 'fly_to_place',
    summary: 'Fly the camera to a place in a destination.',
    arguments: 'destination: string, place?: whole number (default 0)',
    parse(args, catalogue) {
      const extra = unexpectedArgument(args, ['destination', 'place']);
      if (extra) return fail(extra);
      const destination = readName(args, 'destination');
      if (!destination.ok) return destination;
      const count = Object.hasOwn(catalogue.places, destination.value)
        ? catalogue.places[destination.value]
        : undefined;
      if (count === undefined)
        return fail(`Unknown destination "${destination.value}"`);
      const place = Object.hasOwn(args, 'place') ? args['place'] : 0;
      if (
        typeof place !== 'number' ||
        !Number.isInteger(place) ||
        place < 0 ||
        place >= count
      )
        return fail(`"place" must be a whole number from 0 to ${count - 1}`);
      return { ok: true, value: { destination: destination.value, place } };
    },
    async run(controls, { destination, place }) {
      return controls.flyToPlace(destination, place)
        ? done
        : fail('That place could not be reached');
    },
  }),
  verb<{ layer: string; visible: boolean }>({
    name: 'set_layer',
    summary: 'Show or hide a data layer.',
    arguments: 'layer: string, visible: boolean',
    parse(args, catalogue) {
      const extra = unexpectedArgument(args, ['layer', 'visible']);
      if (extra) return fail(extra);
      const layer = readName(args, 'layer');
      if (!layer.ok) return layer;
      if (!catalogue.layerIds.includes(layer.value))
        return fail(`Unknown layer "${layer.value}"`);
      const visible = readBoolean(args, 'visible');
      if (!visible.ok) return visible;
      return {
        ok: true,
        value: { layer: layer.value, visible: visible.value },
      };
    },
    async run(controls, { layer, visible }) {
      await controls.setLayerVisible(layer, visible);
      return done;
    },
  }),
  verb<null>({
    name: 'play_tour',
    summary: 'Play the guided tour of the oil chokepoints.',
    arguments: 'none',
    parse: (args) => noArguments(args),
    async run(controls) {
      return (await controls.playTour())
        ? done
        : fail('The tour could not start');
    },
  }),
  verb<null>({
    name: 'stop_tour',
    summary: 'Stop the guided tour.',
    arguments: 'none',
    parse: (args) => noArguments(args),
    async run(controls) {
      controls.stopTour();
      return done;
    },
  }),
  verb<{ on: boolean }>({
    name: 'global_context',
    summary:
      'Pull back to the whole globe with the oil layers on, or return to the previous view.',
    arguments: 'on: boolean',
    parse(args) {
      const extra = unexpectedArgument(args, ['on']);
      if (extra) return fail(extra);
      const on = readBoolean(args, 'on');
      return on.ok ? { ok: true, value: { on: on.value } } : on;
    },
    async run(controls, { on }) {
      await (on ? controls.enterGlobalContext() : controls.exitGlobalContext());
      return done;
    },
  }),
  verb<null>({
    name: 'reset_view',
    summary: 'Return to the opening view.',
    arguments: 'none',
    parse: (args) => noArguments(args),
    async run(controls) {
      controls.resetView();
      return done;
    },
  }),
];

const VERBS_BY_NAME: ReadonlyMap<string, Verb<unknown>> = new Map(
  VERBS.map((entry) => [entry.name, entry]),
);

export interface ActionRegistry {
  describe(): readonly VerbDescription[];
  /** Run a verb by name. Never throws: a refusal or a failure comes back as `{ ok: false }`. */
  run(name: unknown, args?: unknown): Promise<ActionResult>;
}

export function createActionRegistry(
  controls: ShellControls,
  catalogue: ActionCatalogue,
): ActionRegistry {
  return {
    describe: () =>
      VERBS.map(({ name, summary, arguments: signature }) => ({
        name,
        summary,
        arguments: signature,
      })),
    async run(name, args = {}) {
      const found =
        typeof name === 'string' ? VERBS_BY_NAME.get(name) : undefined;
      if (!found)
        return fail(
          `Unknown action ${typeof name === 'string' ? `"${name.slice(0, 40)}"` : '(not a name)'}`,
        );
      if (typeof args !== 'object' || args === null || Array.isArray(args))
        return fail('Arguments must be an object');
      const parsed = found.parse(args as Args, catalogue);
      if (!parsed.ok) return fail(`${found.name}: ${parsed.error}`);
      try {
        return await found.run(controls, parsed.value);
      } catch (error) {
        return fail(
          `${found.name} failed: ${error instanceof Error ? error.message : 'unknown error'}`,
        );
      }
    },
  };
}

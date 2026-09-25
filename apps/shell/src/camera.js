import * as Cesium from 'cesium';
import { OIL_OVERVIEW } from './nexus/oilPlaces.ts';

const START_HEIGHT_M = 26_000_000;
const FLIGHT_DELAY_MS = 500;
const FLIGHT_SECONDS = 4.0;

/**
 * Open on the whole globe, then ease down to the oil overview.
 * @returns {Function} Cancels the pending or active startup flight.
 */
export function flyToStartView(viewer) {
  const at = (heightM) =>
    Cesium.Cartesian3.fromDegrees(
      OIL_OVERVIEW.longitude,
      OIL_OVERVIEW.latitude,
      heightM,
    );
  const straightDown = {
    heading: 0,
    pitch: Cesium.Math.toRadians(-90),
    roll: 0,
  };
  viewer.camera.setView({
    destination: at(START_HEIGHT_M),
    orientation: straightDown,
  });

  const timer = setTimeout(() => {
    if (viewer.isDestroyed()) return;
    viewer.camera.flyTo({
      destination: at(OIL_OVERVIEW.heightM),
      orientation: straightDown,
      duration: FLIGHT_SECONDS,
      easingFunction: Cesium.EasingFunction.CUBIC_IN_OUT,
    });
  }, FLIGHT_DELAY_MS);
  return () => {
    clearTimeout(timer);
    if (!viewer.isDestroyed()) viewer.camera.cancelFlight();
  };
}

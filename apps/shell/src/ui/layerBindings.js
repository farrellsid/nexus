import {
  flyToWorldTarget,
  registerWorldFocusRequestListener,
  routeWorldFocusRequest,
} from '../worldFocus.js';
import { registerNavigationAuthorityListener } from '../navigationPolicy.js';
/** Own manager subscriptions and the camera-entry events that outlive controls. */
export class LayerBindings {
  constructor({ viewer, services, operations, feedback, shareRestoration }) {
    Object.assign(
      this,
      {
        viewer,
        services,
        _feedback: feedback,
        _shareRestoration: shareRestoration,
      },
      operations,
    );
    this._disposed = false;
    this._dataManager = null;
    this._directionsShellModule = null;
    this._worldRequestFocusHandler = null;
    this._removeWorldRequestFocusListener = null;
    this._removeNavigationAuthorityListener = null;
    this._navigationOwnerChangedRemover = null;
    this._awarenessSelectedHandler = null;
    this._awarenessClearedHandler = null;
  }
  observeCamera() {
    this._worldRequestFocusHandler = (event) =>
      routeWorldFocusRequest(
        event,
        (detail, fly) => this._runExplicitWorldFocus(detail, fly),
        (detail) => flyToWorldTarget(this.viewer, detail),
      );
    this._removeWorldRequestFocusListener = registerWorldFocusRequestListener(
      window,
      this._worldRequestFocusHandler,
    );
    this._navigationOwnerChangedRemover =
      this.viewer.trackedEntityChanged.addEventListener((entity) => {
        if (entity && !this._disposed)
          this._stampNavigation({ cancelPendingSelection: false });
      });
    // A layer that flies the camera without assigning a tracked entity cannot
    // reach the listener above. It announces instead.
    this._removeNavigationAuthorityListener =
      registerNavigationAuthorityListener(window, (event) => {
        if (this._disposed) return;
        this._stampNavigation({
          cancelPendingSelection:
            event?.detail?.cancelPendingSelection !== false,
        });
      });
  }
  _connectDirectionsCamera() {
    if (!this._dataManager) {
      // Detaching: the layer outlives this shell, so it must not keep calling
      // a facade whose viewer is going away.
      this._directionsShellModule?.attachShellServices?.(null);
      this._directionsShellModule = null;
      return;
    }
    const directions = this._dataManager.layers?.get('directions')?.module;
    if (this._directionsShellModule !== directions) {
      this._directionsShellModule?.attachShellServices?.(null);
      this._directionsShellModule = null;
    }
    if (typeof directions?.attachShellServices !== 'function') return;
    this._directionsShellModule = directions;
    directions.attachShellServices({
      runNavigation: (navigate) =>
        this.runImmediateNavigation('route', navigate),
      floorFn: (lat, lon) => this.services.cachedGroundFloor(lat, lon),
      warmFn: (cells) => this.services.warmGroundFloor(cells),
      showToast: (message) => this._showToast(message),
    });
  }

  attachDataManager(dataManager) {
    if (this._disposed) return;
    this._dataManager = dataManager || null;
    if (this._dataManagerUnsubscribe) {
      this._dataManagerUnsubscribe();
      this._dataManagerUnsubscribe = null;
    }
    if (typeof this._dataManager?.subscribe === 'function') {
      this._dataManagerUnsubscribe = this._dataManager.subscribe((change) => {
        this._feedback._loadingFeedbackEvent = change;
        this._updateGlobalLoadingFeedback(performance.now());
      });
    }
    this._updateGlobalLoadingFeedback(performance.now());
    this._connectDirectionsCamera();
    this._shareRestoration.connect(this._dataManager);
  }
  stop() {
    if (this._disposed) return;
    this._disposed = true;
    this._removeWorldRequestFocusListener?.();
    this._removeWorldRequestFocusListener = null;
    this._worldRequestFocusHandler = null;
    this._navigationOwnerChangedRemover?.();
    this._navigationOwnerChangedRemover = null;
    this._removeNavigationAuthorityListener?.();
    this._removeNavigationAuthorityListener = null;
  }
  disconnect() {
    this._dataManagerUnsubscribe?.();
    this._dataManagerUnsubscribe = null;
    this._directionsShellModule?.attachShellServices?.(null);
    this._directionsShellModule = null;
    this._dataManager = null;
  }
}

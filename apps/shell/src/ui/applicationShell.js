import { ShellFacade } from './shellFacade.js';
import { LayerBindings } from './layerBindings.js';
import { PanelChrome } from './panelChrome.js';
import { VisualSettings } from './visualSettings.js';
import { NavigationController } from './navigationController.js';
import { ShareRestoration } from './shareRestoration.js';
import { DisplayBindings } from './displayBindings.js';
import { createStateChannel } from '../app/stateChannel.js';
import { UiLifetime } from './uiLifetime.js';
import { RecordingControls } from './recordingControls.js';
import { readShellElements } from './shellElements.js';
import { LocationNavigation } from './locationNavigation.js';
import { bindClearLayersControl } from './layers.js';
import { bindCameraOrientationControls } from './cameraOrientationControls.js';
import { createMapSourceControls } from './mapSource.js';
import { STYLES } from './effects.js';

import * as Cesium from 'cesium';

import { ShellFeedback } from './shellFeedback.js';

/**
 * Central UI orchestrator for the God's Eye View application.
 *
 * Responsibilities:
 * - Visual controls and presets backed by the VisualEffects controller.
 * - Bloom and sharpen post-processing toggle/intensity control.
 * - Draggable/collapsible panel system with localStorage persistence,
 *   z-order stacking, and viewport-clamped positioning.
 * - Location bar with city/POI preset pills, QWERTY key navigation,
 *   geocoding search, and inter-city world-jump transitions.
 * - Orbit controller integration for POI fly-around.
 * - Recording mode with safe-frame overlay and HUD mode switching.
 * - Share link encoding/decoding (delegates to ShareLinkManager).
 * - Toast notification system.
 * - Intel HUD lifecycle and variant switching.
 */

export class StyleManager extends ShellFacade {
  /**
   * @param {Cesium.Viewer} viewer - The CesiumJS viewer instance.
   * @param {object} [options]
   */
  constructor(
    viewer,
    { mapStackController = null, placeSearch, services } = {},
  ) {
    super();
    const { IntelHUD, ShareLinkManager, CelestialRing } = services;
    this.services = services;
    this._lifetime = new UiLifetime();
    this._recording = new RecordingControls({
      syncShareState: () => this._syncShareState(),
    });
    Object.assign(this, readShellElements());
    this._panelChrome = new PanelChrome({
      elements: {
        _leftPanelStack: this._leftPanelStack,
        _locationSearch: this._locationSearch,
        _ppToggles: this._ppToggles,
        _rightPanelStack: this._rightPanelStack,
      },
      operations: {
        _showToast: (...args) => this._showToast(...args),
      },
      readHud: () => this.hud,
      readShareLinks: () => this.shareLinkManager,
      readInitialShare: () => this._initialShareState,
      readScrollRestoreOwner: () => this._displayPortalScrollRestoreOwner,
      readDisplayScrollTop: () => this._standardDisplayScrollTop,
    });
    this._feedback = new ShellFeedback({
      readLayers: () => this._dataManager?.getAll?.() || [],
    });
    this.viewer = viewer;
    this.mapStackController = mapStackController;
    this.placeSearch = placeSearch;

    this._navigation = new NavigationController({
      viewer,
      searchInput: this._locationSearch,
      clearLocation: () => this.clearSearchedLocation(),
      getDataManager: () => this._dataManager,
      stopOrbit: () => this._stopOrbit(),
      cancelOrientation: () => this._cameraOrientationControls?.cancel(),
      showToast: (text) => this._showToast(text),
    });
    this._shareRestoration = new ShareRestoration({
      viewer,
      navigation: this._navigation,
      syncShareState: () => this._syncShareState(),
      feedback: this._feedback,
    });

    this._visualSettings = new VisualSettings({
      viewer,
      mapStackController,
      services: {
        setScopeTerminusOverride: services.setScopeTerminusOverride,
        clampScopeTerminusPct: services.clampScopeTerminusPct,
        getScopeMaskFeather: services.getScopeMaskFeather,
        getScopeTerminusOverride: services.getScopeTerminusOverride,
        governorRequestRender: services.governorRequestRender,
        holdContinuousRender: services.holdContinuousRender,
        isCelestialRingStyleSupported: services.isCelestialRingStyleSupported,
        isScopeMaskEnabled: services.isScopeMaskEnabled,
        releaseContinuousRender: services.releaseContinuousRender,
        setScopeMaskEnabled: services.setScopeMaskEnabled,
        setScopeMaskFeather: services.setScopeMaskFeather,
      },
      elements: {
        _bloomBtn: this._bloomBtn,
        _bloomSlider: this._bloomSlider,
        _bloomSliderRow: this._bloomSliderRow,
        _bloomSliderValue: this._bloomSliderValue,
        _celestialBtn: this._celestialBtn,
        _hudBtn: this._hudBtn,
        _hudLayoutRow: this._hudLayoutRow,
        _hudLayoutSelect: this._hudLayoutSelect,
        _ppToggles: this._ppToggles,
        _scopeBtn: this._scopeBtn,
        _scopeFeatherSlider: this._scopeFeatherSlider,
        _scopeFeatherValue: this._scopeFeatherValue,
        _sharpenBtn: this._sharpenBtn,
        _sharpenSlider: this._sharpenSlider,
        _sharpenSliderRow: this._sharpenSliderRow,
        _sharpenSliderValue: this._sharpenSliderValue,
        _sliderContainer: this._sliderContainer,
        _sliderPanel: this._sliderPanel,
        _styleIndicator: this._styleIndicator,
        _styleMiniValue: this._styleMiniValue,
      },
      operations: {
        _restorePanelState: (...args) => this._restorePanelState(...args),
        _layoutRightPanels: (...args) => this._layoutRightPanels(...args),
        _scheduleAdaptivePanelLayout: (...args) =>
          this._scheduleAdaptivePanelLayout(...args),
        _scheduleRightPanelLayout: (...args) =>
          this._scheduleRightPanelLayout(...args),
        _setMapStack: (...args) => this._setMapStack(...args),
        _syncPanelCollapseButton: (...args) =>
          this._syncPanelCollapseButton(...args),
        _syncShareState: (...args) => this._syncShareState(...args),
        setPanelCollapsed: (...args) => this.setPanelCollapsed(...args),
      },
      readHud: () => this.hud,
      readDataManager: () => this._dataManager,
      readShareLinks: () => this.shareLinkManager,
      readCelestialRing: () => this.celestialRing,
    });

    this._layerBindings = new LayerBindings({
      viewer,
      services: {
        cachedGroundFloor: services.cachedGroundFloor,
        warmGroundFloor: services.warmGroundFloor,
      },
      operations: {
        _updateGlobalLoadingFeedback: (...args) =>
          this._updateGlobalLoadingFeedback(...args),
        _stampNavigation: (...args) => this._stampNavigation(...args),
        _runExplicitWorldFocus: (...args) =>
          this._runExplicitWorldFocus(...args),
        runImmediateNavigation: (...args) =>
          this.runImmediateNavigation(...args),
        _showToast: (...args) => this._showToast(...args),
      },
      feedback: this._feedback,
      shareRestoration: this._shareRestoration,
    });

    this._windowResizeHandler = null;
    this._disposed = false;

    this._mapStackChangeHandler = null;

    this._locationNavigation = new LocationNavigation({
      viewer,
      placeSearch,
      navigation: this._navigation,
      services: {
        CITY_POIS: services.CITY_POIS,
        searchAndFlyTo: services.searchAndFlyTo,
        LocationSearch: services.LocationSearch,
        OrbitController: services.OrbitController,
        flyToPresetLocation: services.flyToPresetLocation,
        flyToPOI: services.flyToPOI,
        GLOBE_VIEW: services.GLOBE_VIEW,
        flyToGlobeView: services.flyToGlobeView,
      },
      elements: {
        _locationPills: this._locationPills,
        _poiRow: this._poiRow,
        _locationBarDivider: this._locationBarDivider,
        _locationSearch: this._locationSearch,
        _searchToggle: this._searchToggle,
        _resetGlobeBtn: this._resetGlobeBtn,
        _locationMiniCity: this._locationMiniCity,
        _locationMiniPoi: this._locationMiniPoi,
      },
      operations: {
        _beginDeferredNavigation: (...args) =>
          this._beginDeferredNavigation(...args),
        _reassertNavigationHandoff: (...args) =>
          this._reassertNavigationHandoff(...args),
        _settleLocationSearchUi: (...args) =>
          this._settleLocationSearchUi(...args),
        _runExplicitNavigation: (...args) =>
          this._runExplicitNavigation(...args),
        _stampNavigation: (...args) => this._stampNavigation(...args),
        _showToast: (...args) => this._showToast(...args),
      },
    });

    // Intel HUD
    this.hud = new IntelHUD(viewer);
    this._recording.hud = this.hud;

    // Full-globe sun/moon ring. It is a crisp screen-space overlay above the
    // Cesium canvas but below the HUD/detection/readout z ladder.
    this.celestialRing = new CelestialRing(viewer, {
      enabled: false,
      onAutoDisable: () =>
        this.setCelestialRingEnabled(false, {
          syncShare: !!this.shareLinkManager,
          focus: false,
        }),
    });

    // Share Link Manager
    this.shareLinkManager = new ShareLinkManager(viewer, {
      onRestore: async (state) => {
        return this._visualSettings.restoreShareState(state);
      },
      isNavigationCurrent: (generation) =>
        generation === this._navigationGeneration,
      cancelOwnedNavigation: () => this.viewer.camera.cancelFlight(),
    });
    this.shareLinkManager.setPanelStateProvider(() =>
      this._buildSharePanelState(),
    );
    this.shareLinkManager.setStyleParamStateProvider((styleName) => {
      const shader = STYLES[styleName];
      const stage = this.stages[styleName];
      if (!shader?.uniforms || !stage) return null;
      return Object.fromEntries(
        Object.keys(shader.uniforms).map((uniformName) => [
          uniformName,
          stage.uniforms[uniformName],
        ]),
      );
    });
    this._shareState = createStateChannel(() => this._readShareState());
    this._shareState.subscribe(
      ({ state }) => {
        this.shareLinkManager.onToggleChange(
          state.bloomEnabled,
          state.sharpenEnabled,
          state.options,
        );
      },
      { emitCurrent: false },
    );
    // Parse before panel chrome initializes so every valid share URL starts
    // from deterministic markup defaults instead of recipient-local panel
    // preferences. Encoded panel fields are applied after all panels exist.
    this._shareRestoration.attachLinks(this.shareLinkManager);

    this._initStages();
    this._initBloomSharpen();
    this._displayBindings = new DisplayBindings({
      viewer,
      services: {
        setScopeMaskEnabled: services.setScopeMaskEnabled,
        isScopeMaskEnabled: services.isScopeMaskEnabled,
        setScopeMaskFeather: services.setScopeMaskFeather,
      },
      elements: {
        _locationSearch: this._locationSearch,
        _bloomBtn: this._bloomBtn,
        _bloomSlider: this._bloomSlider,
        _sharpenBtn: this._sharpenBtn,
        _sharpenSlider: this._sharpenSlider,
        _scopeBtn: this._scopeBtn,
        _scopeFeatherSlider: this._scopeFeatherSlider,
        _hudLayoutSelect: this._hudLayoutSelect,
        _hudBtn: this._hudBtn,
        _cleanViewBtn: this._cleanViewBtn,
        _cleanViewExitBtn: this._cleanViewExitBtn,
        _celestialBtn: this._celestialBtn,
        _scopeFeatherValue: this._scopeFeatherValue,
        _sharpenSliderValue: this._sharpenSliderValue,
      },
      operations: {
        setStyle: (...args) => this.setStyle(...args),
        _updateHudButtonState: (...args) => this._updateHudButtonState(...args),
        _syncShareState: (...args) => this._syncShareState(...args),
        _toggleOrbit: (...args) => this._toggleOrbit(...args),
        toggleCleanView: (...args) => this.toggleCleanView(...args),
        _setBloomEnabled: (...args) => this._setBloomEnabled(...args),
        _setBloomIntensity: (...args) => this._setBloomIntensity(...args),
        _setSharpenEnabled: (...args) => this._setSharpenEnabled(...args),
        _applySharpenIntensity: (...args) =>
          this._applySharpenIntensity(...args),
        _setHudVariant: (...args) => this._setHudVariant(...args),
        setCelestialRingEnabled: (...args) =>
          this.setCelestialRingEnabled(...args),
      },
      readState: () => ({
        shareLinkManager: this.shareLinkManager,
        hud: this.hud,
        bloomEnabled: this.bloomEnabled,
        sharpenEnabled: this.sharpenEnabled,
        celestialRing: this.celestialRing,
        celestialRingEnabled: this.celestialRingEnabled,
      }),
    });
    this._initUI();
    this._initMapStackControl();
    this._initPanelChrome();
    this._initLeftPanelAdaptiveLayout();
    this._initRightPanelAdaptiveLayout();
    this._initLocationBar();
    this._initShareButton();
    this._initCameraOrientationControls();
    this._initClearSelectedLayersButton();
    this._initHUDToggle();
    this._applyGlobalPostDefaults();
    this._initOrbit();
    this._initRecordingOverlay();
    this._startAnimationLoop();
    this._startFeedbackTicker();
    this._updateStyleMiniStatus();
    this._updateLocationMiniStatus();

    this._shareRestoration.start();

    // Keep the parameter panel from overlapping toggle controls.
    this._layoutRightPanels();
    this._windowResizeHandler = () => {
      this._scheduleRightPanelLayout({ reconsiderAutoCollapse: true });
      this._scheduleLeftPanelLayout({ reconsiderAutoCollapse: true });
    };
    window.addEventListener('resize', this._windowResizeHandler);
    // The loading-chip ticker is stopped while the tab is hidden (it can do no
    // useful work off-screen and must not hold a 60ms timer there). Resample on
    // return so the time-driven reducer catches up on real elapsed time — and
    // re-arms its own ticker if the batch is still running.
    this._feedback.observeVisibility();
    this._layerBindings.observeCamera();
  }

  // Compatibility reads for existing controls, scene snapshots and Cockpit.

  /** Advance camera authority and settle any older search UI immediately. */
  _stampNavigation({
    cancelPendingSelection = true,
    clearSearchedLocation = true,
  } = {}) {
    return this._navigation._stampNavigation(...arguments);
  }

  /** Release every follow owner while preserving Contact and vessel selection. */
  _releaseFollowCamera({
    preserveVesselSelection = true,
    preserveCameraFlight = false,
    trackingOrigin = 'tool',
  } = {}) {
    return this._navigation._releaseFollowCamera(...arguments);
  }

  /** Accept a delayed lookup without releasing its current camera owner. */
  _beginDeferredNavigation(
    noun = 'location',
    { cancelPendingSelection = true } = {},
  ) {
    return this._navigation._beginDeferredNavigation(...arguments);
  }

  /** Public authority facade used by validated voice camera destinations. */
  runImmediateNavigation(noun, navigate, releaseOptions = undefined) {
    return this._runExplicitNavigation(noun, navigate, releaseOptions);
  }

  /** Route a valid vessel/fire request through the shared navigation policy. */
  _runExplicitWorldFocus(detail, fly) {
    return this._runExplicitNavigation(detail?.kind || 'target', fly);
  }

  /**
   * Sets the bloom intensity, updates the slider UI, and applies the value.
   * @param {number} intensity - Raw intensity percentage.
   * @param {object} [options]
   * @param {boolean} [options.syncShare=true] - Whether to push state to the share link.
   * @returns {void}
   */
  _setBloomIntensity(intensity, { syncShare = true } = {}) {
    return this._visualSettings._setBloomIntensity(...arguments);
  }

  /**
   * Wires up all primary UI event listeners: style buttons, keyboard shortcuts
   * (1-8 style keys, H/O/V/F/D/C hotkeys, Escape), AI prompt input with
   * debounce, bloom/sharpen/HUD toggles, detection density slider, and
   * clean-view toggle.
   * @returns {void}
   */
  _initUI() {
    this._displayBindings._initUI();
  }

  /**
   * Renders the owner-approved map stack chip row from the matching controller
   * entries. Cesium ion/Bing chips remain keyboard-focusable but unavailable,
   * with an accessible explanation, until a CESIUM_ION_TOKEN is configured.
   * @returns {void}
   */
  _initMapStackControl() {
    if (!this.mapStackController) return;
    this._mapSourceControls?.destroy();
    this._mapSourceControls = createMapSourceControls({
      container: this._mapStackChips,
      statusElement: this._mapStackStatus,
      controller: this.mapStackController,
      subscribe: (onChange) => {
        window.addEventListener('gev:map-stack-changed', onChange);
        return () =>
          window.removeEventListener('gev:map-stack-changed', onChange);
      },
      claimSelection: () => this.shareLinkManager?.claimRestoreLane?.('map'),
      onStateChanged: () => this._syncShareState(),
      onError: (message) => this._showToast(message),
    });
  }

  /**
   * Switches the active map/globe source stack.
   * @param {string} stackId - Map stack id.
   * @param {object} [options]
   * @param {boolean} [options.syncShare=true] - Whether to update the share link.
   * @returns {Promise<void>}
   */
  async _setMapStack(stackId, { syncShare = true } = {}) {
    if (!this.mapStackController) return;
    return this._mapSourceControls.select(stackId, { syncShare });
  }

  /**
   * Syncs the map stack chip row and status chip with controller state. The
   * lit chip always follows `state.activeId`, never the click — a rejected or
   * superseded switch therefore leaves the genuinely active stack lit.
   * @param {object} state - Map stack controller state.
   * @returns {void}
   */
  _renderMapStackState(state) {
    this._mapSourceControls?.render(state);
  }

  /**
   * Pushes the current visual state (bloom, sharpen, HUD, detection) to
   * the ShareLinkManager so the URL hash stays in sync.
   * @returns {void}
   */

  _syncShareState() {
    if (this._disposed) return;
    this._shareState.publish({ type: 'settings-changed' });
  }

  _setCommandDockPanelPinState(
    panelId,
    pin,
    { restore = false, persist = true, syncShare = true } = {},
  ) {
    return this._panelChrome._setCommandDockPanelPinState(...arguments);
  }

  /**
   * Configures intentional hover-expand / leave-collapse behavior on a panel.
   * Uses separate open/close timers to prevent accidental flicker from fast
   * mouse passes. Wheel events cancel pending opens to avoid surprise expansion
   * during scroll-through.
   * @param {string} panelId - DOM id of the panel element.
   * @param {object} [options]
   * @param {number} [options.openDelayMs=850] - Hover dwell time before auto-expanding.
   * @param {number} [options.closeDelayMs=1000] - Delay after pointer leaves before collapsing.
   * @returns {void}
   */
  _initAutoHoverPanel(
    panelId,
    { openDelayMs = 850, closeDelayMs = 1000 } = {},
  ) {
    return this._panelChrome._initAutoHoverPanel(...arguments);
  }

  /**
   * Makes a panel draggable via its handle element. Implements:
   * - Z-order promotion: each pointerdown increments the global z-counter
   *   so the clicked panel floats above siblings.
   * - Viewport clamping: drag moves are clamped to a 6px inset from all edges.
   * - Right-rail pinning: pp-toggles panel is re-anchored right after drag.
   * @param {string} panelId - DOM id of the panel.
   * @param {HTMLElement} panelEl - The panel DOM element.
   * @param {HTMLElement} handleEl - The drag handle element within the panel.
   * @returns {void}
   */

  /**
   * Programmatically collapses or expands a panel, persists the state,
   * and triggers layout recalculation for dependent panels.
   * @param {string} panelId - DOM id of the panel.
   * @param {boolean} collapsed - Whether to collapse the panel.
   * @param {object} [options] Disclosure ownership options.
   * @param {boolean} [options.explicit=false] Whether a direct user action owns the panel lane.
   * @returns {void}
   */
  setPanelCollapsed(
    panelId,
    collapsed,
    {
      explicit = false,
      restore = false,
      persist = true,
      syncShare = true,
    } = {},
  ) {
    return this._panelChrome.setPanelCollapsed(...arguments);
  }

  /**
   * Toggles "clean view" mode which hides all UI panels via a CSS body class.
   * @param {boolean} [forceEnabled] - Explicit on/off. Omit to toggle.
   * @returns {void}
   */
  toggleCleanView(forceEnabled) {
    const shouldEnable =
      typeof forceEnabled === 'boolean'
        ? forceEnabled
        : !document.body.classList.contains('ui-clean-view');
    document.body.classList.toggle('ui-clean-view', shouldEnable);
    if (this._cleanViewBtn) {
      this._cleanViewBtn.classList.toggle('active', shouldEnable);
    }
    this._scheduleLeftPanelLayout();
  }

  // ── Public control facade ──────────────────────────────────────────────
  // Deliberate API for voice tools and scripting. Every setter keeps the DOM
  // sliders, share-link state, and scene snapshots in sync, and returns
  // { ok, ...resultingState } so callers confirm only what actually happened.

  /**
   * Controls the celestial ring. The Display button uses `focus=true` when the
   * ring is disabled or unavailable at the current zoom, turning the control
   * into a reveal action instead of requiring a separate globe-navigation step.
   * @param {boolean} enabled
   * @param {object} [options]
   * @param {boolean} [options.syncShare=true]
   * @param {boolean} [options.focus=false]
   * @returns {{ok:boolean, celestialRing:{enabled:boolean,visible:boolean}, cameraFocused:boolean, error?:string}}
   */
  setCelestialRingEnabled(enabled, { syncShare = true, focus = false } = {}) {
    return this._visualSettings.setCelestialRingEnabled(...arguments);
  }

  /**
   * Captures the current camera position and orientation as a serializable object.
   * @returns {{lat: number, lon: number, alt: number, heading: number, pitch: number, roll: number}|null}
   */
  getCameraState() {
    const carto = this.viewer.camera.positionCartographic;
    if (!carto) return null;
    return {
      lat: Cesium.Math.toDegrees(carto.latitude),
      lon: Cesium.Math.toDegrees(carto.longitude),
      alt: carto.height,
      heading: Cesium.Math.toDegrees(this.viewer.camera.heading),
      pitch: Cesium.Math.toDegrees(this.viewer.camera.pitch),
      roll: Cesium.Math.toDegrees(this.viewer.camera.roll),
    };
  }

  /**
   * Restores a full visual state snapshot, applying style, bloom, sharpen,
   * HUD, detection, and per-style shader uniforms. Used by scene recipes
   * and share-link restore. Async so the map-stack switch resolves before
   * the share state is synced; callers may fire-and-forget.
   * @param {object} [state={}] - Visual state object (as returned by getVisualState).
   * @param {object} [options]
   * @param {(() => boolean)|null} [options.isCurrent] Caller liveness predicate.
   *   The map-stack switch is this method's ONLY suspension point, and the
   *   shader-uniform writes come after it — so a caller superseded while that
   *   switch is in flight would otherwise resume and commit the look of a
   *   state the operator has already moved past. Scene playback reproduced
   *   exactly that: a stale shot's uniforms landing on top of the live run.
   *   Omit it and the method behaves as it always has.
   * @returns {Promise<boolean>} Whether the state was committed.
   */
  async applyVisualState(state = {}, { isCurrent = null } = {}) {
    return this._visualSettings.applyVisualState(...arguments);
  }

  // ── Parameter Sliders ─────────────────────────

  /**
   * Rebuilds the parameter slider panel for the given style's shader uniforms.
   * Creates a labeled range input for each tunable uniform. Hides the panel
   * for 'normal' mode which has no shader parameters.
   * @param {string} styleName - Style name whose uniforms to display.
   * @returns {void}
   */
  _updateSliderPanel(styleName, { reveal = false } = {}) {
    return this._visualSettings._updateSliderPanel(...arguments);
  }

  // ── Style switching ───────────────────────────

  /**
   * Switches the active visual style. Handles full lifecycle:
   * 1. Crossfades the previous shader stage intensity to 0.
   * 2. Crossfades the new shader stage intensity to 1.
   * 3. Applies style preset defaults (bloom/sharpen/HUD) if applyPreset is true.
   * 4. Updates button highlights, style indicator, slider panel, HUD, and detection overlay.
   * @param {string} styleName - Target style ('normal'|'retro'|'surveillance'|'thermal'|'anime'|'noir'|'snow').
   * @param {object} [options]
   * @param {boolean} [options.applyPreset=true] - Whether to apply STYLE_PRESET_DEFAULTS for the new style.
   * @returns {void}
   */
  setStyle(
    styleName,
    {
      applyPreset = true,
      revealParameters = applyPreset,
      restore = false,
    } = {},
  ) {
    return this._visualSettings.setStyle(...arguments);
  }

  // ── Shader transitions ────────────────────────

  /**
   * Style animation loop — self-stopping (perf wave 2). Runs only while a
   * crossfade is in flight or an animated (time-uniform) stage is visible,
   * holding continuous scene render for exactly that long. Re-armed by
   * _startTransition and by _setStageIntensity enabling an animated stage.
   * The traffic sync chip no longer rides this loop — it has its own 500 ms
   * interval (see _startFeedbackTicker).
   */
  _startAnimationLoop() {
    this._visualEffects.startAnimationLoop();
  }

  /** Turn every enabled data layer off, report the outcome, and never run two clears at once. */
  clearSelectedLayers() {
    if (this._clearSelectedLayersPromise)
      return this._clearSelectedLayersPromise;
    const nothing = {
      targetIds: [],
      items: [],
      clearedIds: [],
      notClearedIds: [],
    };
    if (this._disposed || !this._dataManager?.clearSelectedLayers)
      return Promise.resolve({ ...nothing, cancelled: this._disposed });
    this._clearLayersControl?.setBusy(true);
    const operation = this._dataManager
      .clearSelectedLayers({ origin: 'user' })
      .then((result) => {
        const noun = (n) => `${n} data layer${n === 1 ? '' : 's'}`;
        if (result.targetIds.length === 0)
          this._showToast('No selected data layers');
        else if (result.notClearedIds.length > 0)
          this._showToast(
            `${noun(result.notClearedIds.length)} could not be cleared`,
          );
        else this._showToast(`Cleared ${noun(result.clearedIds.length)}`);
        return result;
      })
      .catch((error) => {
        console.warn('[Data] clear selected layers failed', error);
        this._showToast('Selected data layers could not be cleared');
        return { ...nothing, error };
      })
      .finally(() => {
        if (!this._disposed) this._clearLayersControl?.setBusy(false);
        this._clearSelectedLayersPromise = null;
      });
    this._clearSelectedLayersPromise = operation;
    return operation;
  }

  /** Wire the top-center action that clears only manager-owned data layers. */
  _initClearSelectedLayersButton() {
    if (!this._clearSelectedLayersBtn) return;
    this._clearLayersControl?.destroy();
    this._clearLayersControl = bindClearLayersControl(
      this._clearSelectedLayersBtn,
      () => this.clearSelectedLayers(),
    );
  }

  /** Wire Google Maps-style tilt and north-up camera actions. */
  _initCameraOrientationControls() {
    this._cameraOrientationControls?.destroy();
    this._cameraOrientationControls = bindCameraOrientationControls({
      viewer: this.viewer,
      elements: {
        tiltButton: this._tiltMapBtn,
        northButton: this._northUpBtn,
      },
      runNavigation: (noun, navigate) =>
        this._navigation.runOrientation(noun, navigate),
      showToast: (message) => this._showToast(message),
    });
  }

  // ── Share Button ─────────────────────────────

  /**
   * Wires the share button click to copy the current share link to the clipboard.
   * @returns {void}
   */
  _initShareButton() {
    this._lifetime.listen(this._shareBtn, 'click', async () => {
      const success = await this.shareLinkManager.copyLink();
      if (!this._disposed)
        this._showToast(success ? 'Link copied!' : 'Copy failed');
    });
  }

  // ── HUD Toggle ───────────────────────────────

  /**
   * Initializes the HUD to its default 'tactical' variant and shows it.
   * @returns {void}
   */
  _initHUDToggle() {
    if (this._hudLayoutSelect) {
      this._hudLayoutSelect.value = 'tactical';
    }
    this._setHudVariant('tactical');
    this.hud.setMode('on');
    this._updateHudButtonState();
  }

  /** Terminal result for the complete initial share restoration. */
  get initialRestorePromise() {
    return (
      this._initialShareRestorePromise ||
      Promise.resolve({ status: 'not-requested' })
    );
  }

  /**
   * Tear down the StyleManager — cancel animation loop, clear intervals,
   * and release resources. Call this before discarding the instance to
   * prevent leaked rAF loops and event listeners.
   * @returns {Promise<void>} Resolves after focused-session state restoration.
   */
  async dispose() {
    if (this._disposed) return;
    this._shareRestoration.destroy();
    this._feedback._globalStatusNotice = null;
    if (this._globalLoadingStatus) this._globalLoadingStatus.hidden = true;
    this._disposed = true;
    this._navigation.stop();
    this._shareState.destroy();
    this._locationNavigation.destroy();
    this._lifetime.destroy();
    this._recording.destroy();
    this._panelChrome.destroy();
    this._feedback.destroy();

    this._displayBindings.destroy();
    this._mapSourceControls?.destroy();
    this._cameraOrientationControls?.destroy();
    this._clearLayersControl?.destroy();
    this._visualSettings.stop();
    this.shareLinkManager?.destroy();
    this._layerBindings.stop();

    this._navigation.destroy();
    this._layerBindings.disconnect();

    if (this._windowResizeHandler) {
      window.removeEventListener('resize', this._windowResizeHandler);
      this._windowResizeHandler = null;
    }
    this.celestialRing?.destroy();
    this._visualSettings.destroy();
  }
}

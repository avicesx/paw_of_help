
(function () {
  const DEFAULT_CENTER = [56.8389, 60.6057];

  function setFieldValue(id, value) {
    const el = document.getElementById(id);
    if (el) el.value = value;
  }

  function getFieldValue(id) {
    return (document.getElementById(id)?.value || '').trim();
  }

  function ensureLeafletReady(mapId) {
    const mapEl = document.getElementById(mapId);
    if (!mapEl) return false;
    if (!window.L) {
      mapEl.innerHTML = '<div class="map-fallback">Карта недоступна. Проверь подключение к интернету.</div>';
      return false;
    }
    return true;
  }

  window.initLocationMap = function initLocationMap({
    mapId,
    addressInputId,
    latInputId,
    lngInputId,
    zoom = 12,
    defaultCenter = DEFAULT_CENTER,
  }) {
    if (!ensureLeafletReady(mapId)) return;
    const mapEl = document.getElementById(mapId);
    if (mapEl.dataset.mapReady === '1') return;
    mapEl.dataset.mapReady = '1';

    const savedLat = parseFloat(getFieldValue(latInputId));
    const savedLng = parseFloat(getFieldValue(lngInputId));
    const center = Number.isFinite(savedLat) && Number.isFinite(savedLng)
      ? [savedLat, savedLng]
      : defaultCenter;

    const map = L.map(mapId, {
      zoomControl: false,
      attributionControl: false,
    }).setView(center, zoom);

    L.control.zoom({ position: 'bottomright' }).addTo(map);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      crossOrigin: true,
    }).addTo(map);

    const marker = L.marker(center, { draggable: true }).addTo(map);

    function applyPosition(latlng, writeAddress = true) {
      const lat = Number(latlng.lat).toFixed(6);
      const lng = Number(latlng.lng).toFixed(6);
      setFieldValue(latInputId, lat);
      setFieldValue(lngInputId, lng);
      if (writeAddress && !getFieldValue(addressInputId)) {
        setFieldValue(addressInputId, `${lat}, ${lng}`);
      }
    }

    applyPosition(marker.getLatLng(), false);

    map.on('click', (event) => {
      marker.setLatLng(event.latlng);
      applyPosition(event.latlng);
    });

    marker.on('dragend', () => {
      applyPosition(marker.getLatLng());
    });

    setTimeout(() => map.invalidateSize(), 250);
  };
})();

const DEFAULT_MAP_CENTER = [56.8389, 60.6057];

function setMapStatus(statusId, text) {
  const el = statusId ? document.getElementById(statusId) : null;
  if (el) el.textContent = text || "";
}

function setHiddenCoords(latId, lngId, lat, lng) {
  const latEl = document.getElementById(latId);
  const lngEl = document.getElementById(lngId);
  if (latEl) latEl.value = lat != null ? String(lat) : "";
  if (lngEl) lngEl.value = lng != null ? String(lng) : "";
}

function normalizeAddressFromNominatim(data) {
  if (!data) return "";
  if (data.display_name) return data.display_name;

  const a = data.address || {};
  return [
    a.road,
    a.house_number,
    a.suburb,
    a.city || a.town || a.village,
    a.state,
  ].filter(Boolean).join(", ");
}

async function reverseGeocode(lat, lng) {
  const url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lng)}&accept-language=ru`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Не удалось получить адрес");
  return normalizeAddressFromNominatim(await res.json());
}

async function geocodeAddress(address) {
  const url = `https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&q=${encodeURIComponent(address)}&accept-language=ru`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Не удалось найти адрес");
  const data = await res.json();
  if (!Array.isArray(data) || !data.length) return null;
  return {
    lat: Number(data[0].lat),
    lng: Number(data[0].lon),
    address: normalizeAddressFromNominatim(data[0]) || address,
  };
}

function initAddressMap(options) {
  const {
    mapId,
    inputId,
    latId,
    lngId,
    statusId,
    searchButtonId,
    defaultCenter = DEFAULT_MAP_CENTER,
    defaultZoom = 14,
  } = options;

  const mapEl = document.getElementById(mapId);
  const inputEl = document.getElementById(inputId);

  if (!mapEl || !inputEl) return null;

  if (typeof L === "undefined") {
    mapEl.innerHTML = '<div class="map-fallback">Карта не загрузилась. Проверь интернет.</div>';
    setMapStatus(statusId, "Карта не загрузилась.");
    return null;
  }

  const map = L.map(mapId, {
    zoomControl: true,
    attributionControl: false,
  }).setView(defaultCenter, defaultZoom);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
  }).addTo(map);

  const marker = L.marker(defaultCenter, { draggable: true }).addTo(map);
  setHiddenCoords(latId, lngId, defaultCenter[0], defaultCenter[1]);

  async function applyPoint(lat, lng, { move = true, updateAddress = true } = {}) {
    marker.setLatLng([lat, lng]);
    setHiddenCoords(latId, lngId, lat, lng);

    if (move) map.setView([lat, lng], Math.max(map.getZoom(), 15));

    if (updateAddress) {
      setMapStatus(statusId, "Определяю адрес...");
      try {
        const address = await reverseGeocode(lat, lng);
        inputEl.value = address || `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
        setMapStatus(statusId, "Адрес выбран на карте.");
      } catch (err) {
        inputEl.value = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
        setMapStatus(statusId, "Адрес не найден, сохранены координаты.");
      }
    }
  }

  map.on("click", (event) => {
    applyPoint(event.latlng.lat, event.latlng.lng);
  });

  marker.on("dragend", () => {
    const pos = marker.getLatLng();
    applyPoint(pos.lat, pos.lng, { move: false });
  });

  const searchButton = searchButtonId ? document.getElementById(searchButtonId) : null;
  async function findTypedAddress() {
    const value = inputEl.value.trim();
    if (!value) return;

    setMapStatus(statusId, "Ищу адрес...");
    try {
      const found = await geocodeAddress(value);
      if (!found) {
        setMapStatus(statusId, "Адрес не найден. Выбери точку на карте.");
        return;
      }

      inputEl.value = found.address || value;
      await applyPoint(found.lat, found.lng, { updateAddress: false });
      setMapStatus(statusId, "Адрес найден.");
    } catch (err) {
      setMapStatus(statusId, "Не удалось найти адрес.");
    }
  }

  if (searchButton) {
    searchButton.addEventListener("click", findTypedAddress);
  }

  inputEl.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      findTypedAddress();
    }
  });

  inputEl.addEventListener("blur", () => {
    const value = inputEl.value.trim();
    const lat = document.getElementById(latId)?.value;
    const lng = document.getElementById(lngId)?.value;
    if (value && (!lat || !lng)) findTypedAddress();
  });

  setTimeout(() => map.invalidateSize(), 250);

  return { map, marker, applyPoint, findTypedAddress };
}

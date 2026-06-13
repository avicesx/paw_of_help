const EVENT_ORG_ID_KEY = "paw_org_id";
let currentEventsMonth = new Date();

function getOrgId() {
  const orgId = localStorage.getItem(EVENT_ORG_ID_KEY);
  return orgId || "1";
}

function eventTypeLabel(type) {
  const map = {
    adoption: "Пристройство",
    fundraising: "Сбор помощи",
    volunteer: "Волонтёрство",
    meeting: "Встреча",
    other: "Другое"
  };
  return map[type] || type || "Мероприятие";
}

function eventDateLabel(value) {
  if (!value) return "Дата не указана";
  try {
    return new Date(value).toLocaleString("ru-RU", {
      day: "2-digit",
      month: "long",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  } catch {
    return String(value);
  }
}

async function loadEventsPage() {
  const list = document.getElementById("eventsList");
  if (!list) return;

  list.innerHTML = '<div class="empty-small">Загрузка мероприятий...</div>';

  try {
    const orgId = document.getElementById("eventsOrgFilter")?.value || "";
    const type = document.getElementById("eventsTypeFilter")?.value || "";
    const search = (document.getElementById("eventsSearch")?.value || "").trim().toLowerCase();
    const path = orgId ? `/events?organization_id=${encodeURIComponent(orgId)}` : "/events";
    const { data } = await apiRequest(path);
    let events = data || [];

    if (type) events = events.filter(event => event.event_type === type);
    if (search) {
      events = events.filter(event =>
        (event.title || "").toLowerCase().includes(search) ||
        (event.description || "").toLowerCase().includes(search) ||
        (event.location || "").toLowerCase().includes(search)
      );
    }

    renderEventsList(events);
  } catch (err) {
    list.innerHTML = `<div class="empty-small">${escapeHtml(err.message || "Ошибка загрузки мероприятий")}</div>`;
  }
}

function renderEventsList(events) {
  const list = document.getElementById("eventsList");
  if (!list) return;

  if (!events.length) {
    list.innerHTML = '<div class="empty-small">Мероприятий пока нет</div>';
    return;
  }

  list.innerHTML = events.map(event => `
    <article class="event-card">
      <div class="event-card-head">
        <div class="event-date-box">${escapeHtml(shortEventDate(event.start_datetime))}</div>
        <div class="event-info">
          <h2>${escapeHtml(event.title || "Без названия")}</h2>
          <div class="event-type">${escapeHtml(eventTypeLabel(event.event_type))}</div>
        </div>
      </div>
      <p>${escapeHtml(event.description || "Описание не указано")}</p>
      <div class="event-meta">Начало: ${escapeHtml(eventDateLabel(event.start_datetime))}</div>
      <div class="event-meta">Окончание: ${escapeHtml(eventDateLabel(event.end_datetime))}</div>
      <div class="event-meta">Место: ${escapeHtml(event.location || "Не указано")}</div>
      <div id="eventPreviewMap-${event.id}" class="event-preview-map" data-location="${escapeHtml(event.location || "")}"></div>
      <div class="event-actions">
        <button class="task-primary-btn" type="button" onclick="registerForEvent(${event.id})">Участвовать</button>
        <button class="task-outline-btn" type="button" onclick="cancelEventRegistration(${event.id})">Отменить участие</button>
      </div>
    </article>
  `).join("");

  initEventPreviewMaps(events);
}



async function initEventPreviewMaps(events) {
  if (typeof L === "undefined" || typeof geocodeAddress !== "function") return;

  const candidates = (events || []).filter(event => event?.id && event?.location).slice(0, 8);

  for (const event of candidates) {
    const el = document.getElementById(`eventPreviewMap-${event.id}`);
    if (!el || el.dataset.initialized === "1") continue;
    el.dataset.initialized = "1";

    try {
      const found = await geocodeAddress(event.location);
      if (!found) {
        el.style.display = "none";
        continue;
      }

      const map = L.map(el, {
        zoomControl: false,
        attributionControl: false,
        dragging: false,
        scrollWheelZoom: false,
        doubleClickZoom: false,
        boxZoom: false,
        keyboard: false,
        tap: false,
      }).setView([found.lat, found.lng], 15);

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
      }).addTo(map);

      L.marker([found.lat, found.lng]).addTo(map);
      setTimeout(() => map.invalidateSize(), 150);
    } catch (err) {
      console.warn("EVENT PREVIEW MAP ERROR:", err);
      el.style.display = "none";
    }
  }
}

function shortEventDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit" });
}

async function eventGetCurrentUserSafe() {
  try {
    const { data } = await apiRequest("/users/me", { auth: true });
    return data;
  } catch {
    const { data } = await apiRequest("/auth/me", { auth: true });
    return data;
  }
}

async function eventFindExistingUserOrganization() {
  if (!getToken()) return null;
  try {
    const user = await eventGetCurrentUserSafe();
    const { data } = await apiRequest("/organizations");
    const orgs = Array.isArray(data) ? data : [];
    return orgs.find((org) => Number(org.created_by) === Number(user.id)) || null;
  } catch {
    return null;
  }
}

async function eventCreateFallbackOrganization() {
  const stamp = new Date().toLocaleDateString("ru-RU");
  const { data } = await apiRequest("/organizations", {
    method: "POST",
    auth: true,
    body: JSON.stringify({
      name: `Моя организация ${stamp}`,
      description: "Временная организация для мероприятий",
      address_components: {},
      contacts: {},
      documents: [],
      photos: []
    }),
  });
  return data;
}

async function eventGetWorkingOrganizationId({ createIfMissing = true } = {}) {
  // Мероприятия требуют, чтобы пользователь был ПРИНЯТЫМ сотрудником (admin/curator)
  // организации (backend: require_org_staff). Поэтому берём организацию из /organizations/my
  // — там только те, где пользователь реально состоит. Иначе backend вернёт 403 и
  // мероприятие «не сохранится». (#17)
  try {
    const { data } = await apiRequest("/organizations/my", { auth: true });
    const orgs = Array.isArray(data) ? data : [];
    if (orgs.length && orgs[0] && orgs[0].id) {
      const id = String(orgs[0].id);
      localStorage.setItem(EVENT_ORG_ID_KEY, id);
      return id;
    }
  } catch (_) {
    // нет сети/доступа — попробуем создать организацию ниже
  }

  if (!createIfMissing) return localStorage.getItem(EVENT_ORG_ID_KEY) || null;

  // организации нет — создаём (создатель автоматически становится admin'ом, см. backend)
  const created = await eventCreateFallbackOrganization();
  if (!created?.id) throw new Error("Не удалось получить ID организации");
  localStorage.setItem(EVENT_ORG_ID_KEY, String(created.id));
  return String(created.id);
}

async function createEvent(event) {
  event.preventDefault();
  const token = ensureAuth("login.html");
  if (!token) return;

  const title = getValue("eventTitle");
  const description = getValue("eventDescription");
  const eventType = getValue("eventType");
  const start = getValue("eventStart");
  const end = getValue("eventEnd");
  const location = getValue("eventLocation");

  if (!title) {
    setStatus("eventCreateStatus", "Укажи название мероприятия.");
    return;
  }

  try {
    let orgId = await eventGetWorkingOrganizationId({ createIfMissing: true });
    const payload = {
      title,
      description: nullIfEmpty(description),
      event_type: nullIfEmpty(eventType),
      start_datetime: start ? new Date(start).toISOString() : null,
      end_datetime: end ? new Date(end).toISOString() : null,
      location: nullIfEmpty(location)
    };

    try {
      await apiRequest(`/events/organizations/${encodeURIComponent(orgId)}`, {
        method: "POST",
        auth: true,
        body: JSON.stringify(payload)
      });
    } catch (err) {
      localStorage.removeItem(EVENT_ORG_ID_KEY);
      orgId = await eventGetWorkingOrganizationId({ createIfMissing: true });
      await apiRequest(`/events/organizations/${encodeURIComponent(orgId)}`, {
        method: "POST",
        auth: true,
        body: JSON.stringify(payload)
      });
    }

    setStatus("eventCreateStatus", "Мероприятие сохранено.");
    setTimeout(() => window.location.href = "calendar.html", 600);
  } catch (err) {
    setStatus("eventCreateStatus", err.message || "Ошибка создания мероприятия");
  }
}

async function registerForEvent(eventId) {
  try {
    await apiRequest(`/events/${eventId}/register`, { method: "POST", auth: true });
    alert("Участие подтверждено.");
  } catch (err) {
    alert(err.message || "Ошибка регистрации на мероприятие");
  }
}

async function cancelEventRegistration(eventId) {
  try {
    await apiRequest(`/events/${eventId}/register`, { method: "DELETE", auth: true });
    alert("Участие отменено.");
  } catch (err) {
    alert(err.message || "Ошибка отмены участия");
  }
}

async function loadCalendarPage() {
  await renderCalendar();
}

async function renderCalendar() {
  const grid = document.getElementById("calendarGrid");
  const label = document.getElementById("calendarMonthLabel");
  const list = document.getElementById("calendarEventsList");
  if (!grid || !label || !list) return;

  const year = currentEventsMonth.getFullYear();
  const month = currentEventsMonth.getMonth();
  label.textContent = currentEventsMonth.toLocaleDateString("ru-RU", { month: "long", year: "numeric" });
  grid.innerHTML = "";
  list.innerHTML = '<div class="empty-small">Загрузка...</div>';

  let events = [];
  try {
    const { data } = await apiRequest("/events");
    events = data || [];
  } catch (err) {
    list.innerHTML = `<div class="empty-small">${escapeHtml(err.message || "Ошибка загрузки мероприятий")}</div>`;
  }

  const weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];
  weekdays.forEach(day => {
    const cell = document.createElement("div");
    cell.className = "calendar-weekday";
    cell.textContent = day;
    grid.appendChild(cell);
  });

  const firstDay = new Date(year, month, 1);
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const offset = (firstDay.getDay() + 6) % 7;

  // Дни предыдущего месяца
  const prevMonthDays = new Date(year, month, 0).getDate();
  for (let i = 0; i < offset; i++) {
    const d = prevMonthDays - offset + 1 + i;
    const cell = document.createElement("button");
    cell.className = "calendar-day muted";
    cell.type = "button";
    cell.innerHTML = `<span>${d}</span>`;
    grid.appendChild(cell);
  }

  for (let day = 1; day <= daysInMonth; day++) {
    const dateKey = toDateKey(new Date(year, month, day));
    const dayEvents = events.filter(event => toDateKey(event.start_datetime) === dateKey);
    const cell = document.createElement("button");
    const isToday = (new Date().toDateString() === new Date(year, month, day).toDateString());
    const dayOfWeek = new Date(year, month, day).getDay(); // 0=Sun, 6=Sat
    const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;
    cell.className = [
      "calendar-day",
      dayEvents.length ? "has-events" : "",
      isToday ? "today" : "",
      isWeekend ? "weekend" : ""
    ].filter(Boolean).join(" ");
    cell.type = "button";
    cell.innerHTML = `<span>${day}</span>${dayEvents.length ? '<b></b>' : ''}`;
    cell.onclick = () => renderDayEvents(dayEvents, dateKey);
    grid.appendChild(cell);
  }

  // Дни следующего месяца для заполнения сетки
  const totalCells = offset + daysInMonth;
  const remainingCells = totalCells % 7 === 0 ? 0 : 7 - (totalCells % 7);
  for (let i = 1; i <= remainingCells; i++) {
    const cell = document.createElement("button");
    cell.className = "calendar-day muted";
    cell.type = "button";
    cell.innerHTML = `<span>${i}</span>`;
    grid.appendChild(cell);
  }

  const monthEvents = events.filter(event => {
    const d = new Date(event.start_datetime);
    return !Number.isNaN(d.getTime()) && d.getFullYear() === year && d.getMonth() === month;
  });
  renderDayEvents(monthEvents, null, "Мероприятия месяца");
}

function changeCalendarMonth(delta) {
  currentEventsMonth = new Date(currentEventsMonth.getFullYear(), currentEventsMonth.getMonth() + delta, 1);
  renderCalendar();
}

// Полноценная карточка мероприятия (используется и в ленте, и в дне календаря)
function eventCardHtml(event) {
  return `
    <article class="event-card">
      <div class="event-card-head">
        <div class="event-date-box">${escapeHtml(shortEventDate(event.start_datetime))}</div>
        <div class="event-info">
          <h2>${escapeHtml(event.title || "Без названия")}</h2>
          <div class="event-type">${escapeHtml(eventTypeLabel(event.event_type))}</div>
        </div>
      </div>
      <p>${escapeHtml(event.description || "Описание не указано")}</p>
      <div class="event-meta">Начало: ${escapeHtml(eventDateLabel(event.start_datetime))}</div>
      <div class="event-meta">Окончание: ${escapeHtml(eventDateLabel(event.end_datetime))}</div>
      <div class="event-meta">Место: ${escapeHtml(event.location || "Не указано")}</div>
      <div class="event-actions">
        <button class="task-primary-btn" type="button" onclick="registerForEvent(${event.id})">Участвовать</button>
        <button class="task-outline-btn" type="button" onclick="cancelEventRegistration(${event.id})">Отменить участие</button>
      </div>
    </article>
  `;
}

function renderDayEvents(events, dateKey, title = null) {
  const list = document.getElementById("calendarEventsList");
  const heading = document.getElementById("calendarSelectedTitle");
  if (!list) return;

  let h = title;
  if (!h) {
    if (dateKey) {
      const d = new Date(dateKey);
      h = "Мероприятия " + (Number.isNaN(d.getTime())
        ? dateKey
        : d.toLocaleDateString("ru-RU", { day: "numeric", month: "long" }));
    } else {
      h = "Мероприятия";
    }
  }
  if (heading) heading.textContent = h;

  if (!events.length) {
    list.innerHTML = '<div class="empty-small">На выбранную дату мероприятий нет</div>';
    return;
  }

  list.innerHTML = events.map(eventCardHtml).join("");
}

function toDateKey(value) {
  if (!value) return "";
  const d = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

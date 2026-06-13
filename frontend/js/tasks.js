const TASKS_SELECTED_ANIMAL_KEY = "paw_selected_animal";
const TASKS_ORG_ID_KEY = "paw_org_id";
let currentTaskTab = "active";

function initTaskStorage() {
}

function getSelectedAnimal() {
  try {
    return JSON.parse(localStorage.getItem(TASKS_SELECTED_ANIMAL_KEY) || "null");
  } catch {
    return null;
  }
}

function setSelectedAnimal(animal) {
  localStorage.setItem(TASKS_SELECTED_ANIMAL_KEY, JSON.stringify(animal));
}

function getPageBack(defaultBack = "animal-select.html") {
  const params = new URLSearchParams(window.location.search);
  return params.get("back") || defaultBack;
}

function setupAnimalSelectPage() {
  // По умолчанию (открытие из меню «Животные») возвращаемся на профиль,
  // а НЕ на создание задачи. В поток задачи попадаем только когда явно
  // передан ?back=task-create.html со страницы создания задачи (#9).
  const back = getPageBack("profile.html");
  const backLink = document.getElementById("animalBackLink");
  const createLink = document.getElementById("createAnimalLink");

  if (backLink) backLink.href = back;
  if (createLink) createLink.href = `animal-create.html?back=${encodeURIComponent(back)}`;
}

function setupAnimalCreatePage() {
  const back = getPageBack("animal-select.html");
  const backLink = document.getElementById("animalCreateBackLink");
  if (backLink) backLink.href = `animal-select.html?back=${encodeURIComponent(back)}`;
}

async function getCurrentUserSafe() {
  try {
    const { data } = await apiRequest("/users/me", { auth: true });
    return data;
  } catch {
    const { data } = await apiRequest("/auth/me", { auth: true });
    return data;
  }
}

async function getMyAnimals() {
  const { data } = await apiRequest("/animals");
  const animals = Array.isArray(data) ? data : [];

  if (!getToken()) return animals;

  try {
    const user = await getCurrentUserSafe();
    const mine = animals.filter((animal) => {
      return animal.owner_type === "private" && Number(animal.owner_id) === Number(user.id);
    });
    return mine.length ? mine : animals;
  } catch {
    return animals;
  }
}

async function renderAnimals() {
  const list = document.getElementById("animalsList");
  if (!list) return;

  list.innerHTML = '<div class="empty-small">Загрузка...</div>';

  try {
    const search = (document.getElementById("animalSearch")?.value || "").trim().toLowerCase();
    let animals = await getMyAnimals();

    if (search) {
      animals = animals.filter((animal) =>
        [animal.name, animal.species, animal.breed]
          .filter(Boolean)
          .some((value) => String(value).toLowerCase().includes(search))
      );
    }

    if (!animals.length) {
      list.innerHTML = `
        <div class="empty-small">
          Животные не найдены.<br>
          Нажми «+ Добавить животное», чтобы создать первый профиль.
        </div>
      `;
      return;
    }

    list.innerHTML = animals
      .map((animal) => `
        <button class="animal-card" type="button" onclick="selectAnimal(${animal.id})">
          <div class="animal-card-paw" aria-hidden="true"></div>
          <div>
            <div class="animal-card-name">${escapeHtml(animal.name || "Без имени")}</div>
            <div class="animal-card-sub">
              ${escapeHtml(animal.species || "Вид не указан")} · ${escapeHtml(animal.breed || "Порода не указана")}
            </div>
          </div>
        </button>
      `)
      .join("");
  } catch (err) {
    list.innerHTML = `<div class="empty-small">${escapeHtml(err.message || "Ошибка загрузки животных")}</div>`;
  }
}

async function selectAnimal(animalId) {
  try {
    const { data: animal } = await apiRequest(`/animals/${animalId}`);
    setSelectedAnimal(animal);

    // Если пришли из task-create — вернуться туда (выбор животного для задачи)
    // Если пришли из меню (нет ?back= параметра) — открыть профиль животного
    const params = new URLSearchParams(window.location.search);
    const back = params.get("back");
    if (back) {
      window.location.href = back;
    } else {
      window.location.href = `animal-profile.html?id=${animalId}`;
    }
  } catch (err) {
    alert(err.message || "Ошибка выбора животного");
  }
}

async function createAnimal(event) {
  event.preventDefault();

  const token = ensureAuth("login.html");
  if (!token) return;

  const name = getValue("animalName");
  if (!name) {
    setStatus("animalCreateStatus", "Укажи имя животного.");
    return;
  }

  try {
    const user = await getCurrentUserSafe();
    const payload = {
      owner_type: "private",
      owner_id: Number(user.id),
      name,
      description: nullIfEmpty(getValue("animalDescription")),
      species: nullIfEmpty(getValue("animalSpecies")),
      breed: nullIfEmpty(getValue("animalBreed")),
      age: nullIfEmpty(getValue("animalAge")),
      gender: getValue("animalGender") || "unknown",
      size: nullIfEmpty(getValue("animalSize")),
      character: nullIfEmpty(getValue("animalCharacter")),
      health_status: nullIfEmpty(getValue("animalHealth")),
      special_needs: nullIfEmpty(getValue("animalSpecialNeeds")),
      photos: []
    };

    const { data: animal } = await apiRequest("/animals", {
      method: "POST",
      auth: true,
      body: JSON.stringify(payload),
    });

    setStatus("animalCreateStatus", "Животное сохранено.");

    const back = getPageBack("animal-select.html");
    if (back.includes("task-create.html")) {
      setSelectedAnimal(animal);
      setTimeout(() => window.location.href = "task-create.html", 450);
    } else {
      setTimeout(() => window.location.href = `animal-select.html?back=${encodeURIComponent(back)}`, 450);
    }
  } catch (err) {
    setStatus("animalCreateStatus", err.message || "Ошибка создания животного");
  }
}

function restoreSelectedAnimal() {
  const label = document.getElementById("selectedAnimalLabel");
  if (!label) return;

  const animal = getSelectedAnimal();
  if (!animal) {
    label.textContent = "Животное не выбрано";
    return;
  }

  label.textContent = animal.name || "Без имени";
}

// --- Черновик задачи: сохраняем введённые поля, чтобы они не сбрасывались
// при переходе на выбор животного и обратно (#11) ---
const TASK_DRAFT_KEY = "paw_task_draft";
const TASK_DRAFT_FIELDS = [
  "taskTitle", "taskDescription", "taskDateFrom", "taskDateTo",
  "taskLocation", "taskLocationLat", "taskLocationLng",
  "taskConditions", "taskType", "taskUrgency"
];

function saveTaskDraft() {
  const draft = {};
  TASK_DRAFT_FIELDS.forEach((id) => {
    const el = document.getElementById(id);
    if (el) draft[id] = el.value;
  });
  localStorage.setItem(TASK_DRAFT_KEY, JSON.stringify(draft));
}

function restoreTaskDraft() {
  let draft = null;
  try {
    draft = JSON.parse(localStorage.getItem(TASK_DRAFT_KEY) || "null");
  } catch {
    draft = null;
  }
  if (!draft) return;
  TASK_DRAFT_FIELDS.forEach((id) => {
    const el = document.getElementById(id);
    if (el && draft[id] != null && draft[id] !== "") el.value = draft[id];
  });
}

function clearTaskDraft() {
  localStorage.removeItem(TASK_DRAFT_KEY);
}

async function findExistingUserOrganization() {
  if (!getToken()) return null;

  try {
    const user = await getCurrentUserSafe();
    const { data } = await apiRequest("/organizations");
    const orgs = Array.isArray(data) ? data : [];
    return orgs.find((org) => Number(org.created_by) === Number(user.id)) || null;
  } catch {
    return null;
  }
}

async function createFallbackOrganization() {
  const stamp = new Date().toLocaleDateString("ru-RU");
  const { data } = await apiRequest("/organizations", {
    method: "POST",
    auth: true,
    body: JSON.stringify({
      name: `Моя организация ${stamp}`,
      description: "Временная организация для создания задач",
      address_components: {},
      contacts: {},
      documents: [],
      photos: []
    }),
  });
  return data;
}

async function getWorkingOrganizationId({ createIfMissing = false } = {}) {
  const saved = localStorage.getItem(TASKS_ORG_ID_KEY);
  if (saved) return saved;

  const existing = await findExistingUserOrganization();
  if (existing?.id) {
    localStorage.setItem(TASKS_ORG_ID_KEY, String(existing.id));
    return String(existing.id);
  }

  if (!createIfMissing) return null;

  const created = await createFallbackOrganization();
  if (!created?.id) throw new Error("Не удалось получить ID организации");
  localStorage.setItem(TASKS_ORG_ID_KEY, String(created.id));
  return String(created.id);
}

async function createTask(event) {
  event.preventDefault();

  const token = ensureAuth("login.html");
  if (!token) return;

  const title = document.getElementById("taskTitle")?.value.trim() || "";
  const description = document.getElementById("taskDescription")?.value.trim() || "";
  const dateFrom = document.getElementById("taskDateFrom")?.value || "";
  const dateTo = document.getElementById("taskDateTo")?.value || "";
  const location = document.getElementById("taskLocation")?.value.trim() || "";
  const locationLat = parseFloat(document.getElementById("taskLocationLat")?.value || "");
  const locationLng = parseFloat(document.getElementById("taskLocationLng")?.value || "");
  const conditions = document.getElementById("taskConditions")?.value.trim() || "";
  const taskType = document.getElementById("taskType")?.value || "other";
  const urgency = document.getElementById("taskUrgency")?.value || "normal";
  const selectedAnimal = getSelectedAnimal();

  if (!title) {
    setTaskCreateStatus("Нужно указать заголовок.");
    return;
  }

  const payload = {
    title,
    description: [description, conditions ? `Условия для волонтёра: ${conditions}` : ""].filter(Boolean).join("\n\n") || null,
    task_type: taskType || null,
    urgency,
    location: location || null,
    location_lat: Number.isFinite(locationLat) ? locationLat : null,
    location_lng: Number.isFinite(locationLng) ? locationLng : null,
    end_date: dateTo ? (dateTo.length === 16 ? `${dateTo}:00` : dateTo) : null,
    scheduled_time: dateFrom ? { from: dateFrom } : null,
    animal_id: selectedAnimal?.id || null
  };

  try {
    let orgId = await getWorkingOrganizationId({ createIfMissing: true });

    try {
      await apiRequest(`/tasks/organizations/${encodeURIComponent(orgId)}`, {
        method: "POST",
        auth: true,
        body: JSON.stringify(payload),
      });
    } catch (err) {
      localStorage.removeItem(TASKS_ORG_ID_KEY);
      orgId = await getWorkingOrganizationId({ createIfMissing: true });
      await apiRequest(`/tasks/organizations/${encodeURIComponent(orgId)}`, {
        method: "POST",
        auth: true,
        body: JSON.stringify(payload),
      });
    }

    localStorage.removeItem(TASKS_SELECTED_ANIMAL_KEY);
    clearTaskDraft();
    setTaskCreateStatus("Задача сохранена.");
    setTimeout(() => {
      window.location.href = "tasks.html";
    }, 500);
  } catch (err) {
    setTaskCreateStatus(err.message || "Ошибка сохранения задачи");
  }
}

async function renderTasks() {
  const list = document.getElementById("tasksList");
  if (!list) return;

  list.innerHTML = '<div class="empty-small">Загрузка...</div>';

  try {
    const search = (document.getElementById("taskSearch")?.value || "").trim().toLowerCase();
    const typeFilter = document.getElementById("taskTypeFilter")?.value || "";
    const statusFilter = document.getElementById("taskStatusFilter")?.value || "";

    const query = new URLSearchParams();
    const orgId = await getWorkingOrganizationId({ createIfMissing: false });
    if (orgId) query.set("organization_id", orgId);

    const { data } = await apiRequest(`/tasks${query.toString() ? `?${query}` : ""}`);
    let tasks = Array.isArray(data) ? data : [];

    tasks = tasks.filter((task) => {
      const completedStatuses = ["done", "cancelled"];
      const activeStatuses = ["open", "in_progress"];
      return currentTaskTab === "done"
        ? completedStatuses.includes(task.status)
        : activeStatuses.includes(task.status);
    });

    if (search) tasks = tasks.filter((task) => (task.title || "").toLowerCase().includes(search));
    if (typeFilter) tasks = tasks.filter((task) => task.task_type === typeFilter);
    if (statusFilter) tasks = tasks.filter((task) => task.status === statusFilter);

    if (!tasks.length) {
      list.innerHTML = `<div class="empty-small">Задач пока нет</div>`;
      return;
    }

    const animalNames = await buildAnimalNameMap();

    list.innerHTML = tasks
      .map((task) => {
        const animalText = task.animal_id
          ? `Животное: ${escapeHtml(animalNames[task.animal_id] || `ID ${task.animal_id}`)}`
          : "Без привязки к животному";

        return `
          <article class="task-card" onclick="openTaskDetails(${task.id})">
            <div class="task-card-row">
              <div class="task-paw" aria-hidden="true"></div>
              <div class="task-main">
                <div class="task-title">${escapeHtml(task.title || "Без названия")}</div>
                <div class="task-animal">${animalText}</div>
                <div class="task-type-badge">${getTaskTypeLabel(task.task_type)}</div>
                <button class="task-outline-btn" type="button" onclick="event.stopPropagation(); openTaskDetails(${task.id})">
                  Связаться с владельцем
                </button>
              </div>
            </div>
          </article>
        `;
      })
      .join("");
  } catch (err) {
    list.innerHTML = `<div class="empty-small">${escapeHtml(err.message || "Ошибка загрузки задач")}</div>`;
  }
}

async function buildAnimalNameMap() {
  try {
    const { data } = await apiRequest("/animals");
    const map = {};
    (Array.isArray(data) ? data : []).forEach((animal) => {
      map[animal.id] = animal.name;
    });
    return map;
  } catch {
    return {};
  }
}


async function openTaskDetails(taskId) {
  const overlay = document.getElementById("taskDetailsOverlay");
  const card = document.getElementById("taskDetailsCard");
  if (!overlay || !card) return;

  card.innerHTML = '<div class="empty-small">Загрузка...</div>';
  overlay.classList.remove("hidden");

  try {
    const { data: task } = await apiRequest(`/tasks/${taskId}`);
    const animals = await buildAnimalNameMap();
    const animalName = task.animal_id ? (animals[task.animal_id] || `ID ${task.animal_id}`) : "Без профиля животного";

    card.innerHTML = `
      <div class="task-detail-top">
        <button class="task-detail-back" type="button" onclick="closeTaskDetails()">⬅</button>
      </div>
      <div class="task-detail-box">
        <h2>${escapeHtml(task.title || "Помогите бедной Мусе")}</h2>
        <div class="task-detail-line">
          <b>Подробности:</b>
          <span>${escapeHtml(task.description || "Краткая информация")}</span>
        </div>
        <div class="task-detail-animal">
          <div class="task-detail-paw"></div>
          <span>Профиль ${escapeHtml(animalName)}</span>
        </div>
        <div class="task-detail-separator"></div>
        <div class="task-detail-label">Компетенции волонтёра</div>
        <div class="task-detail-badge">${getTaskTypeLabel(task.task_type)}</div>
        <button class="task-outline-btn task-detail-contact" type="button" onclick="openTaskChat(${task.id})">Связаться с владельцем</button>
        <div class="task-detail-actions">
          <button type="button" onclick="changeTaskStatus(${task.id}, 'in_progress'); closeTaskDetails();">Принять</button>
          <button type="button" onclick="changeTaskStatus(${task.id}, 'cancelled'); closeTaskDetails();">Отказаться</button>
        </div>
      </div>
    `;
  } catch (err) {
    card.innerHTML = `<div class="empty-small">${escapeHtml(err.message || "Ошибка загрузки задачи")}</div>`;
  }
}

function closeTaskDetails(event) {
  if (event && event.target && event.target.id !== "taskDetailsOverlay") return;
  const overlay = document.getElementById("taskDetailsOverlay");
  if (overlay) overlay.classList.add("hidden");
}

function switchTaskTab(tab) {
  currentTaskTab = tab;
  document.getElementById("activeTabBtn")?.classList.toggle("active", tab === "active");
  document.getElementById("doneTabBtn")?.classList.toggle("active", tab === "done");
  renderTasks();
}

function toggleFilter() {
  const panel = document.getElementById("filterPanel");
  if (!panel) return;
  panel.classList.toggle("hidden");
}

function getStatusActions(task) {
  if (task.status === "open") {
    return `
      <button class="task-primary-btn" type="button" onclick="changeTaskStatus(${task.id}, 'in_progress')">В работу</button>
      <button class="task-secondary-btn" type="button" onclick="changeTaskStatus(${task.id}, 'cancelled')">Отменить</button>
    `;
  }

  if (task.status === "in_progress") {
    return `
      <button class="task-primary-btn" type="button" onclick="changeTaskStatus(${task.id}, 'done')">Завершить</button>
      <button class="task-secondary-btn" type="button" onclick="changeTaskStatus(${task.id}, 'cancelled')">Отменить</button>
    `;
  }

  return "";
}

async function changeTaskStatus(taskId, newStatus) {
  try {
    await apiRequest(`/tasks/${taskId}`, {
      method: "PATCH",
      auth: true,
      body: JSON.stringify({ status: newStatus }),
    });
    await renderTasks();
  } catch (err) {
    alert(err.message || "Ошибка смены статуса");
  }
}

function setTaskCreateStatus(text) {
  const status = document.getElementById("taskCreateStatus");
  if (status) status.textContent = text;
}

function getTaskTypeLabel(type) {
  const map = {
    transport: "Перевозка",
    foster: "Передержка",
    care: "Уход",
    other: "Другое"
  };
  return map[type] || "Другое";
}

function getStatusLabel(status) {
  const map = {
    open: "Открыта",
    in_progress: "В работе",
    done: "Завершена",
    cancelled: "Отменена"
  };
  return map[status] || status || "—";
}

function getUrgencyLabel(urgency) {
  const map = {
    normal: "Обычная",
    urgent: "Срочная",
    low: "Низкая",
    medium: "Средняя",
    high: "Высокая"
  };
  return map[urgency] || urgency || "—";
}

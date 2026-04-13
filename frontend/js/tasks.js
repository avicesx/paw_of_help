const TASKS_KEY = "paw_tasks";
const ANIMALS_KEY = "paw_animals";
const SELECTED_ANIMAL_KEY = "paw_selected_animal";
const ORG_ID_KEY = "paw_org_id";

let currentTaskTab = "active";

function initTaskStorage() {
  if (!localStorage.getItem(ORG_ID_KEY)) {
    localStorage.setItem(ORG_ID_KEY, "1");
  }

  if (!localStorage.getItem(ANIMALS_KEY)) {
    const demoAnimals = [
      { id: 1, name: "Муся" },
      { id: 2, name: "Сима" },
      { id: 3, name: "Граф Шеремейстер" },
      { id: 4, name: "Ричард" }
    ];
    localStorage.setItem(ANIMALS_KEY, JSON.stringify(demoAnimals));
  }

  if (!localStorage.getItem(TASKS_KEY)) {
    const demoTasks = [
      {
        id: Date.now(),
        org_id: Number(localStorage.getItem(ORG_ID_KEY)),
        title: "Помогите бедной Мусе",
        description: "Нужна помощь с перевозкой",
        task_type: "transport",
        urgency: "medium",
        location: "Екатеринбург",
        end_date: "2026-04-30",
        scheduled_time: null,
        animal_id: 1,
        animal_name: "Муся",
        status: "open",
        conditions: "Связаться с владельцем",
        created_by_org: true
      }
    ];
    localStorage.setItem(TASKS_KEY, JSON.stringify(demoTasks));
  }
}

function getTasks() {
  return JSON.parse(localStorage.getItem(TASKS_KEY) || "[]");
}

function setTasks(tasks) {
  localStorage.setItem(TASKS_KEY, JSON.stringify(tasks));
}

function getAnimals() {
  return JSON.parse(localStorage.getItem(ANIMALS_KEY) || "[]");
}

function getSelectedAnimal() {
  return JSON.parse(localStorage.getItem(SELECTED_ANIMAL_KEY) || "null");
}

function setSelectedAnimal(animal) {
  localStorage.setItem(SELECTED_ANIMAL_KEY, JSON.stringify(animal));
}

function switchTaskTab(tab) {
  currentTaskTab = tab;

  const activeBtn = document.getElementById("activeTabBtn");
  const doneBtn = document.getElementById("doneTabBtn");

  if (activeBtn && doneBtn) {
    activeBtn.classList.toggle("active", tab === "active");
    doneBtn.classList.toggle("active", tab === "done");
  }

  renderTasks();
}

function toggleFilter() {
  const panel = document.getElementById("filterPanel");
  if (!panel) return;
  panel.classList.toggle("hidden");
}

function renderTasks() {
  const list = document.getElementById("tasksList");
  if (!list) return;

  const search = (document.getElementById("taskSearch")?.value || "").trim().toLowerCase();
  const typeFilter = document.getElementById("taskTypeFilter")?.value || "";
  const statusFilter = document.getElementById("taskStatusFilter")?.value || "";

  let tasks = getTasks();

  tasks = tasks.filter((task) => {
    const isDoneTab = currentTaskTab === "done";
    const completedStatuses = ["done", "cancelled"];
    const activeStatuses = ["open", "in_progress"];

    if (isDoneTab) {
      return completedStatuses.includes(task.status);
    }

    return activeStatuses.includes(task.status);
  });

  if (search) {
    tasks = tasks.filter((task) =>
      (task.title || "").toLowerCase().includes(search)
    );
  }

  if (typeFilter) {
    tasks = tasks.filter((task) => task.task_type === typeFilter);
  }

  if (statusFilter) {
    tasks = tasks.filter((task) => task.status === statusFilter);
  }

  if (!tasks.length) {
    list.innerHTML = `<div class="empty-small">Задач пока нет</div>`;
    return;
  }

  list.innerHTML = tasks
    .map(
      (task) => `
        <div class="task-card">
          <div class="task-card-row">
            <div class="task-paw">🐾</div>

            <div class="task-main">
              <div class="task-title">${escapeHtml(task.title || "Без названия")}</div>
              <div class="task-animal">${task.animal_name ? `Животное: ${escapeHtml(task.animal_name)}` : "Без привязки к животному"}</div>
              <div class="task-type-badge">${getTaskTypeLabel(task.task_type)}</div>
              <div class="task-status-label">Статус: ${getStatusLabel(task.status)}</div>

              <div class="task-actions">
                ${getStatusActions(task)}
                <button class="task-outline-btn" type="button">Связаться с владельцем</button>
              </div>
            </div>
          </div>
        </div>
      `
    )
    .join("");
}

function getStatusActions(task) {
  const isCreator = !!task.created_by_org;
  if (!isCreator) return "";

  if (task.status === "open") {
    return `
      <button class="task-primary-btn" type="button" onclick="changeTaskStatus(${task.id}, 'in_progress')">
        В работу
      </button>
      <button class="task-secondary-btn" type="button" onclick="changeTaskStatus(${task.id}, 'cancelled')">
        Отменить
      </button>
    `;
  }

  if (task.status === "in_progress") {
    return `
      <button class="task-primary-btn" type="button" onclick="changeTaskStatus(${task.id}, 'done')">
        Завершить
      </button>
      <button class="task-secondary-btn" type="button" onclick="changeTaskStatus(${task.id}, 'cancelled')">
        Отменить
      </button>
    `;
  }

  return "";
}

function changeTaskStatus(taskId, newStatus) {
  const tasks = getTasks().map((task) => {
    if (task.id === taskId && task.created_by_org) {
      return { ...task, status: newStatus };
    }
    return task;
  });

  setTasks(tasks);
  renderTasks();
}

function renderAnimals() {
  const list = document.getElementById("animalsList");
  if (!list) return;

  const search = (document.getElementById("animalSearch")?.value || "").trim().toLowerCase();
  let animals = getAnimals();

  if (search) {
    animals = animals.filter((animal) =>
      (animal.name || "").toLowerCase().includes(search)
    );
  }

  if (!animals.length) {
    list.innerHTML = `<div class="empty-small">Животные не найдены</div>`;
    return;
  }

  list.innerHTML = animals
    .map(
      (animal) => `
        <button class="animal-card" type="button" onclick="selectAnimal(${animal.id})">
          <div class="animal-card-paw">🐾</div>
          <div class="animal-card-name">${escapeHtml(animal.name)}</div>
        </button>
      `
    )
    .join("");
}

function selectAnimal(animalId) {
  const animal = getAnimals().find((item) => item.id === animalId);
  if (!animal) return;

  setSelectedAnimal(animal);
  window.location.href = "task-create.html";
}

function restoreSelectedAnimal() {
  const label = document.getElementById("selectedAnimalLabel");
  if (!label) return;

  const animal = getSelectedAnimal();
  if (!animal) {
    label.textContent = "Животное не выбрано";
    return;
  }

  label.textContent = `Профиль ${animal.name}`;
}

function createTask(event) {
  event.preventDefault();

  const title = document.getElementById("taskTitle")?.value.trim() || "";
  const description = document.getElementById("taskDescription")?.value.trim() || "";
  const dateFrom = document.getElementById("taskDateFrom")?.value || "";
  const dateTo = document.getElementById("taskDateTo")?.value || "";
  const location = document.getElementById("taskLocation")?.value.trim() || "";
  const conditions = document.getElementById("taskConditions")?.value.trim() || "";
  const taskType = document.getElementById("taskType")?.value || "other";
  const urgency = document.getElementById("taskUrgency")?.value || "medium";
  const selectedAnimal = getSelectedAnimal();

  if (!title) {
    setTaskCreateStatus("Нужно указать заголовок.");
    return;
  }

  const task = {
    id: Date.now(),
    org_id: Number(localStorage.getItem(ORG_ID_KEY) || "1"),
    title,
    description,
    task_type: taskType,
    urgency,
    location,
    location_lat: null,
    location_lng: null,
    end_date: dateTo || null,
    scheduled_time: dateFrom || null,
    animal_id: selectedAnimal?.id || null,
    animal_name: selectedAnimal?.name || null,
    status: "open",
    conditions,
    created_by_org: true
  };

  const tasks = getTasks();
  tasks.unshift(task);
  setTasks(tasks);

  localStorage.removeItem(SELECTED_ANIMAL_KEY);
  setTaskCreateStatus("Задача сохранена.");
  setTimeout(() => {
    window.location.href = "tasks.html";
  }, 500);
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
  return map[status] || status;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

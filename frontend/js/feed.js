let currentFeedMode = "recommended";

function switchFeedMode(mode) {
  currentFeedMode = mode;
  document.getElementById("feedRecommendedBtn")?.classList.toggle("active", mode === "recommended");
  document.getElementById("feedAllBtn")?.classList.toggle("active", mode === "all");
  loadTaskFeed();
}

async function loadTaskFeed() {
  const list = document.getElementById("feedList");
  if (!list) return;
  list.innerHTML = '<div class="empty-small">Загрузка ленты...</div>';

  try {
    const search = (document.getElementById("feedSearch")?.value || "").trim().toLowerCase();
    const type = document.getElementById("feedTypeFilter")?.value || "";
    const urgency = document.getElementById("feedUrgencyFilter")?.value || "";
    let tasks = [];

    if (currentFeedMode === "recommended" && getToken()) {
      const { data } = await apiRequest("/volunteer/feed?limit=50&offset=0", { auth: true });
      tasks = data || [];
    } else {
      const query = new URLSearchParams();
      if (type) query.set("task_type", type);
      if (urgency) query.set("urgency", urgency);
      const { data } = await apiRequest(`/tasks${query.toString() ? `?${query}` : ""}`);
      tasks = data || [];
    }

    if (search) {
      tasks = tasks.filter(task =>
        (task.title || "").toLowerCase().includes(search) ||
        (task.description || "").toLowerCase().includes(search)
      );
    }
    if (type && currentFeedMode === "recommended") tasks = tasks.filter(task => task.task_type === type || !task.task_type);
    if (urgency && currentFeedMode === "recommended") tasks = tasks.filter(task => task.urgency === urgency || !task.urgency);

    renderFeed(tasks);
  } catch (err) {
    list.innerHTML = `<div class="empty-small">${escapeHtml(err.message || "Ошибка загрузки ленты")}</div>`;
  }
}

function renderFeed(tasks) {
  const list = document.getElementById("feedList");
  if (!list) return;
  if (!tasks.length) {
    list.innerHTML = '<div class="empty-small">Подходящих задач пока нет</div>';
    return;
  }

  list.innerHTML = tasks.map(task => `
    <article class="feed-card">
      <div class="task-card-row">
        <div class="task-paw">🐾</div>
        <div class="task-main">
          <div class="task-title">${escapeHtml(task.title || "Без названия")}</div>
          <p>${escapeHtml(task.description || "Описание не указано")}</p>
          <div class="task-status-label">Статус: ${escapeHtml(getStatusLabel(task.status || "open"))}</div>
          <div class="task-status-label">До: ${escapeHtml(formatDateTime(task.end_date))}</div>
          <div class="task-actions">
            <button class="task-primary-btn" type="button" onclick="respondToTask(${task.id})">Откликнуться</button>
            <button class="task-outline-btn" type="button" onclick="openTaskDetails(${task.id})">Подробнее</button>
          </div>
        </div>
      </div>
    </article>
  `).join("");
}

async function respondToTask(taskId) {
  try {
    await apiRequest(`/task-responses/${taskId}`, {
      method: "POST",
      auth: true,
      body: JSON.stringify({ message: "Готов помочь" })
    });
    alert("Отклик отправлен.");
  } catch (err) {
    alert(err.message || "Ошибка отправки отклика");
  }
}

function openTaskDetails(taskId) {
  alert(`ID задачи: ${taskId}`);
}

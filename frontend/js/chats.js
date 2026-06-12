// Чаты (дизайн: для чата.svg). Бэкенд: /chats, /chats/open, /chats/{id}/messages, /chats/{id}/read.
// Чат привязан к контексту (task / foster_request): переписка «сотрудник организации ↔ откликнувшийся волонтёр».

function getCurrentUserId() {
  const token = getToken();
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.sub ? parseInt(payload.sub, 10) : null;
  } catch (e) {
    return null;
  }
}

function chatTime(dateStr) {
  if (!dateStr) return "";
  try {
    return new Date(dateStr).toLocaleString("ru-RU", {
      day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit",
    });
  } catch (e) { return ""; }
}

// ----- Список чатов -----
async function loadChatList() {
  const list = document.getElementById("chatList");
  if (!list) return;
  list.innerHTML = '<div class="empty-small">Загрузка чатов...</div>';
  try {
    const { data } = await apiRequest("/chats", { auth: true });
    const chats = Array.isArray(data) ? data : [];
    if (!chats.length) {
      list.innerHTML = '<div class="empty-small">У вас пока нет активных чатов.</div>';
      return;
    }
    const enriched = await Promise.all(chats.map(async (c) => {
      let title = `Чат · ${c.context_type} #${c.context_id}`;
      if (c.context_type === "task") {
        try { const { data: t } = await apiRequest(`/tasks/${c.context_id}`); if (t?.title) title = t.title; } catch (e) {}
      }
      return { ...c, title };
    }));
    list.innerHTML = enriched.map(renderChatCard).join("");
  } catch (err) {
    list.innerHTML = `<div class="empty-small">${escapeHtml(err.message || "Не удалось загрузить чаты")}</div>`;
  }
}

async function loadChatList() {
    const container = document.getElementById('chatList') || document.querySelector('.chat-list');
    if (!container) return;

    container.innerHTML = '<div class="empty">Загрузка...</div>';

    const chats = await getAllChats();
    
    if (chats.length === 0) {
        container.innerHTML = '<div class="results-placeholder">У вас пока нет активных чатов.</div>';
        return;
    }

    container.innerHTML = chats.map(createChatCard).join('');

    // Глобальная индикация в заголовке списка
    const hasUnread = await hasUnreadMessages();
    const title = document.querySelector('.chat-screen .screen-title');
    if (title) {
        title.classList.toggle('has-unread-global', hasUnread);
    }
}

function openChat(chatId) {
  if (!chatId) return;
  window.location.href = `chat.html?id=${chatId}`;
}

// Открыть/создать чат для задачи (кнопка «Связаться» в задаче)
async function openTaskChat(taskId) {
  if (!getToken()) { window.location.href = "login.html"; return; }
  try {
    const { data } = await apiRequest("/chats/open", {
      method: "POST", auth: true,
      body: JSON.stringify({ context_type: "task", context_id: taskId }),
    });
    openChat(data.id);
  } catch (err) {
    alert(err.message || "Не удалось открыть чат");
  }
}

// ----- Переписка -----
let _chatPollTimer = null;

async function getChatMessages(chatId) {
  const { data } = await apiRequest(`/chats/${chatId}/messages`, { auth: true });
  const me = getCurrentUserId();
  return (Array.isArray(data) ? data : []).map((m) => ({
    mine: me != null && String(m.sender_id) === String(me),
    text: m.content || "",
    time: chatTime(m.created_at),
  }));
}

function renderMessages(messages) {
  const box = document.getElementById("messagesList");
  if (!box) return;
  if (!messages.length) {
    box.innerHTML = '<div class="empty-small">Здесь пока нет сообщений. Начните общение!</div>';
    return;
  }
  box.innerHTML = messages.map((m) => `
    <div class="msg-bubble ${m.mine ? "mine" : "theirs"}">
      <div class="msg-text">${escapeHtml(m.text)}</div>
      <div class="msg-time">${m.time}</div>
    </div>`).join("");
  box.scrollTop = box.scrollHeight;
}

async function sendChatMessage() {
  const input = document.getElementById("messageInput");
  const text = (input?.value || "").trim();
  if (!text) return;
  const chatId = new URLSearchParams(location.search).get("id");
  try {
    input.disabled = true;
    await apiRequest(`/chats/${chatId}/messages`, {
      method: "POST", auth: true,
      body: JSON.stringify({ content: text, message_type: "text" }),
    });
    input.value = "";
    input.disabled = false;
    input.focus();
    renderMessages(await getChatMessages(chatId));
  } catch (err) {
    input.disabled = false;
    alert(err.message || "Не удалось отправить сообщение");
  }
}

async function initChatConversation() {
  const box = document.getElementById("messagesList");
  if (!box) return;
  if (!getToken()) { window.location.href = "login.html"; return; }
  const chatId = new URLSearchParams(location.search).get("id");
  if (!chatId) { box.innerHTML = '<div class="empty-small">Чат не найден</div>'; return; }

async function manualMarkAsRead() {
    const urlParams = new URLSearchParams(window.location.search);
    const chatId = urlParams.get('id');
    if (!chatId) return;

    try {
        await markChatAsRead(chatId);
        const btn = document.querySelector('.mark-read-btn');
        if (btn) btn.classList.add('success');
    } catch (err) { console.error(err); }
}

// TODO: Реализовать логику для acceptVolunteer и declineVolunteer
// Эти функции должны взаимодействовать с бэкендом для изменения статуса заявки/отклика
// и затем обновлять UI чата (скрывать acceptNotification).
function acceptVolunteer() {
    alert('Принять волонтера (логика будет реализована)');
    // Здесь должна быть логика отправки запроса на бэкенд (например, PATCH /task_responses/{id})
    // document.getElementById('acceptNotification').classList.add('hidden');
}

function declineVolunteer() {
    alert('Отказаться от волонтера (логика будет реализована)');
    // Здесь должна быть логика отправки запроса на бэкенд
    // document.getElementById('acceptNotification').classList.add('hidden');
}

function createChatCard(chat) {
  return `
    <div class="chat-card ${chat.unread > 0 ? 'unread' : ''}" onclick="openChat(${chat.id})">
      <div class="chat-avatar">💬</div>
      <div class="chat-info">
        <div class="chat-name">${chat.name}</div>
        <div class="chat-message">${chat.lastMessage}</div>
      </div>
      <div class="chat-meta">
        <div class="chat-time">${chat.time}</div>
        ${chat.unread > 0 ? `<div class="unread-badge">${chat.unread}</div>` : ''}
        ${chat.online ? '<div class="online-indicator"></div>' : ''}
      </div>
    </div>
  `;
}

  try {
    const { data: chat } = await apiRequest(`/chats/${chatId}`, { auth: true });
    const titleEl = document.getElementById("chatTitle");
    let t = `Чат · ${chat.context_type} #${chat.context_id}`;
    if (chat.context_type === "task") {
      try { const { data: task } = await apiRequest(`/tasks/${chat.context_id}`); if (task?.title) t = task.title; } catch (e) {}
    }
    if (titleEl) titleEl.textContent = t;
    document.body.dataset.contextType = chat.context_type;
    document.body.dataset.contextId = chat.context_id;
  } catch (e) {}

  try {
    renderMessages(await getChatMessages(chatId));
  } catch (err) {
    box.innerHTML = '<div class="empty-small">Не удалось загрузить сообщения</div>';
    return;
  }

  const input = document.getElementById("messageInput");
  if (input && !input.dataset.bound) {
    input.addEventListener("keypress", (e) => { if (e.key === "Enter") { e.preventDefault(); sendChatMessage(); } });
    input.dataset.bound = "1";
  }

  if (_chatPollTimer) clearInterval(_chatPollTimer);
  _chatPollTimer = setInterval(async () => {
    try {
      const box2 = document.getElementById("messagesList");
      if (!box2) return;
      renderMessages(await getChatMessages(chatId));
    } catch (e) {}
  }, 5000);
  window.addEventListener("beforeunload", () => { if (_chatPollTimer) clearInterval(_chatPollTimer); });
}

// «Оставить отзыв» из чата → экран отзыва с контекстом задачи
function leaveReviewFromChat() {
  const ct = document.body.dataset.contextType || "task";
  const ci = document.body.dataset.contextId || "";
  window.location.href = `leave-review.html?context_type=${encodeURIComponent(ct)}&context_id=${encodeURIComponent(ci)}`;
}

    if (document.querySelector('.chat-title')) {
        document.querySelector('.chat-title').innerText = chatData.name;
    }
    
    // TODO: Здесь должна быть логика для отображения acceptNotification
    // Например, если chatData содержит информацию о pending-заявке волонтера
    // document.getElementById('acceptNotification').classList.remove('hidden');

// ----- Экран «Оставить отзыв» (leave-review.html), дизайн: оставить отзыв.svg -----
async function initLeaveReview() {
  if (!getToken()) { window.location.href = "login.html"; return; }
  const params = new URLSearchParams(location.search);
  const ct = params.get("context_type") || "task";
  const ci = params.get("context_id");

  let task = null;
  if (ct === "task" && ci) { try { const { data } = await apiRequest(`/tasks/${ci}`); task = data; } catch (e) {} }

  const ctx = document.getElementById("reviewContext");
  if (ctx && task) {
    const tag = typeof getTaskTypeLabel === "function" ? getTaskTypeLabel(task.task_type) : (task.task_type || "");
    ctx.innerHTML = `
      <div class="task-paw" aria-hidden="true"></div>
      <div class="rev-ctx-main">
        <div class="rev-ctx-title">${escapeHtml(task.title || "Задача")}</div>
        <div class="rev-ctx-tag">${escapeHtml(tag)}</div>
      </div>`;
  }

  // кому оставляем отзыв: я волонтёр → владельцу задачи; я владелец → откликнувшемуся волонтёру
  const me = getCurrentUserId();
  let reviewee = null;
  if (task) {
    if (Number(task.created_by) !== Number(me)) {
      reviewee = task.created_by;
    } else {
      try {
        const { data: resps } = await apiRequest(`/task-responses/task/${ci}`, { auth: true });
        if (Array.isArray(resps) && resps.length) reviewee = resps[0].volunteer_id;
      } catch (e) {}
    }
  }
  document.body.dataset.reviewee = reviewee || "";
  document.body.dataset.targetType = ct;
  document.body.dataset.targetId = ci || "";
  setReviewStars(5);
}

    setupChatEventListeners();

    if (chatRefreshInterval) clearInterval(chatRefreshInterval);
    chatRefreshInterval = setInterval(async () => {
        const newMessages = await getChatMessages(chatId);
        await markChatAsRead(chatId).catch(() => {});

        const list = document.getElementById('messagesList');
        if (list) {
            const isAtBottom = list.scrollTop + list.clientHeight >= list.scrollHeight - 50;
            
            list.innerHTML = newMessages.map(createMessageBubble).join('');
            
            if (isAtBottom) {
                list.scrollTop = list.scrollHeight;
            }
        }
    }, 5000);
    
    isChatInitializing = false;
}

async function submitLeaveReview(e) {
  if (e) e.preventDefault();
  const status = document.getElementById("reviewStatus");
  const reviewee = parseInt(document.body.dataset.reviewee || "", 10);
  const rating = parseInt(document.getElementById("reviewRating")?.value || "5", 10);
  const comment = (document.getElementById("reviewComment")?.value || "").trim();
  if (!reviewee) { if (status) status.textContent = "Не удалось определить, кому оставить отзыв."; return; }
  try {
    if (status) status.textContent = "Сохраняем...";
    await apiRequest("/reviews", {
      method: "POST", auth: true,
      body: JSON.stringify({
        reviewee_id: reviewee,
        target_type: document.body.dataset.targetType || "task",
        target_id: parseInt(document.body.dataset.targetId || "0", 10),
        rating,
        comment: comment || null,
      }),
    });
    if (status) status.textContent = "Отзыв сохранён!";
    setTimeout(() => history.back(), 900);
  } catch (err) {
    if (status) status.textContent = err.message || "Не удалось сохранить отзыв";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("chatList")) loadChatList();
  if (document.getElementById("messagesList")) initChatConversation();
  if (document.getElementById("reviewStars")) initLeaveReview();
});

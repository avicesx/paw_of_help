// Уведомления. Дизайн: «уведомления.svg» / «Профиль для уведомлений.svg».
// Карточка = красный заголовок + текст, по которому можно перейти. Бэкенд: /notifications.

function notifTarget(n) {
  const d = n.data || {};
  const t = n.type || "";
  if (t.startsWith("organization") && d.organization_id) return `org.html?id=${d.organization_id}`;
  if (t.startsWith("article") && d.article_id) return `kb-article.html?id=${d.article_id}`;
  if (t.startsWith("post")) return "feed.html";
  if ((t.startsWith("chat") || t.startsWith("message")) && d.chat_id) return `chat.html?id=${d.chat_id}`;
  if (t.startsWith("chat") || t.startsWith("message")) return "chats.html";
  if (t.startsWith("task") && d.task_id) return `tasks.html`;
  return null;
}

async function loadNotifications() {
  const box = document.getElementById("notifList");
  if (!box) return;
  if (!getToken()) { location.href = "login.html"; return; }
  box.innerHTML = '<div class="empty-small">Загрузка...</div>';
  try {
    const { data } = await apiRequest("/notifications?limit=100", { auth: true });
    const list = Array.isArray(data) ? data : [];
    if (!list.length) {
      box.innerHTML = '<div class="empty-small">Уведомлений пока нет</div>';
      return;
    }
    box.innerHTML = list.map(notifCardHtml).join("");
  } catch (e) {
    box.innerHTML = '<div class="empty-small">Не удалось загрузить уведомления</div>';
  }
}

function notifCardHtml(n) {
  const target = notifTarget(n);
  const isInvite = (n.type || "") === "organization_invite";
  const orgId = (n.data || {}).organization_id;
  const clickable = target && !isInvite;
  return `
    <div class="notif-card${n.is_read ? "" : " unread"}"${clickable ? ` onclick="openNotif(${n.id}, '${target}')"` : ""}>
      <div class="notif-title">${escapeHtml(n.title || "Уведомление")}</div>
      <div class="notif-body">${escapeHtml(n.body || "")}</div>
      ${isInvite && orgId ? `
        <div class="notif-actions">
          <button type="button" class="notif-accept" onclick="event.stopPropagation(); respondInvite(${orgId}, true, ${n.id})">Принять</button>
          <button type="button" class="notif-decline" onclick="event.stopPropagation(); respondInvite(${orgId}, false, ${n.id})">Отклонить</button>
        </div>` : ""}
    </div>`;
}

async function openNotif(id, target) {
  try { await apiRequest(`/notifications/${id}/read`, { method: "POST", auth: true }); } catch (e) {}
  if (target) location.href = target;
}

async function respondInvite(orgId, accept, notifId) {
  try {
    await apiRequest(`/organizations/${orgId}/${accept ? "accept-invite" : "decline-invite"}`, { method: "POST", auth: true });
    if (notifId) { try { await apiRequest(`/notifications/${notifId}/read`, { method: "POST", auth: true }); } catch (e) {} }
    if (accept) { location.href = `org.html?id=${orgId}`; return; }
    await loadNotifications();
  } catch (err) {
    alert(err.message || "Не удалось обработать приглашение");
  }
}

async function markAllNotificationsRead() {
  try {
    await apiRequest("/notifications/read-all", { method: "POST", auth: true });
    await loadNotifications();
    if (typeof loadNotificationsCount === "function") loadNotificationsCount();
  } catch (e) { alert(e.message || "Ошибка"); }
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("notifList")) loadNotifications();
});

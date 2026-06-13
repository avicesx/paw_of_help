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

async function getUnreadCount() {
    try {
        const res = await apiRequest('/notifications/unread-count', { auth: true });
        return res.data.unread_count || 0;
    } catch { return 0; }
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

async function updateNotificationDot() {
    const dot = document.getElementById('notificationDot');
    const bellImg = document.querySelector('.notification-btn .layout-bell');
    if (!dot && !bellImg) return;

    try {
        const count = await getUnreadCount();
        const hasUnread = count > 0;

        if (dot) dot.style.display = hasUnread ? 'block' : 'none';
        
        if (bellImg) {
            const isNested = window.location.pathname.includes('/chats/') || window.location.pathname.includes('/comments/');
            const assetPath = isNested ? '../../assets/topbar/' : '../assets/topbar/';
            
            bellImg.src = hasUnread 
                ? `${assetPath}notifications-active.svg` 
                : `${assetPath}notifications-inactive.svg`;
        }
    } catch (err) {
        console.error("Ошибка обновления индикатора уведомлений:", err);
    }
}

function toggleNotifications() {
    const dropdown = document.getElementById('notificationsDropdown');
    dropdown.classList.toggle('hidden');
    dropdown.classList.toggle('show');
    if (dropdown.classList.contains('show')) {
        renderDropdownList();
    }
}

async function renderDropdownList() {
    const list = document.getElementById('notificationsList');
    if (!list) return;
    const data = await getNotifications(null, 5);
    
    list.innerHTML = data.length ? data.map(n => `
        <div class="notification-item ${n.is_read ? '' : 'unread'}">
            <strong>${n.title}</strong>
            <p>${n.body}</p>
            ${!n.is_read ? `<button onclick="markAsRead(${n.id})">Прочитать</button>` : ''}
        </div>
    `).join('') : '<div class="notification-item">Уведомлений нет</div>';
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("notifList")) loadNotifications();
});

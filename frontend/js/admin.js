let adminTimer = null;
function debounce(fn) {
  clearTimeout(adminTimer);
  adminTimer = setTimeout(fn, 350);
}

function debouncedLoadUsers() { debounce(loadUsers); }
function debouncedLoadOrganizations() { debounce(loadOrganizations); }
function debouncedLoadReports() { debounce(loadReports); }
function debouncedLoadTickets() { debounce(loadTickets); }

async function loadAdminDashboard() {
  if (!adminRequireAuth()) return;
  try {
    adminSetStatus("Загрузка...");
    const { data } = await adminRequest("/admin/dashboard");
    const cards = [
      ["Пользователи", data.total_users],
      ["Новые за неделю", data.users_new_week],
      ["Организации", data.total_organizations_verified],
      ["Активные задачи", data.active_tasks],
      ["Посты", data.total_posts],
      ["Открытые тикеты", data.open_tickets],
      ["Жалобы", data.pending_reports],
    ];
    document.getElementById("dashboardCards").innerHTML = cards.map(([label, value]) => `
      <article class="admin-stat"><strong>${adminEscape(value)}</strong><span>${adminEscape(label)}</span></article>
    `).join("");
    adminSetStatus("");
  } catch (err) {
    const msg = err.message || "Ошибка";
    const hint = (err.status === 403 || msg.includes("прав") || msg.includes("Forbidden"))
      ? "Нет прав администратора. Попросите superadmin выдать вашему аккаунту роль admin, moderator или superadmin."
      : (err.status === 401 || msg.includes("токен") || msg.includes("Срок"))
        ? "Сессия истекла — войдите снова."
        : msg;
    adminSetStatus(hint, "error");
  }
}

async function loadUsers() {
  if (!adminRequireAuth()) return;
  const search = document.getElementById("userSearch")?.value || "";
  const status = document.getElementById("userStatus")?.value || "";
  try {
    adminSetStatus("Загрузка пользователей...");
    const { data } = await adminRequest(`/admin/users${adminQuery({ search, status })}`);
    const list = document.getElementById("usersList");
    list.innerHTML = (data || []).map(user => `
      <article class="admin-card">
        <div class="admin-card-head">
          <div><h3>${adminEscape([user.name, user.last_name].filter(Boolean).join(" ") || user.username || `Пользователь #${user.id}`)}</h3><p>ID ${user.id} · ${adminEscape(user.username || "без логина")}</p></div>
          <span class="admin-badge ${user.is_active ? "ok" : "danger"}">${user.is_active ? "Активен" : "Заблокирован"}</span>
        </div>
        <p>Email: ${adminEscape(user.email || "—")}</p>
        <p>Телефон: ${adminEscape(user.phone || "—")}</p>
        <p>Рейтинг: ${Number(user.rating || 0).toFixed(1)} · задач: ${adminEscape(user.completed_tasks)}</p>
        <p>Создан: ${adminDate(user.created_at)}</p>
        <div class="admin-actions">
          ${user.is_active
            ? `<button onclick="blockUser(${user.id})">Заблокировать</button>`
            : `<button onclick="unblockUser(${user.id})">Разблокировать</button>`}
          <select onchange="changeUserRole(${user.id}, this.value)">
            <option value="">Сменить роль</option>
            <option value="user">user</option>
            <option value="moderator">moderator</option>
            <option value="support_agent">support_agent</option>
            <option value="admin">admin</option>
            <option value="superadmin">superadmin</option>
          </select>
        </div>
      </article>
    `).join("") || `<div class="admin-empty">Пользователи не найдены</div>`;
    adminSetStatus("");
  } catch (err) {
    adminSetStatus(err.message || "Ошибка загрузки пользователей", "error");
  }
}

async function blockUser(id) { await adminAction(`/admin/users/${id}/block`, { method: "PATCH" }, loadUsers); }
async function unblockUser(id) { await adminAction(`/admin/users/${id}/unblock`, { method: "PATCH" }, loadUsers); }
async function changeUserRole(id, role) {
  if (!role) return;
  await adminAction(`/admin/users/${id}/role`, { method: "PATCH", body: JSON.stringify({ role }) }, loadUsers);
}

async function loadOrganizations() {
  if (!adminRequireAuth()) return;
  const search = document.getElementById("orgSearch")?.value || "";
  const status = document.getElementById("orgStatus")?.value || "";
  try {
    adminSetStatus("Загрузка организаций...");
    const { data } = await adminRequest(`/admin/organizations${adminQuery({ search, status })}`);
    document.getElementById("organizationsList").innerHTML = (data || []).map(org => `
      <article class="admin-card">
        <div class="admin-card-head">
          <div><h3>${adminEscape(org.name)}</h3><p>ID ${org.id} · ${adminDate(org.created_at)}</p></div>
          <span class="admin-badge ${org.status === "active" ? "ok" : org.status === "blocked" ? "danger" : "warn"}">${adminEscape(org.status)}</span>
        </div>
        <p>Контактное лицо: ${adminEscape(org.contact_person || "—")}</p>
        <div class="admin-actions">
          <button onclick="verifyOrg(${org.id})">Подтвердить</button>
          <button onclick="rejectOrg(${org.id})">Отклонить</button>
          <button onclick="blockOrg(${org.id})">Заблокировать</button>
        </div>
      </article>
    `).join("") || `<div class="admin-empty">Организации не найдены</div>`;
    adminSetStatus("");
  } catch (err) { adminSetStatus(err.message || "Ошибка загрузки организаций", "error"); }
}

async function verifyOrg(id) { await adminAction(`/admin/organizations/${id}/verify`, { method: "PATCH" }, loadOrganizations); }
async function blockOrg(id) { await adminAction(`/admin/organizations/${id}/block`, { method: "PATCH" }, loadOrganizations); }
async function rejectOrg(id) {
  const reason = prompt("Причина отклонения организации:");
  if (!reason) return;
  await adminAction(`/admin/organizations/${id}/reject`, { method: "POST", body: JSON.stringify({ reason }) }, loadOrganizations);
}

async function loadReports() {
  if (!adminRequireAuth()) return;
  const search = document.getElementById("reportSearch")?.value || "";
  const status = document.getElementById("reportStatus")?.value || "";
  try {
    adminSetStatus("Загрузка жалоб...");
    const { data } = await adminRequest(`/admin/reports${adminQuery({ search, status })}`);
    document.getElementById("reportsList").innerHTML = (data || []).map(report => `
      <article class="admin-card">
        <div class="admin-card-head"><div><h3>Жалоба #${report.id}</h3><p>${adminEscape(report.target_type)} · объект ${adminEscape(report.target_id)}</p></div><span class="admin-badge warn">${adminDate(report.created_at)}</span></div>
        <p>Причина: ${adminEscape(report.reason || "—")}</p>
        <p>Комментарий: ${adminEscape(report.comment || "—")}</p>
        <p>Автор жалобы: ${adminEscape(report.reporter_name || "—")}</p>
        <div class="admin-actions"><button onclick="dismissReport(${report.id})">Отклонить жалобу</button><button onclick="removeReportContent(${report.id})">Удалить контент</button></div>
      </article>
    `).join("") || `<div class="admin-empty">Жалоб нет</div>`;
    adminSetStatus("");
  } catch (err) { adminSetStatus(err.message || "Ошибка загрузки жалоб", "error"); }
}
async function dismissReport(id) { await adminAction(`/admin/reports/${id}/dismiss`, { method: "POST" }, loadReports); }
async function removeReportContent(id) {
  if (!confirm("Удалить/скрыть контент по этой жалобе?")) return;
  await adminAction(`/admin/reports/${id}/remove-content`, { method: "POST" }, loadReports);
}

async function loadContentReview() {
  if (!adminRequireAuth()) return;
  const content_type = document.getElementById("contentType")?.value || "post";
  try {
    adminSetStatus("Загрузка контента...");
    const { data } = await adminRequest(`/admin/content-review${adminQuery({ content_type })}`);
    document.getElementById("contentReviewList").innerHTML = (data || []).map(item => {
      const fullText = item.content || "Без текста";
      const preview = fullText.length > 220 ? `${fullText.slice(0, 220)}…` : fullText;
      const reason = item.reason ? `<p>Причина: ${adminEscape(item.reason)}</p>` : "";
      const fullBlock = fullText.length > 220
        ? `<details class="admin-expand"><summary>Развернуть полный текст</summary><p>${adminEscape(fullText)}</p></details>`
        : "";
      return `
      <article class="admin-card">
        <div class="admin-card-head"><div><h3>${adminEscape(labelContentType(item.type))} #${item.id}</h3><p>Автор: ${adminEscape(item.author_name || "—")}</p></div><span class="admin-badge warn">${adminDate(item.created_at)}</span></div>
        <p class="admin-content-preview">${adminEscape(preview)}</p>
        ${fullBlock}
        ${reason}
        <div class="admin-actions"><button onclick="approveContent('${item.type}', ${item.id})">Одобрить</button><button onclick="rejectContent('${item.type}', ${item.id})">Отклонить</button><button onclick="blockContentAuthor('${item.type}', ${item.id})">Блок автора</button></div>
      </article>`;
    }).join("") || `<div class="admin-empty">Контента на модерации нет</div>`;
    adminSetStatus("");
  } catch (err) { adminSetStatus(err.message || "Ошибка загрузки модерации", "error"); }
}
function labelContentType(type) { return ({post:"Пост", comment:"Комментарий", article:"Статья", review:"Отзыв"})[type] || type; }
async function approveContent(type, id) { await adminAction(`/admin/content-review/${type}/${id}/approve`, { method: "POST" }, loadContentReview); }
async function rejectContent(type, id) {
  const reason = prompt("Причина отклонения:");
  if (!reason) return;
  await adminAction(`/admin/content-review/${type}/${id}/reject`, { method: "POST", body: JSON.stringify({ reason }) }, loadContentReview);
}
async function blockContentAuthor(type, id) {
  if (!confirm("Заблокировать автора этого контента?")) return;
  await adminAction(`/admin/content-review/${type}/${id}/block-author`, { method: "POST" }, loadContentReview);
}

async function loadTickets() {
  if (!adminRequireAuth()) return;
  const search = document.getElementById("ticketSearch")?.value || "";
  const status = document.getElementById("ticketStatus")?.value || "";
  try {
    adminSetStatus("Загрузка тикетов...");
    const { data } = await adminRequest(`/admin/support-tickets${adminQuery({ search, status })}`);
    document.getElementById("ticketsList").innerHTML = (data || []).map(t => `
      <button class="admin-ticket" onclick="loadTicketDetail(${t.id})"><strong>#${t.id} ${adminEscape(t.subject)}</strong><span>${adminEscape(t.status)} · ${adminDate(t.created_at)}</span><small>${adminEscape(t.user_name || `user ${t.user_id}`)}</small></button>
    `).join("") || `<div class="admin-empty">Тикетов нет</div>`;
    adminSetStatus("");
  } catch (err) { adminSetStatus(err.message || "Ошибка загрузки тикетов", "error"); }
}

async function loadTicketDetail(id) {
  try {
    const { data: t } = await adminRequest(`/admin/support-tickets/${id}`);
    document.getElementById("ticketDetail").innerHTML = `
      <h2>#${t.id} ${adminEscape(t.subject)}</h2>
      <p><b>Статус:</b> ${adminEscape(t.status)} · <b>Приоритет:</b> ${adminEscape(t.priority)}</p>
      <p>${adminEscape(t.body)}</p>
      <h3>Сообщения</h3>
      <div class="admin-messages">${(t.messages || []).map(m => `<div><b>${adminEscape(m.sender_id)}</b> <small>${adminDate(m.created_at)}</small><p>${adminEscape(m.body)}</p></div>`).join("") || "Сообщений нет"}</div>
      <textarea id="ticketReply" placeholder="Ответ пользователю"></textarea>
      <div class="admin-actions"><button onclick="replyTicket(${t.id})">Ответить</button><button onclick="setTicketStatus(${t.id}, 'in_progress')">В работу</button><button onclick="setTicketStatus(${t.id}, 'closed')">Закрыть</button></div>
    `;
  } catch (err) { adminSetStatus(err.message || "Ошибка загрузки тикета", "error"); }
}
async function replyTicket(id) {
  const message = document.getElementById("ticketReply")?.value.trim();
  if (!message) return alert("Напиши ответ");
  await adminAction(`/admin/support-tickets/${id}/reply`, { method: "POST", body: JSON.stringify({ message }) }, () => loadTicketDetail(id));
}
async function setTicketStatus(id, status) { await adminAction(`/admin/support-tickets/${id}/status`, { method: "PATCH", body: JSON.stringify({ status }) }, () => loadTicketDetail(id)); }

async function loadAdminSettings() {
  if (!adminRequireAuth()) return;
  try {
    const [{ data: settings }, { data: tags }] = await Promise.all([
      adminRequest("/admin/moderation-settings"),
      adminRequest("/admin/tags"),
    ]);
    document.getElementById("postAutoPublish").checked = !!settings.post_auto_publish;
    document.getElementById("articleAutoPublish").checked = !!settings.article_auto_publish;
    renderTags(tags || []);
  } catch (err) { adminSetStatus(err.message || "Ошибка загрузки настроек", "error"); }
}
async function saveModerationSettings() {
  await adminAction("/admin/moderation-settings", {
    method: "PATCH",
    body: JSON.stringify({
      post_auto_publish: document.getElementById("postAutoPublish").checked,
      article_auto_publish: document.getElementById("articleAutoPublish").checked,
    }),
  }, loadAdminSettings);
}
async function createAdminTag() {
  const name = document.getElementById("newTagName")?.value.trim();
  if (!name) return;
  await adminAction("/admin/tags", { method: "POST", body: JSON.stringify({ name }) }, loadAdminSettings);
}
async function deleteAdminTag(id) { await adminAction(`/admin/tags/${id}`, { method: "DELETE" }, loadAdminSettings); }
function renderTags(tags) {
  document.getElementById("tagsList").innerHTML = tags.map(t => `<span class="admin-tag">${adminEscape(t.name)} <button onclick="deleteAdminTag(${t.id})">×</button></span>`).join("") || "Тегов нет";
}

async function loadAuditLogs() {
  if (!adminRequireAuth()) return;
  const entity_type = document.getElementById("auditEntityType")?.value || "";
  const entity_id = document.getElementById("auditEntityId")?.value || "";
  try {
    adminSetStatus("Загрузка аудита...");
    const { data } = await adminRequest(`/admin/audit-logs${adminQuery({ entity_type, entity_id, limit: 100 })}`);
    document.getElementById("auditList").innerHTML = (data || []).map(log => `
      <article class="admin-card"><div class="admin-card-head"><div><h3>${adminEscape(log.action)}</h3><p>${adminEscape(log.entity_type)} #${adminEscape(log.entity_id)}</p></div><span class="admin-badge">${adminDate(log.created_at)}</span></div><p>actor_id: ${adminEscape(log.actor_id)}</p><details class="admin-expand"><summary>before/after</summary><pre>${adminEscape(JSON.stringify({ before: log.before_state, after: log.after_state }, null, 2))}</pre></details></article>
    `).join("") || `<div class="admin-empty">Журнал пуст</div>`;
    adminSetStatus("");
  } catch (err) {
    const list = document.getElementById("auditList");
    if (list) {
      list.innerHTML = `<div class="admin-empty admin-empty-error">Аудит сейчас не загрузился: сервер вернул ${adminEscape(err.status || "ошибку")}. Фронт не падает, но сами записи аудита должен отдать backend.</div>`;
    }
    adminSetStatus(err.message || "Ошибка загрузки аудита", "error");
  }
}

async function adminAction(path, options, after) {
  try {
    adminSetStatus("Выполняю...");
    await adminRequest(path, options);
    adminSetStatus("Готово", "ok");
    if (after) await after();
  } catch (err) { adminSetStatus(err.message || "Ошибка действия", "error"); }
}

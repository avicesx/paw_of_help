// Организации: каталог, профиль, создание заявки.
// Дизайн: Каталог организаций.svg, Посты\Профиль организации*, Создание профиля заявки организации.svg.

function orgMediaUrl(u) {
  if (!u) return "";
  return /^https?:/i.test(u) ? u : `${API_URL}${u.startsWith("/") ? "" : "/"}${u}`;
}

function orgStatusBadge(o) {
  if (!o.status || ["verified", "approved", "active"].includes(o.status)) return "";
  const label = o.status === "pending" ? "на модерации" : (o.status === "rejected" ? "отклонена" : o.status);
  return `<span class="org-badge">${escapeHtml(label)}</span>`;
}

function orgCardHtml(o) {
  const icon = orgMediaUrl(o.logo_url);
  return `
    <button class="org-card" type="button" onclick="location.href='org.html?id=${o.id}'">
      <div class="org-icon" aria-hidden="true">${icon ? `<img src="${escapeHtml(icon)}" alt="">` : ""}</div>
      <div class="org-card-main">
        <div class="org-card-name">${escapeHtml(o.name || "Организация")}</div>
        ${orgStatusBadge(o)}
      </div>
    </button>`;
}

// ----- Каталог -----
async function loadOrgCatalog() {
  let all = [], my = [], subs = [];
  try { all = (await apiRequest("/organizations")).data || []; } catch (e) {}
  if (getToken()) {
    try { my = (await apiRequest("/organizations/my", { auth: true })).data || []; } catch (e) {}
    try { subs = (await apiRequest("/organizations/subscriptions", { auth: true })).data || []; } catch (e) {}
  }
  window.__orgAll = all;
  const myBox = document.getElementById("orgMy");
  const subBox = document.getElementById("orgSubs");
  const allBox = document.getElementById("orgAll");
  if (myBox) myBox.innerHTML = my.length ? my.map(orgCardHtml).join("") : '<div class="empty-small">Вы пока не состоите в организациях. Нажмите «+», чтобы подать заявку.</div>';
  if (subBox) subBox.innerHTML = subs.length ? subs.map(orgCardHtml).join("") : '<div class="empty-small">Подписок нет</div>';
  const exclude = new Set([...my, ...subs].map((o) => o.id));
  const others = all.filter((o) => !exclude.has(o.id));
  if (allBox) allBox.innerHTML = others.length ? others.map(orgCardHtml).join("") : '<div class="empty-small">Других организаций нет</div>';
}

function filterOrgCatalog() {
  const q = (document.getElementById("orgSearch")?.value || "").trim().toLowerCase();
  const all = window.__orgAll || [];
  const allBox = document.getElementById("orgAll");
  if (!allBox) return;
  const filtered = q ? all.filter((o) => (o.name || "").toLowerCase().includes(q)) : all;
  allBox.innerHTML = filtered.length ? filtered.map(orgCardHtml).join("") : '<div class="empty-small">Ничего не найдено</div>';
}

// ----- Создание заявки -----
async function createOrg(e) {
  if (e) e.preventDefault();
  if (!getToken()) { location.href = "login.html"; return; }
  const status = document.getElementById("orgCreateStatus");
  const name = (document.getElementById("orgName")?.value || "").trim();
  if (!name) { if (status) status.textContent = "Укажите название организации"; return; }
  const body = {
    name,
    description: (document.getElementById("orgDescription")?.value || "").trim() || null,
    inn: (document.getElementById("orgInn")?.value || "").trim() || null,
    address: (document.getElementById("orgAddress")?.value || "").trim() || null,
    address_components: {}, contacts: {}, documents: [], photos: [],
  };
  try {
    if (status) status.textContent = "Отправляем заявку...";
    const { data } = await apiRequest("/organizations", { method: "POST", auth: true, body: JSON.stringify(body) });
    if (status) status.textContent = "Заявка отправлена!";
    setTimeout(() => { location.href = `org.html?id=${data.id}`; }, 800);
  } catch (err) {
    if (status) status.textContent = err.message || "Не удалось создать организацию";
  }
}

// ----- Профиль организации -----
let _orgCurrent = null;

async function loadOrgProfile() {
  const id = new URLSearchParams(location.search).get("id");
  if (!id) return;
  try {
    const { data: org } = await apiRequest(`/organizations/${id}`);
    _orgCurrent = org;
    const nameEl = document.getElementById("orgProfileName");
    if (nameEl) nameEl.textContent = org.name || "Организация";
    const icon = orgMediaUrl(org.logo_url);
    const iconEl = document.getElementById("orgProfileIcon");
    if (icon && iconEl) iconEl.innerHTML = `<img src="${escapeHtml(icon)}" alt="">`;
    const infoEl = document.getElementById("orgProfileInfo");
    if (infoEl) infoEl.textContent = org.description || "Информация об организации не указана.";

    // подписка
    await refreshSubscribeBtn(org.id);
    await setupOrgManagement(org.id);
    switchOrgTab("posts");
  } catch (e) {
    const box = document.getElementById("orgTabContent");
    if (box) box.innerHTML = '<div class="empty-small">Организация не найдена</div>';
  }
}

async function refreshSubscribeBtn(orgId) {
  const btn = document.getElementById("orgSubscribeBtn");
  if (!btn || !getToken()) { if (btn) btn.style.display = "none"; return; }
  let subscribed = false;
  try {
    const subs = (await apiRequest("/organizations/subscriptions", { auth: true })).data || [];
    subscribed = subs.some((o) => Number(o.id) === Number(orgId));
  } catch (e) {}
  btn.dataset.subscribed = subscribed ? "1" : "";
  btn.textContent = subscribed ? "Отписаться" : "Подписаться";
}

async function toggleSubscribe() {
  if (!_orgCurrent) return;
  if (!getToken()) { location.href = "login.html"; return; }
  const btn = document.getElementById("orgSubscribeBtn");
  const subscribed = btn?.dataset.subscribed === "1";
  try {
    await apiRequest(`/organizations/${_orgCurrent.id}/subscribe`, { method: subscribed ? "DELETE" : "POST", auth: true });
    await refreshSubscribeBtn(_orgCurrent.id);
  } catch (err) { alert(err.message || "Ошибка"); }
}

function switchOrgTab(tab) {
  document.querySelectorAll(".org-tab").forEach((b) => b.classList.toggle("active", b.dataset.tab === tab));
  const box = document.getElementById("orgTabContent");
  if (!box || !_orgCurrent) return;
  box.innerHTML = '<div class="empty-small">Загрузка...</div>';
  if (tab === "posts") loadOrgPosts(box);
  else if (tab === "animals") loadOrgAnimals(box);
  else loadOrgTasks(box);
}

async function loadOrgPosts(box) {
  try {
    const posts = (await apiRequest(`/posts?organization_id=${_orgCurrent.id}`)).data || [];
    box.innerHTML = posts.length
      ? posts.map((p) => `<article class="org-post"><div class="org-post-text">${escapeHtml(p.content || p.title || "")}</div></article>`).join("")
      : '<div class="empty-small">Постов пока нет</div>';
  } catch (e) { box.innerHTML = '<div class="empty-small">Не удалось загрузить посты</div>'; }
}
async function loadOrgAnimals(box) {
  try {
    const all = (await apiRequest("/animals")).data || [];
    const animals = all.filter((a) => a.owner_type === "organization" && Number(a.owner_id) === Number(_orgCurrent.id));
    box.innerHTML = animals.length
      ? animals.map((a) => {
          const photo = Array.isArray(a.photos) && a.photos.length ? orgMediaUrl(a.photos[0]) : "";
          return `<button class="org-row org-animal-row" type="button" onclick="location.href='animal-profile.html?id=${a.id}'">
            <span class="org-animal-thumb">${photo ? `<img src="${escapeHtml(photo)}" alt="">` : ""}</span>
            <span>${escapeHtml(a.name || "Животное")}</span>
          </button>`;
        }).join("")
      : '<div class="empty-small">Животных пока нет</div>';
  } catch (e) { box.innerHTML = '<div class="empty-small">Не удалось загрузить</div>'; }
}
async function loadOrgTasks(box) {
  try {
    const tasks = (await apiRequest(`/tasks?organization_id=${_orgCurrent.id}`)).data || [];
    box.innerHTML = tasks.length
      ? tasks.map((t) => `<div class="org-row"><b>${escapeHtml(t.title || "Задача")}</b></div>`).join("")
      : '<div class="empty-small">Заявок пока нет</div>';
  } catch (e) { box.innerHTML = '<div class="empty-small">Не удалось загрузить</div>'; }
}

// ----- Управление организацией (для персонала) -----
let _myId = null;
async function getMyId() {
  if (_myId !== null) return _myId;
  if (!getToken()) return (_myId = 0);
  try {
    const { data } = await apiRequest("/auth/me", { auth: true });
    _myId = data.id;
  } catch (e) { _myId = 0; }
  return _myId;
}

// Возвращает роль текущего пользователя в организации (admin/curator) или null.
async function getMyOrgRole(orgId) {
  if (!getToken()) return null;
  try {
    const users = (await apiRequest(`/organizations/${orgId}/users`, { auth: true })).data || [];
    const myId = await getMyId();
    const me = users.find((u) => Number(u.user_id) === Number(myId));
    return me && me.invitation_status === "accepted" ? me.role : null;
  } catch (e) {
    return null; // 403 => не сотрудник
  }
}

async function setupOrgManagement(orgId) {
  const bar = document.getElementById("orgManageBar");
  if (!bar) return;
  const role = await getMyOrgRole(orgId);
  if (!role) { bar.style.display = "none"; return; }
  bar.style.display = "flex";
  const editBtn = document.getElementById("orgEditBtn");
  if (editBtn) editBtn.style.display = role === "admin" ? "" : "none";
  // сотрудник не подписывается на свою организацию
  const subBtn = document.getElementById("orgSubscribeBtn");
  if (subBtn) subBtn.style.display = "none";
}

function orgGoPost() { const id = _orgCurrent?.id; if (id) location.href = `post-create.html?org_id=${id}`; }
function orgGoCurators() { const id = _orgCurrent?.id; if (id) location.href = `org-curators.html?id=${id}`; }
function orgGoEdit() { const id = _orgCurrent?.id; if (id) location.href = `org-edit.html?id=${id}`; }

// ----- Список кураторов -----
async function loadOrgCurators() {
  const id = new URLSearchParams(location.search).get("id");
  if (!id) return;
  window.__orgId = id;
  const addLink = document.getElementById("orgInviteLink");
  if (addLink) addLink.href = `org-invite.html?id=${id}`;
  const adminBox = document.getElementById("orgAdminsList");
  const curBox = document.getElementById("orgCuratorsList");
  try {
    const users = (await apiRequest(`/organizations/${id}/users`, { auth: true })).data || [];
    const myId = await getMyId();
    const accepted = users.filter((u) => u.invitation_status === "accepted");
    const pending = users.filter((u) => u.invitation_status === "pending");
    const admins = accepted.filter((u) => u.role === "admin");
    const curators = accepted.filter((u) => u.role === "curator");
    const me = accepted.find((u) => Number(u.user_id) === Number(myId));
    const iAmAdmin = me && me.role === "admin";

    if (adminBox) adminBox.innerHTML = admins.map((u) => curatorCardHtml(u, myId, iAmAdmin, id)).join("") || '<div class="empty-small">—</div>';
    if (curBox) {
      const cards = curators.map((u) => curatorCardHtml(u, myId, iAmAdmin, id));
      const pend = pending.map((u) => curatorCardHtml(u, myId, iAmAdmin, id, true));
      curBox.innerHTML = (cards.concat(pend)).join("") || '<div class="empty-small">Кураторов пока нет</div>';
    }
    // ссылку «добавить» показываем только админу
    if (addLink) addLink.style.display = iAmAdmin ? "" : "none";
  } catch (e) {
    if (adminBox) adminBox.innerHTML = '<div class="empty-small">Нет доступа к списку сотрудников</div>';
  }
}

function curatorCardHtml(u, myId, iAmAdmin, orgId, pending) {
  const mine = Number(u.user_id) === Number(myId);
  const name = `Пользователь #${u.user_id}${mine ? " (вы)" : ""}`;
  const canRemove = iAmAdmin && !mine;
  return `
    <div class="curator-card">
      <span class="curator-avatar" aria-hidden="true"></span>
      <span class="curator-name">${escapeHtml(name)}${pending ? ' <span class="curator-pending">приглашён</span>' : ""}</span>
      ${canRemove ? `<button type="button" class="curator-remove" title="Удалить" onclick="removeCurator(${orgId}, ${u.user_id})">✕</button>` : ""}
    </div>`;
}

async function removeCurator(orgId, userId) {
  if (!confirm("Удалить этого сотрудника из организации?")) return;
  try {
    await apiRequest(`/organizations/${orgId}/users/${userId}`, { method: "DELETE", auth: true });
    await loadOrgCurators();
  } catch (e) { alert(e.message || "Не удалось удалить"); }
}

// ----- Приглашение куратора -----
async function inviteCurator(e) {
  if (e) e.preventDefault();
  const id = new URLSearchParams(location.search).get("id");
  const status = document.getElementById("orgInviteStatus");
  const username = (document.getElementById("inviteUsername")?.value || "").trim();
  if (!username) { if (status) status.textContent = "Укажите логин куратора"; return; }
  try {
    if (status) status.textContent = "Отправляем приглашение...";
    await apiRequest(`/organizations/${id}/invite`, {
      method: "POST", auth: true,
      body: JSON.stringify({ username, role: "curator" }),
    });
    if (status) status.textContent = "Приглашение отправлено!";
    setTimeout(() => { location.href = `org-curators.html?id=${id}`; }, 800);
  } catch (err) {
    if (status) status.textContent = err.message || "Не удалось пригласить";
  }
}

// ----- Редактирование профиля организации -----
async function loadOrgEdit() {
  const id = new URLSearchParams(location.search).get("id");
  if (!id) return;
  try {
    const { data: org } = await apiRequest(`/organizations/${id}`);
    setValue("edit_org_name", org.name);
    setValue("edit_org_description", org.description);
    setValue("edit_org_inn", org.inn);
    setValue("edit_org_address", org.address);
    const logoEl = document.getElementById("editOrgLogo");
    const icon = orgMediaUrl(org.logo_url);
    if (icon && logoEl) logoEl.style.backgroundImage = `url('${icon}')`;
    window.__editOrgLogoUrl = org.logo_url || null;
  } catch (e) {
    setStatus("orgEditStatus", "Не удалось загрузить организацию");
  }
}

async function uploadOrgLogo(input) {
  const file = input.files && input.files[0];
  if (!file) return;
  try {
    setStatus("orgEditStatus", "Загружаем логотип...");
    const fd = new FormData();
    fd.append("file", file);
    const { data } = await apiRequest("/uploads", { method: "POST", auth: true, body: fd });
    window.__editOrgLogoUrl = data.url;
    const logoEl = document.getElementById("editOrgLogo");
    if (logoEl) logoEl.style.backgroundImage = `url('${orgMediaUrl(data.url)}')`;
    setStatus("orgEditStatus", "Логотип обновлён");
  } catch (e) { setStatus("orgEditStatus", e.message || "Не удалось загрузить логотип"); }
}

async function saveOrgEdit(e) {
  if (e) e.preventDefault();
  const id = new URLSearchParams(location.search).get("id");
  const body = {
    name: getValue("edit_org_name") || null,
    description: getValue("edit_org_description") || null,
    inn: getValue("edit_org_inn") || null,
    address: getValue("edit_org_address") || null,
  };
  if (window.__editOrgLogoUrl) body.logo_url = window.__editOrgLogoUrl;
  try {
    setStatus("orgEditStatus", "Сохраняем...");
    await apiRequest(`/organizations/${id}`, { method: "PATCH", auth: true, body: JSON.stringify(body) });
    setStatus("orgEditStatus", "Сохранено!");
    setTimeout(() => { location.href = `org.html?id=${id}`; }, 700);
  } catch (err) {
    setStatus("orgEditStatus", err.message || "Не удалось сохранить");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("orgAll")) loadOrgCatalog();
  if (document.getElementById("orgTabContent")) loadOrgProfile();
  if (document.getElementById("orgAdminsList")) loadOrgCurators();
  if (document.getElementById("editOrgLogo")) loadOrgEdit();
});

const API_URL = window.API_URL || (window.location.protocol === "file:"
  ? "http://127.0.0.1:8000"
  : `${window.location.protocol}//${window.location.hostname}:8000`);
const ORG_ID_KEY = "paw_org_id";
const SELECTED_ANIMAL_KEY = "paw_selected_animal";
const COMPLAINTS_KEY = "paw_complaints";

function getToken() {
  return localStorage.getItem("token");
}

function ensureAuth(redirect = "login.html") {
  const token = getToken();
  if (!token) {
    window.location.href = redirect;
    return null;
  }
  return token;
}

async function apiRequest(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (!headers["Content-Type"] && !(options.body instanceof FormData) && options.method && options.method !== "GET") {
    headers["Content-Type"] = "application/json";
  }

  if (options.auth) {
    const token = getToken();
    if (!token) {
      throw new Error("Нужна авторизация");
    }
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (res.status === 204) {
    return { ok: true, status: res.status, data: null };
  }

  let data = null;
  try {
    data = await res.json();
  } catch {
    data = null;
  }

  if (!res.ok) {
    const detail = parseErrorDetail(data, `Ошибка ${res.status}`);
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }

  return { ok: true, status: res.status, data };
}

function parseErrorDetail(data, fallback) {
  if (!data) return fallback;
  if (typeof data.detail === "string") {
    const d = data.detail;
    if (d === "Not Found" || d === "Not found") return fallback; // show HTTP status instead
    return d;
  }
  if (Array.isArray(data.detail)) {
    return data.detail.map(item => {
      // Частые ошибки валидации Pydantic переводим на русский
      if (item && item.type === "string_too_short") {
        const min = item.ctx && item.ctx.min_length;
        const field = Array.isArray(item.loc) && item.loc.includes("password") ? "Пароль" : "Поле";
        return `${field} слишком короткое — минимум ${min || 6} символов.`;
      }
      return (item && item.msg) || JSON.stringify(item);
    }).join("\n");
  }
  if (typeof data.message === "string") return data.message;
  return fallback;
}

async function register() {
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value.trim();

  if (!username || !password) {
    alert("Нужно указать логин и пароль.");
    return;
  }

  if (password.length < 6) {
    alert("Пароль слишком короткий — минимум 6 символов.");
    return;
  }

  try {
    const { data } = await apiRequest("/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });

    localStorage.setItem("token", data.access_token);
    window.location.href = "profile.html";
  } catch (err) {
    alert(err.message || "Ошибка регистрации");
    console.error("REGISTER ERROR:", err);
  }
}

async function login() {
  const loginValue = document.getElementById("login").value.trim();
  const password = document.getElementById("password").value.trim();

  if (!loginValue || !password) {
    alert("Заполни логин и пароль.");
    return;
  }

  try {
    const { data } = await apiRequest("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        login: loginValue,
        password
      }),
    });

    localStorage.setItem("token", data.access_token);
    window.location.href = "profile.html";
  } catch (err) {
    alert(err.message || "Ошибка входа");
    console.error("LOGIN ERROR:", err);
  }
}

async function loadProfile() {
  const token = ensureAuth("login.html");
  if (!token) return;

  try {
    const { data: user } = await apiRequest("/auth/me", { auth: true });

    const displayName = [user.name, user.last_name].filter(Boolean).join(" ") || user.username || "Пользователь";
    const firstName = user.name || user.username || "Пользователь";
    const lastName = user.last_name || "";

    const usernameNode = document.getElementById("username");
    const contactLineNode = document.getElementById("contactLine");
    const firstNameNode = document.getElementById("profileFirstName");
    const lastNameNode = document.getElementById("profileLastName");
    const reviewsLink = document.getElementById("profileReviewsLink");

    if (usernameNode) usernameNode.textContent = displayName;
    if (contactLineNode) contactLineNode.textContent = user.phone || user.email || "Контакт не указан";
    if (firstNameNode) firstNameNode.textContent = firstName;
    if (lastNameNode) {
      lastNameNode.textContent = lastName;
      lastNameNode.style.display = lastName ? "block" : "none";
    }
    if (reviewsLink && user.id) {
      reviewsLink.href = `reviews.html?target_type=volunteer&target_id=${encodeURIComponent(user.id)}&reviewee_id=${encodeURIComponent(user.id)}`;
    }

    await loadProfileRating(user.id);
  } catch (err) {
    alert(err.message || "Ошибка загрузки профиля");
    console.error("PROFILE ERROR:", err);
    localStorage.removeItem("token");
    window.location.href = "login.html";
  }
}

async function loadProfileRating(userId) {
  const ratingValueNode = document.getElementById("profileRatingValue");
  const reviewCountNode = document.getElementById("profileReviewCount");
  const legacyRatingNode = document.querySelector(".profile-rating");

  let rating = 0;
  let count = 0;

  try {
    const { data: volunteer } = await apiRequest("/volunteer/profile", { auth: true });
    const stats = volunteer?.stats || {};
    rating = Number(stats.rating_by_reviews || 0);
    count = Number(stats.total_reviews_count || 0);
  } catch (err) {
    console.warn("VOLUNTEER STATS LOAD ERROR:", err);

    if (userId) {
      try {
        const { data: reviews } = await apiRequest(`/reviews?target_type=volunteer&target_id=${encodeURIComponent(userId)}`);
        const list = Array.isArray(reviews) ? reviews : [];
        count = list.length;
        rating = count ? list.reduce((sum, item) => sum + Number(item.rating || 0), 0) / count : 0;
      } catch (reviewsErr) {
        console.warn("PROFILE REVIEWS FALLBACK ERROR:", reviewsErr);
      }
    }
  }

  const ratingText = rating.toFixed(1).replace(".", ",");
  const countText = String(count);

  if (ratingValueNode) ratingValueNode.textContent = ratingText;
  if (reviewCountNode) reviewCountNode.textContent = countText;
  if (legacyRatingNode) legacyRatingNode.innerHTML = `${ratingText} ⭐ <span>${countText} ${pluralizeReviews(count)}</span>`;
}

function pluralizeReviews(count) {
  const n = Math.abs(Number(count)) % 100;
  const n1 = n % 10;
  if (n > 10 && n < 20) return "отзывов";
  if (n1 > 1 && n1 < 5) return "отзыва";
  if (n1 === 1) return "отзыв";
  return "отзывов";
}

async function loadSettingsPage() {
  const token = ensureAuth("login.html");
  if (!token) return;

  loadVolunteerSkills();

  try {
    const [{ data: user }, { data: volunteer }] = await Promise.all([
      apiRequest("/users/me", { auth: true }),
      apiRequest("/volunteer/profile", { auth: true }),
    ]);

    setValue("settings_name", user.name);
    setValue("settings_last_name", user.last_name);
    setValue("settings_username", user.username);
    setValue("settings_email", user.email);
    setValue("settings_phone", user.phone);

    setValue("vol_location", volunteer.location);
    setValue("vol_radius_km", volunteer.radius_km);
    setValue("vol_housing_type", volunteer.housing_type);
    setValue("vol_preferred_animal_types", Array.isArray(volunteer.preferred_animal_types) ? volunteer.preferred_animal_types.join(", ") : "");
    // Заполнить поля доступности из объекта
    const avail = volunteer.availability || {};
    const weekdaysSel = document.getElementById("avail_weekdays");
    const weekendSel = document.getElementById("avail_weekend");
    if (weekdaysSel) weekdaysSel.value = avail.weekdays || avail.weekday || "";
    if (weekendSel) weekendSel.value = avail.weekend || avail.weekends || "";
    setChecked("vol_ready_for_foster", !!volunteer.ready_for_foster);
    setChecked("vol_has_children", !!volunteer.has_children);
    // Заполнить чекбоксы питомцев
    const pets = volunteer.has_other_pets || {};
    const setCb = (id, val) => { const el = document.getElementById(id); if (el) el.checked = !!val; };
    setCb("pets_cats", pets.cats);
    setCb("pets_dogs", pets.dogs);
    setCb("pets_birds", pets.birds);
    setCb("pets_other", pets.other);
    setValue("vol_foster_restrictions", volunteer.foster_restrictions || "");

    setValue("vol_location_lat", volunteer.location_lat);
    setValue("vol_location_lng", volunteer.location_lng);
    if (volunteer.location_lat != null && volunteer.location_lng != null && window.volMapCtl) {
      window.volMapCtl.applyPoint(Number(volunteer.location_lat), Number(volunteer.location_lng), { updateAddress: false });
    }

    const statsNode = document.getElementById("volunteerStats");
    if (statsNode && volunteer.stats) {
      statsNode.textContent = `Задач: ${volunteer.stats.total_completed_tasks} · Рейтинг: ${volunteer.stats.rating_by_reviews} · Отзывов: ${volunteer.stats.total_reviews_count}`;
    }
  } catch (err) {
    setStatus("settingsStatus", err.message || "Ошибка загрузки настроек");
    console.error("SETTINGS LOAD ERROR:", err);
  }
}

async function saveAccountSettings(event) {
  event.preventDefault();
  try {
    const payload = {
      name: nullIfEmpty(getValue("settings_name")),
      last_name: nullIfEmpty(getValue("settings_last_name")),
      username: nullIfEmpty(getValue("settings_username")),
      email: nullIfEmpty(getValue("settings_email")),
      phone: nullIfEmpty(getValue("settings_phone")),
    };
    const { data } = await apiRequest("/users/me", {
      method: "PATCH",
      auth: true,
      body: JSON.stringify(payload),
    });
    setStatus("settingsStatus", "Настройки аккаунта сохранены.");
    const usernameNode = document.getElementById("username");
    if (usernameNode) {
      usernameNode.textContent = [data.name, data.last_name].filter(Boolean).join(" ");
    }
  } catch (err) {
    setStatus("settingsStatus", err.message || "Ошибка сохранения");
  }
}

async function changePassword(event) {
  event.preventDefault();
  try {
    const oldPassword = getValue("old_password");
    const newPassword = getValue("new_password");
    const repeatPassword = getValue("repeat_new_password");

    if (!oldPassword || !newPassword || !repeatPassword) {
      throw new Error("Заполни все поля пароля.");
    }
    if (newPassword !== repeatPassword) {
      throw new Error("Новые пароли не совпадают.");
    }

    await apiRequest("/users/me/change-password", {
      method: "POST",
      auth: true,
      body: JSON.stringify({
        current_password: oldPassword,
        new_password: newPassword
      }),
    });
    setStatus("passwordStatus", "Пароль обновлён.");
    ["old_password", "new_password", "repeat_new_password"].forEach(id => setValue(id, ""));
  } catch (err) {
    setStatus("passwordStatus", err.message || "Ошибка смены пароля");
  }
}

async function saveVolunteerProfile(event) {
  if (event) event.preventDefault();

  const profile = {
    location: nullIfEmpty(getValue("vol_location")),
    location_lat: toNumberOrNull(getValue("vol_location_lat")),
    location_lng: toNumberOrNull(getValue("vol_location_lng")),
    radius_km: toNumberOrNull(getValue("vol_radius_km")),
    housing_type: nullIfEmpty(getValue("vol_housing_type")),
    preferred_animal_types: splitCsv(getValue("vol_preferred_animal_types")),
    availability: (() => {
      const weekdays = document.getElementById("avail_weekdays")?.value || "";
      const weekend = document.getElementById("avail_weekend")?.value || "";
      const obj = {};
      if (weekdays) obj.weekdays = weekdays;
      if (weekend) obj.weekend = weekend;
      return obj;
    })(),
    ready_for_foster: getChecked("vol_ready_for_foster"),
    has_children: getChecked("vol_has_children"),
    has_other_pets: (() => {
      const obj = {};
      const getCb = id => document.getElementById(id)?.checked ? 1 : 0;
      if (getCb("pets_cats")) obj.cats = 1;
      if (getCb("pets_dogs")) obj.dogs = 1;
      if (getCb("pets_birds")) obj.birds = 1;
      if (getCb("pets_other")) obj.other = 1;
      return obj;
    })(),
    foster_restrictions: nullIfEmpty(getValue("vol_foster_restrictions")),
    foster_photos: []
  };

  try {
    await apiRequest("/volunteer/profile", {
      method: "PATCH",
      auth: true,
      body: JSON.stringify(profile),
    });
    await saveVolunteerSkills();
    setStatus("volunteerStatus", "Профиль волонтёра сохранён.");
  } catch (err) {
    setStatus("volunteerStatus", err.message || "Ошибка сохранения профиля");
  }
}

// --- Компетенции волонтёра (навыки) (#6) ---
async function loadVolunteerSkills() {
  const box = document.getElementById("skillsList");
  if (!box) return;
  try {
    const allResp = await apiRequest("/volunteer/skills");
    let mine = [];
    try {
      const mineResp = await apiRequest("/volunteer/my-skills", { auth: true });
      mine = Array.isArray(mineResp.data) ? mineResp.data : [];
    } catch (_) {
      mine = [];
    }

    const skills = (allResp.data && allResp.data.skills) ? allResp.data.skills : [];
    const mineSet = new Set(mine.map(Number));

    if (!skills.length) {
      box.innerHTML = '<div class="small-muted">Список компетенций пока пуст. Добавьте навыки в базе данных (например «Перевозка», «Ветеринарная помощь»).</div>';
      return;
    }

    box.innerHTML = skills.map((s) => `
      <label class="checkbox-item">
        <input type="checkbox" class="skill-cb" value="${s.id}" ${mineSet.has(Number(s.id)) ? "checked" : ""}>
        <span>${escapeHtml(s.name)}${s.description ? ` — <span class="small-muted">${escapeHtml(s.description)}</span>` : ""}</span>
      </label>
    `).join("");
  } catch (err) {
    box.innerHTML = `<div class="small-muted">Не удалось загрузить компетенции: ${escapeHtml(err.message || "")}</div>`;
  }
}

function getSelectedSkillIds() {
  return Array.from(document.querySelectorAll(".skill-cb:checked")).map((cb) => Number(cb.value));
}

async function saveVolunteerSkills() {
  if (!document.getElementById("skillsList")) return;
  try {
    await apiRequest("/volunteer/my-skills", {
      method: "POST",
      auth: true,
      body: JSON.stringify({ skill_ids: getSelectedSkillIds() }),
    });
  } catch (err) {
    console.warn("SAVE SKILLS ERROR:", err);
  }
}

// --- Создание через форму «статьи» из профиля: по факту публикуем пост в ленту (#3) ---
async function createArticle(event) {
  if (event) event.preventDefault();
  const token = ensureAuth("login.html");
  if (!token) return;

  const title = getValue("articleTitle");
  const content = getValue("articleContent");

  if (!title) {
    setStatus("articleStatus", "Укажите заголовок статьи.");
    return;
  }

  if (!content) {
    setStatus("articleStatus", "Напишите текст статьи.");
    return;
  }

  try {
    await apiRequest("/posts", {
      method: "POST",
      auth: true,
      body: JSON.stringify({ title, content, attachments: [] }),
    });
    setStatus("articleStatus", "Статья опубликована как пост в ленте.");
    setTimeout(() => { window.location.href = "feed.html"; }, 800);
  } catch (err) {
    setStatus("articleStatus", err.message || "Ошибка публикации поста");
  }
}

// --- Загрузка фото животного в его профиле (#16) ---
async function uploadAnimalPhoto(animalId) {
  const input = document.getElementById("animalPhotoInput");
  const file = input && input.files && input.files[0];
  if (!file) return;

  try {
    const fd = new FormData();
    fd.append("file", file);
    const { data: up } = await apiRequest("/uploads", { method: "POST", auth: true, body: fd });

    const { data: animal } = await apiRequest(`/animals/${animalId}`);
    const photos = Array.isArray(animal.photos) ? animal.photos.slice() : [];
    photos.unshift(up.url);

    await apiRequest(`/animals/${animalId}`, {
      method: "PATCH",
      auth: true,
      body: JSON.stringify({ photos }),
    });

    window.location.reload();
  } catch (err) {
    alert(err.message || "Не удалось загрузить фото");
  }
}

async function loadReviewsPage() {
  const params = new URLSearchParams(window.location.search);
  const targetType = params.get("target_type") || "organization";
  const targetId = params.get("target_id") || localStorage.getItem(ORG_ID_KEY) || "1";
  const revieweeId = params.get("reviewee_id") || "";

  setValue("review_target_type", targetType);
  setValue("review_target_id", targetId);
  setValue("review_reviewee_id", revieweeId);

  await fetchReviews();
  initReviewStars();
}

async function fetchReviews() {
  try {
    const targetType = getValue("review_target_type") || "organization";
    const targetId = getValue("review_target_id") || "1";

    const { data } = await apiRequest(`/reviews?target_type=${encodeURIComponent(targetType)}&target_id=${encodeURIComponent(targetId)}`);
    const reviews = Array.isArray(data) ? data : [];
    window.__reviews = reviews;
    renderReviewsSummary(reviews);
    renderReviewsList(reviews);
  } catch (err) {
    setStatus("reviewsStatus", err.message || "Ошибка загрузки отзывов");
    window.__reviews = [];
    renderReviewsSummary([]);
    renderReviewsList([]);
  }
}

function starString(rating) {
  const r = Math.max(0, Math.min(5, Math.round(Number(rating) || 0)));
  return "★".repeat(r) + "☆".repeat(5 - r);
}

function renderReviewsSummary(reviews) {
  const avgEl = document.getElementById("reviewsAvg");
  const countEl = document.getElementById("reviewsCountLabel");
  const histEl = document.getElementById("reviewsHistogram");

  const count = reviews.length;
  const sum = reviews.reduce((s, r) => s + Number(r.rating || 0), 0);
  const avg = count ? sum / count : 0;

  if (avgEl) avgEl.textContent = avg.toFixed(1).replace(".", ",");
  if (countEl) countEl.textContent = `${count} ${pluralizeReviews(count)}`;
  if (histEl) {
    histEl.innerHTML = [5, 4, 3, 2, 1].map((star) => {
      const n = reviews.filter((r) => Number(r.rating) === star).length;
      return `<div class="hist-row"><span class="hist-stars">${"★".repeat(star)}${"☆".repeat(5 - star)}</span><span class="hist-count">${n}</span></div>`;
    }).join("");
  }
}

function renderReviewsList(reviews) {
  const list = document.getElementById("reviewsList");
  if (!list) return;

  let items = Array.isArray(reviews) ? reviews.slice() : [];
  const sort = document.getElementById("reviewsSort")?.value || "new";
  items.sort((a, b) => {
    if (sort === "old") return new Date(a.created_at) - new Date(b.created_at);
    if (sort === "high") return Number(b.rating) - Number(a.rating);
    if (sort === "low") return Number(a.rating) - Number(b.rating);
    return new Date(b.created_at) - new Date(a.created_at); // new
  });

  if (!items.length) {
    list.innerHTML = '<div class="empty-small">Отзывов пока нет</div>';
    return;
  }

  list.innerHTML = items.map((review) => `
    <div class="review-card">
      <div class="review-head">
        <div class="review-avatar" aria-hidden="true"></div>
        <div class="review-head-main">
          <div class="review-author">Пользователь #${escapeHtml(String(review.reviewer_id))}</div>
          <div class="review-stars">${starString(review.rating)}</div>
        </div>
      </div>
      <div class="review-comment">${escapeHtml(review.comment || "Без комментария")}</div>
      <div class="review-date">${formatDateTime(review.created_at)}</div>
    </div>
  `).join("");
}

function initReviewStars() {
  const wrap = document.getElementById("reviewStarsInput");
  if (!wrap) return;
  const hidden = document.getElementById("review_rating");
  const stars = Array.from(wrap.querySelectorAll(".rev-star"));
  const paint = (v) => stars.forEach((s) => s.classList.toggle("on", Number(s.dataset.v) <= v));
  stars.forEach((s) => {
    s.addEventListener("click", () => {
      const v = Number(s.dataset.v);
      if (hidden) hidden.value = String(v);
      paint(v);
    });
  });
  paint(Number(hidden && hidden.value ? hidden.value : 5));
}

function toggleLeaveReview() {
  const form = document.getElementById("leaveReviewForm");
  if (!form) return;
  form.classList.toggle("hidden");
  if (!form.classList.contains("hidden")) form.scrollIntoView({ behavior: "smooth", block: "center" });
}

async function submitReview(event) {
  event.preventDefault();
  try {
    const payload = {
      reviewee_id: Number(getValue("review_reviewee_id")),
      target_type: getValue("review_target_type"),
      target_id: Number(getValue("review_target_id")),
      rating: Number(getValue("review_rating")),
      comment: nullIfEmpty(getValue("review_comment")),
    };

    if (!payload.reviewee_id || !payload.target_id || !payload.target_type || !payload.rating) {
      throw new Error("Заполни обязательные поля отзыва.");
    }

    await apiRequest("/reviews", {
      method: "POST",
      auth: true,
      body: JSON.stringify(payload),
    });
    setStatus("reviewsStatus", "Отзыв отправлен.");
    setValue("review_comment", "");
    await fetchReviews();
  } catch (err) {
    setStatus("reviewsStatus", err.message || "Ошибка отправки отзыва");
  }
}

async function loadComplaintsPage() {
  const params = new URLSearchParams(window.location.search);
  const targetType = params.get("target_type") || document.getElementById("complaint_target_type")?.value || "user";
  const targetId = params.get("target_id") || "";
  setValue("complaint_target_type", targetType);
  if (targetId) setValue("complaint_target_id", targetId);
  await loadReportReasons();
}

async function loadReportReasons() {
  const box = document.getElementById("complaintReasons");
  if (!box) return;

  const targetType = getValue("complaint_target_type") || "user";
  let reasons = [];
  try {
    const { data } = await apiRequest(`/reports/reasons?target_type=${encodeURIComponent(targetType)}`);
    reasons = Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn("REPORT REASONS LOAD ERROR:", err);
  }

  // запасной список, если backend ничего не вернул — чтобы экран не был пустым
  if (!reasons.length) {
    reasons = [
      { code: "spam", title: "Спам" },
      { code: "abuse", title: "Оскорбление" },
      { code: "fraud", title: "Мошенничество" },
      { code: "other", title: "Другое" },
    ];
  }

  box.innerHTML = reasons
    .map((reason, i) => `
      <button type="button" class="reason-chip${i === 0 ? " active" : ""}" data-code="${escapeHtml(reason.code)}" onclick="selectReason(this)">${escapeHtml(reason.title)}</button>
    `)
    .join("");
  setValue("complaint_category", reasons[0].code);
}

function selectReason(el) {
  document.querySelectorAll("#complaintReasons .reason-chip").forEach((c) => c.classList.remove("active"));
  el.classList.add("active");
  setValue("complaint_category", el.dataset.code || "other");
}

function renderComplaintsInfo() {
  const list = document.getElementById("complaintsList");
  if (!list) return;
  list.innerHTML = '<div class="empty-small">История отправленных жалоб на backend пока не возвращается. Новые жалобы отправляются через POST /reports.</div>';
}

async function submitComplaint(event) {
  event.preventDefault();

  try {
    const payload = {
      target_type: getValue("complaint_target_type"),
      target_id: Number(getValue("complaint_target_id")),
      reason_code: getValue("complaint_category"),
      description: nullIfEmpty(getValue("complaint_text")),
    };

    if (!payload.target_type || !payload.target_id || !payload.reason_code) {
      throw new Error("Заполни тип, ID сущности и причину жалобы.");
    }

    await apiRequest("/reports/", {
      method: "POST",
      auth: true,
      body: JSON.stringify(payload),
    });

    setStatus("complaintStatus", "Жалоба отправлена.");
    ["complaint_target_id", "complaint_text"].forEach(id => setValue(id, ""));
    renderComplaintsInfo();
  } catch (err) {
    setStatus("complaintStatus", err.message || "Ошибка отправки жалобы");
  }
}

async function loadNotificationsCount() {
  const badge = document.getElementById("notificationBadge");
  if (!badge || !getToken()) return;
  try {
    const { data } = await apiRequest("/notifications?is_read=false", { auth: true });
    const _count = (data || []).length;
    badge.textContent = _count > 0 ? String(_count) : '';
    badge.style.display = _count > 0 ? 'inline-flex' : 'none';
  } catch {}
}

function logout() {
  localStorage.removeItem("token");
  window.location.href = "login.html";
}

function setStatus(id, text) {
  const node = document.getElementById(id);
  if (node) node.textContent = text;
}

function getValue(id) {
  const node = document.getElementById(id);
  return node ? node.value.trim() : "";
}

function setValue(id, value) {
  const node = document.getElementById(id);
  if (node) node.value = value ?? "";
}

function getChecked(id) {
  const node = document.getElementById(id);
  return !!(node && node.checked);
}

function setChecked(id, value) {
  const node = document.getElementById(id);
  if (node) node.checked = !!value;
}

function splitCsv(text) {
  return text
    .split(",")
    .map(item => item.trim())
    .filter(Boolean);
}

function parseJsonOrFallback(text, fallback) {
  if (!text) return fallback;
  try {
    return JSON.parse(text);
  } catch {
    return fallback;
  }
}

function toNumberOrNull(value) {
  if (value === "") return null;
  const num = Number(value);
  return Number.isFinite(num) ? num : null;
}

function nullIfEmpty(value) {
  return value === "" ? null : value;
}

function formatDateTime(value) {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString("ru-RU");
  } catch {
    return String(value);
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

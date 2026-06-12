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

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await apiRequest('/uploads', {
        method: 'POST',
        auth: true,
        body: formData
    });
    return data.url;
}

function parseErrorDetail(data, fallback) {
  if (!data) return fallback;
  if (typeof data.detail === "string") {
    const d = data.detail;
    if (d === "Not Found" || d === "Not found") return fallback; // show HTTP status instead
    return d;
  }
  if (Array.isArray(data.detail)) {
    return data.detail.map(item => item.msg || JSON.stringify(item)).join("\n");
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
    setStatus("volunteerStatus", "Профиль волонтёра сохранён.");
  } catch (err) {
    setStatus("volunteerStatus", err.message || "Ошибка сохранения профиля");
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
}

async function fetchReviews() {
  try {
    const targetType = getValue("review_target_type");
    const targetId = getValue("review_target_id");

    if (!targetType || !targetId) {
      throw new Error("Укажи target_type и target_id.");
    }

    const { data } = await apiRequest(`/reviews?target_type=${encodeURIComponent(targetType)}&target_id=${encodeURIComponent(targetId)}`);
    renderReviewsList(data || []);
  } catch (err) {
    setStatus("reviewsStatus", err.message || "Ошибка загрузки отзывов");
    renderReviewsList([]);
  }
}

function renderReviewsList(reviews) {
  const list = document.getElementById("reviewsList");
  if (!list) return;

  if (!reviews.length) {
    list.innerHTML = '<div class="empty-small">Отзывов пока нет</div>';
    return;
  }

  list.innerHTML = reviews.map((review) => `
    <div class="review-card">
      <div class="review-card-head">
        <div class="review-rating">${"⭐".repeat(review.rating)}</div>
        <div class="review-date">${formatDateTime(review.created_at)}</div>
      </div>
      <div class="review-meta">Отзыв #${review.id} · reviewer_id: ${review.reviewer_id}</div>
      <div class="review-comment">${escapeHtml(review.comment || "Без комментария")}</div>
    </div>
  `).join("");
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
  const targetType = document.getElementById("complaint_target_type")?.value || "user";
  setValue("complaint_target_type", targetType);
  await loadReportReasons();
  renderComplaintsInfo();
}

async function loadReportReasons() {
  const select = document.getElementById("complaint_category");
  if (!select) return;

  const targetType = getValue("complaint_target_type") || "user";
  select.innerHTML = '<option value="other">Другое</option>';

  try {
    const { data } = await apiRequest(`/reports/reasons?target_type=${encodeURIComponent(targetType)}`);
    const reasons = data || [];
    if (reasons.length) {
      select.innerHTML = reasons
        .map((reason) => `<option value="${escapeHtml(reason.code)}">${escapeHtml(reason.title)}</option>`)
        .join("");
    }
  } catch (err) {
    console.warn("REPORT REASONS LOAD ERROR:", err);
  }
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


function truncateText(text, maxLength = 150) {
  if (!text) return "";
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

document.addEventListener('DOMContentLoaded', () => {
    try {
        if (typeof injectNotificationUI === "function") {
            injectNotificationUI();
        }
        if (typeof updateNotificationDot === "function") {
            updateNotificationDot();
        }
    } catch (err) {
        console.warn("Система уведомлений не смогла инициализироваться:", err);
    }
});

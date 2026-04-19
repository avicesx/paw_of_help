const API_URL = "http://127.0.0.1:8000";
const VOLUNTEER_PROFILE_KEY = "volunteerProfileDraft";

function parseErrorDetail(data, fallback) {
  if (!data) return fallback;
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail.map(item => item.msg || JSON.stringify(item)).join("\n");
  }
  return fallback;
}

async function register() {
  const name = document.getElementById("name").value.trim();
  const email = document.getElementById("email").value.trim();
  const phone = document.getElementById("phone").value.trim();
  const password = document.getElementById("password").value.trim();

  if (!name || !password) {
    alert("Нужно указать имя и пароль.");
    return;
  }

  if (!email && !phone) {
    alert("Укажи email или телефон.");
    return;
  }

  try {
    const res = await fetch(`${API_URL}/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name,
        email: email || null,
        phone: phone || null,
        password
      }),
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(parseErrorDetail(data, "Ошибка регистрации"));
    }

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
    const res = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        login: loginValue,
        password
      }),
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(parseErrorDetail(data, "Ошибка входа"));
    }

    localStorage.setItem("token", data.access_token);
    window.location.href = "profile.html";
  } catch (err) {
    alert(err.message || "Ошибка входа");
    console.error("LOGIN ERROR:", err);
  }
}

async function loadProfile() {
  const token = localStorage.getItem("token");

  if (!token) {
    window.location.href = "login.html";
    return;
  }

  try {
    const res = await fetch(`${API_URL}/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const user = await res.json();

    if (!res.ok) {
      throw new Error(parseErrorDetail(user, "Ошибка загрузки профиля"));
    }

    const usernameNode = document.getElementById("username");
    const contactLineNode = document.getElementById("contactLine");

    if (usernameNode) {
      usernameNode.textContent = [user.name, user.last_name].filter(Boolean).join(" ") || user.username || "Пользователь";
    }

    if (contactLineNode) {
      contactLineNode.textContent = user.phone || user.email || "Контакт не указан";
    }
  } catch (err) {
    alert(err.message || "Ошибка загрузки профиля");
    console.error("PROFILE ERROR:", err);
    localStorage.removeItem("token");
    window.location.href = "login.html";
  }
}

function loadVolunteerProfile() {
  const raw = localStorage.getItem(VOLUNTEER_PROFILE_KEY);
  if (!raw) return;

  try {
    const data = JSON.parse(raw);

    setValue("location", data.location);
    setValue("radius_km", data.radius_km);
    setValue("housing_type", data.housing_type);
    setValue("preferred_animal_types", Array.isArray(data.preferred_animal_types) ? data.preferred_animal_types.join(", ") : "");
    setValue("availability", JSON.stringify(data.availability || {}, null, 2));
    setChecked("ready_for_foster", !!data.ready_for_foster);
    setChecked("has_children", !!data.has_children);
    setValue("has_other_pets", JSON.stringify(data.has_other_pets || {}, null, 2));
    setValue("foster_restrictions", data.foster_restrictions || "");
  } catch (err) {
    console.error("VOLUNTEER PROFILE LOAD ERROR:", err);
  }
}

function saveVolunteerProfile(event) {
  if (event) event.preventDefault();

  const profile = {
    location: getValue("location"),
    radius_km: toNumberOrNull(getValue("radius_km")),
    housing_type: getValue("housing_type") || null,
    preferred_animal_types: splitCsv(getValue("preferred_animal_types")),
    availability: parseJsonOrFallback(getValue("availability"), {}),
    ready_for_foster: getChecked("ready_for_foster"),
    has_children: getChecked("has_children"),
    has_other_pets: parseJsonOrFallback(getValue("has_other_pets"), {}),
    foster_restrictions: getValue("foster_restrictions") || null,
    foster_photos: []
  };

  localStorage.setItem(VOLUNTEER_PROFILE_KEY, JSON.stringify(profile));

  const status = document.getElementById("saveStatus");
  if (status) {
    status.textContent = "Сохранено локально. Как только на бэке появятся эндпоинты профиля волонтёра, это можно будет отправлять на сервер.";
  }
}

function logout() {
  localStorage.removeItem("token");
  window.location.href = "login.html";
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

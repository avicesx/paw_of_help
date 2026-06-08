function adminToken() {
  return localStorage.getItem("token");
}

function adminRequireAuth() {
  if (!adminToken()) {
    window.location.href = "../pages/login.html";
    return false;
  }
  return true;
}

async function adminRequest(path, options = {}) {
  try {
    return await apiRequest(path, { ...options, auth: true });
  } catch (err) {
    const msg = err.message || "Ошибка";
    // 401 / просроченный токен -> редирект на логин
    if (err.status === 401 || msg.includes("токен") || msg.includes("Срок") || msg.includes("Недействительный") || msg.includes("авториз") || msg.includes("Нужен заголовок")) {
      setTimeout(() => window.location.href = "../pages/login.html", 800);
      throw new Error("Сессия истекла. Перенаправление на вход...");
    }
    if (err.status === 404 || msg === "Not Found" || msg === "Not found") {
      throw new Error(`Маршрут не найден (404): ${path}. Проверьте, запущен ли бекенд на порту 8000.`);
    }
    if (msg.includes("Failed to fetch") || msg.includes("NetworkError") || msg.includes("net::")) {
      throw new Error(`Нет связи с сервером (${path}). Убедитесь, что бекенд запущен (порт 8000).`);
    }
    throw err;
  }
}

function adminSetStatus(text, type = "") {
  const node = document.getElementById("adminStatus");
  if (!node) return;
  node.textContent = text || "";
  node.className = `admin-status ${type}`.trim();
}

function adminEscape(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function adminDate(value) {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return value;
  }
}

function adminQuery(params) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && String(value).trim() !== "") {
      search.set(key, value);
    }
  });
  const text = search.toString();
  return text ? `?${text}` : "";
}

function adminLogout() {
  localStorage.removeItem("token");
  window.location.href = "../pages/login.html";
}

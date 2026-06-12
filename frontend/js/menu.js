// Боковое меню приложения.
// Список пунктов един для всех страниц и соответствует дизайну (меню.svg):
// Профиль · Задачи · База знаний · Лента · Животные · Организации · Чаты · Мероприятия.
// Меню рисуется здесь, чтобы не дублировать разметку в каждой странице и не расходиться.
const SIDE_MENU_ITEMS = [
  { label: "Профиль", href: "profile.html" },
  { label: "Задачи", href: "tasks.html" },
  { label: "База знаний", href: "knowledge-base.html" },
  { label: "Лента", href: "feed.html" },
  { label: "Животные", href: "animal-select.html" },
  { label: "Организации", href: "org-catalog.html" },
  { label: "Чаты", href: "chats.html" },
  // «Мероприятия» и «Календарь» — один и тот же объединённый экран (calendar.html)
  { label: "Мероприятия", href: "calendar.html" },
];

function renderSideMenu() {
  const inner = document.querySelector("#sideMenu .side-menu-inner");
  if (!inner) return;
  const current = (window.location.pathname.split("/").pop() || "").toLowerCase();
  inner.innerHTML = SIDE_MENU_ITEMS.map((item) => {
    const active = item.href !== "#" && item.href.toLowerCase() === current ? " is-active" : "";
    return `<a href="${item.href}" class="side-link${active}">${item.label}</a>`;
  }).join("");
}

function toggleMenu() {
  const menu = document.getElementById("sideMenu");
  if (!menu) return;
  menu.classList.toggle("open");
}

// Колокольчик в топбаре ведёт на экран уведомлений (на всех страницах с топбаром),
// и подтягивает счётчик непрочитанных. Делается централизованно, чтобы не дублировать в каждой странице.
function wireTopbarBell() {
  const wrap = document.querySelector(".profile-icons .topbar-icon-wrap");
  if (wrap && !wrap.dataset.wired) {
    wrap.dataset.wired = "1";
    wrap.style.cursor = "pointer";
    wrap.addEventListener("click", () => { window.location.href = "notifications.html"; });
  }
  if (typeof loadNotificationsCount === "function") {
    try { loadNotificationsCount(); } catch (e) {}
  }
}

function initChrome() {
  renderSideMenu();
  wireTopbarBell();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initChrome);
} else {
  initChrome();
}

document.addEventListener("click", (event) => {
  const menu = document.getElementById("sideMenu");
  if (!menu) return;

  const isMenuButton = event.target.closest(".icon-btn");
  const isInsideMenu = event.target.closest(".side-menu");

  if (!isMenuButton && !isInsideMenu) {
    menu.classList.remove("open");
  }
});

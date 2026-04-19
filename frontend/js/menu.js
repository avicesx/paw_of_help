function toggleMenu() {
  const menu = document.getElementById("sideMenu");
  if (!menu) return;
  menu.classList.toggle("open");
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

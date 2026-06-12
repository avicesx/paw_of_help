const NOTIFICATION_HTML = `
  <div class="notification-container">
    <button class="notification-btn" type="button" onclick="toggleNotifications()" aria-label="Уведомления">
      <img src="../assets/topbar/notifications-inactive.svg" alt="Уведомления" class="topbar-icon layout-bell">
      <span class="notification-dot" id="notificationDot" style="display:none;"></span>
    </button>
    <div id="notificationsDropdown" class="notifications-dropdown hidden">
      <div class="notifications-header">
        <div class="notifications-title">Уведомления</div>
        <div class="header-actions">
           <button class="small-btn" onclick="markAllAsRead()">✓</button>
           <button class="small-btn" onclick="clearAllNotifications()">🗑</button>
        </div>
      </div>
      <div class="notifications-list" id="notificationsList"></div>
      <div class="notifications-footer">
        <a href="notifications.html">Все уведомления</a>
      </div>
    </div>
  </div>
`;

function injectNotificationUI() {
    const container = document.querySelector('.notification-container-wrapper');
    if (container) {
        container.innerHTML = NOTIFICATION_HTML;
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectNotificationUI);
} else {
    injectNotificationUI();
}
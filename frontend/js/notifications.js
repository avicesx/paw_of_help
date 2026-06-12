(function() {
    const originalApiRequest = window.apiRequest;
    if (typeof originalApiRequest === 'function') {
        window.apiRequest = async function(...args) {
            const options = args[1] || {};
            const method = (options.method || 'GET').toUpperCase();
            const pathname = window.location.pathname;
            const isFeedPage = pathname.includes('post_feed.html');
            const isAuthPage = pathname.includes('login.html') || pathname.includes('register.html');

            try {
                return await originalApiRequest(...args);
            } catch (err) {
                if (err.status === 401) {
                    localStorage.removeItem('token');
                    localStorage.removeItem('access_token');

                    if (isAuthPage) throw err;

                    if (isFeedPage && method === 'GET') throw err;

                    const isNested = pathname.includes('/chats/') || pathname.includes('/comments/');
                    window.location.href = isNested ? '../login.html' : 'login.html';
                }
                throw err;
            }
        };
    }
})();

async function getNotifications(isRead = null, limit = 50, offset = 0) {
    let url = `/notifications?limit=${limit}&offset=${offset}`;
    if (isRead !== null) url += `&is_read=${isRead}`;
    const response = await apiRequest(url, { auth: true });
    return response.data || [];
}

async function getUnreadCount() {
    try {
        const res = await apiRequest('/notifications/unread-count', { auth: true });
        return res.data.unread_count || 0;
    } catch { return 0; }
}

async function markAsRead(id) {
    await apiRequest(`/notifications/${id}/read`, { method: 'POST', auth: true });
    await refreshNotificationsUI();
}

async function markAllAsRead() {
    await apiRequest('/notifications/read-all', { method: 'POST', auth: true });
    await refreshNotificationsUI();
}

async function deleteNotification(id, element) {
    const item = document.getElementById(`notif-${id}`);
    if (item) item.remove(); 

    try {
        await apiRequest(`/notifications/${id}`, { method: 'DELETE', auth: true });
        
        updateNotificationDot();
    } catch (err) {
        console.error("Ошибка удаления:", err);
        if (err.status === 404) return;
        
        alert("Не удалось удалить уведомление");
        if (typeof loadNotifications === 'function') loadNotifications();
    }
}

async function clearAllNotifications() {
  if (!confirm('Удалить все уведомления?')) return;
  
  try {
      await apiRequest('/notifications', { method: 'DELETE', auth: true });
      
      updateNotificationDot();
      
      if (document.getElementById('notificationsDropdown').classList.contains('show')) {
          renderDropdownList();
      }
      
      if (typeof loadNotifications === 'function') {
          loadNotifications();
      }
  } catch (err) {
      console.error("Ошибка очистки:", err);
  }
}

async function refreshNotificationsUI() {
  updateNotificationDot();
  
  if (typeof loadNotifications === 'function') {
      await loadNotifications();
  }
  
  const dropdown = document.getElementById('notificationsDropdown');
  if (dropdown && dropdown.classList.contains('show')) {
      renderDropdownList();
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

document.addEventListener('DOMContentLoaded', () => {
    updateNotificationDot();
});
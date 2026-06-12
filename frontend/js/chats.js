function formatDateTime(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleString('ru-RU', { 
    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' 
  });
}

function getCurrentUserId() {
  const token = localStorage.getItem('token') || localStorage.getItem('access_token');
  if (!token) return null;
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.sub ? parseInt(payload.sub) : null;
  } catch (e) {
    return null;
  }
}

async function getAllChats() {
  try {
    const response = await apiRequest('/chats', { auth: true });
    const data = response.data;
    const chatsData = Array.isArray(data) ? data : (data.chats || data.items || []);

    return chatsData.map(chat => ({
      id: chat.id,
      name: chat.title || `Чат: ${chat.context_type} #${chat.context_id}`,
      lastMessage: chat.last_message?.content || 'Нажмите, чтобы открыть',
      time: chat.created_at ? formatDateTime(chat.created_at) : '',
      unread: chat.unread_count || 0,
      online: false
    }));
  } catch (err) {
    console.error('CHATS LOAD ERROR:', err);
    return [];
  }
}

async function loadChatList() {
    const container = document.getElementById('chatList') || document.querySelector('.chat-list');
    if (!container) return;

    container.innerHTML = '<div class="empty">Загрузка...</div>';

    const chats = await getAllChats();
    
    if (chats.length === 0) {
        container.innerHTML = '<div class="results-placeholder">У вас пока нет активных чатов.</div>';
        return;
    }

    container.innerHTML = chats.map(createChatCard).join('');

    // Глобальная индикация в заголовке списка
    const hasUnread = await hasUnreadMessages();
    const title = document.querySelector('.chat-screen .screen-title');
    if (title) {
        title.classList.toggle('has-unread-global', hasUnread);
    }
}

function openChat(chatId) {
    if (!chatId) {
        console.error("Попытка открыть чат без ID");
        return;
    }
    window.location.href = `chats/index.html?id=${chatId}`;
}

async function hasUnreadMessages() {
    try {
        const { data } = await apiRequest('/chats/has-unread', { auth: true });
        return data.has_unread;
    } catch (err) {
        console.error('UNREAD CHECK ERROR:', err);
        return false;
    }
}

async function openTaskChat(taskId) {
    try {
        const { data } = await apiRequest('/chats/open', {
            method: 'POST',
            auth: true,
            body: JSON.stringify({
                context_type: 'task',
                context_id: taskId
            })
        });
        openChat(data.id);
    } catch (err) {
        console.error('OPEN CHAT ERROR:', err);
        alert("Не удалось открыть чат: " + err.message);
    }
}

async function getChatData(chatId) {
  try {
    const { data } = await apiRequest(`/chats/${chatId}`, { auth: true });
    if (data) {
        return {
            id: data.id,
            name: data.title || `Чат ${data.context_type} #${data.context_id}`
        };
    }
    return null;
  } catch (err) {
    console.error('CHAT DATA LOAD ERROR:', err);
    return null;
  }
}

async function getChatMessages(chatId) {
  try {
    const response = await apiRequest(`/chats/${chatId}/messages`, { auth: true });
    const messagesData = Array.isArray(response.data) ? response.data : [];
    
    const currentUserId = getCurrentUserId(); 
    
    return messagesData.map(msg => ({
      id: msg.id,
      type: (currentUserId && String(msg.sender_id) === String(currentUserId)) ? 'sent' : 'received',
      text: msg.content,
      time: formatDateTime(msg.created_at)
    }));
  } catch (err) {
    console.error('MESSAGES LOAD ERROR:', err);
    return [];
  }
}

async function sendMessage(chatId, text) {
    return await apiRequest(`/chats/${chatId}/messages`, {
        method: 'POST',
        auth: true,
        body: JSON.stringify({
            content: text,
            message_type: 'text'
        })
    }).then(res => res.data);
}

async function sendMessageFromInput() {
    const input = document.getElementById('messageInput');
    const text = input.value.trim();
    if (!text) return;

    const urlParams = new URLSearchParams(window.location.search);
    const chatId = urlParams.get('id');
    
    try {
        input.disabled = true;
        await sendMessage(chatId, text);
        input.value = ''; 
        input.disabled = false;
        input.focus();

        const messages = await getChatMessages(chatId);
        const list = document.getElementById('messagesList');
        list.innerHTML = messages.map(createMessageBubble).join('');
        list.scrollTop = list.scrollHeight;
    } catch (err) {
        console.error("Ошибка при отправке:", err);
        input.disabled = false;
    }
}

async function markChatAsRead(chatId) {
    try {
        await apiRequest(`/chats/${chatId}/read`, {
            method: 'POST',
            auth: true,
        });
        console.log(`Chat ${chatId} marked as read`);
    } catch (err) {
        if (err instanceof SyntaxError || (err.message && err.message.includes('JSON'))) {
            console.log(`Chat ${chatId} marked as read (empty response)`);
        } else {
            console.error('MARK READ ERROR:', err);
        }
    }
}

async function manualMarkAsRead() {
    const urlParams = new URLSearchParams(window.location.search);
    const chatId = urlParams.get('id');
    if (!chatId) return;

    try {
        await markChatAsRead(chatId);
        const btn = document.querySelector('.mark-read-btn');
        if (btn) btn.classList.add('success');
    } catch (err) { console.error(err); }
}

// TODO: Реализовать логику для acceptVolunteer и declineVolunteer
// Эти функции должны взаимодействовать с бэкендом для изменения статуса заявки/отклика
// и затем обновлять UI чата (скрывать acceptNotification).
function acceptVolunteer() {
    alert('Принять волонтера (логика будет реализована)');
    // Здесь должна быть логика отправки запроса на бэкенд (например, PATCH /task_responses/{id})
    // document.getElementById('acceptNotification').classList.add('hidden');
}

function declineVolunteer() {
    alert('Отказаться от волонтера (логика будет реализована)');
    // Здесь должна быть логика отправки запроса на бэкенд
    // document.getElementById('acceptNotification').classList.add('hidden');
}

function createChatCard(chat) {
  return `
    <div class="chat-card ${chat.unread > 0 ? 'unread' : ''}" onclick="openChat(${chat.id})">
      <div class="chat-avatar">💬</div>
      <div class="chat-info">
        <div class="chat-name">${chat.name}</div>
        <div class="chat-message">${chat.lastMessage}</div>
      </div>
      <div class="chat-meta">
        <div class="chat-time">${chat.time}</div>
        ${chat.unread > 0 ? `<div class="unread-badge">${chat.unread}</div>` : ''}
        ${chat.online ? '<div class="online-indicator"></div>' : ''}
      </div>
    </div>
  `;
}

function setupChatEventListeners() {
    const input = document.getElementById('messageInput');
    if (input && !input.dataset.listenerAdded) {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendMessageFromInput();
            }
        });
        input.dataset.listenerAdded = 'true';
    }
}

function createMessageBubble(msg) {
    const bubbleClass = msg.type === 'sent' ? 'message-bubble sent' : 'message-bubble received';
    
    return `
      <div class="${bubbleClass}">
        <div class="message-text">${msg.text}</div>
        <div class="message-time">${msg.time}</div>
      </div>
    `;
}

let chatRefreshInterval = null;
let isChatInitializing = false;

async function initChat() {
    const urlParams = new URLSearchParams(window.location.search);
    const chatId = urlParams.get('id');
    if (!chatId) {
        console.error("ID чата не найден в URL!");
        return;
    }

    if (isChatInitializing) return;
    isChatInitializing = true;

    try {
        await markChatAsRead(chatId).catch(err => console.warn("Пропуск пометки прочтения:", err));
    } catch (e) {
        console.warn("Бэкенд не смог пометить чат прочитанным (ошибка 500), но мы загружаем сообщения...");
    }

    const chatData = await getChatData(chatId);
    if (!chatData) {
        document.getElementById('messagesList').innerHTML = 
            '<div class="empty">Чат не найден. Проверь данные в БД (ID чата: ' + chatId + ')</div>';
        return;
    }

    if (document.querySelector('.chat-title')) {
        document.querySelector('.chat-title').innerText = chatData.name;
    }
    
    // TODO: Здесь должна быть логика для отображения acceptNotification
    // Например, если chatData содержит информацию о pending-заявке волонтера
    // document.getElementById('acceptNotification').classList.remove('hidden');

    let messages = [];
    try {
        messages = await getChatMessages(chatId);
    } catch (err) {
        console.error("Критическая ошибка при загрузке сообщений:", err);
        document.getElementById('messagesList').innerHTML = '<div class="empty">Не удалось загрузить сообщения. Возможно, бэкенд упал.</div>';
        return;
    }

    const list = document.getElementById('messagesList');
    
    if (messages.length === 0) {
        list.innerHTML = '<div class="empty">Здесь пока нет сообщений. Начни общение!</div>';
    } else {
        list.innerHTML = messages.map(createMessageBubble).join('');
        list.scrollTop = list.scrollHeight;
    }

    setupChatEventListeners();

    if (chatRefreshInterval) clearInterval(chatRefreshInterval);
    chatRefreshInterval = setInterval(async () => {
        const newMessages = await getChatMessages(chatId);
        await markChatAsRead(chatId).catch(() => {});

        const list = document.getElementById('messagesList');
        if (list) {
            const isAtBottom = list.scrollTop + list.clientHeight >= list.scrollHeight - 50;
            
            list.innerHTML = newMessages.map(createMessageBubble).join('');
            
            if (isAtBottom) {
                list.scrollTop = list.scrollHeight;
            }
        }
    }, 5000);
    
    isChatInitializing = false;
}

document.addEventListener('DOMContentLoaded', () => {
    window.addEventListener('beforeunload', () => {
        if (chatRefreshInterval) clearInterval(chatRefreshInterval);
    });

    if (document.getElementById('chatList') || document.querySelector('.chat-list')) {
        loadChatList();
    }
    if (document.getElementById('messagesList')) {
        initChat();
    }
});
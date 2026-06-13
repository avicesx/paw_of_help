function truncateText(text, limit = 150) {
  if (!text || text.length <= limit) return text;
  return text.substring(0, limit) + "...";
}

function getPlural(n, one, two, five) {
  let n10 = n % 10;
  if (n % 100 > 10 && n % 100 < 20) return five;
  if (n10 > 1 && n10 < 5) return two;
  if (n10 === 1) return one;
  return five;
}

function getRelativeTime(dateStr) {
  if (!dateStr) return null;
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now - date;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);

  if (diffSec < 60) return 'только что';
  if (diffMin < 60) return `${diffMin} ${getPlural(diffMin, 'минуту', 'минуты', 'минут')} назад`;
  if (diffHour < 24) return `${diffHour} ${getPlural(diffHour, 'час', 'часа', 'часов')} назад`;
  return null;
}

function formatEventDate(baseTime, updateTime) {
  if (!baseTime) return 'На модерации';
  const baseDate = new Date(baseTime);
  const updateDate = updateTime ? new Date(updateTime) : null;
  const isEdited = updateDate && (updateDate.getTime() - baseDate.getTime() > 60000);
  
  const dateToUse = isEdited ? updateDate : baseDate;
  const relative = getRelativeTime(dateToUse);
  const fullDate = dateToUse.toLocaleString('ru-RU', { 
    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' 
  });

  const display = relative || fullDate;
  return isEdited ? `изменено ${display}` : display;
}

function getCurrentUserId() {
  const token = localStorage.getItem('token') || localStorage.getItem('access_token');
  if (!token) return null;
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return parseInt(payload.sub); 
  } catch (e) {
    console.error("Ошибка при чтении ID из токена", e);
    return null;
  }
}

async function loadPosts() {
    try {
        const { data } = await apiRequest('/posts');
        return data;
    } catch (err) {
        console.error('LOAD POSTS ERROR:', err);
        return [];
    }
}

function renderPostCard(post, canManageOverride = false, showFullText = false) {
  const currentUserId = getCurrentUserId();
  
  const authorId = post.author_user_id || post.user_id ? parseInt(post.author_user_id || post.user_id) : null;
  const isCreator = currentUserId && authorId === currentUserId;

  const canManage = isCreator || canManageOverride;
  const isNotMyPost = currentUserId && !isCreator;
  
  let displayName = 'Пользователь';
  if (post.organization_id) {
      displayName = post.organization_name || 'Организация';
  } else {
      displayName = post.author_username || post.author_name || (post.author?.username) || (post.author?.full_name);
      if (!displayName && isCreator) displayName = 'Вы (автор)';
  }
  
  const displayIcon = post.organization_icon_url 
    ? `<img src="${post.organization_icon_url}" class="post-org-img">` 
    : (post.author_avatar ? `<img src="${post.author_avatar}" class="post-org-img">` : '👤');

  const likes = post.likes_count ?? post.likes ?? 0;
  const comments = post.comments_count ?? post.comments ?? 0;
  
  const myVote = post.my_vote != null ? parseInt(post.my_vote) : 0;

  return `
    <div class="post-card" id="post-${post.id}">
      <div class="post-header">
        <div class="post-org-icon">${displayIcon}</div>
        <div class="post-org-info">
          <div class="post-org-name">${displayName}</div>
          <div class="post-time" style="font-size: 11px; color: var(--muted);">${formatEventDate(post.published_at, post.updated_at)}</div>
        </div>
        
        <div class="org-menu-container" style="margin-left: auto;">
          <button class="org-kebab-btn" onclick="togglePostMenu(event, ${post.id})">⋮</button>
          <div id="postMenu-${post.id}" class="org-dropdown hidden">
            ${canManage ? `
              <button class="org-dropdown-item" onclick="handleEditPost(${post.id})">✏️ Редактировать</button>
              <button class="org-dropdown-item delete-btn" onclick="handleDeletePost(${post.id})">🗑️ Удалить</button>
            ` : ''}
            ${isNotMyPost ? `
              <button class="org-dropdown-item" onclick="handleReportPost(${post.id})">🚩 Пожаловаться</button>
            ` : ''}
          </div>
        </div>
      </div>
      
      <div class="post-body" ${!showFullText ? `onclick="openComments(${post.id})" style="cursor:pointer"` : ''}>
        ${post.title ? `<h3 class="post-title">${escapeHtml(post.title)}</h3>` : ''}
        ${post.attachments && post.attachments.length ? `<img src="${post.attachments[0]}" class="post-image" style="width: 100%; border-radius: 8px; margin-bottom: 10px;" onerror="this.style.display='none'">` : ''}
        <p class="post-text">${showFullText ? escapeHtml(post.content) : truncateText(post.content)}</p>
      </div>

      <div class="post-stats">
        <div class="post-stat ${myVote === 1 ? 'active' : ''}" onclick="votePost(${post.id}, 1)">
          <img src="../assets/reactions/${myVote === 1 ? 'like-active.svg' : 'like-inactive.svg'}" class="article-stat-icon" alt="Лайк">
          <span class="stat-count">${likes}</span>
        </div>
        <div class="post-stat" ${!showFullText ? `onclick="openComments(${post.id})" style="cursor:pointer"` : ''}>
          <img src="../assets/reactions/comment-icon.svg" class="article-stat-icon" alt="Комментарии">
          <span class="stat-count">${comments}</span>
        </div>
      </div>
    </div>
  `;
}

function togglePostMenu(event, postId) {
    event.stopPropagation();

    if (window.location.pathname.includes('post_feed.html') && !getToken()) {
        window.location.href = 'login.html';
        return;
    }

    const menu = document.getElementById(`postMenu-${postId}`);
    document.querySelectorAll('.org-dropdown').forEach(m => {
        if (m !== menu) m.classList.add('hidden');
    });
    if (menu) menu.classList.toggle('hidden');
}

function openComments(postId) {
    window.location.href = `comments/index.html?id=${postId}`;
}

async function votePost(postId, vote) {
    if (window.location.pathname.includes('post_feed.html') && !getToken()) {
        window.location.href = 'login.html';
        return;
    }

    const currentPost = document.getElementById(`post-${postId}`);
    const isAlreadyActive = currentPost.querySelector('.post-stat.active');
    const voteToSend = isAlreadyActive ? 0 : vote;

    try {
        await apiRequest(`/posts/${postId}/vote`, {
            method: 'POST',
            auth: true,
            body: JSON.stringify({ vote: voteToSend })
        });
        if (typeof loadFeed === 'function') loadFeed();
        else if (typeof renderOrgPosts === 'function') renderOrgPosts();
    } catch (err) {
        alert("Не удалось проголосовать: " + err.message);
    }
}

async function handleDeletePost(postId) {
    if (!confirm("Удалить этот пост?")) return;
    try {
        await apiRequest(`/posts/${postId}`, {
            method: 'DELETE',
            auth: true
        });
        if (typeof loadFeed === 'function') loadFeed();
        else if (typeof renderOrgPosts === 'function') renderOrgPosts();
    } catch (err) {
        alert("Ошибка при удалении: " + err.message);
    }
}

async function handleEditPost(postId) {
    window.location.href = `edit_post.html?id=${postId}`;
}

async function handleReportPost(postId) {
    alert("Жалоба на пост #" + postId + " отправлена модераторам.");
}

async function createPost(postData) {
    return await apiRequest('/posts', {
        method: 'POST',
        auth: true,
        body: JSON.stringify(postData)
    });
}

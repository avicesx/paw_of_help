function getPostIdFromUrl() {
  const urlParams = new URLSearchParams(window.location.search);
  const postId = urlParams.get('id');
  return postId ? parseInt(postId) : null;
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
  if (!baseTime && !updateTime) return 'Только что';
  
  const baseDate = baseTime ? new Date(String(baseTime).replace(' ', 'T')) : null;
  const updateDate = updateTime ? new Date(String(updateTime).replace(' ', 'T')) : null;
  
  const isBaseValid = baseDate && !isNaN(baseDate.getTime());
  const isUpdateValid = updateDate && !isNaN(updateDate.getTime());

  if (!isBaseValid && !isUpdateValid) return 'Дата не указана';

  const isEdited = isBaseValid && isUpdateValid && (updateDate.getTime() - baseDate.getTime() > 60000);
  const dateToUse = (isEdited || !isBaseValid) ? updateDate : baseDate;

  const relative = getRelativeTime(dateToUse);
  const fullDate = dateToUse.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  
  const display = relative || fullDate;
  return (isEdited && isBaseValid) ? `изменено ${display}` : display;
}

async function getPostData(postId) {
  try {
    const { data } = await apiRequest(`/posts/${postId}`, { auth: true });
    return data;
  } catch (err) {
    console.error('Ошибка загрузки поста:', err);
    return null;
  }
}

async function loadCommentsFromAPI(postId) {
  try {
    const { data } = await apiRequest(`/comments/post/${postId}`, { auth: true });
    return data.map(c => ({
      id: c.id,
      text: c.content,
      likes: c.likes || 0,
      dislikes: c.dislikes || 0,
      my_vote: (c.my_vote === null || c.my_vote === undefined) ? 0 : c.my_vote,
      user_id: c.user_id,
      created_at: c.created_at,
      updated_at: c.updated_at,
      is_deleted: c.is_deleted || false
    }));
  } catch (err) {
    console.error('Ошибка загрузки комментариев:', err);
    return [];
  }
}

let currentPostId = null;
let allComments = [];
let currentUserCache = null;
let currentReplyId = null;

async function initCommentsPage(postId) {
  currentPostId = postId;
  
  if (!currentUserCache) {
    try {
      const meRes = await apiRequest('/users/me', { auth: true });
      currentUserCache = meRes.data;
    } catch (e) {
      console.warn("Не удалось загрузить профиль текущего пользователя");
    }
  }

  let [post, comments] = await Promise.all([
    getPostData(postId),
    loadCommentsFromAPI(postId)
  ]);

  if (post) {
    if (!post.author_username && !post.organization_name && !post.organization_id) {
      try {
        const { data: feedPosts } = await apiRequest('/posts', { auth: true });
        const enriched = feedPosts.find(p => p.id === post.id || (p.organization_id && p.organization_id === post.organization_id));
        if (enriched) {
          post = { ...post, ...enriched };
        }
      } catch (e) {
        console.error("Ошибка при попытке обогатить данные поста из ленты:", e);
      }
    }

    const postAuthorId = post.author_user_id || post.user_id;
    if (!post.organization_id && currentUserCache && 
        postAuthorId == currentUserCache.id && 
        !post.author_username) {
      post.author_username = currentUserCache.username;
    }

    let postHtml = renderPostCard(post, false, true);
    
    postHtml = postHtml.replaceAll('../assets/', '../../assets/');
    
    document.getElementById('postCard').innerHTML = postHtml;
  }
  
  allComments = comments;
  renderComments(allComments);
}

async function deleteComment(commentId) {
    if (!confirm("Удалить комментарий?")) return;
    await apiRequest(`/comments/${commentId}`, { method: 'DELETE', auth: true });
    initCommentsPage(currentPostId);
}

async function startEditComment(commentId) {
    const comment = allComments.find(c => c.id === commentId);
    if (!comment) return;

    const card = document.querySelector(`.comment-card[data-id="${commentId}"]`);
    const textP = card.querySelector('.comment-text');
    const currentText = comment.text;

    textP.innerHTML = `
        <textarea class="field" id="edit-input-${commentId}" style="width: 100%; min-height: 60px; margin-bottom: 8px;">${currentText}</textarea>
        <div style="display:flex; gap: 8px;">
            <button class="task-primary-btn" style="padding: 4px 12px; font-size: 12px;" onclick="saveCommentEdit(${commentId})">Сохранить</button>
            <button class="task-outline-btn" style="padding: 4px 12px; font-size: 12px;" onclick="renderComments(allComments)">Отмена</button>
        </div>
    `;
}

async function saveCommentEdit(commentId) {
    const newText = document.getElementById(`edit-input-${commentId}`).value.trim();
    if (!newText) return;

    await apiRequest(`/comments/${commentId}`, {
        method: 'PATCH',
        auth: true,
        body: JSON.stringify({ content: newText })
    });
    initCommentsPage(currentPostId);
}

function replyToComment(id, username) {
    currentReplyId = id;
    const preview = document.getElementById('replyPreview');
    const text = document.getElementById('replyText');
    if (preview && text) {
        text.textContent = `Ответ пользователю ${username}`;
        preview.classList.remove('hidden');
    }
    document.getElementById('commentInput').focus();
}

function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

function cancelReply() {
    currentReplyId = null;
    document.getElementById('replyPreview')?.classList.add('hidden');
}

async function sendComment() {
  const input = document.getElementById('commentInput');
  const content = input.value.trim();
  if (!content) return;

  const bodyData = { 
    content: content, 
    parent_id: currentReplyId, 
    organization_id: null
  };

  await apiRequest(`/comments/post/${currentPostId}`, {
    method: 'POST',
    auth: true,
    body: JSON.stringify(bodyData)
  });
  
  input.value = '';
  input.style.height = 'auto';
  cancelReply();
  allComments = await loadCommentsFromAPI(currentPostId);
  renderComments(allComments);
}

function getReactionHTML(c) {
  return `
    <span class="comment-action" data-type="like" data-id="${c.id}" style="display: flex; align-items: center; gap: 4px;">
      <img src="../../assets/reactions/${c.my_vote === 1 ? 'like-active.svg' : 'like-inactive.svg'}" class="article-stat-icon" alt="Лайк"> <span class="stat-count">${c.likes || 0}</span>
    </span>
    <span class="comment-action" data-type="dislike" data-id="${c.id}" style="display: flex; align-items: center; gap: 4px;">
      <img src="../../assets/reactions/${c.my_vote === -1 ? 'dislike-active.svg' : 'dislike-inactive.svg'}" class="article-stat-icon" alt="Дизлайк"> <span class="stat-count">${c.dislikes || 0}</span>
    </span>
  `;
}

function renderComments(comments) {
  const list = document.getElementById('commentsList');
  document.getElementById('commentsTitle').textContent = `Комментарии ${comments.length}`;
  
  const postCommentCount = document.querySelector('#postCard .post-stat:last-child .stat-count');
  if (postCommentCount) {
      postCommentCount.textContent = comments.length;
  }

  const me = getCurrentUserId();

  const roots = [];
  const childrenMap = {};

  comments.forEach(c => {
    if (c.parent_id) {
      if (!childrenMap[c.parent_id]) childrenMap[c.parent_id] = [];
      childrenMap[c.parent_id].push(c);
    } else {
      roots.push(c);
    }
  });

  function buildHTML(nodes, depth = 0) {
    return nodes
      .filter(c => !c.is_deleted)
      .map(c => {
      const isAuthor = currentUserCache && c.user_id === currentUserCache.id;
      const authorName = isAuthor ? (currentUserCache.username || 'Вы') : `Пользователь #${c.user_id}`;
      
      const indent = depth * 25;
      const borderStyle = depth > 0 
        ? `border-left: 3px solid var(--brown); margin-left: ${indent}px; background: #fffdfd;` 
        : '';

      return `
        <div class="comment-card" style="${borderStyle}" data-id="${c.id}">
          <div class="comment-header">
            <div class="comment-info">
              <div class="comment-name" style="font-size: 13px; font-weight: 700; color: var(--brown);">${authorName}</div>
              <div class="comment-time" style="font-size: 11px; color: var(--muted);">${formatEventDate(c.created_at, c.updated_at)}</div>
            </div>
            <div class="org-menu-container">
               <button class="org-menu-btn" onclick="toggleCommentMenu(event, ${c.id})">⋮</button>
               <div id="commentMenu-${c.id}" class="org-dropdown hidden">
                  ${renderCommentActions(c)}
               </div>
            </div>
          </div>
          <p class="comment-text" style="margin: 8px 0; font-size: 14px; line-height: 1.4;">${escapeHtml(c.text)}</p>
          <div class="comment-actions">
            ${getReactionHTML(c)}
          </div>
          <div class="comment-footer-links">
            <button class="comment-link-btn" onclick="replyToComment(${c.id}, '${authorName}')">Ответить</button>
            ${!isAuthor ? `<button class="comment-link-btn" onclick="reportComment(${c.id})">Пожаловаться</button>` : ''}
          </div>
        </div>
        ${childrenMap[c.id] ? buildHTML(childrenMap[c.id], depth + 1) : ''}
      `;
    }).join('');
  }
  
  list.innerHTML = buildHTML(roots);
}

function renderCommentActions(c) {
    const me = getCurrentUserId();
    if (c.user_id === me) {
        return `
            <button class="org-dropdown-item" onclick="startEditComment(${c.id})">✏️ Изменить</button>
            <button class="org-dropdown-item delete-btn" onclick="deleteComment(${c.id})">🗑️ Удалить</button>
        `;
    }
    return `<button class="org-dropdown-item" onclick="reportComment(${c.id})">🚩 Пожаловаться</button>`;
}

function toggleCommentMenu(event, id) {
    event.stopPropagation();
    const menu = document.getElementById(`commentMenu-${id}`);
    document.querySelectorAll('.org-dropdown').forEach(m => { if(m !== menu) m.classList.add('hidden'); });
    if (menu) menu.classList.toggle('hidden');
}

async function reportComment(id) {
    if (!confirm("Пожаловаться на комментарий?")) return;
    try {
        await apiRequest('/reports/', {
            method: 'POST',
            auth: true,
            body: JSON.stringify({
                target_type: 'comment',
                target_id: id,
                reason_code: 'spam',
                description: 'Жалоба из ленты комментариев'
            })
        });
        alert("Жалоба отправлена модераторам");
    } catch (e) { alert(e.message); }
}

window.loadFeed = () => {
    if (currentPostId) initCommentsPage(currentPostId);
};

function updateCommentUI(comment) {
  const commentElement = document.querySelector(`.comment-card[data-id="${comment.id}"]`);
  if (!commentElement) return;
  
  commentElement.querySelector('.comment-actions').innerHTML = getReactionHTML(comment);
}

document.getElementById('commentsList').addEventListener('click', async function(e) {
  const target = e.target.closest('[data-type]');
  if (!target) return;

  const id = parseInt(target.dataset.id);
  const type = target.dataset.type;
  const comment = allComments.find(c => c.id === id);
  if (!comment) return;

  let voteToSend = 0;
  if (type === 'like') {
    voteToSend = (comment.my_vote === 1) ? 0 : 1;
  } else {
    voteToSend = (comment.my_vote === -1) ? 0 : -1;
  }

  try {
    const response = await apiRequest(`/comments/${id}/react`, {
      method: 'POST',
      auth: true,
      body: JSON.stringify({ vote: voteToSend })
    });

    const res = response.data || response;

    comment.likes = (res.likes !== undefined) ? res.likes : comment.likes;
    comment.dislikes = (res.dislikes !== undefined) ? res.dislikes : comment.dislikes;
    
    comment.my_vote = (res.my_vote !== null && res.my_vote !== undefined) ? res.my_vote : 0;

    updateCommentUI(comment);

  } catch (err) {
    console.error("Ошибка при отправке реакции:", err);
  }
});
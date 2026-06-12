// «Лента» — социальная лента публикаций (дизайн: Лента.svg) + создание поста (Создание поста организации.svg).
// Чтение — публичный GET /posts. Создание — POST /posts. Задачи живут на отдельном экране «Задачи».

function postMediaUrl(u) {
  if (!u) return "";
  return /^https?:/i.test(u) ? u : `${API_URL}${u.startsWith("/") ? "" : "/"}${u}`;
}

function firstPostImage(attachments) {
  if (!Array.isArray(attachments)) return null;
  for (const item of attachments) {
    if (typeof item === "string") {
      if (item) return item;
    } else if (item && typeof item === "object") {
      const u = item.url || item.src || item.path || item.image || item.image_url;
      if (u) return u;
    }
  }
  return null;
}

async function loadPostsFeed() {
  const list = document.getElementById("postsFeed");
  if (!list) return;
  list.innerHTML = '<div class="empty-small">Загрузка ленты...</div>';

  try {
    const { data } = await apiRequest("/posts", getToken() ? { auth: true } : {});
    renderPostsFeed(data || []);
  } catch (err) {
    list.innerHTML = `<div class="empty-small">${escapeHtml(err.message || "Не удалось загрузить ленту")}</div>`;
  }
}

function renderPostsFeed(posts) {
  const list = document.getElementById("postsFeed");
  if (!list) return;

  if (!posts.length) {
    list.innerHTML = '<div class="empty-small">Пока нет публикаций</div>';
    return;
  }

  list.innerHTML = posts
    .map((p) => {
      const author = p.organization_name || "Публикация пользователя";
      const icon = postMediaUrl(p.organization_icon_url);
      const image = postMediaUrl(firstPostImage(p.attachments));
      // В дизайне у карточки один блок текста (подпись); content приоритетнее заголовка.
      const caption = p.content || p.title || "";
      const liked = p.my_vote === 1;

      return `
      <article class="post-card">
        <div class="post-head">
          <div class="post-avatar">${icon ? `<img src="${escapeHtml(icon)}" alt="">` : ""}</div>
          <div class="post-author">${escapeHtml(author)}</div>
        </div>
        ${image
          ? `<div class="post-photo"><img src="${escapeHtml(image)}" alt=""></div>`
          : `<div class="post-photo post-photo--empty">Фото</div>`}
        <div class="post-text">
          ${caption ? `<div class="post-caption">${escapeHtml(caption)}</div>` : ""}
        </div>
        <div class="post-stats">
          <button type="button" class="post-stat post-like${liked ? " liked" : ""}" onclick="togglePostLike(${p.id}, this)">
            <span class="post-ic">&#9829;</span><span data-likes>${p.likes_count || 0}</span>
          </button>
          <span class="post-stat"><span class="post-ic">&#128172;</span><span>0</span></span>
          <span class="post-stat"><span class="post-ic">&#128065;</span><span>0</span></span>
        </div>
      </article>
    `;
    })
    .join("");
}

async function togglePostLike(postId, btn) {
  if (!getToken()) {
    window.location.href = "login.html";
    return;
  }
  const liked = btn.classList.contains("liked");
  try {
    const { data } = await apiRequest(`/posts/${postId}/vote`, {
      method: "POST",
      auth: true,
      body: JSON.stringify({ vote: liked ? 0 : 1 }),
    });
    btn.classList.toggle("liked", data.my_vote === 1);
    const cnt = btn.querySelector("[data-likes]");
    if (cnt) cnt.textContent = data.likes_count || 0;
  } catch (err) {
    alert(err.message || "Не удалось поставить отметку");
  }
}

// ----- Создание поста (post-create.html) -----
let _postAttachmentUrl = null;

async function attachPostPhoto(input) {
  const file = input.files && input.files[0];
  if (!file) return;
  const statusEl = document.getElementById("postStatus");
  if (!getToken()) { window.location.href = "login.html"; return; }
  try {
    if (statusEl) statusEl.textContent = "Загружаем фото...";
    const fd = new FormData();
    fd.append("file", file);
    const { data } = await apiRequest("/uploads", { method: "POST", auth: true, body: fd });
    _postAttachmentUrl = data.url;
    const thumb = document.getElementById("postPhotoThumb");
    if (thumb) { thumb.src = postMediaUrl(data.url); thumb.style.display = "block"; }
    if (statusEl) statusEl.textContent = "Фото прикреплено";
  } catch (err) {
    if (statusEl) statusEl.textContent = err.message || "Не удалось загрузить фото";
  }
}

async function createPost() {
  const textEl = document.getElementById("postText");
  const statusEl = document.getElementById("postStatus");
  const text = (textEl?.value || "").trim();
  if (!text) { if (statusEl) statusEl.textContent = "Напишите текст поста"; return; }
  if (!getToken()) { window.location.href = "login.html"; return; }

  // title обязателен на бэке — берём первую строку (до 80 символов), весь текст идёт в content.
  const firstLine = (text.split("\n")[0] || text).trim();
  const title = firstLine.slice(0, 80) || "Пост";
  const orgId = new URLSearchParams(location.search).get("org_id");
  const body = {
    title,
    content: text,
    attachments: _postAttachmentUrl ? [_postAttachmentUrl] : [],
  };
  if (orgId) body.organization_id = Number(orgId);

  try {
    if (statusEl) statusEl.textContent = "Публикуем...";
    await apiRequest("/posts", { method: "POST", auth: true, body: JSON.stringify(body) });
    if (statusEl) statusEl.textContent = "Опубликовано!";
    // даём фоновой модерации опубликовать пост, затем возвращаемся туда, откуда пришли
    setTimeout(() => { window.location.href = orgId ? `org.html?id=${orgId}` : "feed.html"; }, 1000);
  } catch (err) {
    if (statusEl) statusEl.textContent = err.message || "Не удалось опубликовать";
  }
}

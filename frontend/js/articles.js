function escapeHtml(text) {
  if (!text) return "";
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return String(text).replace(/[&<>"']/g, m => map[m]);
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
  if (!baseTime && !updateTime) return 'На модерации';
  
  const baseDate = baseTime ? new Date(String(baseTime).replace(' ', 'T')) : null;
  const updateDate = updateTime ? new Date(String(updateTime).replace(' ', 'T')) : null;
  
  const isBaseValid = baseDate && !isNaN(baseDate.getTime());
  const isUpdateValid = updateDate && !isNaN(updateDate.getTime());

  if (!isBaseValid && !isUpdateValid) return 'Дата не указана';

  const isEdited = isBaseValid && isUpdateValid && (updateDate.getTime() - baseDate.getTime() > 60000);
  
  const dateToUse = (isEdited || !isBaseValid) ? updateDate : baseDate;

  const relative = getRelativeTime(dateToUse);
  const fullDate = dateToUse.toLocaleString('ru-RU', { 
    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' 
  });
  
  const display = relative || fullDate;
  return (isEdited && isBaseValid) ? `изменено ${display}` : display;
}

function getCurrentUserId() {
  const token = localStorage.getItem('token') || localStorage.getItem('access_token');
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.sub ? parseInt(payload.sub) : null;
  } catch (e) { return null; }
}


async function fetchArticleDetail(articleId) {
  try {
    const response = await apiRequest(`/knowledge-base/articles/${articleId}`, { auth: true });
    return response.data;
  } catch (err) {
    console.error('Ошибка загрузки деталей статьи:', err);
    return null;
  }
}

async function loadArticleDetail(articleId) {
  const container = document.getElementById('articleDetailContainer');
  if (!container) return;

  try {
    const article = await fetchArticleDetail(articleId);
    if (!article) {
      container.innerHTML = '<div class="results-placeholder">Статья не найдена.</div>';
      return;
    }

    container.innerHTML = renderFullArticle(article);
  } catch (err) {
    console.error('ARTICLE DETAIL LOAD ERROR:', err);
    container.innerHTML = '<div class="results-placeholder">Ошибка загрузки статьи.</div>';
  }
}

function renderFullArticle(article) {
  const currentUserId = getCurrentUserId();
  const isAuthor = currentUserId && article.author_id === currentUserId;
  const isNotAuthor = currentUserId && article.author_id !== currentUserId;

  const myVote = article.my_vote != null ? parseInt(article.my_vote) : 
                 (article.liked_by_user === true ? 1 : 
                 (article.liked_by_user === false ? 0 : 0));

  const isLiked = myVote === 1;
  const isDisliked = myVote === -1;

  const tagsDisplay = article.tags && article.tags.length 
    ? article.tags.map(tagObj => {
        let tagName = (typeof tagObj === 'object' && tagObj !== null) ? (tagObj.name || tagObj.title) : escapeHtml(String(tagObj));
        return `<span class="article-category">${tagName}</span>`;
      }).join('')
    : '';

  return `
    <div class="article-header">
      <div class="article-author-info">
        <div class="article-author">${article.author_name || 'Эксперт Paw'}</div>
        <div class="article-date">${formatEventDate(article.created_at, article.updated_at)}</div>
      </div>
      <div class="org-menu-container">
        <button class="org-menu-btn" type="button" onclick="toggleArticleMenu(event, ${article.id})">⋮</button>
        <div id="articleDropdown-${article.id}" class="org-dropdown hidden">
          ${isAuthor ? `
            <button class="org-dropdown-item" type="button" onclick="handleEditArticle(${article.id})">✏️ Редактировать</button>
            <button class="org-dropdown-item delete-btn" type="button" onclick="handleDeleteArticle(${article.id})">🗑️ Удалить</button>
          ` : ''}
          ${isNotAuthor ? `
            <button class="org-dropdown-item" type="button" onclick="reportArticle(${article.id})">🚩 Пожаловаться</button>
          ` : ''}
        </div>
      </div>
    </div>
    
    <div class="article-content-full" style="padding: 10px 0;">
      <h3 class="article-title">${article.title || 'Без названия'}</h3>
      <div class="article-text-body" style="font-size: 14px; line-height: 1.6; color: var(--text); white-space: pre-wrap;">${article.content || 'Содержание отсутствует.'}</div>
    </div>
    
    <div class="article-meta" style="border-top: 1px solid var(--pink-border); margin-top: 12px; padding-top: 8px;">
      ${article.tags && article.tags.length ? `<div class="article-tags-wrapper">${tagsDisplay}</div>` : ''}
    </div>
    
    <div class="article-stats" style="display: flex; gap: 16px; margin-top: 12px;">
      <div class="article-stat ${isLiked ? 'active' : ''}" onclick="event.stopPropagation(); handleArticleVote(${article.id}, 1, true)" style="cursor:pointer; display: flex; align-items: center; gap: 4px;">
        <img src="../assets/reactions/${isLiked ? 'like-active.svg' : 'like-inactive.svg'}" alt="Лайк" class="article-stat-icon">
        <span class="stat-count" id="likes-count-${article.id}">${article.likes_count || 0}</span>
      </div>
      <div class="article-stat ${isDisliked ? 'active' : ''}" onclick="event.stopPropagation(); handleArticleVote(${article.id}, -1, true)" style="cursor:pointer; display: flex; align-items: center; gap: 4px;">
        <img src="../assets/reactions/${isDisliked ? 'dislike-active.svg' : 'dislike-inactive.svg'}" alt="Дизлайк" class="article-stat-icon">
        <span class="stat-count" id="dislikes-count-${article.id}">${article.dislikes_count || 0}</span>
      </div>
      <div class="article-stat" style="display: flex; align-items: center; gap: 4px;">
        <img src="../assets/reactions/comment-icon.svg" alt="Просмотры" class="article-stat-icon" style="opacity: 0.5;">
        <span class="stat-count">${article.views || 0}</span>
      </div>
    </div>
  `;
}

async function loadArticleForEdit(articleId) {
  const titleInput = document.getElementById('articleTitle');
  const contentTextarea = document.getElementById('articleContent');
  const tagsContainer = document.getElementById('articleTagsContainer');
  const statusDiv = document.getElementById('articleEditStatus');

  if (!titleInput || !contentTextarea || !tagsContainer) return;

  try {
    const article = await fetchArticleDetail(articleId);
    if (!article) {
      if (statusDiv) statusDiv.textContent = 'Статья не найдена.';
      return;
    }

    titleInput.value = article.title || '';
    contentTextarea.value = article.content || '';

    const categories = await fetchEncyclopediaCategories();
    tagsContainer.innerHTML = categories.map(cat => {
      const isChecked = article.tags && article.tags.some(t => (typeof t === 'object' ? t.id === cat.id : (t === cat.name || String(t) === String(cat.id))));
      return `
        <label class="checkbox-item" style="display: block; margin-bottom: 5px; font-size: 13px;">
          <input type="checkbox" value="${cat.id}" ${isChecked ? 'checked' : ''}> ${escapeHtml(cat.name)}
        </label>
      `;
    }).join('');

  } catch (err) {
    if (statusDiv) statusDiv.textContent = 'Ошибка загрузки: ' + err.message;
    console.error('LOAD ARTICLE FOR EDIT ERROR:', err);
  }
}

async function updateArticle(articleId, articleData) {
  const statusDiv = document.getElementById('articleEditStatus');
  try {
    await apiRequest(`/knowledge-base/articles/${articleId}`, {
      method: 'PUT',
      auth: true,
      body: JSON.stringify(articleData)
    });
    if (statusDiv) statusDiv.textContent = 'Статья обновлена!';
    setTimeout(() => {
      window.location.href = `article_view.html?id=${articleId}`;
    }, 1500);
  } catch (err) {
    if (statusDiv) statusDiv.textContent = 'Ошибка: ' + err.message;
    console.error('UPDATE ARTICLE ERROR:', err);
  }
}

async function fetchEncyclopediaCategories() {
  try {
    const response = await apiRequest('/encyclopedia/categories', { auth: true });
    return Array.isArray(response.data) ? response.data : [];
  } catch (err) {
    console.error('Ошибка загрузки категорий:', err);
    return [];
  }
}

async function fetchBreedsBySpecies(speciesId) {
  try {
    const response = await apiRequest(`/encyclopedia/breeds/${speciesId}`, { auth: true });
    return Array.isArray(response.data) ? response.data : [];
  } catch (err) {
    console.error('Ошибка загрузки пород:', err);
    return [];
  }
}

async function loadEncyclopediaData() {
  const categories = await fetchEncyclopediaCategories(); 
  const container = document.getElementById('criteriaSection');
  
  if (!container) return;

  if (categories.length > 0) {
    const breeds = await fetchBreedsBySpecies(categories[0].id);

    container.innerHTML = `
      <div class="criteria-group">
        <div class="criteria-header" onclick="toggleCriteria('animal-type')">
          <span class="criteria-title">Тип животного</span>
          <span class="criteria-arrow" id="animal-type-arrow">▲</span>
        </div>
        <div class="criteria-content" id="animal-type-criteria">
          ${categories.map(cat => `
            <label class="criteria-label">
              <input type="checkbox" class="criteria-checkbox" value="${cat.id}" onchange="updateBreedsFilter(this)"> ${cat.name}
            </label>
          `).join('')}
        </div>
      </div>

      <div class="criteria-group">
        <div class="criteria-header" onclick="toggleCriteria('breed')">
          <span class="criteria-title">Породы</span>
          <span class="criteria-arrow" id="breed-arrow">▲</span>
        </div>
        <div class="criteria-content" id="breed-criteria">
          <select class="criteria-select" id="breedSelect">
            <option value="">Выберите породу</option>
            ${breeds.map(b => `<option value="${b.id}">${b.name}</option>`).join('')}
          </select>
        </div>
      </div>
      <button class="apply-button" onclick="applyEncyclopediaFilters()">Применить</button>
    `;
  } else {
    container.innerHTML = '<div class="results-placeholder">Категории не найдены. Проверьте БД.</div>';
  }
}

async function updateBreedsFilter(changedCheckbox) {
  const checkboxes = document.querySelectorAll('#animal-type-criteria .criteria-checkbox');
  let selectedSpeciesId = null;

  for (const cb of checkboxes) {
    if (cb.checked) {
      selectedSpeciesId = cb.value;
      break;
    }
  }

  const breedSelect = document.getElementById('breedSelect');
  if (breedSelect) {
    const breeds = selectedSpeciesId ? await fetchBreedsBySpecies(selectedSpeciesId) : [];
    breedSelect.innerHTML = '<option value="">Выберите породу</option>' +
      breeds.map(b => `<option value="${b.id}">${b.name}</option>`).join('');
  }
}

async function initArticlesData() {
  const searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.addEventListener('input', performSearch);
  }
}

async function switchTab(tab) {
  const navButtons = document.querySelectorAll('.nav-btn');
  const encyclopediaContent = document.getElementById('encyclopedia-content');
  const articlesContent = document.getElementById('articles-content');
  const addButton = document.querySelector('.add-article-button');
  const criteriaSection = document.querySelector('.criteria-section');

  navButtons.forEach(btn => btn.classList.remove('active'));

  if (encyclopediaContent) encyclopediaContent.classList.add('hidden');
  if (articlesContent) articlesContent.classList.add('hidden');

  if (addButton) {
    addButton.style.display = 'none';
  }

  if (tab === 'encyclopedia') {
    const encBtn = document.querySelector(`[onclick="switchTab('encyclopedia')"]`);
    if (encBtn) encBtn.classList.add('active');
    
    if (encyclopediaContent) encyclopediaContent.classList.remove('hidden'); 
    
    if (criteriaSection) {
      criteriaSection.style.display = 'block';
    }
    await loadEncyclopediaData();
  } else if (tab === 'articles') {
    const artBtn = document.querySelector(`[onclick="switchTab('articles')"]`);
    if (artBtn) artBtn.classList.add('active');
    if (articlesContent) articlesContent.classList.remove('hidden');
    
    if (addButton) {
      addButton.style.display = 'block';
    }
    if (criteriaSection) {
      criteriaSection.style.display = 'none';
    }
    await loadArticlesData();
  }
}

function toggleCriteria(criteriaId) {
  const content = document.getElementById(criteriaId + '-criteria');
  if (content) {
    const arrow = document.getElementById(criteriaId + '-arrow');
    content.classList.toggle('hidden');
    if (arrow) {
      arrow.textContent = content.classList.contains('hidden') ? '▼' : '▲';
    }
  }
}

async function applyEncyclopediaFilters() {
  const breedSelect = document.getElementById('breedSelect');
  const selectedBreed = breedSelect ? breedSelect.value : '';

  const checkboxes = document.querySelectorAll('.criteria-checkbox:checked');
  const selectedTags = Array.from(checkboxes).map(cb => parseInt(cb.value));

  await switchTab('articles');
  await loadArticlesData(selectedTags);
}

let currentArticleTags = [];

async function getKnowledgeArticles(skip = 0, limit = 20, tagIds = []) {
  try {
    currentArticleTags = tagIds;
    const tagParams = tagIds.map(id => `&tag_ids=${id}`).join('');
    const url = `/knowledge-base/articles?skip=${skip}&limit=${limit}${tagParams}&sort_by=created_at`;
    
    const response = await apiRequest(url, { auth: true });
    
    return Array.isArray(response.data) ? response.data : (response.data.articles || []);
    
  } catch (err) {
    console.error('Ошибка при получении списка статей:', err);
    return [];
  }
}

async function loadArticlesData(tagIds = []) {
  const container = document.getElementById('articles-container');
  if (!container) return;

  try {
    const articles = await getKnowledgeArticles(0, 100, tagIds);
    cachedArticles = articles || [];

    renderFilteredArticles();
  } catch (err) {
    console.error('ARTICLES LOAD ERROR:', err);
    container.innerHTML = '<div class="results-placeholder">Ошибка загрузки статей.</div>';
  }
}

function renderFilteredArticles() {
  const container = document.getElementById('articles-container');
  if (!container) return;

  const searchInput = document.getElementById('searchInput');
  const query = searchInput ? searchInput.value.toLowerCase().trim() : '';

  const filtered = cachedArticles.filter(article => {
    const titleMatch = (article.title || '').toLowerCase().includes(query);
    const contentMatch = (article.content || '').toLowerCase().includes(query);
    const previewMatch = (article.content_preview || '').toLowerCase().includes(query);
    return titleMatch || contentMatch || previewMatch;
  });

  if (filtered.length === 0) {
    container.innerHTML = '<div class="results-placeholder">Ничего не найдено</div>';
  } else {
    container.innerHTML = filtered.map(article => createArticleCard(article)).join('');
  }
}

function createArticleCard(article) {
  const currentUserId = getCurrentUserId();
  const isAuthor = currentUserId && article.author_id === currentUserId;
  const isNotAuthor = currentUserId && article.author_id !== currentUserId;

  const myVote = article.my_vote != null ? parseInt(article.my_vote) : 
                 (article.liked_by_user === true ? 1 : 
                 (article.liked_by_user === false ? 0 : 0));

  const isLiked = myVote === 1;
  const isDisliked = myVote === -1;

  const excerpt = article.content_preview || (article.content ? article.content.substring(0, 150) : '');
  const displayExcerpt = excerpt.replace(/\n/g, '<br>') + (excerpt.length > 150 ? '...' : '');
  
  const tagsDisplay = article.tags && article.tags.length 
    ? article.tags.map(tagObj => {
        let tagName;
        if (typeof tagObj === 'object' && tagObj !== null && tagObj.name) {
          tagName = tagObj.name;
        } else {
          tagName = String(tagObj);
        }
        return `<span class="article-category">${tagName}</span>`;
      }).join('')
    : '';
  
  return `
    <div class="article-card" id="article-card-${article.id}">
      <div class="article-header">
        <div class="article-author-info">
          <div class="article-author">${article.author_name || 'Эксперт Paw'}</div>
          <div class="article-date">${formatEventDate(article.created_at, article.updated_at)}</div>
        </div>
        <div class="org-menu-container">
          <button class="org-menu-btn" type="button" onclick="toggleArticleMenu(event, ${article.id})">⋮</button>
          <div id="articleDropdown-${article.id}" class="org-dropdown hidden">
            ${isAuthor ? `
              <button class="org-dropdown-item" type="button" onclick="handleEditArticle(${article.id})">✏️ Редактировать</button>
              <button class="org-dropdown-item delete-btn" type="button" onclick="handleDeleteArticle(${article.id})">🗑️ Удалить</button>
            ` : ''}
            ${isNotAuthor ? `
              <button class="org-dropdown-item" type="button" onclick="reportArticle(${article.id})">🚩 Пожаловаться</button>
            ` : ''}
          </div>
        </div>
      </div>
      
      <div class="article-content-preview" onclick="openArticle(${article.id})" style="cursor:pointer;">
        <h3 class="article-title">${article.title || 'Без названия'}</h3>
        <p class="article-excerpt">${displayExcerpt}</p>
      </div>
      
      <div class="article-meta">
        ${article.tags && article.tags.length ? `
          <div class="article-tags-wrapper">
            ${tagsDisplay}
          </div>
        ` : ''}
      </div>
      
      <div class="article-stats">
        <div class="article-stat ${isLiked ? 'active' : ''}" onclick="event.stopPropagation(); handleArticleVote(${article.id}, 1)" style="cursor:pointer;">
          <img src="../assets/reactions/${isLiked ? 'like-active.svg' : 'like-inactive.svg'}" alt="Лайк" class="article-stat-icon">
          <span class="stat-count" id="likes-count-${article.id}">${article.likes_count || 0}</span>
        </div>
        <div class="article-stat ${isDisliked ? 'active' : ''}" onclick="event.stopPropagation(); handleArticleVote(${article.id}, -1)" style="cursor:pointer;">
          <img src="../assets/reactions/${isDisliked ? 'dislike-active.svg' : 'dislike-inactive.svg'}" alt="Дизлайк" class="article-stat-icon">
          <span class="stat-count" id="dislikes-count-${article.id}">${article.dislikes_count || 0}</span>
        </div>
        <div class="article-stat">
          <img src="../assets/reactions/views.svg" alt="Просмотры" class="article-stat-icon" style="opacity: 0.5;">
          <span class="stat-count">${article.views || 0}</span>
        </div>
      </div>
    </div>
  `;
}

async function handleArticleVote(articleId, voteType, isDetailPage = false) {
  const containerId = isDetailPage ? 'articleDetailContainer' : `article-card-${articleId}`;
  const container = document.getElementById(containerId);
  
  const targetSelector = voteType === 1 ? '.article-stat:nth-child(1).active' : '.article-stat:nth-child(2).active';
  const isAlreadyActive = container ? container.querySelector(targetSelector) : null;
  
  const voteToSend = isAlreadyActive ? 0 : voteType;

  try {
    await apiRequest(`/knowledge-base/articles/${articleId}/like?vote=${voteToSend}`, {
      method: 'POST',
      auth: true
    });

    if (isDetailPage) {
      await loadArticleDetail(articleId);
    } else {
      await loadArticlesData(currentArticleTags);
    }
  } catch (err) {
    console.error("Ошибка при голосовании:", err);
  }
}

function openArticle(articleId) {
  location.href = `article_view.html?id=${articleId}`;
}

async function handleEditArticle(articleId) {
  window.location.href = `edit_article.html?id=${articleId}`;
}

async function handleDeleteArticle(articleId) {
  if (!confirm("Вы уверены, что хотите удалить эту статью?")) {
    return;
  }
  try {
    await apiRequest(`/knowledge-base/articles/${articleId}`, {
      method: 'DELETE',
      auth: true
    });
    alert("Статья успешно удалена.");
    window.location.href = 'knowledge_base.html';
  } catch (err) {
    console.error("Ошибка при удалении статьи:", err);
    alert("Не удалось удалить статью: " + err.message);
  }
}

window.loadArticleDetail = loadArticleDetail;
window.loadArticleForEdit = loadArticleForEdit;
window.updateArticle = updateArticle;
window.handleArticleVote = handleArticleVote;
window.toggleArticleMenu = toggleArticleMenu;

function toggleArticleMenu(event, articleId) {
  event.stopPropagation();
  const allDropdowns = document.querySelectorAll('.org-dropdown');
  allDropdowns.forEach(dropdown => {
    if (dropdown.id !== `articleDropdown-${articleId}`) {
      dropdown.classList.add('hidden');
    }
  });
  
  const dropdown = document.getElementById(`articleDropdown-${articleId}`);
  if (dropdown) dropdown.classList.toggle('hidden');
}

function reportArticle(articleId) {
  alert('Жалоба отправлена модераторам Paw.');
  const dropdown = document.getElementById(`articleDropdown-${articleId}`);
  if (dropdown) dropdown.classList.add('hidden');
}

document.addEventListener('click', function(event) {
  if (!event.target.matches('.org-menu-btn')) {
    document.querySelectorAll('.org-dropdown').forEach(d => d.classList.add('hidden'));
  }
});

async function performSearch() {
  const searchInput = document.getElementById('searchInput');
  const query = searchInput ? searchInput.value.trim() : '';

  const articlesContent = document.getElementById('articles-content');
  
  if (query.length > 0 && articlesContent && articlesContent.classList.contains('hidden')) {
    await switchTab('articles');
  } else {
    renderFilteredArticles();
  }
}

document.addEventListener('DOMContentLoaded', async function() {
  const encyclopediaTab = document.getElementById('encyclopedia-content');
  const articlesTab = document.getElementById('articles-content');
  
  if (encyclopediaTab || articlesTab) {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.placeholder = searchInput.placeholder.replace('🔍', '').trim();
    }
    await initArticlesData();
    await switchTab('encyclopedia');
  }
});
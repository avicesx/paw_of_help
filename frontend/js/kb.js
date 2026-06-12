// База знаний.
// Дизайн: «База знаний 1.svg» (вкладка Энциклопедия — породы по видам),
// «База знаний статья.svg» (вкладка Статьи — лента статей с автором/лайками/просмотрами),
// «База знаний статья 2.svg» (просмотр статьи). Бэкенд: /knowledge-base/* и /encyclopedia/*.

let _kbTab = "articles";

function switchKbTab(tab) {
  _kbTab = tab;
  document.querySelectorAll(".kb-tab").forEach((b) => b.classList.toggle("active", b.dataset.tab === tab));
  const enc = document.getElementById("kbEncyclopedia");
  const art = document.getElementById("kbArticlesPane");
  if (enc) enc.style.display = tab === "encyclopedia" ? "block" : "none";
  if (art) art.style.display = tab === "articles" ? "block" : "none";
  if (tab === "encyclopedia" && !window.__kbSpeciesLoaded) loadKbSpecies();
}

// ----- Статьи -----
async function loadKbArticles() {
  const box = document.getElementById("kbArticles");
  if (!box) return;
  box.innerHTML = '<div class="empty-small">Загрузка...</div>';
  try {
    const { data } = await apiRequest("/knowledge-base/articles?sort_by=created_at&limit=50");
    window.__kbArticles = Array.isArray(data) ? data : [];
    renderKbArticles(window.__kbArticles);
  } catch (e) {
    box.innerHTML = '<div class="empty-small">Не удалось загрузить статьи</div>';
  }
}

function renderKbArticles(list) {
  const box = document.getElementById("kbArticles");
  if (!box) return;
  if (!list.length) {
    box.innerHTML = '<div class="empty-small">Статей пока нет. Нажмите «Написать статью», чтобы добавить первую.</div>';
    return;
  }
  box.innerHTML = list.map(kbCardHtml).join("");
}

function kbCardHtml(a) {
  const preview = (a.content_preview || "").trim();
  return `
    <article class="kb-card" onclick="location.href='kb-article.html?id=${a.id}'">
      <div class="kb-card-head">
        <span class="kb-avatar" aria-hidden="true"></span>
        <span class="kb-author">${escapeHtml(a.author_name || "Автор")}</span>
      </div>
      <div class="kb-card-box">
        <div class="kb-card-title">${escapeHtml(a.title || "Без названия")}</div>
        ${preview ? `<div class="kb-card-text">${escapeHtml(preview)}</div>` : ""}
        <div class="kb-expand">Развернуть...</div>
      </div>
      <div class="kb-card-foot">
        <span class="kb-stat">♡ ${a.likes_count || 0}</span>
        <span class="kb-stat">💔 ${a.dislikes_count || 0}</span>
        <span class="kb-stat">👁 ${a.views || 0}</span>
      </div>
    </article>`;
}

function filterKb() {
  const q = (document.getElementById("kbSearch")?.value || "").trim().toLowerCase();
  const all = window.__kbArticles || [];
  if (_kbTab !== "articles") return;
  const filtered = q
    ? all.filter((a) => (`${a.title || ""} ${a.content_preview || ""}`).toLowerCase().includes(q))
    : all;
  renderKbArticles(filtered);
}

// ----- Энциклопедия (виды → породы) -----
async function loadKbSpecies() {
  const box = document.getElementById("kbSpeciesList");
  if (!box) return;
  box.innerHTML = '<div class="empty-small">Загрузка...</div>';
  try {
    const { data } = await apiRequest("/encyclopedia/categories");
    const species = Array.isArray(data) ? data : [];
    window.__kbSpeciesLoaded = true;
    if (!species.length) {
      box.innerHTML = '<div class="empty-small">Справочник пока пуст</div>';
      return;
    }
    box.innerHTML = species.map((s) => `
      <div class="kb-acc">
        <button type="button" class="kb-acc-head" onclick="toggleKbSpecies(${s.id}, this)">
          <span>${escapeHtml(s.name || "Вид")}</span><span class="kb-acc-arrow">▾</span>
        </button>
        <div class="kb-acc-body" id="kbBreeds-${s.id}"></div>
      </div>`).join("");
  } catch (e) {
    box.innerHTML = '<div class="empty-small">Не удалось загрузить справочник</div>';
  }
}

async function toggleKbSpecies(speciesId, btn) {
  const body = document.getElementById(`kbBreeds-${speciesId}`);
  if (!body) return;
  const open = body.classList.toggle("open");
  if (btn) btn.classList.toggle("open", open);
  if (!open || body.dataset.loaded) return;
  body.innerHTML = '<div class="empty-small">Загрузка...</div>';
  try {
    const { data } = await apiRequest(`/encyclopedia/breeds/${speciesId}`);
    const breeds = Array.isArray(data) ? data : [];
    body.dataset.loaded = "1";
    body.innerHTML = breeds.length
      ? breeds.map((b) => `<button type="button" class="kb-breed" onclick="showKbBreed(${b.id})">${escapeHtml(b.name || "Порода")}</button>`).join("")
      : '<div class="empty-small">Пород пока нет</div>';
  } catch (e) {
    body.innerHTML = '<div class="empty-small">Не удалось загрузить</div>';
  }
}

async function showKbBreed(breedId) {
  try {
    const { data: b } = await apiRequest(`/encyclopedia/breed/${breedId}`);
    const panel = document.getElementById("kbBreedDetail");
    if (!panel) return;
    panel.innerHTML = `
      <button type="button" class="kb-breed-close" onclick="document.getElementById('kbBreedDetail').classList.remove('open')">✕</button>
      <h3 class="kb-breed-name">${escapeHtml(b.name || "Порода")}</h3>
      <div class="kb-breed-text">${escapeHtml(b.description || "Описание пока не добавлено.")}</div>`;
    panel.classList.add("open");
    panel.scrollIntoView({ behavior: "smooth", block: "center" });
  } catch (e) { alert("Не удалось загрузить породу"); }
}

// ----- Просмотр статьи -----
async function loadKbArticle() {
  const id = new URLSearchParams(location.search).get("id");
  if (!id) return;
  if (!getToken()) { location.href = "login.html"; return; }
  try {
    const { data: a } = await apiRequest(`/knowledge-base/articles/${id}`, { auth: true });
    window.__kbArticle = a;
    setText("kbArticleTitle", a.title || "Без названия");
    setText("kbArticleAuthor", a.author_name || "Автор");
    setText("kbArticleContent", a.content || "");
    setText("kbArticleViews", `👁 ${a.views || 0}`);
    const likeBtn = document.getElementById("kbLikeBtn");
    if (likeBtn) likeBtn.classList.toggle("on", a.liked_by_user === true);
  } catch (e) {
    setText("kbArticleContent", "Статья не найдена или недоступна.");
  }
}

async function likeKbArticle() {
  const a = window.__kbArticle;
  if (!a) return;
  if (!getToken()) { location.href = "login.html"; return; }
  try {
    await apiRequest(`/knowledge-base/articles/${a.id}/like?vote=1`, { method: "POST", auth: true });
    const likeBtn = document.getElementById("kbLikeBtn");
    if (likeBtn) likeBtn.classList.toggle("on");
  } catch (e) { alert(e.message || "Не удалось поставить лайк"); }
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("kbArticles")) { loadKbArticles(); switchKbTab("articles"); }
  if (document.getElementById("kbArticleContent")) loadKbArticle();
});

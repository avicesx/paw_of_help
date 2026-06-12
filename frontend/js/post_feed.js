let currentUserCache = null;

async function loadFeed() {
    const container = document.getElementById('feedPostsList');
    if (!container) return;

    container.innerHTML = '<div class="results-placeholder">Загрузка ленты...</div>';

    try {
        if (!currentUserCache) {
            const meRes = await apiRequest('/users/me', { auth: true });
            currentUserCache = meRes.data;
        }

        const { data: posts } = await apiRequest('/posts', { auth: true });
        
        const publishedPosts = (posts || []).filter(p => p.is_published);

        if (publishedPosts.length === 0) {
            container.innerHTML = '<div class="results-placeholder">В ленте пока пусто 🐾</div>';
            return;
        }

        // Собираем ID авторов, у которых нет имен в ответе, и загружаем их пачкой
        const missingUserIds = publishedPosts
            .filter(p => !p.organization_id && !p.author_username)
            .map(p => p.author_user_id || p.user_id);
        
        if (missingUserIds.length > 0) {
            await resolveUserNames(missingUserIds);
        }
        
        container.innerHTML = publishedPosts.map(post => renderPostCard(post)).join('');
        
    } catch (err) {
        container.innerHTML = '<div class="results-placeholder">Ошибка загрузки ленты</div>';
    }
}

document.addEventListener('DOMContentLoaded', loadFeed);
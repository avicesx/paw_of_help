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

        const processedPosts = publishedPosts.map(post => {
            if (!post.organization_id && post.author_user_id === currentUserCache.id) {
                return { ...post, author_username: currentUserCache.username };
            }
            return post;
        });
        
        container.innerHTML = processedPosts.map(post => renderPostCard(post)).join('');
        
    } catch (err) {
        container.innerHTML = '<div class="results-placeholder">Ошибка загрузки ленты</div>';
    }
}

document.addEventListener('DOMContentLoaded', loadFeed);
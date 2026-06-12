let cachedOrgs = { my: [], sub: [], all: [], invites: [] };

async function loadOrganizationCatalog() {
    const container = document.getElementById('orgList');
    const searchInput = document.getElementById('orgSearchInput');
    
    try {
        const [myRes, subRes, allRes, invitesRes] = await Promise.all([
            apiRequest('/organizations/my', { auth: true }).catch(() => ({ data: [] })),
            apiRequest('/organizations/subscriptions', { auth: true }).catch(() => ({ data: [] })),
            apiRequest('/organizations'),
            apiRequest('/organizations/invites', { auth: true }).catch(() => ({ data: [] }))
        ]);

        const myData = Array.isArray(myRes.data) ? myRes.data : [];
        const subData = Array.isArray(subRes.data) ? subRes.data : [];
        const allData = Array.isArray(allRes.data) ? allRes.data : [];

        const rawInvites = Array.isArray(invitesRes.data) ? invitesRes.data : [];

        const inviteData = rawInvites
            .map(invite => {
                const orgInfo = allData.find(o => o.id === invite.organization_id);
                return orgInfo ? { ...invite, organization: orgInfo } : null;
            })
            .filter(i => i !== null);

        cachedOrgs = { my: myData, sub: subData, all: allData, invites: inviteData };

        renderFilteredCatalog();

        if (searchInput && !searchInput.dataset.listener) {
            searchInput.addEventListener('input', renderFilteredCatalog);
            searchInput.dataset.listener = 'true';
        }
    } catch (err) {
        console.error("Ошибка:", err);
        container.innerHTML = `<p>Ошибка: ${err.message}</p>`;
    }
}

function renderFilteredCatalog() {
    const container = document.getElementById('orgList');
    const query = document.getElementById('orgSearchInput').value.toLowerCase();

    const filterFn = (o) => o.name.toLowerCase().includes(query);

    const myData = cachedOrgs.my.filter(filterFn);
    const subData = cachedOrgs.sub.filter(filterFn);
    const allData = cachedOrgs.all.filter(filterFn);
    const inviteData = cachedOrgs.invites.filter(i => i.organization && i.organization.name.toLowerCase().includes(query));

    if (myData.length === 0 && subData.length === 0 && allData.length === 0 && inviteData.length === 0) {
        container.innerHTML = '<p class="results-placeholder">Ничего не найдено</p>';
        return;
    }

    const shownIds = new Set([
        ...myData.map(o => o.id),
        ...subData.map(o => o.id),
        ...cachedOrgs.invites.map(i => i.organization?.id || i.organization_id)
    ]);

    const otherOrgs = allData.filter(o => !shownIds.has(o.id));

    container.innerHTML = `
        ${renderOrgSection('Приглашения', inviteData.map(i => i.organization), 'invite')}
        ${renderOrgSection('Мои организации', myData, 'my')}
        ${renderOrgSection('Вы подписаны', subData, 'sub')}
        ${renderOrgSection('Другие организации', otherOrgs, 'other')}
    `;
}

function getOrgAvatar(org) {
    if (org.logo_url && !org.logo_url.includes('placeholder')) {
        return `<img src="${org.logo_url}" class="org-avatar-img" onerror="this.parentElement.innerHTML='🐾'">`;
    }
    return '🐾';
}

function renderOrgSection(title, orgs, type) {
    if (orgs.length === 0) return '';
    const myId = getUserIdFromToken();
    
    return `
        <div class="org-section">
            <div class="section-label">${title}</div>
            <div class="org-section-list">
            ${orgs.map(org => `
                <div class="org-card" onclick="location.href='org.html?id=${org.id}'">
                    <div class="org-card-logo">
                        ${getOrgAvatar(org)}
                    </div>
                    
                    <div class="org-card-info">
                        <h3>${escapeHtml(org.name)}</h3>
                        <p>${escapeHtml(org.address || 'Адрес не указан')}</p>
                    </div>
                    
                    <div class="org-menu-container" onclick="event.stopPropagation()">
                        <button class="org-kebab-btn" onclick="toggleOrgKebab(event, ${org.id})">⋮</button>
                        <div id="orgKebab-${org.id}" class="org-dropdown hidden">
                            ${renderKebabOptions(org, type, myId)}
                        </div>
                    </div>
                </div>
            `).join('')}
            </div>
        </div>
    `;
}

function renderKebabOptions(org, type, myId) {
    if (type === 'invite') {
        return `
            <button class="org-dropdown-item" onclick="handleInvite(${org.id}, 'accept')">✅ Принять</button>
            <button class="org-dropdown-item" onclick="handleInvite(${org.id}, 'decline')">❌ Отклонить</button>
        `;
    }
    if (type === 'my') {
        return `
            <button class="org-dropdown-item" onclick="location.href='edit_profile.html?id=${org.id}'">✏️ Редактировать</button>
        `;
    }
    if (type === 'sub') {
        return `<button class="org-dropdown-item" onclick="toggleSubscription(${org.id}, false)">🚶 Отписаться</button>`;
    }
    return `<button class="org-dropdown-item" onclick="toggleSubscription(${org.id}, true)">🔔 Подписаться</button>`;
}

function toggleOrgKebab(event, id) {
    event.stopPropagation();
    const menu = document.getElementById(`orgKebab-${id}`);
    document.querySelectorAll('.org-dropdown').forEach(m => {
        if (m !== menu) m.classList.add('hidden');
    });
    menu.classList.toggle('hidden');
}

async function toggleSubscription(orgId, subscribe) {
    try {
        const method = subscribe ? 'POST' : 'DELETE';
        await apiRequest(`/organizations/${orgId}/subscribe`, { method, auth: true });
        loadOrganizationCatalog();
    } catch (err) {
        alert("Ошибка: " + err.message);
    }
}

async function handleInvite(orgId, action) {
    try {
        await apiRequest(`/organizations/${orgId}/${action}-invite`, { method: 'POST', auth: true });
        loadOrganizationCatalog();
    } catch (err) {
        alert("Ошибка: " + err.message);
    }
}

function getUserIdFromToken() {
    const token = localStorage.getItem('token');
    if (!token) return null;
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload.sub ? parseInt(payload.sub) : null;
    } catch (e) { return null; }
}

document.addEventListener('click', () => {
    document.querySelectorAll('.org-dropdown').forEach(m => m.classList.add('hidden'));
});

document.addEventListener('DOMContentLoaded', loadOrganizationCatalog);
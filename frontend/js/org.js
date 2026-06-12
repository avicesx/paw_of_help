let currentOrgId = getOrganizationIdFromUrl();

async function loadOrgProfile() {
    if (!currentOrgId) {
        console.error("ID организации не найден!");
        return;
    }

    try {
        const [org, usersRes] = await Promise.all([
            getOrgData(currentOrgId),
            apiRequest(`/organizations/${currentOrgId}/users`, { auth: true }).catch(() => ({ data: [] }))
        ]);

        if (!org) return;

        const elHeader = document.getElementById('orgHeader');
        const currentUserId = getUserIdFromToken();
        const myMemberInfo = usersRes.data.find(u => u.user_id == currentUserId && u.invitation_status === 'accepted');
        
        window.isOrgMember = !!myMemberInfo;
        
        const isCreator = currentUserId == org.created_by;
        const acceptedAdmins = usersRes.data.filter(u => u.role === 'admin' && u.invitation_status === 'accepted');
        const isLastAdmin = (myMemberInfo?.role === 'admin') && acceptedAdmins.length === 1;
        const showReport = currentUserId && !isCreator && !isLastAdmin;

        if (elHeader) {
            elHeader.style.position = 'relative'; 
            const logoSrc = getOrgImageUrl(org);
            
            let contactDisplay = '';
            if (org.contacts) {
                if (typeof org.contacts === 'string' && org.contacts !== '{}') contactDisplay = org.contacts;
                else if (org.contacts.phone) contactDisplay = org.contacts.phone;
                else if (org.contacts.email) contactDisplay = org.contacts.email;
            }
            if (!contactDisplay || contactDisplay === '{}') contactDisplay = 'Не указаны';

            elHeader.innerHTML = `
                <div class="org-avatar" style="width: 80px; height: 80px; overflow: hidden; border-radius: 50%;">
                    <img src="${logoSrc}" style="width: 100%; height: 100%; object-fit: cover;" onerror="this.src='../assets/default-avatar.png'">
                </div>
                <div class="org-meta">
                    <h2>${org.name}</h2>
                    <p>📍 ${org.address || 'Адрес не указан'}</p>
                    <p>ИНН: ${org.inn || 'Не указан'} | 📞 ${contactDisplay}</p>
                </div>

                <div class="org-header-actions" style="position: absolute; top: 12px; right: 12px; display: flex; flex-direction: column; gap: 10px; align-items: center;">
                    ${myMemberInfo ? `
                        <button class="kebab-menu-btn" type="button" onclick="toggleOrgMenu(event)" style="position: static;">⋮</button>
                    ` : ''}
                    
                    ${showReport ? `
                        <button class="report-org-icon-btn" onclick="handleReportOrg(${org.id})" title="Пожаловаться" style="background:none; border:none; cursor:pointer; padding:0; display:flex;">
                            <img src="../assets/reactions/report.svg" style="width: 24px; height: 24px; display: block;">
                        </button>
                    ` : ''}
                </div>
                
                <div id="orgContextMenu" class="context-menu hidden">
                    <ul>
                        <li onclick="navigateToEdit()">✏️ Изменить профиль</li>
                        <li onclick="navigateToCurators()">👥 Список кураторов</li>
                    </ul>
                </div>
            `;
        }

        const postContainer = document.getElementById('addPostContainer');
        if (postContainer) {
            postContainer.classList.toggle('hidden', !window.isOrgMember);
        }

        document.getElementById('infoText').textContent = org.description || 'Описание отсутствует.';
        document.querySelector('.screen-title').textContent = org.name;

        await renderOrgPosts();

    } catch (err) {
        console.error("Ошибка загрузки:", err);
    }
}

async function renderOrgPosts() {
    const container = document.getElementById('postsList');
    if (!container) return;
    
    container.innerHTML = '<div class="results-placeholder">Загрузка...</div>';
    try {
        const posts = await getOrgPosts(currentOrgId);
        const userId = getUserIdFromToken();
        const org = await getOrgData(currentOrgId);

        if (!posts || posts.length === 0) {
            container.innerHTML = '<div class="results-placeholder">Пока нет постов</div>';
            return;
        }

        const missingUserIds = posts.filter(p => !p.organization_id && !p.author_username).map(p => p.author_user_id || p.user_id);
        if (missingUserIds.length > 0) await resolveUserNames(missingUserIds);

        const canManage = userId && (userId == org.created_by); 
        container.innerHTML = posts.map(post => renderPostCard(post, canManage)).join('');
    } catch (err) {
        container.innerHTML = '<div class="results-placeholder">Ошибка загрузки</div>';
    }
}

function toggleInfo() {
    const infoText = document.getElementById('infoText');
    const btn = document.querySelector('.expand-btn');
    if (!infoText) return;

    infoText.classList.toggle('expanded');
    btn.textContent = infoText.classList.contains('expanded') ? 'Свернуть' : 'Развернуть...';
}

function toggleOrgMenu(event) {
    event.stopPropagation();
    const menu = document.getElementById('orgContextMenu');
    if (menu) menu.classList.toggle('hidden');
}

async function handleReportOrg(orgId) {
    if (!confirm("Вы уверены, что хотите пожаловаться на эту организацию?")) return;
    try {
        await apiRequest('/reports/', {
            method: 'POST',
            auth: true,
            body: JSON.stringify({
                target_type: 'organization',
                target_id: orgId,
                reason_code: 'other',
                description: 'Жалоба со страницы организации'
            })
        });
        alert("Жалоба отправлена. Спасибо за бдительность!");
    } catch (err) {
        console.error(err);
        alert("Не удалось отправить жалобу: " + (err.detail || err.message));
    }
}

function navigateToEdit() { window.location.href = `edit_profile.html?id=${currentOrgId}`; }
function navigateToCurators() { window.location.href = `curators.html?id=${currentOrgId}`; }

function getUserIdFromToken() {
    const token = localStorage.getItem('token') || localStorage.getItem('access_token');
    if (!token) return null;
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return parseInt(payload.sub);
    } catch (e) { return null; }
}

document.addEventListener('DOMContentLoaded', () => {
    if (ensureAuth()) loadOrgProfile();
});

document.addEventListener('click', () => {
    const menu = document.getElementById('orgContextMenu');
    if (menu) menu.classList.add('hidden');
});
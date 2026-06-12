// Единые шаблоны для организации
function renderOrgLogo(orgData, containerElement) {
    if (orgData.logo_url && !orgData.logo_url.includes('via.placeholder')) {
        containerElement.innerHTML = `<img src="${orgData.logo_url}" class="org-logo-img" />`;
    } else {
        containerElement.innerHTML = '<span class="org-logo-placeholder">📷</span>';
    }
}

function getOrganizationIdFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const id = params.get('id') || params.get('organization_id');
  return id ? parseInt(id) : null;
}

// API функции для работы с организациями
async function getOrgData(orgId) {
    if (!orgId) {
        console.error("ID организации не найден!");
        return null; // Или верни дефолтный объект с ошибкой
    }
    try {
        const { data } = await apiRequest(`/organizations/${orgId}`);
        return data;
    } catch (err) {
        console.error('Ошибка загрузки организации:', err);
        throw err;
    }
}

async function getOrgPosts(orgId) {
  try {
    const { data } = await apiRequest(`/posts?organization_id=${orgId}`);
    return data || [];
  } catch (err) {
    console.error('Ошибка загрузки постов:', err);
    return [];
  }
}

async function getCuratorsData(orgId) {
  try {
    const { data } = await apiRequest(`/organizations/${orgId}/users`, { auth: true });
    const users = data.filter(u => u.role === 'curator');
    const admin = data.find(u => u.role === 'admin');
    
    return {
      administrator: admin ? {
        id: admin.user_id,
        name: 'Администратор',
        avatar: '',
        email: '',
        phone: '',
        role: 'administrator'
      } : null,
      curators: users.map(u => ({
        id: u.user_id,
        name: 'Куратор',
        avatar: '',
        email: '',
        phone: '',
        role: 'curator'
      }))
    };
  } catch (err) {
    console.error('CURATORS LOAD ERROR:', err);
    return { administrator: null, curators: [] };
  }
}

async function addCurator(orgId, curatorData) {
  try {
    const { data } = await apiRequest(`/organizations/${orgId}/invite`, {
      method: 'POST',
      auth: true,
      body: JSON.stringify({
        username: curatorData.username,
        role: 'curator'
      })
    });
    return {
      id: data.user_id,
      name: curatorData.name || 'Новый куратор',
      avatar: '',
      email: curatorData.email || '',
      phone: curatorData.phone || '',
      role: 'curator'
    };
  } catch (err) {
    console.error('ADD CURATOR ERROR:', err);
    throw err;
  }
}
// Получить животных организации (заглушка для API)
function getOrgAnimals() {
  return [
    { breed: "Беспородный", age: "2 года", type: "Собака", gender: "Кобель", applications: ["На выгул", "Передержка"] },
    { breed: "Сиамская", age: "1 год", type: "Кошка", gender: "Самка", applications: ["В добрые руки"] }
  ];
}

// Получить заявки организации (заглушка для API)
function getOrgApplications() {
  return [
    { title: "Выгул собак", type: "Волонтерство" },
    { title: "Покупка корма", type: "Пожертвование" }
  ];
}
// Обновить данные организации
async function updateOrgData(orgId, orgData) {
  try {
    const { data } = await apiRequest(`/organizations/${orgId}`, {
      method: 'PATCH',
      auth: true,
      body: JSON.stringify({
        name: orgData.name,
        description: orgData.description,
        inn: orgData.inn,
        address: orgData.address,
        contacts: orgData.contacts,
        logo_url: orgData.logo_url,
        photos: orgData.photos
      })
    });
    return data;
  } catch (err) {
    console.error('ORG UPDATE ERROR:', err);
    throw err;
  }
}

function renderOrgPostsList(posts, orgData, currentUserId) {
    const container = document.getElementById('postsList');
    if (!container) return;

    const isOrgAdmin = (currentUserId === orgData.created_by);

    container.innerHTML = posts.map(post => {
        return renderPostCard(post, isOrgAdmin);
    }).join('');
}

function getOrgImageUrl(org) {
    const url = org.logo_url;
    if (url && !url.includes('via.placeholder')) {
        return url;
    }
    return `https://picsum.photos/seed/${org.id}/200/200`;
}

function createAnimalCard(animal) {
  return `
    <div class="animal-card-org">
      <div class="animal-card-header">
        <div class="animal-paw">🐾</div>
        <div class="animal-info">
          <div class="animal-detail">Вид: <span class="animal-value">${animal.type}</span></div>
          <div class="animal-detail">Порода: <span class="animal-value">${animal.breed}</span></div>
          <div class="animal-detail">Возраст: <span class="animal-value">${animal.age}</span></div>
          <div class="animal-detail">Пол: <span class="animal-value">${animal.gender}</span></div>
        </div>
      </div>
      <div class="animal-actions">
        <button class="animal-btn" type="button" onclick="alert('Подробности о животном')">Узнать больше...</button>
      </div>
      <div class="animal-applications">
        <div class="applications-title">Активные заявки</div>
        ${animal.applications.map(app => `<button class="application-btn" type="button" onclick="alert('Отклик на: ${app}')">${app}</button>`).join('')}
      </div>
    </div>
  `;
}

function createApplicationCard(application) {
  return `
    <div class="application-card">
      <div class="application-header">
        <div class="application-paw">🐾</div>
        <div class="application-content">
          <div class="application-title">${application.title}</div>
          <button class="application-type-btn" type="button">${application.type}</button>
        </div>
      </div>
      <button class="contact-org-btn" type="button" onclick="alert('Открыть чат с организацией')">Связаться</button>
    </div>
  `;
}

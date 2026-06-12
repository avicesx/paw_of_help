async function fetchBreedsBySpecies(speciesId) {
  try {
    const { data } = await apiRequest(`/encyclopedia/breeds/${speciesId}`, { auth: true });
    return data;
  } catch (err) {
    console.error('Ошибка загрузки пород:', err);
    return [];
  }
}

async function fetchBreedDetail(breedId) {
  try {
    const { data } = await apiRequest(`/encyclopedia/breed/${breedId}`, { auth: true });
    return data;
  } catch (err) {
    console.error('Ошибка загрузки деталей породы:', err);
    return null;
  }
}

async function toggleKnowledgeArticleLike(articleId, voteValue) {
  const path = `/knowledge-base/articles/${articleId}/like?vote=${voteValue}`; 

  return await apiRequest(path, {
    method: 'POST',
    auth: true,
    headers: {
      'Accept': 'application/json'
    },
    body: JSON.stringify({})
  });
}

async function generateCriteriaHTML() {
  const species = await fetchEncyclopediaCategories();
  
  const breeds = species.length > 0 ? await fetchBreedsBySpecies(species[0].id) : [];

  return `
    <div class="criteria-section">
      <div class="criteria-group">
        <div class="criteria-header" onclick="toggleCriteria('breed')">
          <span class="criteria-title">Породы</span>
        </div>
        <div class="criteria-content" id="breed-criteria">
          <select class="criteria-select" id="breedSelect">
            <option value="">Выберите породу</option>
            ${breeds.map(b => `<option value="${b.id}">${b.name}</option>`).join('')}
          </select>
        </div>
      </div>

      <div class="criteria-group">
        <div class="criteria-header" onclick="toggleCriteria('animal-type')">
          <span class="criteria-title">Тип животного</span>
        </div>
        <div class="criteria-content" id="animal-type-criteria">
          ${species.map(s => `
            <label class="criteria-label">
              <input type="checkbox" class="criteria-checkbox" value="${s.id}"> ${s.name}
            </label>
          `).join('')}
        </div>
      </div>
    </div>
  `;
}

async function updateCriteriaSection() {
  const container = document.querySelector('.criteria-section');
  if (container) {
    const html = await generateCriteriaHTML();
    container.innerHTML = html;
  }
}

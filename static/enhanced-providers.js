// Enhanced Dashboard - Providers Module
// AI Provider & Model CRUD operations, trending data

// ============================================
// PROVIDER MANAGEMENT
// ============================================

let providers = [];
let models = [];

function initProviderManagement() {
    loadProviders();

    document.getElementById('addProviderBtn')?.addEventListener('click', () => {
        openProviderModal();
    });

    document.getElementById('saveProviderBtn')?.addEventListener('click', () => {
        saveProvider();
    });

    document.getElementById('cancelProviderBtn')?.addEventListener('click', () => {
        closeProviderModal();
    });

    document.getElementById('closeProviderModal')?.addEventListener('click', () => {
        closeProviderModal();
    });
}

async function loadProviders() {
    try {
        const response = await fetch('/api/providers');
        providers = await response.json();
        renderProviders();
        updateModelProviderDropdown();
    } catch (error) {
        console.error('Error loading providers:', error);
        showToast('Failed to load providers', 'error');
    }
}

function renderProviders() {
    const container = document.getElementById('providerList');
    if (!container) return;

    if (providers.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-robot"></i>
                <p>No AI providers configured. Add one to get started.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = providers.map(provider => `
        <div class="provider-card">
            <div class="provider-info">
                <div class="provider-name">${provider.name}</div>
                <div class="provider-url">${provider.api_url}</div>
                <div class="provider-models">Models: ${provider.models || 'Not specified'}</div>
            </div>
            <div class="provider-actions">
                <button class="btn-small edit" onclick="editProvider(${provider.id})">
                    <i class="bi bi-pencil"></i> Edit
                </button>
                <button class="btn-small delete" onclick="deleteProvider(${provider.id})">
                    <i class="bi bi-trash"></i> Delete
                </button>
            </div>
        </div>
    `).join('');
}

function openProviderModal(providerId = null) {
    const modal = document.getElementById('providerModal');
    const title = document.getElementById('providerModalTitle');

    if (providerId) {
        const provider = providers.find(p => p.id === providerId);
        if (provider) {
            title.textContent = 'Edit AI Provider';
            document.getElementById('providerIdField').value = provider.id;
            document.getElementById('providerName').value = provider.name;
            document.getElementById('providerApiUrl').value = provider.api_url;
            document.getElementById('providerApiKey').value = provider.api_key;
            document.getElementById('providerModels').value = provider.models || '';
        }
    } else {
        title.textContent = 'Add AI Provider';
        document.getElementById('providerForm').reset();
        document.getElementById('providerIdField').value = '';
    }

    modal.classList.add('active');
}

function closeProviderModal() {
    document.getElementById('providerModal').classList.remove('active');
    document.getElementById('providerForm').reset();
}

async function saveProvider() {
    const providerId = document.getElementById('providerIdField').value;
    const data = {
        name: document.getElementById('providerName').value,
        api_url: document.getElementById('providerApiUrl').value,
        api_key: document.getElementById('providerApiKey').value,
        models: document.getElementById('providerModels').value
    };

    try {
        const url = providerId ? `/api/providers/${providerId}` : '/api/providers';
        const method = providerId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            showToast(`Provider ${providerId ? 'updated' : 'added'} successfully`, 'success');
            closeProviderModal();
            await loadProviders();
        } else {
            const error = await response.json();
            showToast(error.error || 'Failed to save provider', 'error');
        }
    } catch (error) {
        console.error('Error saving provider:', error);
        showToast('Failed to save provider', 'error');
    }
}

function editProvider(providerId) {
    openProviderModal(providerId);
}

async function deleteProvider(providerId) {
    if (!confirm('Are you sure you want to delete this provider?')) {
        return;
    }

    try {
        const response = await fetch(`/api/providers/${providerId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showToast('Provider deleted successfully', 'success');
            await loadProviders();
        } else {
            const error = await response.json();
            showToast(error.error || 'Failed to delete provider', 'error');
        }
    } catch (error) {
        console.error('Error deleting provider:', error);
        showToast('Failed to delete provider', 'error');
    }
}

// ============================================
// MODEL MANAGEMENT
// ============================================

function initModelManagement() {
    loadModelsConfig();

    document.getElementById('addModelBtn')?.addEventListener('click', () => {
        openModelModal();
    });

    document.getElementById('saveModelBtn')?.addEventListener('click', () => {
        saveModel();
    });

    document.getElementById('cancelModelBtn')?.addEventListener('click', () => {
        closeModelModal();
    });

    document.getElementById('closeModelModal')?.addEventListener('click', () => {
        closeModelModal();
    });

    document.getElementById('loadModelsBtn')?.addEventListener('click', async () => {
        await loadAvailableModels();
    });
}

async function loadAvailableModels() {
    const providerId = document.getElementById('modelProvider').value;

    if (!providerId) {
        showToast('Please select an AI provider first', 'error');
        return;
    }

    // Find the selected provider
    const provider = providers.find(p => p.id === parseInt(providerId));
    if (!provider) {
        showToast('Provider not found', 'error');
        return;
    }

    const loadBtn = document.getElementById('loadModelsBtn');
    const statusText = document.getElementById('modelLoadStatus');
    const datalist = document.getElementById('availableModelsList');

    try {
        // Show loading state
        loadBtn.disabled = true;
        loadBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Loading...';
        statusText.style.display = 'none';

        const response = await fetch('/api/providers/models', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                api_url: provider.api_url,
                api_key: provider.api_key
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to fetch models');
        }

        const result = await response.json();
        const modelsList = result.models || [];

        // Populate datalist
        datalist.innerHTML = modelsList.map(model => `<option value="${model}">`).join('');

        // Show success message
        statusText.textContent = `✓ Loaded ${modelsList.length} models`;
        statusText.style.display = 'block';
        statusText.style.color = 'var(--color-success)';

        showToast(`Loaded ${modelsList.length} available models`, 'success');

    } catch (error) {
        console.error('Error loading available models:', error);
        statusText.textContent = `✗ ${error.message}`;
        statusText.style.display = 'block';
        statusText.style.color = 'var(--color-danger)';
        showToast(`Failed to load models: ${error.message}`, 'error');
    } finally {
        // Restore button
        loadBtn.disabled = false;
        loadBtn.innerHTML = '<i class="bi bi-cloud-download"></i> Load Models';
    }
}

async function loadModelsConfig() {
    try {
        const response = await fetch('/api/models');
        models = await response.json();
        renderModelsConfig();
    } catch (error) {
        console.error('Error loading models:', error);
        showToast('Failed to load models', 'error');
    }
}

function renderModelsConfig() {
    const container = document.getElementById('modelListConfig');
    if (!container) return;

    if (models.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-cpu"></i>
                <p>No models configured. Add an AI provider first, then create a model.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = models.map(model => `
        <div class="model-card">
            <div class="model-info">
                <div class="model-name">${model.name}</div>
                <div class="model-details">Provider: ${model.provider_name || 'None'} | Model: ${model.model_name}</div>
                <div class="model-details">Capital: $${model.initial_capital.toLocaleString()}</div>
            </div>
            <div class="model-actions">
                <button class="btn-small edit" onclick="editModel(${model.id})">
                    <i class="bi bi-pencil"></i> Edit
                </button>
                <button class="btn-small delete" onclick="deleteModel(${model.id})">
                    <i class="bi bi-trash"></i> Delete
                </button>
            </div>
        </div>
    `).join('');
}

function updateModelProviderDropdown() {
    const select = document.getElementById('modelProvider');
    if (!select) return;

    select.innerHTML = '<option value="">Select a provider...</option>' +
        providers.map(provider => `
            <option value="${provider.id}">${provider.name}</option>
        `).join('');
}

function openModelModal(modelId = null) {
    const modal = document.getElementById('modelModal');
    const title = document.getElementById('modelModalTitle');

    if (modelId) {
        const model = models.find(m => m.id === modelId);
        if (model) {
            title.textContent = 'Edit Trading Model';
            document.getElementById('modelIdField').value = model.id;
            document.getElementById('modelName').value = model.name;
            document.getElementById('modelProvider').value = model.provider_id || '';
            document.getElementById('modelAiModel').value = model.model_name;
            document.getElementById('modelCapital').value = model.initial_capital;
        }
    } else {
        title.textContent = 'Create Trading Model';
        document.getElementById('modelForm').reset();
        document.getElementById('modelIdField').value = '';
    }

    modal.classList.add('active');
}

function closeModelModal() {
    document.getElementById('modelModal').classList.remove('active');
    document.getElementById('modelForm').reset();
}

async function saveModel() {
    const modelId = document.getElementById('modelIdField').value;
    const data = {
        name: document.getElementById('modelName').value,
        provider_id: parseInt(document.getElementById('modelProvider').value),
        model_name: document.getElementById('modelAiModel').value,
        initial_capital: parseFloat(document.getElementById('modelCapital').value)
    };

    try {
        const url = modelId ? `/api/models/${modelId}` : '/api/models';
        const method = modelId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            showToast(`Model ${modelId ? 'updated' : 'created'} successfully`, 'success');
            closeModelModal();
            await loadModelsConfig();
            // Reload main model selector
            if (window.loadModels) window.loadModels();
        } else {
            const error = await response.json();
            showToast(error.error || 'Failed to save model', 'error');
        }
    } catch (error) {
        console.error('Error saving model:', error);
        showToast('Failed to save model', 'error');
    }
}

function editModel(modelId) {
    openModelModal(modelId);
}

async function deleteModel(modelId) {
    if (!confirm('Are you sure you want to delete this model? All associated data will be lost.')) {
        return;
    }

    try {
        const response = await fetch(`/api/models/${modelId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showToast('Model deleted successfully', 'success');
            await loadModelsConfig();
            // Reload main model selector
            if (window.loadModels) window.loadModels();
        } else {
            const error = await response.json();
            showToast(error.error || 'Failed to delete model', 'error');
        }
    } catch (error) {
        console.error('Error deleting model:', error);
        showToast('Failed to delete model', 'error');
    }
}

// ============================================
// TRENDING DATA
// ============================================

function initTrendingData() {
    loadTrendingData();

    document.getElementById('refreshTrendingBtn')?.addEventListener('click', () => {
        loadTrendingData();
    });

    // Auto-refresh every 60 seconds - FIX: Store interval to prevent memory leak
    if (trendingInterval) {
        clearInterval(trendingInterval);
    }
    trendingInterval = setInterval(loadTrendingData, 60000);
}

function cleanupTrendingData() {
    if (trendingInterval) {
        clearInterval(trendingInterval);
        trendingInterval = null;
    }
}

async function loadTrendingData() {
    const container = document.getElementById('trendingGrid');
    if (!container) return;

    try {
        // Get current prices for popular coins
        const coins = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'DOGE'];
        const response = await fetch(`/api/market/prices?symbols=${coins.join(',')}`);
        const data = await response.json();

        if (data && Object.keys(data).length > 0) {
            container.innerHTML = coins.map(coin => {
                const coinData = data[coin];
                if (!coinData) return '';

                const change = coinData.change_24h || 0;
                const changeClass = change >= 0 ? 'positive' : 'negative';
                const changeIcon = change >= 0 ? '▲' : '▼';

                return `
                    <div class="trending-card">
                        <div class="trending-symbol">${coin}</div>
                        <div class="trending-price">$${coinData.price.toLocaleString(undefined, {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2
                        })}</div>
                        <div class="trending-change ${changeClass}">
                            ${changeIcon} ${Math.abs(change).toFixed(2)}%
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-graph-up"></i>
                    <p>Unable to load market data</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading trending data:', error);
        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-exclamation-triangle"></i>
                <p>Failed to load market data</p>
            </div>
        `;
    }
}

console.log('✓ Enhanced Providers Module Loaded');

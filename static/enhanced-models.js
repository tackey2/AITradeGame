// Enhanced Dashboard - Models Module
// Model loading, multi-model views, models page

// ============================================
// MODELS PAGE VARIABLES
// ============================================

let allModelsData = [];
let modelsFilter = 'all';

// ============================================
// MODEL LOADING & SELECTION
// ============================================

async function loadModels() {
    try {
        const response = await fetch('/api/models');
        const models = await response.json();

        const select = document.getElementById('modelSelect');
        select.innerHTML = models.length === 0
            ? '<option value="">No models available</option>'
            : '<option value="">Select a model...</option>';

        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.id;
            option.textContent = model.name;
            select.appendChild(option);
        });

        // Auto-select first model
        if (models.length > 0) {
            select.value = models[0].id;
            currentModelId = models[0].id;
            loadModelData();
        }
    } catch (error) {
        console.error('Failed to load models:', error);
        showToast('Failed to load models', 'error');
    }
}

async function loadModelData() {
    // Clean up resources from previous model
    stopAutoRefresh();
    disposeCharts();

    // FIX: Clean up trending data interval
    if (typeof cleanupTrendingData !== 'undefined') {
        cleanupTrendingData();
    }

    // Clear enhanced auto-refresh intervals
    if (typeof autoRefreshIntervals !== 'undefined') {
        Object.values(autoRefreshIntervals).forEach(id => clearInterval(id));
        autoRefreshIntervals = {};
    }

    // Load new model data
    await loadTradingMode();
    await loadDashboardData();

    // Restart auto-refresh with new model
    startAutoRefresh();
    if (typeof setupAutoRefresh !== 'undefined') {
        setupAutoRefresh();
    }
}

// ============================================
// MULTI-MODEL VIEW
// ============================================

async function showAllModelsView() {
    try {
        // Fetch aggregated data
        const response = await fetch('/api/aggregated/portfolio');
        if (!response.ok) {
            showToast('Failed to load aggregated data', 'error');
            return;
        }

        const data = await response.json();

        // Update metrics with aggregated totals
        updateDashboardAggregatedMetrics(data.portfolio);

        // Show multi-model chart
        await loadMultiModelChart(data.chart_data);

        showToast(`Showing ${data.model_count} models`, 'info');

    } catch (error) {
        console.error('Failed to load aggregated view:', error);
        showToast('Failed to load aggregated view', 'error');
    }
}

function updateDashboardAggregatedMetrics(portfolio) {
    const initialCapital = portfolio.initial_capital || 10000;
    const totalValue = portfolio.total_value || initialCapital;
    const totalPnL = totalValue - initialCapital;
    const totalPnLPct = (totalPnL / initialCapital) * 100;

    // Update Total Value
    document.getElementById('totalValue').textContent = formatCurrency(totalValue);
    const valueChange = totalValue - initialCapital;
    updateMetricChange('totalValueChange', valueChange, (valueChange / initialCapital) * 100);

    // Update Total P&L
    document.getElementById('totalPnL').textContent = formatCurrency(totalPnL);
    document.getElementById('totalPnLPercent').textContent = formatPercent(totalPnLPct);
    document.getElementById('totalPnLPercent').className = `metric-change ${totalPnL >= 0 ? 'positive' : 'negative'}`;

    // Update other metrics
    document.getElementById('todayPnL').textContent = 'N/A';
    document.getElementById('todayPnLPercent').textContent = '--';
    document.getElementById('winRate').textContent = 'N/A';
    document.getElementById('winRateDetails').textContent = 'Aggregated view';
    document.getElementById('totalTrades').textContent = 'N/A';
    document.getElementById('tradesBreakdown').textContent = 'See individual models';
    document.getElementById('openPositionsCount').textContent = portfolio.positions ? portfolio.positions.length : 0;
    document.getElementById('positionsValue').textContent = formatCurrency(portfolio.positions_value || 0);
}

async function loadMultiModelChart(chartData) {
    if (!chartData || chartData.length === 0) {
        console.warn('No chart data available for multi-model view');
        return;
    }

    // Ensure chart is initialized
    if (typeof echarts === 'undefined') {
        console.error('ECharts library not loaded');
        return;
    }

    const chartDom = document.getElementById('portfolioChart');
    if (!chartDom) return;

    // Dispose existing chart
    if (portfolioChart) {
        portfolioChart.dispose();
    }

    portfolioChart = echarts.init(chartDom);

    // Colors for different models
    const colors = [
        '#3370ff', '#ff6b35', '#00b96b', '#722ed1', '#fa8c16',
        '#eb2f96', '#13c2c2', '#faad14', '#f5222d', '#52c41a'
    ];

    // Prepare time axis - collect all unique timestamps
    const allTimestamps = new Set();
    chartData.forEach(model => {
        model.data.forEach(point => {
            allTimestamps.add(point.timestamp);
        });
    });

    // Sort timestamps
    const timeAxis = Array.from(allTimestamps).sort().map(ts => {
        const date = new Date(ts);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    });

    // Prepare series for each model
    const series = chartData.map((model, index) => {
        // Create a map of timestamp to value
        const dataMap = {};
        model.data.forEach(point => {
            dataMap[point.timestamp] = point.value;
        });

        // Fill in values for all timestamps (null if missing)
        const values = Array.from(allTimestamps).sort().map(ts => dataMap[ts] || null);

        return {
            name: model.model_name,
            type: 'line',
            data: values,
            smooth: true,
            lineStyle: { color: colors[index % colors.length], width: 2 },
            itemStyle: { color: colors[index % colors.length] }
        };
    });

    const option = {
        backgroundColor: 'transparent',
        tooltip: {
            trigger: 'axis',
            backgroundColor: '#1a1f2e',
            borderColor: '#3c4556',
            textStyle: { color: '#e8eaed' },
            formatter: function(params) {
                let result = `${params[0].axisValue}<br/>`;
                params.forEach(param => {
                    if (param.value !== null) {
                        result += `${param.marker}${param.seriesName}: $${param.value.toLocaleString()}<br/>`;
                    }
                });
                return result;
            }
        },
        legend: {
            data: chartData.map(m => m.model_name),
            textStyle: { color: '#e8eaed' },
            top: 10
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            top: '60px',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: timeAxis,
            axisLine: { lineStyle: { color: '#3c4556' } },
            axisLabel: { color: '#9aa0a6' }
        },
        yAxis: {
            type: 'value',
            scale: true,  // Dynamic scaling to show value changes more clearly
            axisLine: { lineStyle: { color: '#3c4556' } },
            axisLabel: {
                color: '#9aa0a6',
                formatter: '${value}'
            },
            splitLine: { lineStyle: { color: '#252d3d' } }
        },
        series: series
    };

    portfolioChart.setOption(option);
}

// ============================================
// MODELS PAGE
// ============================================

async function loadModelsPage() {
    try {
        const response = await fetch('/api/models/all-summary');
        if (!response.ok) {
            throw new Error('Failed to fetch models summary');
        }

        const data = await response.json();
        allModelsData = data.models || [];

        // Always show aggregated metrics (simplified - no toggle needed)
        if (allModelsData.length > 0 && data.aggregated) {
            updateAggregatedMetrics(data.aggregated);
            document.getElementById('aggregatedSection').style.display = 'block';
        } else {
            document.getElementById('aggregatedSection').style.display = 'none';
        }

        // Render models grid
        renderModelsGrid(allModelsData);

        console.log('✓ Loaded models page with', allModelsData.length, 'models');

    } catch (error) {
        console.error('Failed to load models page:', error);
        showToast('Failed to load models', 'error');
    }
}

function updateAggregatedMetrics(agg) {
    document.getElementById('aggTotalCapital').textContent = formatCurrency(agg.total_capital);
    document.getElementById('aggTotalValue').textContent = formatCurrency(agg.total_value);
    document.getElementById('aggTotalPnL').textContent = formatCurrency(agg.total_pnl);

    const pnlPercent = document.getElementById('aggTotalPnLPercent');
    const sign = agg.total_pnl >= 0 ? '+' : '';
    pnlPercent.textContent = `${sign}${agg.total_pnl_pct.toFixed(2)}%`;
    pnlPercent.className = `agg-metric-change ${agg.total_pnl >= 0 ? 'positive' : 'negative'}`;

    document.getElementById('aggActiveModels').textContent = `${agg.active_models}/${agg.total_models}`;
    document.getElementById('aggTotalTrades').textContent = agg.total_trades;
    document.getElementById('aggAvgWinRate').textContent = `${agg.avg_win_rate.toFixed(1)}%`;
}

function renderModelsGrid(models) {
    const grid = document.getElementById('modelsGrid');

    // Apply filter
    let filteredModels = models;
    if (modelsFilter === 'active') {
        filteredModels = models.filter(m => m.is_active);
    } else if (modelsFilter === 'paused') {
        filteredModels = models.filter(m => !m.is_active);
    }

    if (filteredModels.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-cpu"></i>
                <p>No models ${modelsFilter !== 'all' ? `(${modelsFilter})` : 'created yet'}</p>
                <button class="btn-primary" onclick="switchPage('settings'); setTimeout(() => document.getElementById('addModelBtn').click(), 100)">
                    Create Your First Model
                </button>
            </div>
        `;
        return;
    }

    grid.innerHTML = filteredModels.map(model => `
        <div class="model-card ${model.is_active ? '' : 'paused'}">
            <div class="model-header">
                <div class="model-title-section">
                    <div class="model-icon">${getModelIcon(model.model_name)}</div>
                    <div class="model-name">${model.name}</div>
                    <div class="model-provider">
                        ${model.provider_name} • ${model.model_name}
                    </div>
                </div>
                <span class="model-status-badge ${model.status}">
                    ${model.is_active ? '🟢 Active' : '⏸️ Paused'}
                </span>
            </div>

            <div class="model-stats">
                <div class="model-stat">
                    <div class="model-stat-label">Capital</div>
                    <div class="model-stat-value">${formatCurrencyShort(model.initial_capital)}</div>
                </div>
                <div class="model-stat">
                    <div class="model-stat-label">Current Value</div>
                    <div class="model-stat-value ${model.pnl >= 0 ? 'positive' : 'negative'}">
                        ${formatCurrencyShort(model.current_value)}
                    </div>
                </div>
                <div class="model-stat">
                    <div class="model-stat-label">P&L</div>
                    <div class="model-stat-value ${model.pnl >= 0 ? 'positive' : 'negative'}">
                        ${model.pnl >= 0 ? '+' : ''}${formatCurrencyShort(model.pnl)}
                    </div>
                    <div class="model-stat-subtitle">
                        ${model.pnl >= 0 ? '+' : ''}${model.pnl_pct.toFixed(2)}%
                    </div>
                </div>
                <div class="model-stat">
                    <div class="model-stat-label">Win Rate</div>
                    <div class="model-stat-value">${model.win_rate.toFixed(1)}%</div>
                    <div class="model-stat-subtitle">${model.wins}W / ${model.losses}L</div>
                </div>
            </div>

            <div class="model-metrics">
                <div class="model-metric">
                    <div class="model-metric-label">Trades</div>
                    <div class="model-metric-value">${model.total_trades}</div>
                </div>
                <div class="model-metric">
                    <div class="model-metric-label">Positions</div>
                    <div class="model-metric-value">${model.open_positions}</div>
                </div>
            </div>

            <div class="model-actions">
                <button class="model-action-btn primary" onclick="viewModelDashboard(${model.id})">
                    <i class="bi bi-eye"></i>
                    View
                </button>
                <button class="model-action-btn" onclick="editModelSettings(${model.id})">
                    <i class="bi bi-gear"></i>
                    Settings
                </button>
                <button class="model-action-btn ${model.is_active ? 'danger' : 'success'}" onclick="toggleModelStatus(${model.id}, ${model.is_active})">
                    <i class="bi bi-${model.is_active ? 'pause' : 'play'}-circle"></i>
                    ${model.is_active ? 'Pause' : 'Resume'}
                </button>
            </div>
        </div>
    `).join('');
}

function viewModelDashboard(modelId) {
    // Set the model in dropdown
    document.getElementById('modelSelect').value = modelId;

    // Trigger change event to load model data
    const event = new Event('change');
    document.getElementById('modelSelect').dispatchEvent(event);

    // Switch to dashboard page
    switchPage('dashboard');

    showToast(`Switched to Model ${modelId}`, 'success');
}

function editModelSettings(modelId) {
    switchPage('settings');
    showToast('Model settings - Coming soon!', 'info');
}

function toggleModelStatus(modelId, isCurrentlyActive) {
    const action = isCurrentlyActive ? 'pause' : 'resume';
    const actionText = isCurrentlyActive ? 'Paused' : 'Resumed';

    // TODO: Implement actual API call to pause/resume model
    showToast(`Model ${actionText} - Feature coming soon!`, 'info');

    // For now, just reload the page after a delay
    setTimeout(() => {
        loadModelsPage();
    }, 1000);
}

// Models Filter Handler
document.getElementById('modelsFilter')?.addEventListener('change', function() {
    modelsFilter = this.value;
    renderModelsGrid(allModelsData);
});

console.log('✓ Enhanced Models Module Loaded');

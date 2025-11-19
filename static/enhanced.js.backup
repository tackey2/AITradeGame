// Enhanced Dashboard JavaScript

let currentModelId = null;
let currentDecisionId = null;
let refreshInterval = null;
let trendingInterval = null;

// Initialize on page load - CONSOLIDATED from multiple listeners
document.addEventListener('DOMContentLoaded', () => {
    // Core initialization
    initializeApp();
    setupEventListeners();

    // Exchange credentials (from second listener)
    const modelSelect = document.getElementById('modelSelect');
    if (modelSelect) {
        modelSelect.addEventListener('change', function() {
            if (typeof loadExchangeCredentials !== 'undefined') {
                loadExchangeCredentials();
            }
        });
    }
    if (typeof initExchangeCredentials !== 'undefined') {
        initExchangeCredentials();
    }

    // Initialize provider/model management (from second listener)
    if (typeof initProviderManagement !== 'undefined') {
        initProviderManagement();
    }
    if (typeof initModelManagement !== 'undefined') {
        initModelManagement();
    }
    if (typeof initTrendingData !== 'undefined') {
        initTrendingData();
    }
    if (typeof initPasswordToggles !== 'undefined') {
        initPasswordToggles();
    }

    // Chart initialization (from third listener)
    if (document.getElementById('assetAllocationChart')) {
        if (typeof initAssetAllocationChart !== 'undefined') {
            initAssetAllocationChart();
        }
    }

    // Analytics setup (from third listener)
    if (typeof setupAnalyticsRefresh !== 'undefined') {
        setupAnalyticsRefresh();
    }
    if (typeof setupConversationFilters !== 'undefined') {
        setupConversationFilters();
    }

    // Start auto-refresh last
    startAutoRefresh();
});

function initializeApp() {
    loadModels();
}

function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            if (btn.hasAttribute('data-page')) {
                e.preventDefault();
                switchPage(btn.dataset.page);
            }
        });
    });

    // Model selector
    document.getElementById('modelSelect').addEventListener('change', (e) => {
        currentModelId = parseInt(e.target.value);
        if (currentModelId) {
            loadModelData();
        }
    });

    // Environment selection
    document.querySelectorAll('input[name="environment"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (currentModelId) {
                const newEnv = e.target.value;
                // Warn before switching to Live
                if (newEnv === 'live') {
                    showLiveWarning(() => {
                        setTradingEnvironment(newEnv);
                    }, () => {
                        // Cancelled - revert to simulation
                        document.getElementById('envSimulation').checked = true;
                    });
                } else {
                    setTradingEnvironment(newEnv);
                }
            }
        });
    });

    // Automation selection
    document.querySelectorAll('input[name="automation"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (currentModelId) {
                setAutomationLevel(e.target.value);
            }
        });
    });

    // Multi-model view toggle buttons
    const showAllBtn = document.getElementById('showAllModelsBtn');
    const showSingleBtn = document.getElementById('showSingleModelBtn');

    if (showAllBtn) {
        showAllBtn.addEventListener('click', () => {
            showAllModelsView();
            showAllBtn.style.display = 'none';
            showSingleBtn.style.display = 'inline-block';
        });
    }

    if (showSingleBtn) {
        showSingleBtn.addEventListener('click', () => {
            if (currentModelId) {
                loadModelData();
            }
            showSingleBtn.style.display = 'none';
            showAllBtn.style.display = 'inline-block';
        });
    }

    // Live warning modal
    document.getElementById('cancelLiveBtn').addEventListener('click', () => closeLiveWarning(false));
    document.getElementById('confirmLiveBtn').addEventListener('click', () => closeLiveWarning(true));

    // Action buttons
    document.getElementById('refreshBtn').addEventListener('click', () => refreshCurrentPage());
    document.getElementById('emergencyStopBtn').addEventListener('click', () => emergencyStopAll());
    document.getElementById('executeTradingBtn').addEventListener('click', () => executeTradingCycle());
    document.getElementById('pauseModelBtn').addEventListener('click', () => pauseModel());

    // Settings page
    document.getElementById('saveSettingsBtn').addEventListener('click', () => saveSettings());
    document.getElementById('resetSettingsBtn').addEventListener('click', () => loadSettings());
    document.getElementById('refreshIncidentsBtn').addEventListener('click', () => loadIncidents());

    // Modal
    document.getElementById('closeDecisionModal').addEventListener('click', () => closeModal());
    document.getElementById('approveDecisionBtn').addEventListener('click', () => approveDecision());
    document.getElementById('rejectDecisionBtn').addEventListener('click', () => rejectDecision());
    document.getElementById('modifyDecisionBtn').addEventListener('click', () => modifyDecision());
}

// Page Navigation
function switchPage(pageName) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));

    document.getElementById(`${pageName}Page`).classList.add('active');
    document.querySelector(`[data-page="${pageName}"]`).classList.add('active');

    // Load page-specific data
    if (currentModelId) {
        switch(pageName) {
            case 'dashboard':
                loadDashboardData();
                break;
            case 'settings':
                loadSettings();
                break;
            case 'readiness':
                loadReadinessAssessment();
                break;
            case 'incidents':
                loadIncidents();
                break;
        }
    }
}

function refreshCurrentPage() {
    const activePage = document.querySelector('.page.active');
    if (!activePage || !currentModelId) return;

    const pageName = activePage.id.replace('Page', '');
    switchPage(pageName);
    showToast('Refreshed');
}

// Auto-refresh
function startAutoRefresh() {
    // Clear existing interval first to prevent duplicates
    stopAutoRefresh();

    refreshInterval = setInterval(() => {
        if (currentModelId) {
            const activePage = document.querySelector('.page.active');
            if (activePage && activePage.id === 'dashboardPage') {
                // Refresh all dashboard data like classic view
                loadPendingDecisions();
                loadRiskStatus();
                loadPortfolioChartData(currentTimeRange); // Match classic view's 10-second refresh
                loadPortfolioMetrics();
                loadPositionsTable();
                loadAssetAllocation();
            }
        }
    }, 10000); // Every 10 seconds
}

function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

function disposeCharts() {
    // Dispose portfolio chart
    if (typeof portfolioChart !== 'undefined' && portfolioChart) {
        portfolioChart.dispose();
        portfolioChart = null;
    }

    // Dispose asset allocation chart
    if (typeof assetAllocationChart !== 'undefined' && assetAllocationChart) {
        assetAllocationChart.dispose();
        assetAllocationChart = null;
    }
}

// Load Models
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

// Load Model Data
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

// Show All Models View - Like Classic View's Aggregated Mode
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

// Update dashboard metrics for aggregated view
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

// Load Multi-Model Chart - Shows all models' trends
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

async function loadDashboardData() {
    // FIX: Use parallel loading like classic view for better performance
    try {
        // Load core data first (critical)
        await Promise.all([
            loadRiskStatus(),
            loadPendingDecisions()
        ]);

        // Load all dashboard features in parallel (faster!)
        await Promise.all([
            loadPortfolioMetrics().catch(e => console.error('Portfolio metrics:', e)),
            initPortfolioChart().catch(e => console.error('Portfolio chart:', e)),
            loadPositionsTable().catch(e => console.error('Positions:', e)),
            loadTradeHistory().catch(e => console.error('Trade history:', e)),
            updateMarketTicker().catch(e => console.error('Market ticker:', e)),
            loadAIConversations().catch(e => console.error('AI conversations:', e)),
            loadAssetAllocation().catch(e => console.error('Asset allocation:', e)),
            loadPerformanceAnalytics().catch(e => console.error('Performance analytics:', e)),
            (typeof loadTradeAnalytics === 'function' ? loadTradeAnalytics() : Promise.resolve()).catch(e => console.error('Trade analytics:', e)),
            (typeof loadModelSettingsWidget === 'function' ? loadModelSettingsWidget() : Promise.resolve()).catch(e => console.error('Model settings:', e)),
            (typeof loadGraduationStatus === 'function' ? loadGraduationStatus(currentModelId) : Promise.resolve()).catch(e => console.error('Graduation status:', e)),
            (typeof loadBenchmarkComparison === 'function' ? loadBenchmarkComparison(currentModelId) : Promise.resolve()).catch(e => console.error('Benchmark comparison:', e))
        ]);
    } catch (error) {
        console.error('Failed to load dashboard data:', error);
        showToast('Failed to load some dashboard data', 'error');
    }
}

// Trading Configuration (Environment + Automation)
async function loadTradingMode() {
    try {
        const response = await fetch(`/api/models/${currentModelId}/config`);
        if (!response.ok) {
            console.error(`Failed to load config: ${response.status}`);
            return;
        }
        const config = await response.json();

        const environment = config.environment || 'simulation';
        const automation = config.automation || 'manual';

        // Update environment radio buttons
        document.querySelectorAll('input[name="environment"]').forEach(radio => {
            radio.checked = radio.value === environment;
        });

        // Update automation radio buttons
        document.querySelectorAll('input[name="automation"]').forEach(radio => {
            radio.checked = radio.value === automation;
        });

        // Update header badge
        updateModeBadge(environment, automation);
    } catch (error) {
        console.error('Failed to load trading configuration:', error);
    }
}

async function setTradingEnvironment(environment) {
    try {
        const response = await fetch(`/api/models/${currentModelId}/environment`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ environment })
        });

        const data = await response.json();

        if (data.success) {
            // Reload to update badge
            await loadTradingMode();
            showToast(`Environment changed to ${formatEnvironmentName(environment)}`);
        } else {
            showToast(data.error || 'Failed to change environment', 'error');
            // Revert on failure
            await loadTradingMode();
        }
    } catch (error) {
        console.error('Failed to set trading environment:', error);
        showToast('Failed to change environment', 'error');
        // Revert on failure
        await loadTradingMode();
    }
}

async function setAutomationLevel(automation) {
    try {
        const response = await fetch(`/api/models/${currentModelId}/automation`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ automation })
        });

        const data = await response.json();

        if (data.success) {
            // Reload to update badge
            await loadTradingMode();
            showToast(`Automation changed to ${formatAutomationName(automation)}`);
        } else {
            showToast(data.error || 'Failed to change automation', 'error');
            // Revert on failure
            await loadTradingMode();
        }
    } catch (error) {
        console.error('Failed to set automation level:', error);
        showToast('Failed to change automation', 'error');
        // Revert on failure
        await loadTradingMode();
    }
}

function updateModeBadge(environment, automation) {
    const badge = document.getElementById('currentModeBadge');
    const envText = document.getElementById('currentEnvironmentText');
    const autoText = document.getElementById('currentAutomationText');
    const icon = badge.querySelector('.mode-icon');

    envText.textContent = formatEnvironmentName(environment);
    autoText.textContent = formatAutomationName(automation);

    // Update color based on combination
    if (environment === 'simulation') {
        icon.style.color = 'var(--color-info)';
    } else if (environment === 'live' && automation === 'manual') {
        icon.style.color = 'var(--color-info)';
    } else if (environment === 'live' && automation === 'semi_automated') {
        icon.style.color = 'var(--color-warning)';
    } else if (environment === 'live' && automation === 'fully_automated') {
        icon.style.color = 'var(--color-danger)';
    }
}

function formatEnvironmentName(environment) {
    const names = {
        'simulation': 'Simulation',
        'live': 'Live'
    };
    return names[environment] || environment;
}

function formatAutomationName(automation) {
    const names = {
        'manual': 'Manual',
        'semi_automated': 'Semi-Auto',
        'fully_automated': 'Full-Auto'
    };
    return names[automation] || automation;
}

// Risk Status
async function loadRiskStatus() {
    try {
        const response = await fetch(`/api/models/${currentModelId}/risk-status`);

        if (!response.ok) {
            console.warn('Risk status endpoint returned error:', response.status);
            // Don't show error to user, just skip updating risk cards
            return;
        }

        const risk = await response.json();

        // Check if response contains error
        if (risk.error) {
            console.warn('Risk status error:', risk.error);
            return;
        }

        // Update each risk card
        updateRiskCard('PositionSize', risk.position_size);
        updateRiskCard('DailyLoss', risk.daily_loss);
        updateRiskCard('OpenPositions', risk.open_positions);
        updateRiskCard('CashReserve', risk.cash_reserve);
        updateRiskCard('DailyTrades', risk.daily_trades);
    } catch (error) {
        console.error('Failed to load risk status:', error);
        // Don't block page loading
    }
}

function updateRiskCard(name, data) {
    const valueEl = document.getElementById(`risk${name}`);
    const statusEl = document.getElementById(`status${name}`);
    const progressEl = document.getElementById(`progress${name}`);

    if (!valueEl || !statusEl || !data) return;

    // Format value based on type and calculate percentage for progress bar
    let value = '';
    let percentage = 0;

    if (data.usage_pct !== undefined) {
        value = `${data.usage_pct.toFixed(1)}%`;
        percentage = data.usage_pct;
    } else if (data.current_pct !== undefined) {
        value = `${data.current_pct.toFixed(1)}%`;
        percentage = data.current_pct;
    } else if (data.current !== undefined) {
        value = data.current.toString();
        // For count-based metrics, calculate percentage if limit available
        if (data.limit && data.limit > 0) {
            percentage = (data.current / data.limit) * 100;
        } else {
            // Default visualization for counts without limits
            percentage = Math.min((data.current / 10) * 100, 100);
        }
    }

    valueEl.textContent = value;

    // Update status
    statusEl.textContent = data.status.toUpperCase();
    statusEl.className = 'risk-status';
    statusEl.classList.add(`status-${data.status}`);

    // Update progress bar if element exists
    if (progressEl) {
        // Clamp percentage between 0 and 100
        percentage = Math.max(0, Math.min(100, percentage));

        // Set width
        progressEl.style.width = `${percentage}%`;

        // Set color based on status
        let color;
        if (data.status === 'ok') {
            color = '#4caf50'; // Green
        } else if (data.status === 'warning') {
            color = '#ff9800'; // Orange
        } else if (data.status === 'danger') {
            color = '#f44336'; // Red
        } else {
            color = '#2196f3'; // Blue (default)
        }

        progressEl.style.backgroundColor = color;

        // Add animation
        progressEl.style.transition = 'width 0.5s ease, background-color 0.3s ease';
    }
}

// Pending Decisions
async function loadPendingDecisions() {
    try {
        const response = await fetch(`/api/pending-decisions?model_id=${currentModelId}`);
        const decisions = await response.json();

        const container = document.getElementById('pendingDecisionsContainer');
        const countBadge = document.getElementById('pendingCount');

        countBadge.textContent = decisions.length;

        if (decisions.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-inbox"></i>
                    <p>No pending decisions</p>
                </div>
            `;
            // Monitor for notifications
            if (typeof monitorPendingDecisions === 'function') {
                monitorPendingDecisions(decisions);
            }
            return;
        }

        container.innerHTML = decisions.map(decision => renderDecisionCard(decision)).join('');

        // Add event listeners to decision cards
        document.querySelectorAll('.decision-card').forEach(card => {
            card.addEventListener('click', () => {
                const decisionId = parseInt(card.dataset.decisionId);
                showDecisionDetail(decisionId);
            });
        });

        // Monitor pending decisions for notifications
        if (typeof monitorPendingDecisions === 'function') {
            monitorPendingDecisions(decisions);
        }
    } catch (error) {
        console.error('Failed to load pending decisions:', error);
    }
}

function renderDecisionCard(decision) {
    const data = decision.decision_data;
    const signalClass = data.signal.includes('buy') ? 'signal-buy' : 'signal-sell';

    return `
        <div class="decision-card" data-decision-id="${decision.id}">
            <div class="decision-header">
                <div class="decision-coin">${decision.coin}</div>
                <div class="decision-signal ${signalClass}">${formatSignal(data.signal)}</div>
            </div>
            <div class="decision-details">
                <div class="decision-detail">
                    <div class="decision-detail-label">Quantity</div>
                    <div class="decision-detail-value">${data.quantity}</div>
                </div>
                <div class="decision-detail">
                    <div class="decision-detail-label">Leverage</div>
                    <div class="decision-detail-value">${data.leverage}x</div>
                </div>
                <div class="decision-detail">
                    <div class="decision-detail-label">Confidence</div>
                    <div class="decision-detail-value">${(data.confidence * 100).toFixed(0)}%</div>
                </div>
            </div>
            <div class="decision-justification">
                ${data.justification || 'No justification provided'}
            </div>
            <div class="decision-expires">
                Created: ${formatTimestamp(decision.created_at)}
            </div>
        </div>
    `;
}

function formatSignal(signal) {
    const signals = {
        'buy_to_enter': 'Buy to Enter',
        'buy_to_exit': 'Buy to Exit',
        'sell_to_enter': 'Sell to Enter',
        'sell_to_exit': 'Sell to Exit',
        'hold': 'Hold'
    };
    return signals[signal] || signal;
}

function formatTimestamp(timestamp) {
    return new Date(timestamp).toLocaleString();
}

// Decision Detail Modal
async function showDecisionDetail(decisionId) {
    try {
        const response = await fetch(`/api/pending-decisions`);
        const decisions = await response.json();
        const decision = decisions.find(d => d.id === decisionId);

        if (!decision) {
            showToast('Decision not found', 'error');
            return;
        }

        currentDecisionId = decisionId;

        const data = decision.decision_data;
        const explanation = decision.explanation_data || {};

        const modalBody = document.getElementById('decisionModalBody');
        modalBody.innerHTML = `
            <div style="margin-bottom: 20px;">
                <h3>${decision.coin} - ${formatSignal(data.signal)}</h3>
            </div>

            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 20px;">
                <div>
                    <div style="color: var(--text-secondary); margin-bottom: 4px;">Quantity</div>
                    <div style="font-weight: 600;">${data.quantity}</div>
                </div>
                <div>
                    <div style="color: var(--text-secondary); margin-bottom: 4px;">Leverage</div>
                    <div style="font-weight: 600;">${data.leverage}x</div>
                </div>
                <div>
                    <div style="color: var(--text-secondary); margin-bottom: 4px;">Confidence</div>
                    <div style="font-weight: 600;">${(data.confidence * 100).toFixed(0)}%</div>
                </div>
                <div>
                    <div style="color: var(--text-secondary); margin-bottom: 4px;">Created</div>
                    <div style="font-weight: 600;">${formatTimestamp(decision.created_at)}</div>
                </div>
            </div>

            ${data.profit_target ? `
                <div style="margin-bottom: 12px;">
                    <div style="color: var(--text-secondary); margin-bottom: 4px;">Profit Target</div>
                    <div style="font-weight: 600;">$${data.profit_target.toFixed(2)}</div>
                </div>
            ` : ''}

            ${data.stop_loss ? `
                <div style="margin-bottom: 12px;">
                    <div style="color: var(--text-secondary); margin-bottom: 4px;">Stop Loss</div>
                    <div style="font-weight: 600;">$${data.stop_loss.toFixed(2)}</div>
                </div>
            ` : ''}

            <div style="margin-bottom: 20px;">
                <h4 style="margin-bottom: 12px;">Justification</h4>
                <div style="padding: 12px; background: var(--bg-primary); border-radius: 6px;">
                    ${data.justification || 'No justification provided'}
                </div>
            </div>

            ${explanation.decision_summary ? `
                <div style="margin-bottom: 20px;">
                    <h4 style="margin-bottom: 12px;">AI Explanation</h4>
                    <div style="padding: 12px; background: var(--bg-primary); border-radius: 6px;">
                        ${explanation.decision_summary}
                    </div>
                </div>
            ` : ''}

            ${explanation.market_analysis ? `
                <div style="margin-bottom: 20px;">
                    <h4 style="margin-bottom: 12px;">Market Analysis</h4>
                    <div style="padding: 12px; background: var(--bg-primary); border-radius: 6px; white-space: pre-wrap;">
                        ${typeof explanation.market_analysis === 'object'
                            ? JSON.stringify(explanation.market_analysis, null, 2)
                            : explanation.market_analysis}
                    </div>
                </div>
            ` : ''}
        `;

        document.getElementById('decisionModal').classList.add('active');
    } catch (error) {
        console.error('Failed to load decision detail:', error);
        showToast('Failed to load decision details', 'error');
    }
}

function closeModal() {
    document.getElementById('decisionModal').classList.remove('active');
    currentDecisionId = null;
}

async function approveDecision() {
    if (!currentDecisionId) return;

    try {
        const response = await fetch(`/api/pending-decisions/${currentDecisionId}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ modified: false })
        });

        const result = await response.json();

        if (result.success || response.ok) {
            showToast('Decision approved and executed');
            closeModal();
            loadPendingDecisions();
        } else {
            showToast(result.error || 'Failed to approve decision', 'error');
        }
    } catch (error) {
        console.error('Failed to approve decision:', error);
        showToast('Failed to approve decision', 'error');
    }
}

async function rejectDecision() {
    if (!currentDecisionId) return;

    const reason = prompt('Reason for rejection (optional):');

    try {
        const response = await fetch(`/api/pending-decisions/${currentDecisionId}/reject`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reason: reason || 'User rejected' })
        });

        const result = await response.json();

        if (result.success || response.ok) {
            showToast('Decision rejected');
            closeModal();
            loadPendingDecisions();
        } else {
            showToast(result.error || 'Failed to reject decision', 'error');
        }
    } catch (error) {
        console.error('Failed to reject decision:', error);
        showToast('Failed to reject decision', 'error');
    }
}

function modifyDecision() {
    showToast('Modify feature coming soon', 'info');
}

// Settings
async function loadSettings() {
    try {
        const response = await fetch(`/api/models/${currentModelId}/settings`);
        const settings = await response.json();

        document.getElementById('maxPositionSizePct').value = settings.max_position_size_pct || 10.0;
        document.getElementById('maxDailyLossPct').value = settings.max_daily_loss_pct || 3.0;
        document.getElementById('maxDailyTrades').value = settings.max_daily_trades || 20;
        document.getElementById('maxOpenPositions').value = settings.max_open_positions || 5;
        document.getElementById('minCashReservePct').value = settings.min_cash_reserve_pct || 20.0;
        document.getElementById('maxDrawdownPct').value = settings.max_drawdown_pct || 15.0;
        document.getElementById('tradingIntervalMinutes').value = settings.trading_interval_minutes || 60;
    } catch (error) {
        console.error('Failed to load settings:', error);
        showToast('Failed to load settings', 'error');
    }
}

async function saveSettings() {
    try {
        const settings = {
            max_position_size_pct: parseFloat(document.getElementById('maxPositionSizePct').value),
            max_daily_loss_pct: parseFloat(document.getElementById('maxDailyLossPct').value),
            max_daily_trades: parseInt(document.getElementById('maxDailyTrades').value),
            max_open_positions: parseInt(document.getElementById('maxOpenPositions').value),
            min_cash_reserve_pct: parseFloat(document.getElementById('minCashReservePct').value),
            max_drawdown_pct: parseFloat(document.getElementById('maxDrawdownPct').value),
            trading_interval_minutes: parseInt(document.getElementById('tradingIntervalMinutes').value)
        };

        const response = await fetch(`/api/models/${currentModelId}/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });

        const result = await response.json();

        if (result.success) {
            showToast('Settings saved successfully');
        } else {
            showToast(result.error || 'Failed to save settings', 'error');
        }
    } catch (error) {
        console.error('Failed to save settings:', error);
        showToast('Failed to save settings', 'error');
    }
}

// Readiness Assessment
async function loadReadinessAssessment() {
    try {
        const response = await fetch(`/api/models/${currentModelId}/readiness`);
        const readiness = await response.json();

        document.getElementById('scoreValue').textContent = readiness.score || 0;
        document.getElementById('scoreMessage').textContent = readiness.message || 'Loading...';

        // Update circle color based on score
        const circle = document.getElementById('scoreCircle');
        if (readiness.ready) {
            circle.style.borderColor = 'var(--color-success)';
        } else if (readiness.score >= 50) {
            circle.style.borderColor = 'var(--color-warning)';
        } else {
            circle.style.borderColor = 'var(--color-danger)';
        }

        // Update metrics
        const metrics = readiness.metrics || {};
        document.getElementById('metricTotalTrades').textContent = metrics.total_trades || 0;
        document.getElementById('metricWinRate').textContent = metrics.win_rate ? `${metrics.win_rate.toFixed(1)}%` : '--';
        document.getElementById('metricApprovalRate').textContent = metrics.approval_rate ? `${metrics.approval_rate.toFixed(1)}%` : '--';
        document.getElementById('metricModificationRate').textContent = metrics.modification_rate ? `${metrics.modification_rate.toFixed(1)}%` : '--';
        document.getElementById('metricRiskViolations').textContent = metrics.risk_violations || 0;
        document.getElementById('metricTotalReturn').textContent = metrics.total_return ? `${metrics.total_return.toFixed(2)}%` : '--';
        document.getElementById('metricReturnVolatility').textContent = metrics.return_volatility ? `${metrics.return_volatility.toFixed(2)}%` : '--';
    } catch (error) {
        console.error('Failed to load readiness assessment:', error);
        showToast('Failed to load readiness assessment', 'error');
    }
}

// Incidents
async function loadIncidents() {
    try {
        const response = await fetch(`/api/models/${currentModelId}/incidents?limit=50`);
        const incidents = await response.json();

        const container = document.getElementById('incidentsContainer');

        if (incidents.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-shield-check"></i>
                    <p>No incidents</p>
                </div>
            `;
            return;
        }

        container.innerHTML = incidents.map(incident => `
            <div class="incident-item severity-${incident.severity}">
                <div class="incident-header">
                    <div class="incident-type">${incident.incident_type.replace(/_/g, ' ')}</div>
                    <div class="incident-time">${formatTimestamp(incident.timestamp)}</div>
                </div>
                <div class="incident-message">${incident.message}</div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load incidents:', error);
        showToast('Failed to load incidents', 'error');
    }
}

// Actions
async function executeTradingCycle() {
    try {
        showToast('Executing trading cycle...');

        const response = await fetch(`/api/models/${currentModelId}/execute-enhanced`, {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            showToast('Trading cycle executed');
            loadPendingDecisions();
        } else {
            showToast(result.error || 'Failed to execute trading cycle', 'error');
        }
    } catch (error) {
        console.error('Failed to execute trading cycle:', error);
        showToast('Failed to execute trading cycle', 'error');
    }
}

async function pauseModel() {
    if (!confirm('Pause this model? (switches automation to manual)')) return;

    try {
        // Set automation to manual
        const response = await fetch(`/api/models/${currentModelId}/automation`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ automation: 'manual' })
        });

        const result = await response.json();

        if (result.success) {
            showToast('Model paused (switched to manual)');
            loadTradingMode();
        } else {
            showToast(result.error || 'Failed to pause model', 'error');
        }
    } catch (error) {
        console.error('Failed to pause model:', error);
        showToast('Failed to pause model', 'error');
    }
}

async function emergencyStopAll() {
    if (!confirm('EMERGENCY STOP ALL MODELS? This will switch all models to simulation mode.')) return;

    try {
        const response = await fetch('/api/emergency-stop-all', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reason: 'User-initiated emergency stop' })
        });

        const result = await response.json();

        if (result.success) {
            showToast(`Emergency stop: ${result.switched_count} models stopped`);
            loadTradingMode();
        } else {
            showToast('Failed to stop models', 'error');
        }
    } catch (error) {
        console.error('Failed to emergency stop:', error);
        showToast('Failed to emergency stop', 'error');
    }
}

// Live Warning Modal
let liveWarningCallback = null;
let liveWarningCancelCallback = null;

function showLiveWarning(onConfirm, onCancel) {
    liveWarningCallback = onConfirm;
    liveWarningCancelCallback = onCancel;
    document.getElementById('liveWarningModal').classList.add('active');
}

function closeLiveWarning(confirmed) {
    document.getElementById('liveWarningModal').classList.remove('active');

    if (confirmed && liveWarningCallback) {
        liveWarningCallback();
    } else if (!confirmed && liveWarningCancelCallback) {
        liveWarningCancelCallback();
    }

    liveWarningCallback = null;
    liveWarningCancelCallback = null;
}

// Toast Notification
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');

    toastMessage.textContent = message;
    toast.classList.add('active');

    setTimeout(() => {
        toast.classList.remove('active');
    }, 3000);
}

// ============ Exchange Credentials Management ============

// Load exchange credentials status
async function loadExchangeCredentials() {
    if (!currentModelId) return;

    try {
        const response = await fetch(`/api/models/${currentModelId}/exchange/credentials`);
        const data = await response.json();

        // Update status indicators
        const statusIndicator = document.getElementById('exchangeStatusIndicator');
        const statusText = document.getElementById('exchangeStatusText');
        const mainnetBadge = document.getElementById('mainnetStatusBadge');
        const testnetBadge = document.getElementById('testnetStatusBadge');
        const lastValidated = document.getElementById('lastValidatedText');

        if (data.configured) {
            statusIndicator.className = 'status-indicator status-ok';
            statusText.textContent = 'Configured';

            mainnetBadge.textContent = data.has_mainnet ? 'Configured' : 'Not Set';
            mainnetBadge.className = data.has_mainnet ? 'status-badge badge-ok' : 'status-badge badge-error';

            testnetBadge.textContent = data.has_testnet ? 'Configured' : 'Not Set';
            testnetBadge.className = data.has_testnet ? 'status-badge badge-ok' : 'status-badge badge-error';

            if (data.last_validated) {
                const date = new Date(data.last_validated);
                lastValidated.textContent = date.toLocaleString();
            } else {
                lastValidated.textContent = 'Never';
            }
        } else {
            statusIndicator.className = 'status-indicator status-inactive';
            statusText.textContent = 'Not Configured';
            mainnetBadge.textContent = 'Not Set';
            mainnetBadge.className = 'status-badge badge-error';
            testnetBadge.textContent = 'Not Set';
            testnetBadge.className = 'status-badge badge-error';
            lastValidated.textContent = 'Never';
        }

        // Load exchange environment
        const configResponse = await fetch(`/api/models/${currentModelId}/config`);
        const config = await configResponse.json();

        const exchangeEnv = config.exchange_environment || 'testnet';
        document.getElementById(`exchangeEnv${exchangeEnv.charAt(0).toUpperCase() + exchangeEnv.slice(1)}`).checked = true;

    } catch (error) {
        console.error('Failed to load exchange credentials:', error);
    }
}

// Save exchange credentials
async function saveExchangeCredentials() {
    if (!currentModelId) {
        showToast('Please select a model first', 'error');
        return;
    }

    const mainnetApiKey = document.getElementById('mainnetApiKey').value.trim();
    const mainnetApiSecret = document.getElementById('mainnetApiSecret').value.trim();
    const testnetApiKey = document.getElementById('testnetApiKey').value.trim();
    const testnetApiSecret = document.getElementById('testnetApiSecret').value.trim();

    // At least one set of credentials must be provided
    if (!mainnetApiKey && !testnetApiKey) {
        showToast('Please enter at least testnet or mainnet credentials', 'error');
        return;
    }

    // Validate paired credentials
    if ((mainnetApiKey && !mainnetApiSecret) || (!mainnetApiKey && mainnetApiSecret)) {
        showToast('Both mainnet API key and secret are required', 'error');
        return;
    }

    if ((testnetApiKey && !testnetApiSecret) || (!testnetApiKey && testnetApiSecret)) {
        showToast('Both testnet API key and secret are required', 'error');
        return;
    }

    try {
        const payload = {
            exchange_type: 'binance'
        };

        // Add mainnet credentials if provided
        if (mainnetApiKey && mainnetApiSecret) {
            payload.api_key = mainnetApiKey;
            payload.api_secret = mainnetApiSecret;
        } else {
            // Use placeholder if not provided but testnet is
            payload.api_key = 'not_configured';
            payload.api_secret = 'not_configured';
        }

        // Add testnet credentials if provided
        if (testnetApiKey && testnetApiSecret) {
            payload.testnet_api_key = testnetApiKey;
            payload.testnet_api_secret = testnetApiSecret;
        }

        const response = await fetch(`/api/models/${currentModelId}/exchange/credentials`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (result.success) {
            showToast('✅ Exchange credentials saved successfully');

            // Clear sensitive input fields
            document.getElementById('mainnetApiKey').value = '';
            document.getElementById('mainnetApiSecret').value = '';
            document.getElementById('testnetApiKey').value = '';
            document.getElementById('testnetApiSecret').value = '';

            // Reload status
            loadExchangeCredentials();
        } else {
            showToast(`Failed to save credentials: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Failed to save credentials:', error);
        showToast('Failed to save credentials', 'error');
    }
}

// Validate exchange credentials
async function validateExchangeCredentials() {
    if (!currentModelId) {
        showToast('Please select a model first', 'error');
        return;
    }

    const validateBtn = document.getElementById('validateCredentialsBtn');
    const originalText = validateBtn.innerHTML;

    validateBtn.disabled = true;
    validateBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Validating...';

    try {
        const response = await fetch(`/api/models/${currentModelId}/exchange/validate`, {
            method: 'POST'
        });

        const result = await response.json();

        if (result.valid) {
            showToast('✅ Credentials validated successfully!');
            loadExchangeCredentials(); // Reload to show updated validation time
        } else {
            showToast('❌ Credential validation failed. Please check your API keys.', 'error');
        }
    } catch (error) {
        console.error('Failed to validate credentials:', error);
        showToast('Failed to validate credentials', 'error');
    } finally {
        validateBtn.disabled = false;
        validateBtn.innerHTML = originalText;
    }
}

// Delete exchange credentials
async function deleteExchangeCredentials() {
    if (!currentModelId) {
        showToast('Please select a model first', 'error');
        return;
    }

    if (!confirm('Are you sure you want to delete all exchange credentials for this model? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`/api/models/${currentModelId}/exchange/credentials`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            showToast('🗑️ Exchange credentials deleted');

            // Clear input fields
            document.getElementById('mainnetApiKey').value = '';
            document.getElementById('mainnetApiSecret').value = '';
            document.getElementById('testnetApiKey').value = '';
            document.getElementById('testnetApiSecret').value = '';

            // Reload status
            loadExchangeCredentials();
        } else {
            showToast(`Failed to delete credentials: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Failed to delete credentials:', error);
        showToast('Failed to delete credentials', 'error');
    }
}

// Set exchange environment (testnet/mainnet)
async function setExchangeEnvironment(environment) {
    if (!currentModelId) return;

    try {
        const response = await fetch(`/api/models/${currentModelId}/exchange/environment`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ exchange_environment: environment })
        });

        const result = await response.json();

        if (result.success) {
            showToast(`Exchange environment set to ${environment}`);
        } else {
            showToast(`Failed to set exchange environment: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Failed to set exchange environment:', error);
        showToast('Failed to set exchange environment', 'error');
    }
}

// Toggle password visibility
function togglePasswordVisibility(targetId) {
    const input = document.getElementById(targetId);
    const button = event.target.closest('.toggle-visibility');
    const icon = button.querySelector('i');

    if (input.type === 'password') {
        input.type = 'text';
        icon.className = 'bi bi-eye-slash';
    } else {
        input.type = 'password';
        icon.className = 'bi bi-eye';
    }
}

// Initialize exchange credentials listeners
function initExchangeCredentials() {
    // Save credentials button
    document.getElementById('saveCredentialsBtn')?.addEventListener('click', saveExchangeCredentials);

    // Validate credentials button
    document.getElementById('validateCredentialsBtn')?.addEventListener('click', validateExchangeCredentials);

    // Delete credentials button
    document.getElementById('deleteCredentialsBtn')?.addEventListener('click', deleteExchangeCredentials);

    // Exchange environment radio buttons
    document.querySelectorAll('input[name="exchangeEnv"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            setExchangeEnvironment(e.target.value);
        });
    });

    // Password visibility toggles
    document.querySelectorAll('.toggle-visibility').forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            togglePasswordVisibility(targetId);
        });
    });

    // Load initial status
    loadExchangeCredentials();
}

// Add to initialization
const originalInit = window.addEventListener('DOMContentLoaded', function() {
    // ... existing init code ...
});

// Add exchange credentials init after model selection
const originalModelSelect = document.getElementById('modelSelect')?.addEventListener('change', function() {
    // ... existing model select code ...
});

// REMOVED: Duplicate DOMContentLoaded listener - consolidated at line 8

// ===================================================
//      AI Provider Management
// ===================================================

let providers = [];

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

// ===================================================
//      Model Management
// ===================================================

let models = [];

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

// ===================================================
//      Trending Data
// ===================================================

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

// ===================================================
//      Password Visibility Toggles
// ===================================================

function initPasswordToggles() {
    document.querySelectorAll('.toggle-visibility').forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const input = document.getElementById(targetId);

            if (input.type === 'password') {
                input.type = 'text';
                this.innerHTML = '<i class="bi bi-eye-slash"></i>';
            } else {
                input.type = 'password';
                this.innerHTML = '<i class="bi bi-eye"></i>';
            }
        });
    });
}

// ========================================
// NEW DASHBOARD FEATURES - Session 1
// ========================================

// Global variables for dashboard
let portfolioChart = null;
let currentTimeRange = '24h';
let tradesCurrentPage = 1;
let tradesPerPage = 10;
let autoRefreshIntervals = {};

// Load Portfolio Metrics
async function loadPortfolioMetrics() {
    if (!currentModelId) return;

    try {
        // Simplified approach like classic view - use basic portfolio endpoint
        const [portfolioResp, modelResp, tradesResp] = await Promise.all([
            fetch(`/api/models/${currentModelId}/portfolio`),
            fetch(`/api/models/${currentModelId}`),
            fetch(`/api/models/${currentModelId}/trades?limit=1000`)
        ]);

        if (!portfolioResp.ok) {
            console.error(`Portfolio endpoint failed: ${portfolioResp.status}`);
            document.getElementById('totalValue').textContent = 'Error loading';
            document.getElementById('totalPnL').textContent = 'Error loading';
            document.getElementById('todayPnL').textContent = 'Error loading';
            showToast('Failed to load portfolio data', 'error');
            return;
        }

        const data = await portfolioResp.json();
        const portfolio = data.portfolio;
        const model = await modelResp.json();
        const trades = await tradesResp.json();

        const initialCapital = model.initial_capital || 10000;
        const totalValue = portfolio.total_value || initialCapital;
        const totalPnL = totalValue - initialCapital;
        const totalPnLPct = (totalPnL / initialCapital) * 100;

        // Calculate win rate and trades
        const totalTrades = trades.length;
        const wins = trades.filter(t => t.pnl > 0).length;
        const winRate = totalTrades > 0 ? (wins / totalTrades) * 100 : 0;

        // Calculate today's P&L from trades
        const today = new Date().toISOString().split('T')[0];
        const todayTrades = trades.filter(t => t.exit_time && t.exit_time.startsWith(today));
        const todayPnL = todayTrades.reduce((sum, t) => sum + (t.pnl || 0), 0);
        const todayPnLPct = totalValue > 0 ? (todayPnL / totalValue) * 100 : 0;

        // Update UI - Total Value
        document.getElementById('totalValue').textContent = formatCurrency(totalValue);
        const valueChange = totalValue - initialCapital;
        updateMetricChange('totalValueChange', valueChange, (valueChange / initialCapital) * 100);

        // Update Total P&L
        document.getElementById('totalPnL').textContent = formatCurrency(totalPnL);
        document.getElementById('totalPnLPercent').textContent = formatPercent(totalPnLPct);
        document.getElementById('totalPnLPercent').className = `metric-change ${totalPnL >= 0 ? 'positive' : 'negative'}`;

        // Update Today's P&L
        document.getElementById('todayPnL').textContent = formatCurrency(todayPnL);
        document.getElementById('todayPnLPercent').textContent = formatPercent(todayPnLPct);
        document.getElementById('todayPnLPercent').className = `metric-change ${todayPnL >= 0 ? 'positive' : 'negative'}`;

        // Update Win Rate
        document.getElementById('winRate').textContent = `${winRate.toFixed(1)}%`;
        document.getElementById('winRateDetails').textContent = `${wins} wins / ${totalTrades} trades`;

        // Update Total Trades
        document.getElementById('totalTrades').textContent = totalTrades;
        document.getElementById('tradesBreakdown').textContent = `${wins} wins, ${totalTrades - wins} losses`;

        // Update Open Positions
        const openPositions = portfolio.positions ? portfolio.positions.length : 0;
        document.getElementById('openPositionsCount').textContent = openPositions;
        document.getElementById('positionsValue').textContent = formatCurrency(portfolio.positions_value || 0);

    } catch (error) {
        console.error('Failed to load portfolio metrics:', error);
        showToast('Failed to load portfolio data', 'error');
    }
}

// Helper to update metric change display
function updateMetricChange(elementId, value, percent) {
    const el = document.getElementById(elementId);
    const sign = value >= 0 ? '+' : '';
    el.textContent = `${sign}${formatCurrency(value)} (${sign}${percent.toFixed(2)}%)`;
    el.className = `metric-change ${value >= 0 ? 'positive' : 'negative'}`;
}

// Initialize Portfolio Chart
async function initPortfolioChart() {
    if (!currentModelId) return;

    // Safety check: Ensure ECharts library is loaded
    if (typeof echarts === 'undefined') {
        console.error('ECharts library not loaded yet. Retrying in 500ms...');
        setTimeout(initPortfolioChart, 500);
        return;
    }

    const chartDom = document.getElementById('portfolioChart');
    if (!chartDom) return;

    // Dispose existing chart first to prevent memory leak
    if (portfolioChart) {
        portfolioChart.dispose();
    }

    // Initialize chart
    portfolioChart = echarts.init(chartDom);

    // Load initial data
    await loadPortfolioChartData(currentTimeRange);

    // Setup time range buttons
    document.querySelectorAll('.time-range-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            document.querySelectorAll('.time-range-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentTimeRange = btn.dataset.range;
            await loadPortfolioChartData(currentTimeRange);
        });
    });
}

// Load Portfolio Chart Data - Simplified like Classic View
async function loadPortfolioChartData(range) {
    if (!currentModelId || !portfolioChart) return;

    try {
        // Use simple portfolio endpoint which includes account_value_history
        // Pass the range parameter to filter data by time
        const url = range && range !== 'all'
            ? `/api/models/${currentModelId}/portfolio?range=${range}`
            : `/api/models/${currentModelId}/portfolio`;
        const response = await fetch(url);
        if (!response.ok) {
            console.warn('Portfolio endpoint failed');
            return;
        }

        const data = await response.json();
        const history = data.account_value_history || [];

        if (history.length === 0) {
            console.warn('No historical data available');
            return;
        }

        // Add current value to history
        const currentValue = data.portfolio.total_value;
        const chartData = [...history];

        // Format data for chart
        const timestamps = chartData.map(h => {
            const date = new Date(h.timestamp);
            return date.toLocaleString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        });

        const values = chartData.map(h => h.total_value);

        // Add current value if we have it
        if (currentValue && values.length > 0) {
            timestamps.push('Now');
            values.push(currentValue);
        }

        const firstValue = values[0];
        const lastValue = values[values.length - 1];
        const isProfit = lastValue >= firstValue;

        const option = {
            backgroundColor: 'transparent',
            tooltip: {
                trigger: 'axis',
                backgroundColor: '#1a1f2e',
                borderColor: '#3c4556',
                textStyle: { color: '#e8eaed' },
                formatter: function(params) {
                    const point = params[0];
                    return `${point.axisValue}<br/>Value: $${point.value.toLocaleString()}`;
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                top: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: timestamps,
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
            series: [{
                data: values,
                type: 'line',
                smooth: true,
                lineStyle: {
                    color: isProfit ? '#4caf50' : '#f44336',
                    width: 2
                },
                areaStyle: {
                    color: {
                        type: 'linear',
                        x: 0, y: 0, x2: 0, y2: 1,
                        colorStops: [{
                            offset: 0,
                            color: isProfit ? 'rgba(76, 175, 80, 0.3)' : 'rgba(244, 67, 54, 0.3)'
                        }, {
                            offset: 1,
                            color: 'rgba(0, 0, 0, 0)'
                        }]
                    }
                },
                itemStyle: {
                    color: isProfit ? '#4caf50' : '#f44336'
                }
            }]
        };

        portfolioChart.setOption(option);

    } catch (error) {
        console.error('Failed to load portfolio chart data:', error);
    }
}

// Load Positions Table
async function loadPositionsTable() {
    if (!currentModelId) return;

    try {
        const response = await fetch(`/api/models/${currentModelId}/portfolio`);
        if (!response.ok) return;

        const data = await response.json();
        const positions = data.portfolio.positions || [];

        const tbody = document.getElementById('positionsTableBody');

        if (positions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No open positions</td></tr>';
            return;
        }

        tbody.innerHTML = positions.map(pos => {
            const pnl = pos.unrealized_pnl || 0;
            const pnlPct = pos.unrealized_pnl_pct || 0;
            const pnlClass = pnl >= 0 ? 'pnl-positive' : 'pnl-negative';

            return `
                <tr>
                    <td><strong>${pos.coin}</strong></td>
                    <td>${pos.amount.toFixed(4)}</td>
                    <td>$${pos.avg_buy_price.toFixed(2)}</td>
                    <td>$${pos.current_price.toFixed(2)}</td>
                    <td class="${pnlClass}">
                        ${pnl >= 0 ? '+' : ''}$${pnl.toFixed(2)}<br>
                        <small>(${pnl >= 0 ? '+' : ''}${pnlPct.toFixed(2)}%)</small>
                    </td>
                    <td>
                        <button class="btn-secondary btn-small" onclick="closePosition('${pos.coin}')">
                            Close
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

    } catch (error) {
        console.error('Failed to load positions:', error);
    }
}

// Load Trade History
async function loadTradeHistory(page = 1) {
    if (!currentModelId) return;

    tradesCurrentPage = page;

    try {
        const response = await fetch(`/api/models/${currentModelId}/trades?limit=1000`);
        if (!response.ok) {
            console.error(`Failed to load trades: ${response.status} ${response.statusText}`);
            const tbody = document.getElementById('tradesTableBody');
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state" style="color: #f44336;">Failed to load trades. Please try again.</td></tr>';
            return;
        }

        const allTrades = await response.json();

        const tbody = document.getElementById('tradesTableBody');

        if (allTrades.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No trades yet</td></tr>';
            document.getElementById('tradesPagination').style.display = 'none';
            return;
        }

        // Pagination
        const totalPages = Math.ceil(allTrades.length / tradesPerPage);
        const startIdx = (page - 1) * tradesPerPage;
        const endIdx = startIdx + tradesPerPage;
        const pageTrades = allTrades.slice(startIdx, endIdx);

        tbody.innerHTML = pageTrades.map(trade => {
            const pnl = trade.pnl || 0;
            const pnlClass = pnl > 0 ? 'pnl-positive' : pnl < 0 ? 'pnl-negative' : '';
            const actionClass = trade.action === 'buy' ? 'trade-buy' : 'trade-sell';

            return `
                <tr>
                    <td>${formatDate(trade.timestamp)}</td>
                    <td><strong>${trade.coin}</strong></td>
                    <td class="${actionClass}">${trade.action.toUpperCase()}</td>
                    <td>${trade.amount.toFixed(4)}</td>
                    <td>$${trade.price.toFixed(2)}</td>
                    <td class="${pnlClass}">
                        ${pnl !== 0 ? (pnl > 0 ? '+' : '') + '$' + pnl.toFixed(2) : '-'}
                    </td>
                </tr>
            `;
        }).join('');

        // Update pagination
        document.getElementById('paginationInfo').textContent = `Page ${page} of ${totalPages}`;
        document.getElementById('prevPageBtn').disabled = page === 1;
        document.getElementById('nextPageBtn').disabled = page === totalPages;
        document.getElementById('tradesPagination').style.display = 'flex';

    } catch (error) {
        console.error('Failed to load trade history:', error);
    }
}

// Update Market Ticker
async function updateMarketTicker() {
    try {
        const response = await fetch('/api/market/prices?symbols=BTC,ETH,BNB,SOL,XRP,DOGE');
        if (!response.ok) return;

        const prices = await response.json();

        const ticker = document.getElementById('marketTicker');

        const items = Object.entries(prices).map(([coin, data]) => {
            const change = data.change_24h || 0;
            const changeClass = change >= 0 ? 'positive' : 'negative';
            const sign = change >= 0 ? '+' : '';

            return `
                <div class="ticker-item">
                    <span class="ticker-coin">${coin}</span>
                    <span class="ticker-price">$${data.price.toLocaleString()}</span>
                    <span class="ticker-change ${changeClass}">${sign}${change.toFixed(2)}%</span>
                </div>
            `;
        }).join('');

        // Duplicate items for seamless scroll
        ticker.innerHTML = items + items;

    } catch (error) {
        console.error('Failed to update market ticker:', error);
    }
}

// Load AI Conversations
// REMOVED: Duplicate loadAIConversations function - using the better version at line ~2940

// Close Position (placeholder)
function closePosition(coin) {
    showToast(`Close position for ${coin} - Coming soon!`, 'info');
}

// View Conversation (placeholder)
function viewConversation(id) {
    showToast('View full conversation - Coming soon!', 'info');
}

// Export Trades
document.getElementById('exportTradesBtn')?.addEventListener('click', async () => {
    if (!currentModelId) {
        showToast('Please select a model first', 'error');
        return;
    }

    try {
        const response = await fetch(`/api/models/${currentModelId}/trades?limit=10000`);
        const trades = await response.json();

        // Convert to CSV
        const headers = ['Date', 'Coin', 'Action', 'Amount', 'Price', 'P&L'];
        const rows = trades.map(t => [
            t.timestamp,
            t.coin,
            t.action,
            t.amount,
            t.price,
            t.pnl || ''
        ]);

        const csv = [headers, ...rows].map(row => row.join(',')).join('\n');

        // Download
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `trades_model_${currentModelId}_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();

        showToast('Trades exported successfully', 'success');
    } catch (error) {
        console.error('Export failed:', error);
        showToast('Failed to export trades', 'error');
    }
});

// Pagination event listeners
document.getElementById('prevPageBtn')?.addEventListener('click', () => {
    loadTradeHistory(tradesCurrentPage - 1);
});

document.getElementById('nextPageBtn')?.addEventListener('click', () => {
    loadTradeHistory(tradesCurrentPage + 1);
});

// Toggle conversations
document.getElementById('toggleConversations')?.addEventListener('click', () => {
    const container = document.getElementById('conversationsContainer');
    const icon = document.querySelector('#toggleConversations i');

    if (container.style.display === 'none') {
        container.style.display = 'block';
        icon.className = 'bi bi-chevron-down';
    } else {
        container.style.display = 'none';
        icon.className = 'bi bi-chevron-up';
    }
});

// Helper: Format Currency
function formatCurrency(value) {
    if (value === undefined || value === null) return '$0.00';
    return '$' + value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// Helper: Format Percent
function formatPercent(value) {
    if (value === undefined || value === null) return '0.00%';
    return value.toFixed(2) + '%';
}

// Helper: Format Date
function formatDate(timestamp) {
    if (!timestamp) return '--';
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Setup Auto-Refresh
function setupAutoRefresh() {
    // Clear existing intervals
    Object.values(autoRefreshIntervals).forEach(clearInterval);
    autoRefreshIntervals = {};

    // Only refresh when tab is visible
    const refreshWhenVisible = (fn, interval) => {
        const id = setInterval(() => {
            if (!document.hidden && currentModelId) {
                fn();
            }
        }, interval);
        return id;
    };

    // Set up intervals (gentle, not harsh)
    autoRefreshIntervals.ticker = refreshWhenVisible(updateMarketTicker, 30000); // 30s
    autoRefreshIntervals.metrics = refreshWhenVisible(loadPortfolioMetrics, 60000); // 1min
    autoRefreshIntervals.positions = refreshWhenVisible(loadPositionsTable, 45000); // 45s
    autoRefreshIntervals.conversations = refreshWhenVisible(loadAIConversations, 60000); // 1min
}

// Pause auto-refresh when tab hidden
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        console.log('Tab hidden, pausing auto-refresh');
    } else {
        console.log('Tab visible, resuming auto-refresh');
    }
});

// NOTE: loadDashboardData() has been updated in the main section to include all enhanced features
// No need for override here anymore

console.log('✓ Enhanced Dashboard Features Loaded');

// ========================================
// MODELS PAGE - Session 2
// ========================================

let allModelsData = [];
let modelsFilter = 'all';

// Load Models Page
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

// Update Aggregated Metrics
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

// Render Models Grid
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

// Get Model Icon based on model name
function getModelIcon(modelName) {
    const name = modelName.toLowerCase();
    if (name.includes('gpt') || name.includes('openai')) return '🤖';
    if (name.includes('claude')) return '🧠';
    if (name.includes('gemini')) return '💎';
    if (name.includes('llama')) return '🦙';
    if (name.includes('deepseek')) return '🔍';
    return '⚡';
}

// Format Currency (Short version for cards)
function formatCurrencyShort(value) {
    if (value === undefined || value === null) return '$0';
    if (Math.abs(value) >= 1000000) {
        return '$' + (value / 1000000).toFixed(2) + 'M';
    } else if (Math.abs(value) >= 1000) {
        return '$' + (value / 1000).toFixed(2) + 'K';
    }
    return '$' + value.toFixed(2);
}

// View Model Dashboard
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

// Edit Model Settings
function editModelSettings(modelId) {
    switchPage('settings');
    showToast('Model settings - Coming soon!', 'info');
}

// Toggle Model Status (Pause/Resume)
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

// Multi-Model Toggle Handler - REMOVED (not needed, models always trade independently)

// Models Filter Handler
document.getElementById('modelsFilter')?.addEventListener('change', function() {
    modelsFilter = this.value;
    renderModelsGrid(allModelsData);
});

// Enhanced switchPage to load models page
const originalSwitchPage = typeof switchPage !== 'undefined' ? switchPage : null;
switchPage = function(pageName) {
    if (originalSwitchPage) {
        originalSwitchPage(pageName);
    } else {
        // Fallback implementation
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));

        document.getElementById(`${pageName}Page`)?.classList.add('active');
        document.querySelector(`[data-page="${pageName}"]`)?.classList.add('active');
    }

    // Load models page data when switched to
    if (pageName === 'models') {
        loadModelsPage();
    }

    // Dispatch page change event
    document.dispatchEvent(new CustomEvent('pageChange', { detail: pageName }));
};

console.log('✓ Models Page JavaScript Loaded');

// ============================================
// SESSION 3: ANALYTICS & INSIGHTS JAVASCRIPT
// ============================================

// Global variables for charts
let assetAllocationChart = null;
let conversationsData = [];

// Initialize Asset Allocation Donut Chart
function initAssetAllocationChart() {
    const chartDom = document.getElementById('assetAllocationChart');
    if (!chartDom) return;

    // Safety check: Ensure ECharts library is loaded
    if (typeof echarts === 'undefined') {
        console.error('ECharts library not loaded yet. Retrying in 500ms...');
        setTimeout(initAssetAllocationChart, 500);
        return;
    }

    // Dispose existing chart first to prevent memory leak
    if (assetAllocationChart) {
        assetAllocationChart.dispose();
    }

    assetAllocationChart = echarts.init(chartDom);

    const option = {
        tooltip: {
            trigger: 'item',
            formatter: '{b}: ${c} ({d}%)',
            backgroundColor: 'rgba(0, 0, 0, 0.9)',
            borderColor: '#333',
            textStyle: {
                color: '#fff'
            }
        },
        series: [{
            name: 'Asset Allocation',
            type: 'pie',
            radius: ['45%', '70%'],
            avoidLabelOverlap: true,
            itemStyle: {
                borderRadius: 8,
                borderColor: '#1a1a1a',
                borderWidth: 2
            },
            label: {
                show: false
            },
            emphasis: {
                label: {
                    show: true,
                    fontSize: 16,
                    fontWeight: 'bold'
                },
                itemStyle: {
                    shadowBlur: 10,
                    shadowOffsetX: 0,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            },
            data: []
        }]
    };

    assetAllocationChart.setOption(option);

    // Resize chart on window resize
    window.addEventListener('resize', () => {
        assetAllocationChart?.resize();
    });
}

// Load Asset Allocation Data
async function loadAssetAllocation() {
    if (!currentModelId) return;

    try {
        const response = await fetch(`/api/models/${currentModelId}/asset-allocation`);
        if (!response.ok) throw new Error('Failed to load asset allocation');

        const data = await response.json();

        // Update chart
        if (assetAllocationChart) {
            const chartData = data.allocations.map(item => ({
                name: item.name,
                value: item.value,
                itemStyle: {
                    color: item.color
                }
            }));

            assetAllocationChart.setOption({
                series: [{
                    data: chartData
                }]
            });
        }

        // Update legend
        updateAllocationLegend(data.allocations);

        // Update timestamp
        const timestamp = new Date(data.timestamp);
        document.getElementById('allocationTimestamp').textContent =
            `Updated: ${timestamp.toLocaleTimeString()}`;

    } catch (error) {
        console.error('Error loading asset allocation:', error);
        showToast('Failed to load asset allocation', 'error');
    }
}

// Update Allocation Legend
function updateAllocationLegend(allocations) {
    const legendContainer = document.getElementById('allocationLegend');
    if (!legendContainer) return;

    if (allocations.length === 0) {
        legendContainer.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-pie-chart"></i>
                <p>No allocations yet</p>
            </div>
        `;
        return;
    }

    legendContainer.innerHTML = allocations.map(item => `
        <div class="allocation-legend-item">
            <div class="allocation-legend-left">
                <div class="allocation-color-dot" style="background: ${item.color}"></div>
                <span class="allocation-name">${item.name}</span>
            </div>
            <div class="allocation-legend-right">
                <span class="allocation-percentage">${item.percentage.toFixed(1)}%</span>
                <span class="allocation-value">$${item.value.toFixed(2)}</span>
            </div>
        </div>
    `).join('');
}

// Load Performance Analytics
async function loadPerformanceAnalytics() {
    if (!currentModelId) return;

    try {
        const response = await fetch(`/api/models/${currentModelId}/performance-analytics`);
        if (!response.ok) throw new Error('Failed to load performance analytics');

        const data = await response.json();

        // Update Sharpe Ratio
        const sharpeEl = document.getElementById('sharpeRatio');
        if (sharpeEl) {
            sharpeEl.textContent = data.sharpe_ratio.toFixed(2);
            sharpeEl.className = 'perf-metric-value';
            if (data.sharpe_ratio > 1) sharpeEl.classList.add('positive');
            else if (data.sharpe_ratio < 0) sharpeEl.classList.add('negative');
        }

        // Update Max Drawdown
        const drawdownEl = document.getElementById('maxDrawdown');
        if (drawdownEl) {
            drawdownEl.textContent = `-${data.max_drawdown_pct.toFixed(2)}%`;
            drawdownEl.className = 'perf-metric-value negative';
        }

        // Update Win Streak
        const winStreakEl = document.getElementById('winStreak');
        if (winStreakEl) {
            winStreakEl.textContent = data.win_streak;
            winStreakEl.className = 'perf-metric-value';
            if (data.current_win_streak > 0) {
                winStreakEl.textContent += ` (${data.current_win_streak} current)`;
                winStreakEl.classList.add('positive');
            }
        }

        // Update Loss Streak
        const lossStreakEl = document.getElementById('lossStreak');
        if (lossStreakEl) {
            lossStreakEl.textContent = data.loss_streak;
            lossStreakEl.className = 'perf-metric-value';
            if (data.current_loss_streak > 0) {
                lossStreakEl.textContent += ` (${data.current_loss_streak} current)`;
                lossStreakEl.classList.add('negative');
            }
        }

        // Update Best Trade
        const bestTradeEl = document.getElementById('bestTrade');
        if (bestTradeEl) {
            bestTradeEl.textContent = `$${data.best_trade.toFixed(2)}`;
            bestTradeEl.className = 'perf-metric-value positive';
        }

        // Update Worst Trade
        const worstTradeEl = document.getElementById('worstTrade');
        if (worstTradeEl) {
            worstTradeEl.textContent = `$${data.worst_trade.toFixed(2)}`;
            worstTradeEl.className = 'perf-metric-value negative';
        }

        // Update Avg Win
        const avgWinEl = document.getElementById('avgWin');
        if (avgWinEl) {
            avgWinEl.textContent = `$${data.avg_win.toFixed(2)}`;
            avgWinEl.className = 'perf-metric-value positive';
        }

        // Update Avg Loss
        const avgLossEl = document.getElementById('avgLoss');
        if (avgLossEl) {
            avgLossEl.textContent = `$${data.avg_loss.toFixed(2)}`;
            avgLossEl.className = 'perf-metric-value negative';
        }

        // Update Profit Factor
        const profitFactorEl = document.getElementById('profitFactor');
        if (profitFactorEl) {
            profitFactorEl.textContent = data.profit_factor.toFixed(2);
            profitFactorEl.className = 'perf-metric-value';
            if (data.profit_factor > 1) profitFactorEl.classList.add('positive');
            else if (data.profit_factor < 1) profitFactorEl.classList.add('negative');
        }

        // Update Win Rate
        const winRateEl = document.getElementById('winRate');
        if (winRateEl) {
            winRateEl.textContent = `${data.win_rate.toFixed(1)}%`;
            winRateEl.className = 'perf-metric-value';
            if (data.win_rate >= 50) winRateEl.classList.add('positive');
            else winRateEl.classList.add('negative');
        }

        // Update Total Return
        const totalReturnEl = document.getElementById('totalReturn');
        if (totalReturnEl) {
            totalReturnEl.textContent = `$${data.total_return.toFixed(2)} (${data.total_return_pct >= 0 ? '+' : ''}${data.total_return_pct.toFixed(2)}%)`;
            totalReturnEl.className = 'perf-metric-value';
            if (data.total_return > 0) totalReturnEl.classList.add('positive');
            else if (data.total_return < 0) totalReturnEl.classList.add('negative');
        }

    } catch (error) {
        console.error('Error loading performance analytics:', error);
        showToast('Failed to load performance analytics', 'error');
    }
}

// Refresh Analytics Button
function setupAnalyticsRefresh() {
    const refreshBtn = document.getElementById('refreshAnalyticsBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
            refreshBtn.classList.add('refreshing');
            await Promise.all([
                loadAssetAllocation(),
                loadPerformanceAnalytics()
            ]);
            setTimeout(() => refreshBtn.classList.remove('refreshing'), 1000);
        });
    }
}

// Enhanced AI Conversations with Filtering
async function loadAIConversations() {
    if (!currentModelId) return;

    try {
        const response = await fetch(`/api/models/${currentModelId}/conversations?limit=50`);
        if (!response.ok) throw new Error('Failed to load conversations');

        conversationsData = await response.json();
        renderConversations(conversationsData);

    } catch (error) {
        console.error('Error loading conversations:', error);
        const container = document.getElementById('conversationsContainer');
        if (container) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-chat-dots"></i>
                    <p>Failed to load conversations</p>
                </div>
            `;
        }
    }
}

// Render Conversations
function renderConversations(conversations) {
    const container = document.getElementById('conversationsContainer');
    if (!container) return;

    if (conversations.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-chat-dots"></i>
                <p>No conversations yet</p>
            </div>
        `;
        return;
    }

    container.innerHTML = conversations.map((conv, index) => {
        const timestamp = new Date(conv.timestamp);
        const action = conv.decision?.action || 'unknown';
        const reasoning = conv.reasoning || 'No reasoning provided';

        return `
            <div class="conversation-item" data-action="${action.toLowerCase()}" data-index="${index}">
                <div class="conversation-header">
                    <span class="conversation-action ${action.toLowerCase()}">${action.toUpperCase()}</span>
                    <span class="conversation-timestamp">${timestamp.toLocaleString()}</span>
                </div>
                <div class="conversation-body" id="convBody${index}">
                    ${reasoning.substring(0, 150)}${reasoning.length > 150 ? '...' : ''}
                </div>
                ${reasoning.length > 150 ? `
                    <button class="conversation-expand" onclick="toggleConversation(${index})">
                        <span id="convToggle${index}">Show more</span>
                    </button>
                ` : ''}
            </div>
        `;
    }).join('');
}

// Toggle Conversation Expansion
function toggleConversation(index) {
    const bodyEl = document.getElementById(`convBody${index}`);
    const toggleEl = document.getElementById(`convToggle${index}`);
    const conv = conversationsData[index];

    if (!bodyEl || !toggleEl || !conv) return;

    if (bodyEl.classList.contains('expanded')) {
        bodyEl.classList.remove('expanded');
        bodyEl.textContent = conv.reasoning.substring(0, 150) +
            (conv.reasoning.length > 150 ? '...' : '');
        toggleEl.textContent = 'Show more';
    } else {
        bodyEl.classList.add('expanded');
        bodyEl.textContent = conv.reasoning;
        toggleEl.textContent = 'Show less';
    }
}

// Setup Conversation Filters
function setupConversationFilters() {
    const searchInput = document.getElementById('conversationSearch');
    const filterSelect = document.getElementById('conversationFilter');
    const sortSelect = document.getElementById('conversationSort');

    if (searchInput) {
        searchInput.addEventListener('input', filterConversations);
    }

    if (filterSelect) {
        filterSelect.addEventListener('change', filterConversations);
    }

    if (sortSelect) {
        sortSelect.addEventListener('change', sortAndFilterConversations);
    }
}

// Filter Conversations
function filterConversations() {
    const searchTerm = document.getElementById('conversationSearch')?.value.toLowerCase() || '';
    const actionFilter = document.getElementById('conversationFilter')?.value || 'all';

    const items = document.querySelectorAll('.conversation-item');
    items.forEach(item => {
        const action = item.dataset.action;
        const text = item.textContent.toLowerCase();

        const matchesSearch = text.includes(searchTerm);
        const matchesAction = actionFilter === 'all' || action === actionFilter;

        if (matchesSearch && matchesAction) {
            item.classList.remove('filtered-out');
        } else {
            item.classList.add('filtered-out');
        }
    });
}

// Sort and Filter Conversations
function sortAndFilterConversations() {
    const sortOrder = document.getElementById('conversationSort')?.value || 'newest';

    let sortedConversations = [...conversationsData];
    if (sortOrder === 'oldest') {
        sortedConversations.reverse();
    }

    renderConversations(sortedConversations);
    filterConversations(); // Reapply filters after sorting
}

// NOTE: Analytics features are now included in the main loadDashboardData() function

// Update auto-refresh to include analytics
if (window.setupAutoRefresh) {
    const originalSetupAutoRefresh = window.setupAutoRefresh;
    window.setupAutoRefresh = function() {
        originalSetupAutoRefresh();

        // Add analytics refresh intervals
        const refreshWhenVisible = (fn, interval) => {
            const id = setInterval(() => {
                if (!document.hidden && currentModelId) {
                    fn();
                }
            }, interval);
            return id;
        };

        window.autoRefreshIntervals = window.autoRefreshIntervals || {};
        window.autoRefreshIntervals.allocation = refreshWhenVisible(loadAssetAllocation, 120000); // 2 min
        window.autoRefreshIntervals.analytics = refreshWhenVisible(loadPerformanceAnalytics, 180000); // 3 min
    };
}

// REMOVED: Duplicate DOMContentLoaded listener - consolidated at line 8

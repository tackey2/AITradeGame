// Enhanced Dashboard JavaScript

let currentModelId = null;
let currentDecisionId = null;
let refreshInterval = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
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
    refreshInterval = setInterval(() => {
        if (currentModelId) {
            const activePage = document.querySelector('.page.active');
            if (activePage && activePage.id === 'dashboardPage') {
                loadPendingDecisions();
                loadRiskStatus();
            }
        }
    }, 10000); // Every 10 seconds
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
    await loadTradingMode();
    await loadDashboardData();
}

async function loadDashboardData() {
    await Promise.all([
        loadRiskStatus(),
        loadPendingDecisions()
    ]);
}

// Trading Configuration (Environment + Automation)
async function loadTradingMode() {
    try {
        const response = await fetch(`/api/models/${currentModelId}/config`);
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
        const risk = await response.json();

        // Update each risk card
        updateRiskCard('PositionSize', risk.position_size);
        updateRiskCard('DailyLoss', risk.daily_loss);
        updateRiskCard('OpenPositions', risk.open_positions);
        updateRiskCard('CashReserve', risk.cash_reserve);
        updateRiskCard('DailyTrades', risk.daily_trades);
    } catch (error) {
        console.error('Failed to load risk status:', error);
    }
}

function updateRiskCard(name, data) {
    const valueEl = document.getElementById(`risk${name}`);
    const statusEl = document.getElementById(`status${name}`);

    if (!valueEl || !statusEl || !data) return;

    // Format value based on type
    let value = '';
    if (data.usage_pct !== undefined) {
        value = `${data.usage_pct.toFixed(1)}%`;
    } else if (data.current_pct !== undefined) {
        value = `${data.current_pct.toFixed(1)}%`;
    } else if (data.current !== undefined) {
        value = data.current.toString();
    }

    valueEl.textContent = value;

    // Update status
    statusEl.textContent = data.status.toUpperCase();
    statusEl.className = 'risk-status';
    statusEl.classList.add(`status-${data.status}`);
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

// Initialize exchange credentials when model changes
document.addEventListener('DOMContentLoaded', function() {
    // Wait for model selection
    const modelSelect = document.getElementById('modelSelect');
    if (modelSelect) {
        modelSelect.addEventListener('change', function() {
            loadExchangeCredentials();
        });
    }

    // Initialize exchange credentials functionality
    initExchangeCredentials();
});

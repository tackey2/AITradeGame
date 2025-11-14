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

    // Initialize new features
    initProviderManagement();
    initModelManagement();
    initTrendingData();
    initPasswordToggles();
});

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

    // Auto-refresh every 60 seconds
    setInterval(loadTrendingData, 60000);
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
        const response = await fetch(`/api/models/${currentModelId}/portfolio-metrics`);
        if (!response.ok) {
            console.warn('Portfolio metrics endpoint failed:', response.status);
            return;
        }

        const metrics = await response.json();

        // Update Total Value
        document.getElementById('totalValue').textContent = formatCurrency(metrics.total_value);
        updateMetricChange('totalValueChange', metrics.value_change, metrics.value_change_pct);

        // Update Total P&L
        document.getElementById('totalPnL').textContent = formatCurrency(metrics.total_pnl);
        document.getElementById('totalPnLPercent').textContent = formatPercent(metrics.total_pnl_pct);
        document.getElementById('totalPnLPercent').className = `metric-change ${metrics.total_pnl >= 0 ? 'positive' : 'negative'}`;

        // Update Today's P&L
        document.getElementById('todayPnL').textContent = formatCurrency(metrics.today_pnl);
        document.getElementById('todayPnLPercent').textContent = formatPercent(metrics.today_pnl_pct);
        document.getElementById('todayPnLPercent').className = `metric-change ${metrics.today_pnl >= 0 ? 'positive' : 'negative'}`;

        // Update Win Rate
        document.getElementById('winRate').textContent = `${metrics.win_rate.toFixed(1)}%`;
        document.getElementById('winRateDetails').textContent = `${metrics.wins} wins / ${metrics.total_trades} trades`;

        // Update Total Trades
        document.getElementById('totalTrades').textContent = metrics.total_trades;
        document.getElementById('tradesBreakdown').textContent = `${metrics.wins} wins, ${metrics.total_trades - metrics.wins} losses`;

        // Update Open Positions
        document.getElementById('openPositionsCount').textContent = metrics.open_positions;
        document.getElementById('positionsValue').textContent = formatCurrency(metrics.positions_value);

    } catch (error) {
        console.error('Failed to load portfolio metrics:', error);
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

    // Check if ECharts is loaded
    if (typeof echarts === 'undefined') {
        console.error('ECharts not loaded');
        return;
    }

    const chartDom = document.getElementById('portfolioChart');
    if (!chartDom) return;

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

// Load Portfolio Chart Data
async function loadPortfolioChartData(range) {
    if (!currentModelId || !portfolioChart) return;

    try {
        const response = await fetch(`/api/models/${currentModelId}/portfolio-history?range=${range}`);
        if (!response.ok) {
            console.warn('Portfolio history endpoint failed');
            return;
        }

        const data = await response.json();

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
                data: data.timestamps,
                axisLine: { lineStyle: { color: '#3c4556' } },
                axisLabel: { color: '#9aa0a6' }
            },
            yAxis: {
                type: 'value',
                axisLine: { lineStyle: { color: '#3c4556' } },
                axisLabel: {
                    color: '#9aa0a6',
                    formatter: '${value}'
                },
                splitLine: { lineStyle: { color: '#252d3d' } }
            },
            series: [{
                data: data.values,
                type: 'line',
                smooth: true,
                lineStyle: {
                    color: data.values[data.values.length - 1] >= data.values[0] ? '#4caf50' : '#f44336',
                    width: 2
                },
                areaStyle: {
                    color: {
                        type: 'linear',
                        x: 0, y: 0, x2: 0, y2: 1,
                        colorStops: [{
                            offset: 0,
                            color: data.values[data.values.length - 1] >= data.values[0] ? 'rgba(76, 175, 80, 0.3)' : 'rgba(244, 67, 54, 0.3)'
                        }, {
                            offset: 1,
                            color: 'rgba(0, 0, 0, 0)'
                        }]
                    }
                },
                itemStyle: {
                    color: data.values[data.values.length - 1] >= data.values[0] ? '#4caf50' : '#f44336'
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
        if (!response.ok) return;

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
async function loadAIConversations() {
    if (!currentModelId) return;

    try {
        const response = await fetch(`/api/models/${currentModelId}/conversations?limit=5`);
        if (!response.ok) return;

        const conversations = await response.json();

        const container = document.getElementById('conversationsContainer');

        if (conversations.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-chat-dots"></i>
                    <p>No conversations yet</p>
                </div>
            `;
            return;
        }

        container.innerHTML = conversations.map(conv => {
            const statusClass = conv.approved ? 'approved' : conv.rejected ? 'rejected' : 'pending';
            const statusText = conv.approved ? '✅ Approved' : conv.rejected ? '❌ Rejected' : '⏳ Pending';

            return `
                <div class="conversation-item">
                    <div class="conversation-header">
                        <span class="conversation-model">Model ${currentModelId}</span>
                        <span class="conversation-time">${formatDate(conv.timestamp)}</span>
                    </div>
                    <div class="conversation-summary">
                        💭 "${conv.ai_reasoning ? conv.ai_reasoning.substring(0, 100) + '...' : 'No reasoning provided'}"
                    </div>
                    <div class="conversation-decision">
                        → Decision: ${conv.decision_type} ${conv.coin || ''} ${conv.amount ? conv.amount + ' at $' + conv.price : ''}
                    </div>
                    <div class="conversation-status">
                        <span class="conversation-badge ${statusClass}">${statusText}</span>
                        <button class="view-full-btn" onclick="viewConversation(${conv.id})">View Full ▶️</button>
                    </div>
                </div>
            `;
        }).join('');

    } catch (error) {
        console.error('Failed to load AI conversations:', error);
    }
}

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

// Enhanced loadDashboardData function
const originalLoadDashboardData = typeof loadDashboardData !== 'undefined' ? loadDashboardData : null;
loadDashboardData = async function() {
    if (originalLoadDashboardData) {
        await originalLoadDashboardData();
    }

    // Load new dashboard features
    await loadPortfolioMetrics();
    await initPortfolioChart();
    await loadPositionsTable();
    await loadTradeHistory();
    await updateMarketTicker();
    await loadAIConversations();
};

// Initialize on page load
if (typeof currentModelId !== 'undefined' && currentModelId) {
    loadDashboardData();
    setupAutoRefresh();
}

console.log('✓ Enhanced Dashboard Features Loaded');

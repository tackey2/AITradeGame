// Enhanced Dashboard - Settings Module
// Model settings, readiness assessment, incidents

// ============================================
// SETTINGS
// ============================================

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

// ============================================
// READINESS ASSESSMENT
// ============================================

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

// ============================================
// INCIDENTS
// ============================================

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

console.log('✓ Enhanced Settings Module Loaded');

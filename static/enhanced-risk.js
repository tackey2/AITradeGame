// Enhanced Dashboard - Risk Management Module
// Risk status monitoring and display

// ============================================
// RISK STATUS
// ============================================

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

console.log('✓ Enhanced Risk Management Module Loaded');

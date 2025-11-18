// ============================================
// LIVE ACTIVITY FEED
// ============================================

const activityFeed = [];
let activityIdCounter = 0;
const MAX_ACTIVITY_ITEMS = 50;

// Activity types
const ActivityType = {
    TRADE_EXECUTED: 'trade_executed',
    DECISION_CREATED: 'decision_created',
    DECISION_APPROVED: 'decision_approved',
    DECISION_REJECTED: 'decision_rejected',
    RISK_WARNING: 'risk_warning',
    MODEL_STARTED: 'model_started',
    MODEL_STOPPED: 'model_stopped',
    PORTFOLIO_UPDATE: 'portfolio_update',
    PRICE_ALERT: 'price_alert',
    SYSTEM_EVENT: 'system_event'
};

// Initialize activity feed
function initActivityFeed() {
    const clearBtn = document.getElementById('clearActivityBtn');
    if (clearBtn) {
        clearBtn.addEventListener('click', clearActivityFeed);
    }

    // Add welcome activity
    addActivity(ActivityType.SYSTEM_EVENT, 'Dashboard loaded', 'All systems operational', 'info');
}

// Add activity to feed
function addActivity(type, title, description, severity = 'info') {
    const activity = {
        id: ++activityIdCounter,
        type: type,
        title: title,
        description: description,
        severity: severity, // 'info', 'success', 'warning', 'danger'
        timestamp: new Date()
    };

    // Add to beginning of array
    activityFeed.unshift(activity);

    // Trim to max items
    if (activityFeed.length > MAX_ACTIVITY_ITEMS) {
        activityFeed.pop();
    }

    renderActivityFeed();
}

// Render activity feed
function renderActivityFeed() {
    const container = document.getElementById('activityFeedContainer');
    if (!container) return;

    if (activityFeed.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-activity"></i>
                <p>No recent activity</p>
            </div>
        `;
        return;
    }

    container.innerHTML = activityFeed.map(activity => {
        const icon = getActivityIcon(activity.type);
        const timeAgo = getTimeAgo(activity.timestamp);
        const severityClass = `activity-${activity.severity}`;

        return `
            <div class="activity-item ${severityClass}">
                <div class="activity-icon">
                    <i class="bi ${icon}"></i>
                </div>
                <div class="activity-content">
                    <div class="activity-title">${activity.title}</div>
                    <div class="activity-description">${activity.description}</div>
                    <div class="activity-time">${timeAgo}</div>
                </div>
            </div>
        `;
    }).join('');

    // Auto-scroll to top
    container.scrollTop = 0;
}

// Get activity icon based on type
function getActivityIcon(type) {
    const icons = {
        [ActivityType.TRADE_EXECUTED]: 'bi-arrow-left-right',
        [ActivityType.DECISION_CREATED]: 'bi-lightbulb',
        [ActivityType.DECISION_APPROVED]: 'bi-check-circle',
        [ActivityType.DECISION_REJECTED]: 'bi-x-circle',
        [ActivityType.RISK_WARNING]: 'bi-exclamation-triangle',
        [ActivityType.MODEL_STARTED]: 'bi-play-circle',
        [ActivityType.MODEL_STOPPED]: 'bi-stop-circle',
        [ActivityType.PORTFOLIO_UPDATE]: 'bi-graph-up',
        [ActivityType.PRICE_ALERT]: 'bi-bell',
        [ActivityType.SYSTEM_EVENT]: 'bi-info-circle'
    };
    return icons[type] || 'bi-dot';
}

// Clear activity feed
function clearActivityFeed() {
    activityFeed.length = 0;
    renderActivityFeed();
    addActivity(ActivityType.SYSTEM_EVENT, 'Activity cleared', 'Activity feed has been cleared', 'info');
}

// Helper function for time ago (reuse from notifications if available)
function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);

    let interval = seconds / 31536000;
    if (interval > 1) return Math.floor(interval) + 'y ago';

    interval = seconds / 2592000;
    if (interval > 1) return Math.floor(interval) + 'mo ago';

    interval = seconds / 86400;
    if (interval > 1) return Math.floor(interval) + 'd ago';

    interval = seconds / 3600;
    if (interval > 1) return Math.floor(interval) + 'h ago';

    interval = seconds / 60;
    if (interval > 1) return Math.floor(interval) + 'm ago';

    if (seconds < 10) return 'just now';
    return Math.floor(seconds) + 's ago';
}

// ============================================
// ACTIVITY MONITORING HOOKS
// ============================================

// Monitor trades
let lastTradeTimestamp = null;
function monitorTradesForActivity(trades) {
    if (!trades || trades.length === 0) return;

    const latestTrade = trades[0];
    if (!lastTradeTimestamp || latestTrade.timestamp !== lastTradeTimestamp) {
        lastTradeTimestamp = latestTrade.timestamp;

        const action = latestTrade.action.toUpperCase();
        const pnl = latestTrade.pnl || 0;
        const severity = pnl > 0 ? 'success' : (pnl < 0 ? 'danger' : 'info');

        addActivity(
            ActivityType.TRADE_EXECUTED,
            `${action} ${latestTrade.coin}`,
            `${latestTrade.amount.toFixed(4)} @ $${latestTrade.price.toFixed(2)}${pnl !== 0 ? ` | P&L: $${pnl.toFixed(2)}` : ''}`,
            severity
        );
    }
}

// Monitor portfolio changes
let lastPortfolioValue = null;
function monitorPortfolioForActivity(portfolio) {
    if (!portfolio || !portfolio.total_value) return;

    const currentValue = portfolio.total_value;

    if (lastPortfolioValue !== null) {
        const change = currentValue - lastPortfolioValue;
        const changePct = (change / lastPortfolioValue) * 100;

        // Only log significant changes (> 1%)
        if (Math.abs(changePct) > 1) {
            const severity = change > 0 ? 'success' : 'danger';
            addActivity(
                ActivityType.PORTFOLIO_UPDATE,
                'Portfolio Value Changed',
                `${change > 0 ? '+' : ''}$${change.toFixed(2)} (${changePct > 0 ? '+' : ''}${changePct.toFixed(2)}%)`,
                severity
            );
        }
    }

    lastPortfolioValue = currentValue;
}

// Monitor risk status
let lastRiskWarning = {};
function monitorRiskForActivity(riskData) {
    if (!riskData) return;

    // Check for risk warnings
    Object.keys(riskData).forEach(key => {
        const metric = riskData[key];
        if (metric && metric.status) {
            const warningKey = `${key}_${metric.status}`;

            if (metric.status === 'danger' && !lastRiskWarning[warningKey]) {
                addActivity(
                    ActivityType.RISK_WARNING,
                    `Risk Alert: ${key.replace(/_/g, ' ').toUpperCase()}`,
                    `Status: ${metric.status.toUpperCase()}`,
                    'danger'
                );
                lastRiskWarning[warningKey] = true;
            } else if (metric.status === 'warning' && !lastRiskWarning[warningKey]) {
                addActivity(
                    ActivityType.RISK_WARNING,
                    `Risk Warning: ${key.replace(/_/g, ' ').toUpperCase()}`,
                    `Approaching limits`,
                    'warning'
                );
                lastRiskWarning[warningKey] = true;
            } else if (metric.status === 'ok') {
                // Clear warning flag when back to ok
                delete lastRiskWarning[`${key}_warning`];
                delete lastRiskWarning[`${key}_danger`];
            }
        }
    });
}

// Monitor decisions
let lastDecisionCount = 0;
function monitorDecisionsForActivity(decisions) {
    if (!decisions) return;

    const currentCount = decisions.length;

    if (currentCount > lastDecisionCount) {
        const newCount = currentCount - lastDecisionCount;
        addActivity(
            ActivityType.DECISION_CREATED,
            'New AI Decision',
            `${newCount} new trading decision${newCount > 1 ? 's' : ''} created`,
            'info'
        );
    }

    lastDecisionCount = currentCount;
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initActivityFeed);
} else {
    initActivityFeed();
}

// Export functions for global access
window.addActivity = addActivity;
window.ActivityType = ActivityType;
window.monitorTradesForActivity = monitorTradesForActivity;
window.monitorPortfolioForActivity = monitorPortfolioForActivity;
window.monitorRiskForActivity = monitorRiskForActivity;
window.monitorDecisionsForActivity = monitorDecisionsForActivity;

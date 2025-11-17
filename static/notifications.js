// ============================================
// NOTIFICATION SYSTEM
// ============================================

// Notification state
const notifications = [];
let notificationIdCounter = 0;
let lastRiskStatus = {};
let lastPendingDecisionsCount = 0;

// Initialize notification system
function initNotificationSystem() {
    const notificationBtn = document.getElementById('notificationBtn');
    const closeBtn = document.getElementById('closeNotificationPanelBtn');
    const clearAllBtn = document.getElementById('clearAllNotificationsBtn');
    const overlay = document.getElementById('notificationOverlay');

    if (notificationBtn) {
        notificationBtn.addEventListener('click', toggleNotificationPanel);
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', closeNotificationPanel);
    }

    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', clearAllNotifications);
    }

    if (overlay) {
        overlay.addEventListener('click', closeNotificationPanel);
    }
}

// Toggle notification panel
function toggleNotificationPanel() {
    const panel = document.getElementById('notificationPanel');
    const overlay = document.getElementById('notificationOverlay');

    if (panel && overlay) {
        panel.classList.toggle('active');
        overlay.classList.toggle('active');

        if (panel.classList.contains('active')) {
            // Mark all as read when opening panel
            markAllNotificationsAsRead();
        }
    }
}

// Close notification panel
function closeNotificationPanel() {
    const panel = document.getElementById('notificationPanel');
    const overlay = document.getElementById('notificationOverlay');

    if (panel && overlay) {
        panel.classList.remove('active');
        overlay.classList.remove('active');
    }
}

// Add notification
function addNotification(type, title, message, actionLabel, actionCallback) {
    const notification = {
        id: ++notificationIdCounter,
        type: type, // 'success', 'warning', 'danger', 'info'
        title: title,
        message: message,
        timestamp: new Date(),
        unread: true,
        actionLabel: actionLabel || null,
        actionCallback: actionCallback || null
    };

    notifications.unshift(notification);

    // Keep only last 50 notifications
    if (notifications.length > 50) {
        notifications.pop();
    }

    renderNotifications();
    updateNotificationBadge();

    // Show toast for important notifications
    if (type === 'danger' || type === 'warning') {
        if (typeof showToast === 'function') {
            showToast(title, type);
        }
    }
}

// Render notifications
function renderNotifications() {
    const container = document.getElementById('notificationList');
    if (!container) return;

    if (notifications.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-bell-slash"></i>
                <p>No notifications yet</p>
            </div>
        `;
        return;
    }

    container.innerHTML = notifications.map(notif => {
        const icons = {
            success: 'bi-check-circle-fill',
            warning: 'bi-exclamation-triangle-fill',
            danger: 'bi-x-circle-fill',
            info: 'bi-info-circle-fill'
        };

        const timeAgo = getTimeAgo(notif.timestamp);
        const actionHTML = notif.actionLabel ?
            `<div class="notification-item-actions">
                <button class="btn-primary btn-small" onclick="handleNotificationAction(${notif.id})">
                    ${notif.actionLabel}
                </button>
            </div>` : '';

        return `
            <div class="notification-item type-${notif.type} ${notif.unread ? 'unread' : ''}" data-notification-id="${notif.id}">
                <div class="notification-item-header">
                    <div class="notification-item-title">
                        <i class="bi ${icons[notif.type]} notification-item-icon"></i>
                        ${notif.title}
                    </div>
                    <div>
                        <span class="notification-item-time">${timeAgo}</span>
                        <button class="notification-close-btn" onclick="removeNotification(${notif.id})">
                            <i class="bi bi-x"></i>
                        </button>
                    </div>
                </div>
                <div class="notification-item-body">
                    ${notif.message}
                </div>
                ${actionHTML}
            </div>
        `;
    }).join('');
}

// Remove notification
function removeNotification(id) {
    const index = notifications.findIndex(n => n.id === id);
    if (index !== -1) {
        notifications.splice(index, 1);
        renderNotifications();
        updateNotificationBadge();
    }
}

// Clear all notifications
function clearAllNotifications() {
    notifications.length = 0;
    renderNotifications();
    updateNotificationBadge();
    if (typeof showToast === 'function') {
        showToast('All notifications cleared', 'info');
    }
}

// Mark all as read
function markAllNotificationsAsRead() {
    notifications.forEach(n => n.unread = false);
    updateNotificationBadge();
}

// Update notification badge
function updateNotificationBadge() {
    const badge = document.getElementById('notificationBadge');
    if (!badge) return;

    const unreadCount = notifications.filter(n => n.unread).length;

    if (unreadCount > 0) {
        badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
        badge.style.display = 'block';
    } else {
        badge.style.display = 'none';
    }
}

// Handle notification action
function handleNotificationAction(id) {
    const notification = notifications.find(n => n.id === id);
    if (notification && notification.actionCallback) {
        notification.actionCallback();
        removeNotification(id);
    }
}

// Get time ago string
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

    return Math.floor(seconds) + 's ago';
}

// ============================================
// NOTIFICATION TRIGGERS
// ============================================

// Monitor risk status and create alerts
function monitorRiskStatus(riskData) {
    if (!riskData) return;

    // High risk position size
    if (riskData.position_size && riskData.position_size.status === 'danger') {
        if (!lastRiskStatus.position_size_danger) {
            addNotification(
                'danger',
                '⚠️ High Risk: Position Size',
                `Position size has reached ${riskData.position_size.usage_pct.toFixed(1)}% - Consider reducing exposure`,
                'View Risk Status',
                () => document.getElementById('dashboardPage').scrollIntoView({ behavior: 'smooth' })
            );
            lastRiskStatus.position_size_danger = true;
        }
    } else {
        lastRiskStatus.position_size_danger = false;
    }

    // Daily loss warning
    if (riskData.daily_loss && riskData.daily_loss.status === 'warning') {
        if (!lastRiskStatus.daily_loss_warning) {
            addNotification(
                'warning',
                '📉 Daily Loss Alert',
                `Daily loss is at ${riskData.daily_loss.current_pct.toFixed(1)}% - Approaching limit`,
                null,
                null
            );
            lastRiskStatus.daily_loss_warning = true;
        }
    } else {
        lastRiskStatus.daily_loss_warning = false;
    }

    // Daily loss danger
    if (riskData.daily_loss && riskData.daily_loss.status === 'danger') {
        if (!lastRiskStatus.daily_loss_danger) {
            addNotification(
                'danger',
                '🚨 Daily Loss Limit Reached',
                `Daily loss has exceeded safe limits at ${riskData.daily_loss.current_pct.toFixed(1)}%`,
                'Stop Trading',
                () => {
                    if (confirm('Do you want to pause all trading?')) {
                        // Implement pause trading logic
                        if (typeof showToast === 'function') {
                            showToast('Trading paused', 'info');
                        }
                    }
                }
            );
            lastRiskStatus.daily_loss_danger = true;
        }
    } else {
        lastRiskStatus.daily_loss_danger = false;
    }
}

// Monitor pending decisions
function monitorPendingDecisions(decisions) {
    if (!decisions) return;

    const currentCount = decisions.length;

    if (currentCount > lastPendingDecisionsCount) {
        const newCount = currentCount - lastPendingDecisionsCount;
        addNotification(
            'info',
            '🤖 New Trading Decision',
            `${newCount} new trading decision${newCount > 1 ? 's' : ''} awaiting your approval`,
            'View Decisions',
            () => {
                const dashboardBtn = document.querySelector('[data-page="dashboard"]');
                if (dashboardBtn) dashboardBtn.click();
                setTimeout(() => {
                    const dashboardPage = document.getElementById('dashboardPage');
                    if (dashboardPage) {
                        dashboardPage.scrollIntoView({ behavior: 'smooth' });
                    }
                }, 100);
            }
        );
    }

    lastPendingDecisionsCount = currentCount;
}

// Monitor trades for execution notifications
let lastTradeCount = 0;
function monitorTradeExecution(newTrades) {
    if (!newTrades || newTrades.length === 0) return;

    // Check for new trades
    if (newTrades.length > lastTradeCount && lastTradeCount > 0) {
        const latestTrade = newTrades[0];
        const action = latestTrade.action.toUpperCase();
        const pnl = latestTrade.pnl || 0;

        addNotification(
            pnl >= 0 ? 'success' : 'danger',
            `✅ Trade Executed: ${action}`,
            `${latestTrade.coin} - ${latestTrade.amount.toFixed(4)} @ $${latestTrade.price.toFixed(2)}${pnl !== 0 ? ` | P&L: $${pnl.toFixed(2)}` : ''}`,
            null,
            null
        );
    }

    lastTradeCount = newTrades.length;
}

// Welcome notification
function showWelcomeNotification() {
    addNotification(
        'info',
        '👋 Welcome Back',
        'Dashboard loaded successfully. All systems operational.',
        null,
        null
    );
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initNotificationSystem);
} else {
    initNotificationSystem();
}

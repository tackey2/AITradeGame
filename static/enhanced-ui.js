// Enhanced Dashboard - UI Utilities Module
// Format helpers, toast notifications, modals

// ============================================
// FORMAT HELPERS
// ============================================

function formatCurrency(value) {
    if (value === undefined || value === null) return '$0.00';
    return '$' + value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatCurrencyShort(value) {
    if (value === undefined || value === null) return '$0';
    if (Math.abs(value) >= 1000000) {
        return '$' + (value / 1000000).toFixed(2) + 'M';
    } else if (Math.abs(value) >= 1000) {
        return '$' + (value / 1000).toFixed(2) + 'K';
    }
    return '$' + value.toFixed(2);
}

function formatPercent(value) {
    if (value === undefined || value === null) return '0.00%';
    return value.toFixed(2) + '%';
}

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

function formatTimestamp(timestamp) {
    return new Date(timestamp).toLocaleString();
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

// ============================================
// TOAST NOTIFICATIONS
// ============================================

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');

    toastMessage.textContent = message;
    toast.classList.add('active');

    setTimeout(() => {
        toast.classList.remove('active');
    }, 3000);
}

// ============================================
// LIVE WARNING MODAL
// ============================================

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

// ============================================
// PASSWORD VISIBILITY TOGGLES
// ============================================

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

// ============================================
// MODEL ICON HELPER
// ============================================

function getModelIcon(modelName) {
    const name = modelName.toLowerCase();
    if (name.includes('gpt') || name.includes('openai')) return '🤖';
    if (name.includes('claude')) return '🧠';
    if (name.includes('gemini')) return '💎';
    if (name.includes('llama')) return '🦙';
    if (name.includes('deepseek')) return '🔍';
    return '⚡';
}

console.log('✓ Enhanced UI Utilities Module Loaded');

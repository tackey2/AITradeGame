// Enhanced Dashboard - Trading Module
// Trading configuration, environment, automation, actions

// ============================================
// TRADING CONFIGURATION
// ============================================

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

// ============================================
// TRADING ACTIONS
// ============================================

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

console.log('✓ Enhanced Trading Module Loaded');

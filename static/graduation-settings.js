// Graduation Settings Management

const strategyPresets = {
    quick_test: {
        min_trades: 20,
        confidence_level: 80,
        min_testing_days: 0,  // Not used when min_testing_minutes is set
        min_testing_minutes: 5,  // 5 minutes for quick testing
        min_win_rate: 50.0,
        min_sharpe_ratio: 0.8,
        max_drawdown_pct: 25.0
    },
    standard: {
        min_trades: 50,
        confidence_level: 95,
        min_testing_days: 7,  // 7 days
        min_testing_minutes: 0,  // Not used when min_testing_days is set
        min_win_rate: 55.0,
        min_sharpe_ratio: 1.0,
        max_drawdown_pct: 20.0
    },
    conservative: {
        min_trades: 100,
        confidence_level: 99,
        min_testing_days: 30,  // 30 days
        min_testing_minutes: 0,  // Not used when min_testing_days is set
        min_win_rate: 60.0,
        min_sharpe_ratio: 1.2,
        max_drawdown_pct: 15.0
    }
};

async function loadGraduationSettings() {
    try {
        const response = await fetch('/api/graduation-settings');
        const settings = await response.json();

        // Populate form fields
        document.getElementById('strategyPreset').value = settings.strategy_preset || 'quick_test';
        document.getElementById('minTrades').value = settings.min_trades || 20;
        document.getElementById('confidenceLevel').value = settings.confidence_level || 80;
        document.getElementById('minTestingDays').value = settings.min_testing_days || 14;
        document.getElementById('minTestingMinutes').value = settings.min_testing_minutes || 0;
        document.getElementById('minWinRate').value = settings.min_win_rate || 50;
        document.getElementById('minSharpeRatio').value = settings.min_sharpe_ratio || 0.8;
        document.getElementById('maxDrawdownPct').value = settings.max_drawdown_pct || 25;

        // Set checkbox states
        document.getElementById('enableWinRate').checked = settings.min_win_rate !== null;
        document.getElementById('enableSharpe').checked = settings.min_sharpe_ratio !== null;
        document.getElementById('enableDrawdown').checked = settings.max_drawdown_pct !== null;

    } catch (error) {
        console.error('Failed to load graduation settings:', error);
        showToast('Failed to load graduation settings', 'error');
    }
}

async function saveGraduationSettings() {
    try {
        const settings = {
            strategy_preset: document.getElementById('strategyPreset').value,
            min_trades: parseInt(document.getElementById('minTrades').value),
            confidence_level: parseInt(document.getElementById('confidenceLevel').value),
            min_testing_days: parseInt(document.getElementById('minTestingDays').value),
            min_testing_minutes: parseInt(document.getElementById('minTestingMinutes').value),
            min_win_rate: document.getElementById('enableWinRate').checked ?
                parseFloat(document.getElementById('minWinRate').value) : null,
            min_sharpe_ratio: document.getElementById('enableSharpe').checked ?
                parseFloat(document.getElementById('minSharpeRatio').value) : null,
            max_drawdown_pct: document.getElementById('enableDrawdown').checked ?
                parseFloat(document.getElementById('maxDrawdownPct').value) : null
        };

        const response = await fetch('/api/graduation-settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });

        if (response.ok) {
            showToast('Graduation settings saved successfully', 'success');
            // Refresh graduation status if a model is selected
            if (currentModelId) {
                loadGraduationStatus(currentModelId);
            }
        } else {
            throw new Error('Failed to save settings');
        }
    } catch (error) {
        console.error('Failed to save graduation settings:', error);
        showToast('Failed to save graduation settings', 'error');
    }
}

function applyPreset(presetName) {
    const preset = strategyPresets[presetName];
    if (!preset) return;

    document.getElementById('minTrades').value = preset.min_trades;
    document.getElementById('confidenceLevel').value = preset.confidence_level;
    document.getElementById('minTestingDays').value = preset.min_testing_days;
    document.getElementById('minTestingMinutes').value = preset.min_testing_minutes;
    document.getElementById('minWinRate').value = preset.min_win_rate;
    document.getElementById('minSharpeRatio').value = preset.min_sharpe_ratio;
    document.getElementById('maxDrawdownPct').value = preset.max_drawdown_pct;
}

function initGraduationSettings() {
    // Preset selector change
    const presetSelect = document.getElementById('strategyPreset');
    if (presetSelect) {
        presetSelect.addEventListener('change', (e) => {
            const preset = e.target.value;
            if (preset !== 'custom') {
                applyPreset(preset);
            }
        });
    }

    // Save button
    const saveBtn = document.getElementById('saveGraduationSettings');
    if (saveBtn) {
        saveBtn.addEventListener('click', saveGraduationSettings);
    }

    // Reset button
    const resetBtn = document.getElementById('resetGraduationSettings');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            const currentPreset = document.getElementById('strategyPreset').value;
            if (currentPreset !== 'custom') {
                applyPreset(currentPreset);
                showToast('Settings reset to preset defaults', 'info');
            }
        });
    }

    // Enable/disable checkboxes
    document.getElementById('enableWinRate')?.addEventListener('change', (e) => {
        document.getElementById('minWinRate').disabled = !e.target.checked;
    });
    document.getElementById('enableSharpe')?.addEventListener('change', (e) => {
        document.getElementById('minSharpeRatio').disabled = !e.target.checked;
    });
    document.getElementById('enableDrawdown')?.addEventListener('change', (e) => {
        document.getElementById('maxDrawdownPct').disabled = !e.target.checked;
    });

    // Load current settings
    loadGraduationSettings();
}

// Initialize when settings page is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('strategyPreset')) {
        initGraduationSettings();
    }
});

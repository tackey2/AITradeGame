// ============================================
// MODEL SETTINGS WIDGET
// ============================================

// Load model settings widget
async function loadModelSettingsWidget() {
    if (!currentModelId) {
        const widget = document.getElementById('modelSettingsWidget');
        if (widget) {
            widget.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-gear"></i>
                    <p>Select a model to view settings</p>
                </div>
            `;
        }
        return;
    }

    try {
        const response = await fetch(`/api/models/${currentModelId}/settings`);
        if (!response.ok) throw new Error('Failed to load settings');

        const settings = await response.json();
        renderModelSettingsWidget(settings);

    } catch (error) {
        console.error('Failed to load model settings:', error);
        const widget = document.getElementById('modelSettingsWidget');
        if (widget) {
            widget.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-exclamation-triangle"></i>
                    <p>Failed to load settings</p>
                </div>
            `;
        }
    }
}

// Render model settings widget
function renderModelSettingsWidget(settings) {
    const widget = document.getElementById('modelSettingsWidget');
    if (!widget) return;

    // Format settings for display
    const displaySettings = [
        {
            icon: 'bi-robot',
            label: 'AI Strategy',
            value: formatStrategy(settings.ai_strategy || 'Not set'),
            key: 'ai_strategy'
        },
        {
            icon: 'bi-speedometer2',
            label: 'Automation',
            value: formatAutomation(settings.automation_level || 'manual'),
            key: 'automation_level',
            badge: getAutomationBadge(settings.automation_level)
        },
        {
            icon: 'bi-shield-check',
            label: 'Risk Tolerance',
            value: formatRiskTolerance(settings.risk_tolerance || 'medium'),
            key: 'risk_tolerance',
            badge: getRiskBadge(settings.risk_tolerance)
        },
        {
            icon: 'bi-percent',
            label: 'Confidence Threshold',
            value: `${((settings.confidence_threshold || 0.7) * 100).toFixed(0)}%`,
            key: 'confidence_threshold'
        },
        {
            icon: 'bi-clock',
            label: 'Trading Frequency',
            value: `Every ${settings.trading_frequency_minutes || 60} min`,
            key: 'trading_frequency_minutes'
        },
        {
            icon: 'bi-cash-coin',
            label: 'Max Position Size',
            value: `${((settings.max_position_size_pct || 20) * 100).toFixed(0)}%`,
            key: 'max_position_size_pct'
        }
    ];

    widget.innerHTML = `
        <div class="settings-widget-grid">
            ${displaySettings.map(setting => `
                <div class="setting-item">
                    <div class="setting-icon">
                        <i class="bi ${setting.icon}"></i>
                    </div>
                    <div class="setting-content">
                        <div class="setting-label">${setting.label}</div>
                        <div class="setting-value">
                            ${setting.value}
                            ${setting.badge ? setting.badge : ''}
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
        <div class="settings-widget-footer">
            <small>Last updated: ${settings.updated_at ? formatTimestamp(settings.updated_at) : 'Never'}</small>
        </div>
    `;

    // Setup edit button
    const editBtn = document.getElementById('editModelSettingsBtn');
    if (editBtn) {
        editBtn.onclick = () => {
            // Navigate to settings page
            document.querySelector('[data-page="settings"]').click();
        };
    }
}

// Format strategy name
function formatStrategy(strategy) {
    const strategies = {
        'conservative': 'Conservative Growth',
        'moderate': 'Moderate Growth',
        'aggressive': 'Aggressive Growth',
        'momentum': 'Momentum Trading',
        'mean_reversion': 'Mean Reversion',
        'trend_following': 'Trend Following'
    };
    return strategies[strategy] || strategy.replace('_', ' ').toUpperCase();
}

// Format automation level
function formatAutomation(level) {
    const levels = {
        'manual': 'Manual',
        'semi_auto': 'Semi-Automatic',
        'full_auto': 'Fully Automatic'
    };
    return levels[level] || level.toUpperCase();
}

// Format risk tolerance
function formatRiskTolerance(risk) {
    const risks = {
        'low': 'Low Risk',
        'medium': 'Medium Risk',
        'high': 'High Risk'
    };
    return risks[risk] || risk.toUpperCase();
}

// Get automation badge
function getAutomationBadge(level) {
    const badges = {
        'manual': '<span class="setting-badge badge-gray">MANUAL</span>',
        'semi_auto': '<span class="setting-badge badge-blue">SEMI-AUTO</span>',
        'full_auto': '<span class="setting-badge badge-green">AUTO</span>'
    };
    return badges[level] || '';
}

// Get risk badge
function getRiskBadge(risk) {
    const badges = {
        'low': '<span class="setting-badge badge-green">LOW</span>',
        'medium': '<span class="setting-badge badge-orange">MEDIUM</span>',
        'high': '<span class="setting-badge badge-red">HIGH</span>'
    };
    return badges[risk] || '';
}

// Export for global access
window.loadModelSettingsWidget = loadModelSettingsWidget;

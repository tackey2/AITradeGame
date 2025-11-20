// Graduation Status Widget

async function loadGraduationStatus(modelId) {
    if (!modelId) return;

    try {
        const response = await fetch(`/api/models/${modelId}/graduation-status`);

        if (!response.ok) {
            // Handle error responses
            const errorData = await response.json();

            if (response.status === 404) {
                // Model not found - show helpful error message
                console.error(`Model ${modelId} not found. Available models:`, errorData.available_model_ids);

                if (errorData.hint) {
                    console.warn(`Hint: ${errorData.hint}`);
                }

                // Show error in UI
                const card = document.getElementById('graduationStatusCard');
                if (card) {
                    card.innerHTML = `
                        <div class="error-message">
                            <i class="bi bi-exclamation-triangle"></i>
                            <h3>Model Not Found</h3>
                            <p>Model ID ${modelId} doesn't exist in the database.</p>
                            ${errorData.hint ? `<p class="hint">${errorData.hint}</p>` : ''}
                            <p>Please select a different model or check the console for details.</p>
                        </div>
                    `;
                }

                document.getElementById('graduationStatusSection').style.display = 'block';
                return;
            }

            throw new Error(errorData.error || 'Failed to load graduation status');
        }

        const status = await response.json();
        renderGraduationStatus(status);

        // Show section
        document.getElementById('graduationStatusSection').style.display = 'block';

    } catch (error) {
        console.error('Failed to load graduation status:', error);
        document.getElementById('graduationStatusSection').style.display = 'none';
    }
}

function renderGraduationStatus(status) {
    const card = document.getElementById('graduationStatusCard');

    const readinessPct = status.readiness_percentage || 0;
    const isReady = status.is_ready || false;

    // Determine status color
    let statusColor = '#6c757d'; // gray
    if (readinessPct >= 100) {
        statusColor = '#28a745'; // green
    } else if (readinessPct >= 75) {
        statusColor = '#ffc107'; // yellow
    } else if (readinessPct >= 50) {
        statusColor = '#fd7e14'; // orange
    } else {
        statusColor = '#dc3545'; // red
    }

    // Build HTML
    let html = `
        <div class="graduation-status-content">
            <!-- Readiness Overview -->
            <div class="readiness-overview">
                <div class="readiness-circle" style="background: conic-gradient(${statusColor} ${readinessPct * 3.6}deg, #2a2e39 0deg);">
                    <div class="readiness-inner">
                        <div class="readiness-percentage">${readinessPct}%</div>
                        <div class="readiness-label">Ready</div>
                    </div>
                </div>
                <div class="readiness-summary">
                    <h3>${isReady ? '✅ Model is Ready!' : '⏳ Testing in Progress'}</h3>
                    <p class="readiness-subtitle">
                        ${status.passed_count} of ${status.total_criteria} criteria met
                        ${status.confidence_level ? `(${status.confidence_level}% confidence)` : ''}
                    </p>
                    <div class="readiness-strategy">
                        Strategy: <span class="badge">${formatPresetName(status.strategy_preset)}</span>
                    </div>
                </div>
            </div>

            <!-- Criteria Checklist -->
            <div class="criteria-checklist">
                ${status.criteria.map(criterion => `
                    <div class="criterion-item ${criterion.met ? 'met' : 'not-met'}">
                        <div class="criterion-icon">
                            ${criterion.met ? '<i class="bi bi-check-circle-fill"></i>' : '<i class="bi bi-circle"></i>'}
                        </div>
                        <div class="criterion-content">
                            <div class="criterion-name">${criterion.name}</div>
                            <div class="criterion-value">${criterion.display}</div>
                        </div>
                        <div class="criterion-status">
                            ${criterion.met ? '<span class="status-badge success">✓ Pass</span>' :
                                            '<span class="status-badge pending">Pending</span>'}
                        </div>
                    </div>
                `).join('')}
            </div>

            <!-- Actions -->
            <div class="graduation-actions">
                ${isReady ?
                    '<button class="btn-success" onclick="confirmGoLive()"><i class="bi bi-rocket"></i> Go Live with This Model</button>' :
                    '<button class="btn-secondary" disabled><i class="bi bi-hourglass"></i> Continue Testing</button>'
                }
                <button class="btn-secondary" onclick="switchPage(\'settings\'); scrollToGraduationSettings();">
                    <i class="bi bi-gear"></i> Adjust Criteria
                </button>
            </div>
        </div>
    `;

    card.innerHTML = html;
}

function formatPresetName(preset) {
    const names = {
        'quick_test': 'Quick Test',
        'standard': 'Standard',
        'conservative': 'Conservative',
        'custom': 'Custom'
    };
    return names[preset] || preset;
}

function scrollToGraduationSettings() {
    setTimeout(() => {
        const elem = document.getElementById('strategyPreset');
        if (elem) {
            elem.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }, 300);
}

function confirmGoLive() {
    if (confirm('Are you ready to switch this model to live trading?\n\nMake sure you have:\n- Tested thoroughly\n- Configured exchange API keys\n- Set appropriate position sizes\n- Understood the risks\n\nProceed?')) {
        // Navigate to trading environment settings
        switchPage('dashboard');
        setTimeout(() => {
            const envSection = document.querySelector('input[name="environment"][value="live"]');
            if (envSection) {
                envSection.scrollIntoView({ behavior: 'smooth' });
                envSection.closest('.mode-option').style.animation = 'pulse 1s ease-in-out 3';
            }
        }, 300);
    }
}

// Refresh button handler
document.addEventListener('DOMContentLoaded', () => {
    const refreshBtn = document.getElementById('refreshGraduationBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            if (currentModelId) {
                loadGraduationStatus(currentModelId);
                showToast('Refreshing graduation status...', 'info');
            }
        });
    }
});

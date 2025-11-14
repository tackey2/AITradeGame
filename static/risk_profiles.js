// ===================================================
//      Risk Profiles Management - Complete JavaScript UI
// ===================================================

// Note: currentModelId is defined in enhanced.js, so we don't redeclare it here
let allRiskProfiles = [];
let activeProfileId = null;

// Initialize risk profiles when settings page loads
async function initRiskProfiles() {
    // Check if we're on the settings page OR if the profilesGrid element exists
    const profilesGrid = document.getElementById('profilesGrid');
    if (!profilesGrid) {
        console.log('Risk profiles grid not found, skipping initialization');
        return;
    }

    try {
        console.log('Initializing risk profiles...');
        await loadRiskProfiles();
        await loadActiveProfile();
        setupProfileEventListeners();
    } catch (error) {
        console.error('Failed to initialize risk profiles:', error);
    }
}

// Load all risk profiles from API
async function loadRiskProfiles() {
    try {
        const response = await fetch('/api/risk-profiles');
        if (!response.ok) throw new Error('Failed to fetch profiles');

        allRiskProfiles = await response.json();
        renderProfilesGrid(allRiskProfiles);

        console.log('✓ Loaded', allRiskProfiles.length, 'risk profiles');
    } catch (error) {
        console.error('Error loading risk profiles:', error);
        showNotification('Failed to load risk profiles', 'error');
    }
}

// Render profiles grid
function renderProfilesGrid(profiles) {
    const grid = document.getElementById('profilesGrid');
    if (!grid) return;

    grid.innerHTML = profiles.map(profile => `
        <div class="profile-card ${profile.id === activeProfileId ? 'active' : ''}"
             data-profile-id="${profile.id}"
             onclick="applyRiskProfile(${profile.id})"
             title="Click to apply this profile">
            <span class="profile-icon">${profile.icon}</span>
            <div class="profile-name">${profile.name}</div>
            <div class="profile-description">${profile.description}</div>
            <div class="profile-stats">
                <div class="profile-stat">
                    <span class="profile-stat-label">Pos</span>
                    <span class="profile-stat-value">${profile.max_position_size_pct}%</span>
                </div>
                <div class="profile-stat">
                    <span class="profile-stat-label">Loss</span>
                    <span class="profile-stat-value">${profile.max_daily_loss_pct}%</span>
                </div>
                <div class="profile-stat">
                    <span class="profile-stat-label">Trades</span>
                    <span class="profile-stat-value">${profile.max_daily_trades}</span>
                </div>
            </div>
        </div>
    `).join('');
}

// Load and display active profile
async function loadActiveProfile() {
    const modelId = getCurrentModelId();
    if (!modelId) return;

    try {
        const response = await fetch(`/api/models/${modelId}/active-profile`);
        if (!response.ok) throw new Error('Failed to fetch active profile');

        const data = await response.json();

        const indicator = document.getElementById('activeProfileIndicator');
        const nameSpan = document.getElementById('activeProfileName');

        if (data.active_profile) {
            activeProfileId = data.active_profile.id;

            if (indicator && nameSpan) {
                indicator.style.display = 'inline-flex';
                nameSpan.textContent = data.active_profile.name;
            }

            // Update active class on cards
            document.querySelectorAll('.profile-card').forEach(card => {
                card.classList.remove('active');
                if (parseInt(card.dataset.profileId) === activeProfileId) {
                    card.classList.add('active');
                }
            });

            console.log('✓ Active profile:', data.active_profile.name);
        } else {
            if (indicator) indicator.style.display = 'none';
            activeProfileId = null;
        }
    } catch (error) {
        console.error('Error loading active profile:', error);
    }
}

// Apply a risk profile to current model
async function applyRiskProfile(profileId) {
    const modelId = getCurrentModelId();
    if (!modelId) {
        showNotification('Please select a model first', 'error');
        return;
    }

    // Find profile name
    const profile = allRiskProfiles.find(p => p.id === profileId);
    if (!profile) return;

    // Confirmation
    const confirmed = confirm(`Apply "${profile.name}" profile?\n\nThis will update all risk settings for this model.`);
    if (!confirmed) return;

    try {
        const response = await fetch(`/api/models/${modelId}/apply-profile`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({profile_id: profileId})
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to apply profile');
        }

        const result = await response.json();

        showNotification(`✓ ${result.message}`, 'success');

        // Reload profiles and settings
        await loadActiveProfile();

        // Reload settings if the function exists
        if (typeof loadModelSettings === 'function') {
            await loadModelSettings();
        }

        console.log('✓ Applied profile:', profile.name);
    } catch (error) {
        console.error('Error applying profile:', error);
        showNotification(`Failed to apply profile: ${error.message}`, 'error');
    }
}

// Get recommendation for current model
async function getProfileRecommendation() {
    const modelId = getCurrentModelId();
    if (!modelId) {
        showNotification('Please select a model first', 'error');
        return;
    }

    try {
        const response = await fetch(`/api/models/${modelId}/recommend-profile`);
        if (!response.ok) throw new Error('Failed to get recommendation');

        const data = await response.json();
        const rec = data.recommendation;

        // Show recommendation modal
        showRecommendationModal(rec, data.metrics);
    } catch (error) {
        console.error('Error getting recommendation:', error);
        showNotification('Failed to get recommendation', 'error');
    }
}

// Show recommendation modal
function showRecommendationModal(recommendation, metrics) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';

    const allReasonsHtml = recommendation.all_reasons && recommendation.all_reasons.length > 1
        ? `<ul style="margin: 10px 0; padding-left: 20px; color: var(--color-text-secondary);">
            ${recommendation.all_reasons.slice(1).map(r => `<li>${r}</li>`).join('')}
           </ul>`
        : '';

    const currentProfileHtml = recommendation.current_profile
        ? `<div style="padding: 12px; background: var(--color-${recommendation.should_switch ? 'warning' : 'success'}); color: white; border-radius: 4px; margin-bottom: 20px;">
            ${recommendation.should_switch
                ? `⚠️ Currently using "${recommendation.current_profile}". Consider switching to "${recommendation.profile_name}".`
                : `✓ You're already using the optimal profile: "${recommendation.current_profile}"`
            }
           </div>`
        : '';

    const applyButtonHtml = recommendation.should_switch
        ? `<button class="btn-primary" onclick="applyRiskProfile(${recommendation.profile_id}); this.closest('.modal-overlay').remove();">
            Apply ${recommendation.profile_name}
           </button>`
        : '';

    modal.innerHTML = `
        <div class="modal-content" style="max-width: 600px;">
            <div class="modal-header">
                <h2>📊 Profile Recommendation</h2>
                <button class="btn-close" onclick="this.closest('.modal-overlay').remove()">×</button>
            </div>
            <div class="modal-body">
                <div style="text-align: center; padding: 20px; background: var(--color-bg-secondary); border-radius: 8px; margin-bottom: 20px;">
                    <div style="font-size: 48px; margin-bottom: 10px;">${recommendation.profile_icon}</div>
                    <h3 style="margin: 10px 0;">${recommendation.profile_name}</h3>
                    <div style="display: inline-block; padding: 6px 12px; background: var(--color-${recommendation.confidence >= 70 ? 'success' : 'warning'}); color: white; border-radius: 4px; font-weight: 600;">
                        ${recommendation.confidence}% Confidence
                    </div>
                </div>

                <div style="margin-bottom: 20px;">
                    <h4 style="margin-bottom: 10px;">Why this profile?</h4>
                    <p style="color: var(--color-text-secondary);">${recommendation.reason}</p>
                    ${allReasonsHtml}
                </div>

                <div style="margin-bottom: 20px;">
                    <h4 style="margin-bottom: 10px;">Current Performance</h4>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                        <div style="padding: 10px; background: var(--color-bg-secondary); border-radius: 4px;">
                            <div style="font-size: 12px; color: var(--color-text-secondary);">Win Rate</div>
                            <div style="font-size: 20px; font-weight: 600;">${metrics.win_rate.toFixed(1)}%</div>
                        </div>
                        <div style="padding: 10px; background: var(--color-bg-secondary); border-radius: 4px;">
                            <div style="font-size: 12px; color: var(--color-text-secondary);">Drawdown</div>
                            <div style="font-size: 20px; font-weight: 600;">${metrics.drawdown_pct.toFixed(1)}%</div>
                        </div>
                        <div style="padding: 10px; background: var(--color-bg-secondary); border-radius: 4px;">
                            <div style="font-size: 12px; color: var(--color-text-secondary);">Volatility</div>
                            <div style="font-size: 20px; font-weight: 600;">${metrics.volatility.toFixed(0)}</div>
                        </div>
                        <div style="padding: 10px; background: var(--color-bg-secondary); border-radius: 4px;">
                            <div style="font-size: 12px; color: var(--color-text-secondary);">Total Trades</div>
                            <div style="font-size: 20px; font-weight: 600;">${metrics.total_trades}</div>
                        </div>
                    </div>
                </div>

                ${currentProfileHtml}
            </div>
            <div class="modal-footer">
                <button class="btn-secondary" onclick="this.closest('.modal-overlay').remove()">Close</button>
                ${applyButtonHtml}
            </div>
        </div>
    `;

    document.body.appendChild(modal);
}

// Show profile comparison
async function showProfileComparison() {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 800px;">
            <div class="modal-header">
                <h2>📊 Compare Risk Profiles</h2>
                <button class="btn-close" onclick="this.closest('.modal-overlay').remove()">×</button>
            </div>
            <div class="modal-body">
                <p>Select profiles to compare (hold Ctrl/Cmd to select multiple):</p>
                <select id="compareProfilesSelect" multiple style="width: 100%; min-height: 150px; margin: 10px 0;">
                    ${allRiskProfiles.map(p => `
                        <option value="${p.id}">${p.icon} ${p.name}</option>
                    `).join('')}
                </select>
            </div>
            <div class="modal-footer">
                <button class="btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                <button class="btn-primary" onclick="executeProfileComparison()">Compare</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
}

// Execute profile comparison
async function executeProfileComparison() {
    const select = document.getElementById('compareProfilesSelect');
    const selectedIds = Array.from(select.selectedOptions).map(opt => parseInt(opt.value));

    if (selectedIds.length < 2) {
        showNotification('Please select at least 2 profiles to compare', 'error');
        return;
    }

    try {
        const response = await fetch('/api/risk-profiles/compare', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({profile_ids: selectedIds})
        });

        if (!response.ok) throw new Error('Failed to compare profiles');

        const data = await response.json();

        // Close selection modal
        document.querySelector('.modal-overlay').remove();

        // Show comparison results
        showComparisonResults(data);
    } catch (error) {
        console.error('Error comparing profiles:', error);
        showNotification('Failed to compare profiles', 'error');
    }
}

// Show comparison results
function showComparisonResults(data) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';

    const profiles = data.profiles;

    modal.innerHTML = `
        <div class="modal-content" style="max-width: 900px;">
            <div class="modal-header">
                <h2>📊 Profile Comparison</h2>
                <button class="btn-close" onclick="this.closest('.modal-overlay').remove()">×</button>
            </div>
            <div class="modal-body">
                <table class="comparison-table">
                    <thead>
                        <tr>
                            <th>Parameter</th>
                            ${profiles.map(p => `<th>${p.icon} ${p.name}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Position Size</strong></td>
                            ${profiles.map(p => `<td>${p.max_position_size_pct}%</td>`).join('')}
                        </tr>
                        <tr>
                            <td><strong>Daily Loss Limit</strong></td>
                            ${profiles.map(p => `<td>${p.max_daily_loss_pct}%</td>`).join('')}
                        </tr>
                        <tr>
                            <td><strong>Max Daily Trades</strong></td>
                            ${profiles.map(p => `<td>${p.max_daily_trades}</td>`).join('')}
                        </tr>
                        <tr>
                            <td><strong>Open Positions</strong></td>
                            ${profiles.map(p => `<td>${p.max_open_positions}</td>`).join('')}
                        </tr>
                        <tr>
                            <td><strong>Cash Reserve</strong></td>
                            ${profiles.map(p => `<td>${p.min_cash_reserve_pct}%</td>`).join('')}
                        </tr>
                        <tr>
                            <td><strong>Max Drawdown</strong></td>
                            ${profiles.map(p => `<td>${p.max_drawdown_pct}%</td>`).join('')}
                        </tr>
                        <tr>
                            <td><strong>Trading Interval</strong></td>
                            ${profiles.map(p => `<td>${p.trading_interval_minutes} min</td>`).join('')}
                        </tr>
                        <tr>
                            <td><strong>Risk Score</strong></td>
                            ${profiles.map(p => {
                                const score = data.comparison.risk_levels[p.name];
                                return `<td><strong>${score.toFixed(0)}/100</strong></td>`;
                            }).join('')}
                        </tr>
                    </tbody>
                </table>
            </div>
            <div class="modal-footer">
                <button class="btn-secondary" onclick="this.closest('.modal-overlay').remove()">Close</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
}

// Setup event listeners for profile buttons
function setupProfileEventListeners() {
    const createBtn = document.getElementById('createCustomProfileBtn');
    const compareBtn = document.getElementById('compareProfilesBtn');

    if (createBtn) {
        createBtn.addEventListener('click', showCreateCustomProfileModal);
    }

    if (compareBtn) {
        compareBtn.addEventListener('click', showProfileComparison);
    }
}

// Show create custom profile modal
function showCreateCustomProfileModal() {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 600px;">
            <div class="modal-header">
                <h2>⚙️ Create Custom Risk Profile</h2>
                <button class="btn-close" onclick="this.closest('.modal-overlay').remove()">×</button>
            </div>
            <div class="modal-body">
                <form id="customProfileForm">
                    <div class="form-group">
                        <label>Profile Name *</label>
                        <input type="text" id="customProfileName" class="form-input" placeholder="e.g., My Custom Strategy" required>
                    </div>

                    <div class="form-group">
                        <label>Description</label>
                        <textarea id="customProfileDescription" class="form-input" rows="2" placeholder="Describe your strategy..."></textarea>
                    </div>

                    <div class="form-group">
                        <label>Icon</label>
                        <input type="text" id="customProfileIcon" class="form-input" value="⭐" maxlength="2">
                    </div>

                    <div class="form-group">
                        <label>Max Position Size (%)</label>
                        <input type="number" id="customMaxPositionSize" class="form-input" value="10" step="0.1" min="1" max="50">
                    </div>

                    <div class="form-group">
                        <label>Max Daily Loss (%)</label>
                        <input type="number" id="customMaxDailyLoss" class="form-input" value="3" step="0.1" min="0.5" max="20">
                    </div>

                    <div class="form-group">
                        <label>Max Daily Trades</label>
                        <input type="number" id="customMaxDailyTrades" class="form-input" value="20" min="1" max="100">
                    </div>

                    <div class="form-group">
                        <label>Max Open Positions</label>
                        <input type="number" id="customMaxOpenPositions" class="form-input" value="5" min="1" max="20">
                    </div>

                    <div class="form-group">
                        <label>Min Cash Reserve (%)</label>
                        <input type="number" id="customMinCashReserve" class="form-input" value="20" min="10" max="80">
                    </div>

                    <div class="form-group">
                        <label>Max Drawdown (%)</label>
                        <input type="number" id="customMaxDrawdown" class="form-input" value="15" min="5" max="50">
                    </div>

                    <div class="form-group">
                        <label>Trading Interval (minutes)</label>
                        <input type="number" id="customTradingInterval" class="form-input" value="60" min="5" max="1440">
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button class="btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                <button class="btn-primary" onclick="createCustomProfile()">Create Profile</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
}

// Create custom profile
async function createCustomProfile() {
    const name = document.getElementById('customProfileName').value.trim();
    const description = document.getElementById('customProfileDescription').value.trim();
    const icon = document.getElementById('customProfileIcon').value.trim();

    if (!name) {
        showNotification('Profile name is required', 'error');
        return;
    }

    const profileData = {
        name: name,
        description: description,
        icon: icon,
        max_position_size_pct: parseFloat(document.getElementById('customMaxPositionSize').value),
        max_daily_loss_pct: parseFloat(document.getElementById('customMaxDailyLoss').value),
        max_daily_trades: parseInt(document.getElementById('customMaxDailyTrades').value),
        max_open_positions: parseInt(document.getElementById('customMaxOpenPositions').value),
        min_cash_reserve_pct: parseFloat(document.getElementById('customMinCashReserve').value),
        max_drawdown_pct: parseFloat(document.getElementById('customMaxDrawdown').value),
        trading_interval_minutes: parseInt(document.getElementById('customTradingInterval').value)
    };

    try {
        const response = await fetch('/api/risk-profiles', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(profileData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to create profile');
        }

        const result = await response.json();

        showNotification(`✓ Profile "${name}" created successfully!`, 'success');

        // Close modal
        document.querySelector('.modal-overlay').remove();

        // Reload profiles
        await loadRiskProfiles();

    } catch (error) {
        console.error('Error creating profile:', error);
        showNotification(`Failed to create profile: ${error.message}`, 'error');
    }
}

// Helper: Get current model ID from dropdown
// Note: Use window.currentModelId if available from enhanced.js, otherwise get from select
function getCurrentModelId() {
    if (typeof window.currentModelId !== 'undefined' && window.currentModelId) {
        return window.currentModelId;
    }
    const select = document.getElementById('modelSelect');
    return select ? parseInt(select.value) : null;
}

// Helper: Check if we're on a specific page
function isOnPage(pageName) {
    const page = document.getElementById(`${pageName}Page`);
    return page && page.classList.contains('active');
}

// Helper: Show notification
function showNotification(message, type = 'info') {
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        border-radius: 6px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
    `;
    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('DOM loaded, initializing risk profiles...');
        initRiskProfiles();
    });
} else {
    console.log('DOM already loaded, initializing risk profiles...');
    initRiskProfiles();
}

// Re-initialize when switching to settings page
document.addEventListener('pageChange', (e) => {
    console.log('Page changed to:', e.detail);
    if (e.detail === 'settings') {
        console.log('Settings page active, re-initializing risk profiles...');
        setTimeout(initRiskProfiles, 100);
    }
});

// Also listen for when elements become visible (in case pages are shown/hidden)
const observer = new MutationObserver(() => {
    const profilesGrid = document.getElementById('profilesGrid');
    if (profilesGrid && profilesGrid.offsetParent !== null && allRiskProfiles.length === 0) {
        console.log('Profiles grid became visible, initializing...');
        initRiskProfiles();
    }
});

// Start observing when the document body is available
if (document.body) {
    observer.observe(document.body, { childList: true, subtree: true });
}

console.log('✓ Risk Profiles JavaScript loaded');

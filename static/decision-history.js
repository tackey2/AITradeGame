// ============================================
// DECISION HISTORY FUNCTIONALITY
// ============================================

let currentDecisionStatus = 'pending';

// Initialize decision history
function initDecisionHistory() {
    setupDecisionTabs();
}

// Setup decision tabs
function setupDecisionTabs() {
    const tabs = document.querySelectorAll('.decision-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Update active tab
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Get status and load decisions
            currentDecisionStatus = tab.dataset.status;
            loadDecisionHistory(currentDecisionStatus);
        });
    });
}

// Load decision history with status filter
async function loadDecisionHistory(status = 'pending') {
    if (!currentModelId) return;

    try {
        // Build URL with filters
        let url = `/api/decision-history?model_id=${currentModelId}`;
        if (status && status !== 'all') {
            url += `&status=${status}`;
        }

        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to load decision history');

        const decisions = await response.json();
        renderDecisionHistory(decisions, status);

        // Update pending count badge
        const pendingCount = status === 'pending' ? decisions.length : 0;
        updatePendingCount(pendingCount);

        // Monitor pending decisions for notifications
        if (status === 'pending' && typeof monitorPendingDecisions === 'function') {
            monitorPendingDecisions(decisions);
        }
    } catch (error) {
        console.error('Failed to load decision history:', error);
        const container = document.getElementById('pendingDecisionsContainer');
        if (container) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-exclamation-triangle"></i>
                    <p>Failed to load decisions</p>
                </div>
            `;
        }
    }
}

// Render decision history
function renderDecisionHistory(decisions, status) {
    const container = document.getElementById('pendingDecisionsContainer');
    if (!container) return;

    if (decisions.length === 0) {
        const statusText = {
            'pending': 'No pending decisions',
            'approved': 'No approved decisions',
            'rejected': 'No rejected decisions',
            'expired': 'No expired decisions',
            'all': 'No decisions yet'
        };

        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-inbox"></i>
                <p>${statusText[status] || 'No decisions'}</p>
            </div>
        `;
        return;
    }

    container.innerHTML = decisions.map(decision => renderDecisionHistoryCard(decision)).join('');

    // Add event listeners for pending decisions only
    if (status === 'pending') {
        document.querySelectorAll('.decision-card').forEach(card => {
            card.addEventListener('click', () => {
                const decisionId = parseInt(card.dataset.decisionId);
                showDecisionDetail(decisionId);
            });
        });
    }
}

// Render decision history card
function renderDecisionHistoryCard(decision) {
    const data = decision.decision_data;
    const signalClass = data.signal.includes('buy') ? 'signal-buy' : 'signal-sell';
    const status = decision.status || 'pending';

    // Status badge
    const statusBadge = `<span class="decision-status-badge status-${status}">
        <i class="bi bi-${getStatusIcon(status)}"></i> ${status.toUpperCase()}
    </span>`;

    // For approved/rejected decisions, show when it was actioned
    const actionInfo = (status === 'approved' || status === 'rejected') && decision.actioned_at
        ? `<div class="decision-action-info">
            ${status === 'approved' ? 'Approved' : 'Rejected'} at ${formatTimestamp(decision.actioned_at)}
           </div>`
        : '';

    // Basic card structure
    const card = `
        <div class="decision-card ${status !== 'pending' ? 'decision-card-readonly' : ''}"
             data-decision-id="${decision.id}"
             style="${status !== 'pending' ? 'opacity: 0.9; cursor: default;' : ''}">
            <div class="decision-header">
                <div class="decision-coin">${decision.coin}</div>
                <div class="decision-signal ${signalClass}">${formatSignal(data.signal)}</div>
            </div>
            ${statusBadge}
            <div class="decision-details">
                <div class="decision-detail">
                    <div class="decision-detail-label">Quantity</div>
                    <div class="decision-detail-value">${data.quantity}</div>
                </div>
                <div class="decision-detail">
                    <div class="decision-detail-label">Leverage</div>
                    <div class="decision-detail-value">${data.leverage}x</div>
                </div>
                <div class="decision-detail">
                    <div class="decision-detail-label">Confidence</div>
                    <div class="decision-detail-value">${(data.confidence * 100).toFixed(0)}%</div>
                </div>
            </div>
            <div class="decision-justification">
                ${data.justification || 'No justification provided'}
            </div>
            ${actionInfo}
            <div class="decision-expires">
                Created: ${formatTimestamp(decision.created_at)}
            </div>
        </div>
    `;

    return card;
}

// Get status icon
function getStatusIcon(status) {
    const icons = {
        'pending': 'clock-history',
        'approved': 'check-circle-fill',
        'rejected': 'x-circle-fill',
        'expired': 'stopwatch'
    };
    return icons[status] || 'question-circle';
}

// Update pending count
function updatePendingCount(count) {
    const badge = document.getElementById('pendingCount');
    if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'inline-block' : 'none';
    }
}

// Override the original loadPendingDecisions to use the new system
const originalLoadPendingDecisions = typeof loadPendingDecisions !== 'undefined' ? loadPendingDecisions : null;

// eslint-disable-next-line no-func-assign
loadPendingDecisions = async function() {
    // Use decision history for pending decisions
    await loadDecisionHistory('pending');
};

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDecisionHistory);
} else {
    initDecisionHistory();
}

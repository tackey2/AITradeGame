// Enhanced Dashboard - Decisions Module
// Pending decisions, approval/rejection, decision modals

// ============================================
// PENDING DECISIONS
// ============================================

async function loadPendingDecisions() {
    try {
        const response = await fetch(`/api/pending-decisions?model_id=${currentModelId}`);
        const decisions = await response.json();

        const container = document.getElementById('pendingDecisionsContainer');
        const countBadge = document.getElementById('pendingCount');

        countBadge.textContent = decisions.length;

        if (decisions.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-inbox"></i>
                    <p>No pending decisions</p>
                </div>
            `;
            // Monitor for notifications
            if (typeof monitorPendingDecisions === 'function') {
                monitorPendingDecisions(decisions);
            }
            return;
        }

        container.innerHTML = decisions.map(decision => renderDecisionCard(decision)).join('');

        // Add event listeners to decision cards
        document.querySelectorAll('.decision-card').forEach(card => {
            card.addEventListener('click', () => {
                const decisionId = parseInt(card.dataset.decisionId);
                showDecisionDetail(decisionId);
            });
        });

        // Monitor pending decisions for notifications
        if (typeof monitorPendingDecisions === 'function') {
            monitorPendingDecisions(decisions);
        }
    } catch (error) {
        console.error('Failed to load pending decisions:', error);
    }
}

function renderDecisionCard(decision) {
    const data = decision.decision_data;
    const signalClass = data.signal.includes('buy') ? 'signal-buy' : 'signal-sell';

    return `
        <div class="decision-card" data-decision-id="${decision.id}">
            <div class="decision-header">
                <div class="decision-coin">${decision.coin}</div>
                <div class="decision-signal ${signalClass}">${formatSignal(data.signal)}</div>
            </div>
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
            <div class="decision-expires">
                Created: ${formatTimestamp(decision.created_at)}
            </div>
        </div>
    `;
}

// ============================================
// DECISION DETAIL MODAL
// ============================================

async function showDecisionDetail(decisionId) {
    try {
        const response = await fetch(`/api/pending-decisions`);
        const decisions = await response.json();
        const decision = decisions.find(d => d.id === decisionId);

        if (!decision) {
            showToast('Decision not found', 'error');
            return;
        }

        currentDecisionId = decisionId;

        const data = decision.decision_data;
        const explanation = decision.explanation_data || {};

        const modalBody = document.getElementById('decisionModalBody');
        modalBody.innerHTML = `
            <div style="margin-bottom: 20px;">
                <h3>${decision.coin} - ${formatSignal(data.signal)}</h3>
            </div>

            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 20px;">
                <div>
                    <div style="color: var(--text-secondary); margin-bottom: 4px;">Quantity</div>
                    <div style="font-weight: 600;">${data.quantity}</div>
                </div>
                <div>
                    <div style="color: var(--text-secondary); margin-bottom: 4px;">Leverage</div>
                    <div style="font-weight: 600;">${data.leverage}x</div>
                </div>
                <div>
                    <div style="color: var(--text-secondary); margin-bottom: 4px;">Confidence</div>
                    <div style="font-weight: 600;">${(data.confidence * 100).toFixed(0)}%</div>
                </div>
                <div>
                    <div style="color: var(--text-secondary); margin-bottom: 4px;">Created</div>
                    <div style="font-weight: 600;">${formatTimestamp(decision.created_at)}</div>
                </div>
            </div>

            ${data.profit_target ? `
                <div style="margin-bottom: 12px;">
                    <div style="color: var(--text-secondary); margin-bottom: 4px;">Profit Target</div>
                    <div style="font-weight: 600;">$${data.profit_target.toFixed(2)}</div>
                </div>
            ` : ''}

            ${data.stop_loss ? `
                <div style="margin-bottom: 12px;">
                    <div style="color: var(--text-secondary); margin-bottom: 4px;">Stop Loss</div>
                    <div style="font-weight: 600;">$${data.stop_loss.toFixed(2)}</div>
                </div>
            ` : ''}

            <div style="margin-bottom: 20px;">
                <h4 style="margin-bottom: 12px;">Justification</h4>
                <div style="padding: 12px; background: var(--bg-primary); border-radius: 6px;">
                    ${data.justification || 'No justification provided'}
                </div>
            </div>

            ${explanation.decision_summary ? `
                <div style="margin-bottom: 20px;">
                    <h4 style="margin-bottom: 12px;">AI Explanation</h4>
                    <div style="padding: 12px; background: var(--bg-primary); border-radius: 6px;">
                        ${explanation.decision_summary}
                    </div>
                </div>
            ` : ''}

            ${explanation.market_analysis ? `
                <div style="margin-bottom: 20px;">
                    <h4 style="margin-bottom: 12px;">Market Analysis</h4>
                    <div style="padding: 12px; background: var(--bg-primary); border-radius: 6px; white-space: pre-wrap;">
                        ${typeof explanation.market_analysis === 'object'
                            ? JSON.stringify(explanation.market_analysis, null, 2)
                            : explanation.market_analysis}
                    </div>
                </div>
            ` : ''}
        `;

        document.getElementById('decisionModal').classList.add('active');
    } catch (error) {
        console.error('Failed to load decision detail:', error);
        showToast('Failed to load decision details', 'error');
    }
}

function closeModal() {
    document.getElementById('decisionModal').classList.remove('active');
    currentDecisionId = null;
}

async function approveDecision() {
    if (!currentDecisionId) return;

    try {
        const response = await fetch(`/api/pending-decisions/${currentDecisionId}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ modified: false })
        });

        const result = await response.json();

        if (result.success || response.ok) {
            showToast('Decision approved and executed');
            closeModal();
            loadPendingDecisions();
        } else {
            showToast(result.error || 'Failed to approve decision', 'error');
        }
    } catch (error) {
        console.error('Failed to approve decision:', error);
        showToast('Failed to approve decision', 'error');
    }
}

async function rejectDecision() {
    if (!currentDecisionId) return;

    const reason = prompt('Reason for rejection (optional):');

    try {
        const response = await fetch(`/api/pending-decisions/${currentDecisionId}/reject`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reason: reason || 'User rejected' })
        });

        const result = await response.json();

        if (result.success || response.ok) {
            showToast('Decision rejected');
            closeModal();
            loadPendingDecisions();
        } else {
            showToast(result.error || 'Failed to reject decision', 'error');
        }
    } catch (error) {
        console.error('Failed to reject decision:', error);
        showToast('Failed to reject decision', 'error');
    }
}

function modifyDecision() {
    showToast('Modify feature coming soon', 'info');
}

console.log('✓ Enhanced Decisions Module Loaded');

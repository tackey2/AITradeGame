// Cost Breakdown Widget

async function loadCostBreakdown(modelId) {
    if (!modelId) return;

    try {
        const response = await fetch(`/api/models/${modelId}/cost-breakdown`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        renderCostBreakdown(data);

        // Show section
        document.getElementById('costBreakdownSection').style.display = 'block';

    } catch (error) {
        console.error('Failed to load cost breakdown:', error);
        document.getElementById('costBreakdownSection').style.display = 'none';
    }
}

function renderCostBreakdown(data) {
    const card = document.getElementById('costBreakdownCard');

    const costs = data.costs;
    const profitability = data.profitability;

    // Determine profitability status
    const isProfitable = profitability.net_pnl > 0;
    const statusClass = isProfitable ? 'profitable' : 'unprofitable';

    let html = `
        <div class="cost-breakdown-content">
            <!-- Profitability Summary -->
            <div class="profitability-summary ${statusClass}">
                <div class="summary-row">
                    <div class="summary-item">
                        <div class="summary-label">Gross P&L</div>
                        <div class="summary-value ${profitability.gross_pnl >= 0 ? 'positive' : 'negative'}">
                            ${profitability.gross_pnl >= 0 ? '+' : ''}$${profitability.gross_pnl.toFixed(2)}
                            <span class="summary-pct">(${profitability.gross_pnl_pct >= 0 ? '+' : ''}${profitability.gross_pnl_pct.toFixed(2)}%)</span>
                        </div>
                    </div>
                    <div class="summary-divider">−</div>
                    <div class="summary-item">
                        <div class="summary-label">Total Costs</div>
                        <div class="summary-value cost">
                            −$${costs.total.amount.toFixed(2)}
                            <span class="summary-pct">(${costs.total.percentage.toFixed(2)}%)</span>
                        </div>
                    </div>
                    <div class="summary-divider">=</div>
                    <div class="summary-item highlight">
                        <div class="summary-label">Net P&L</div>
                        <div class="summary-value ${profitability.net_pnl >= 0 ? 'positive' : 'negative'}">
                            ${profitability.net_pnl >= 0 ? '+' : ''}$${profitability.net_pnl.toFixed(2)}
                            <span class="summary-pct">(${profitability.net_pnl_pct >= 0 ? '+' : ''}${profitability.net_pnl_pct.toFixed(2)}%)</span>
                        </div>
                    </div>
                </div>
                ${profitability.cost_impact > 0 ? `
                    <div class="cost-impact-warning">
                        <i class="bi bi-exclamation-triangle"></i>
                        Costs reduced profit by $${profitability.cost_impact.toFixed(2)}
                    </div>
                ` : ''}
            </div>

            <!-- Cost Breakdown Table -->
            <div class="cost-breakdown-table">
                <table>
                    <thead>
                        <tr>
                            <th>Cost Type</th>
                            <th>Amount</th>
                            <th>% of Capital</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        <!-- Trading Fees -->
                        <tr>
                            <td>
                                <i class="bi bi-cash-coin"></i>
                                <strong>Trading Fees</strong>
                            </td>
                            <td class="cost-amount">$${costs.trading_fees.amount.toFixed(2)}</td>
                            <td class="cost-pct">${costs.trading_fees.percentage.toFixed(3)}%</td>
                            <td class="cost-desc">${costs.trading_fees.description}</td>
                        </tr>

                        <!-- Slippage -->
                        <tr>
                            <td>
                                <i class="bi bi-arrow-down-up"></i>
                                <strong>Slippage</strong>
                            </td>
                            <td class="cost-amount">$${costs.slippage.amount.toFixed(2)}</td>
                            <td class="cost-pct">${costs.slippage.percentage.toFixed(3)}%</td>
                            <td class="cost-desc">${costs.slippage.description}</td>
                        </tr>

                        <!-- AI Costs -->
                        <tr>
                            <td>
                                <i class="bi bi-robot"></i>
                                <strong>AI API Costs</strong>
                            </td>
                            <td class="cost-amount">$${costs.ai_costs.amount.toFixed(4)}</td>
                            <td class="cost-pct">${costs.ai_costs.percentage.toFixed(4)}%</td>
                            <td class="cost-desc">
                                ${costs.ai_costs.description}
                                ${renderAICostBreakdown(costs.ai_costs.breakdown)}
                            </td>
                        </tr>

                        <!-- Total -->
                        <tr class="total-row">
                            <td><strong>Total Costs</strong></td>
                            <td class="cost-amount"><strong>$${costs.total.amount.toFixed(2)}</strong></td>
                            <td class="cost-pct"><strong>${costs.total.percentage.toFixed(3)}%</strong></td>
                            <td></td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- Cost Insights -->
            <div class="cost-insights">
                <div class="insight-item">
                    <div class="insight-icon">📊</div>
                    <div class="insight-text">
                        <strong>${data.trade_count}</strong> trades executed
                    </div>
                </div>
                <div class="insight-item">
                    <div class="insight-icon">💰</div>
                    <div class="insight-text">
                        Average cost per trade: <strong>$${(costs.total.amount / data.trade_count).toFixed(2)}</strong>
                    </div>
                </div>
                <div class="insight-item">
                    <div class="insight-icon">${isProfitable ? '✅' : '⚠️'}</div>
                    <div class="insight-text">
                        ${isProfitable
                            ? `<strong>Profitable</strong> after all costs`
                            : `<strong>Unprofitable</strong> - costs exceed gross profit`}
                    </div>
                </div>
            </div>
        </div>
    `;

    card.innerHTML = html;
}

function renderAICostBreakdown(breakdown) {
    if (!breakdown || Object.keys(breakdown).length === 0) {
        return '';
    }

    const items = Object.entries(breakdown).map(([type, cost]) => {
        return `<span class="ai-cost-item">${type}: $${cost.toFixed(4)}</span>`;
    }).join(', ');

    return `<br><small class="ai-cost-breakdown">(${items})</small>`;
}

// Refresh button handler
document.addEventListener('DOMContentLoaded', () => {
    const refreshBtn = document.getElementById('refreshCostBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            if (currentModelId) {
                loadCostBreakdown(currentModelId);
                if (typeof showToast === 'function') {
                    showToast('Refreshing cost breakdown...', 'info');
                }
            }
        });
    }
});

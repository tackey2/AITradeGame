// Benchmark Comparison Widget

async function loadBenchmarkComparison(modelId) {
    if (!modelId) return;

    try {
        const response = await fetch(`/api/models/${modelId}/benchmark-comparison`);

        if (response.status === 400) {
            // No trades yet
            const data = await response.json();
            renderNoBenchmarkData(data.message);
            return;
        }

        const data = await response.json();
        renderBenchmarkComparison(data);

        // Show section
        document.getElementById('benchmarkComparisonSection').style.display = 'block';

    } catch (error) {
        console.error('Failed to load benchmark comparison:', error);
        document.getElementById('benchmarkComparisonSection').style.display = 'none';
    }
}

function renderNoBenchmarkData(message) {
    const card = document.getElementById('benchmarkComparisonCard');
    card.innerHTML = `
        <div class="empty-state">
            <i class="bi bi-graph-up"></i>
            <p>${message || 'No trading history to compare'}</p>
            <small>Make some trades to see benchmark comparison</small>
        </div>
    `;
    document.getElementById('benchmarkComparisonSection').style.display = 'block';
}

function renderBenchmarkComparison(data) {
    const card = document.getElementById('benchmarkComparisonCard');

    const modelPerf = data.model_performance;
    const verdict = data.verdict;

    // Determine if model is winning
    const isWinning = verdict.recommendation === 'use_ai';
    const isMixed = verdict.recommendation === 'use_ai_conditional';

    let html = `
        <div class="benchmark-content">
            <!-- Verdict Banner -->
            <div class="verdict-banner verdict-${verdict.recommendation}">
                <div class="verdict-icon">${verdict.icon || '📊'}</div>
                <div class="verdict-text">
                    <h3>${verdict.message}</h3>
                    <p class="verdict-subtitle">Based on ${data.testing_period.start} to ${data.testing_period.end}</p>
                </div>
            </div>

            <!-- Performance Comparison Table -->
            <div class="benchmark-table">
                <table>
                    <thead>
                        <tr>
                            <th>Strategy</th>
                            <th>Return</th>
                            <th>Trades</th>
                            <th>Win Rate</th>
                            <th>Result</th>
                        </tr>
                    </thead>
                    <tbody>
                        <!-- AI Model Row -->
                        <tr class="model-row ${isWinning ? 'winning' : ''}">
                            <td>
                                <strong>🤖 ${data.model_name}</strong>
                                <div class="strategy-type">AI Trading</div>
                            </td>
                            <td>
                                <span class="return-value ${modelPerf.return_pct >= 0 ? 'positive' : 'negative'}">
                                    ${modelPerf.return_pct >= 0 ? '+' : ''}${modelPerf.return_pct}%
                                </span>
                                <div class="capital-change">$${modelPerf.initial_capital.toFixed(0)} → $${modelPerf.current_value.toFixed(0)}</div>
                            </td>
                            <td>${modelPerf.total_trades}</td>
                            <td>${modelPerf.win_rate}%</td>
                            <td>
                                ${isWinning ? '<span class="badge-success">🏆 Best</span>' :
                                  isMixed ? '<span class="badge-warning">⚖️ Mixed</span>' :
                                           '<span class="badge-danger">📉 Losing</span>'}
                            </td>
                        </tr>

                        <!-- Benchmark Rows -->
                        ${data.benchmarks.map(benchmark => {
                            if (benchmark.return_pct === null) {
                                return `
                                    <tr class="benchmark-row unavailable">
                                        <td>
                                            ${benchmark.name}
                                            <div class="strategy-type">Passive</div>
                                        </td>
                                        <td colspan="3" class="unavailable-text">
                                            ${benchmark.note || 'Data unavailable'}
                                        </td>
                                        <td>—</td>
                                    </tr>
                                `;
                            }

                            const outperformed = benchmark.outperformed;
                            return `
                                <tr class="benchmark-row ${!outperformed ? 'winning' : ''}">
                                    <td>
                                        ${benchmark.name}
                                        <div class="strategy-type">Passive</div>
                                    </td>
                                    <td>
                                        <span class="return-value ${benchmark.return_pct >= 0 ? 'positive' : 'negative'}">
                                            ${benchmark.return_pct >= 0 ? '+' : ''}${benchmark.return_pct}%
                                        </span>
                                    </td>
                                    <td>—</td>
                                    <td>—</td>
                                    <td>
                                        ${outperformed ?
                                            '<span class="badge-secondary">AI Wins</span>' :
                                            '<span class="badge-success">🏆 Best</span>'}
                                    </td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>

            <!-- Quick Stats -->
            <div class="benchmark-stats">
                <div class="stat-item">
                    <div class="stat-label">Your P&L</div>
                    <div class="stat-value ${modelPerf.total_pnl >= 0 ? 'positive' : 'negative'}">
                        ${modelPerf.total_pnl >= 0 ? '+' : ''}$${modelPerf.total_pnl.toFixed(2)}
                    </div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Total Trades</div>
                    <div class="stat-value">${modelPerf.total_trades}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Win Rate</div>
                    <div class="stat-value">${modelPerf.win_rate}%</div>
                </div>
            </div>
        </div>
    `;

    card.innerHTML = html;
}

// Refresh button handler
document.addEventListener('DOMContentLoaded', () => {
    const refreshBtn = document.getElementById('refreshBenchmarkBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            if (currentModelId) {
                loadBenchmarkComparison(currentModelId);
                showToast('Refreshing benchmark comparison...', 'info');
            }
        });
    }
});

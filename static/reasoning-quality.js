// Reasoning Quality Widget

async function loadReasoningQuality(modelId) {
    if (!modelId) return;

    try {
        const response = await fetch(`/api/models/${modelId}/reasoning-quality?days=30`);

        if (response.status === 404 || response.status === 500) {
            // No evaluations yet
            renderNoReasoningData();
            return;
        }

        const data = await response.json();
        renderReasoningQuality(data);

        // Show section
        document.getElementById('reasoningQualitySection').style.display = 'block';

    } catch (error) {
        console.error('Failed to load reasoning quality:', error);
        document.getElementById('reasoningQualitySection').style.display = 'none';
    }
}

function renderNoReasoningData() {
    const card = document.getElementById('reasoningQualityCard');
    card.innerHTML = `
        <div class="empty-state">
            <i class="bi bi-brain"></i>
            <p>No reasoning evaluations yet</p>
            <small>AI will evaluate reasoning quality as trading decisions are made</small>
        </div>
    `;
    document.getElementById('reasoningQualitySection').style.display = 'block';
}

function renderReasoningQuality(data) {
    const card = document.getElementById('reasoningQualityCard');
    const stats = data.statistics;
    const status = data.quality_status;

    // Check if there are any evaluations
    if (stats.total_evaluations === 0) {
        renderNoReasoningData();
        return;
    }

    let html = `
        <div class="reasoning-quality-content">
            <!-- Quality Score Overview -->
            <div class="quality-overview">
                <div class="quality-circle" style="background: conic-gradient(${status.color} ${stats.average_scores.overall * 72}deg, #2a2e39 0deg);">
                    <div class="quality-inner">
                        <div class="quality-score">${stats.average_scores.overall.toFixed(1)}</div>
                        <div class="quality-max">/5.0</div>
                    </div>
                </div>
                <div class="quality-summary">
                    <h3>${status.icon} ${status.label} Reasoning Quality</h3>
                    <p class="quality-subtitle">
                        Based on ${stats.total_evaluations} evaluation${stats.total_evaluations !== 1 ? 's' : ''}
                        over the last ${data.time_period_days} days
                    </p>
                    <div class="quality-trend">
                        <span class="trend-label">Trend:</span>
                        <span class="trend-badge trend-${stats.trend.direction}">
                            ${getTrendIcon(stats.trend.direction)} ${formatTrend(stats.trend)}
                        </span>
                    </div>
                </div>
            </div>

            <!-- Quality Breakdown -->
            <div class="quality-breakdown">
                <h4>Quality Dimensions</h4>
                <div class="quality-dimensions">
                    ${renderDimension('Logical Consistency', stats.average_scores.logical_consistency, 'How well the reasoning flows logically')}
                    ${renderDimension('Evidence Usage', stats.average_scores.evidence_usage, 'Use of market data and indicators')}
                    ${renderDimension('Risk Awareness', stats.average_scores.risk_awareness, 'Consideration of potential downsides')}
                    ${renderDimension('Clarity', stats.average_scores.clarity, 'How clear and understandable the reasoning is')}
                </div>
            </div>

            <!-- Low Quality Alerts -->
            ${stats.low_quality_decisions.length > 0 ? renderLowQualityAlerts(stats.low_quality_decisions) : ''}

            <!-- Recent Insights -->
            <div class="quality-insights">
                <h4>Insights</h4>
                <div class="insight-item">
                    <i class="bi bi-info-circle"></i>
                    <span>Score range: ${stats.score_range.min.toFixed(1)} - ${stats.score_range.max.toFixed(1)}</span>
                </div>
                <div class="insight-item">
                    <i class="bi bi-graph-up"></i>
                    <span>${getInsightText(stats)}</span>
                </div>
            </div>
        </div>
    `;

    card.innerHTML = html;
}

function renderDimension(name, score, description) {
    const percentage = (score / 5) * 100;
    const color = getScoreColor(score);

    return `
        <div class="dimension-item">
            <div class="dimension-header">
                <span class="dimension-name">${name}</span>
                <span class="dimension-score" style="color: ${color}">${score.toFixed(1)}/5.0</span>
            </div>
            <div class="dimension-bar-container">
                <div class="dimension-bar" style="width: ${percentage}%; background: ${color}"></div>
            </div>
            <div class="dimension-description">${description}</div>
        </div>
    `;
}

function renderLowQualityAlerts(decisions) {
    return `
        <div class="low-quality-alerts">
            <h4>⚠️ Recent Low-Quality Decisions</h4>
            <p class="alert-description">These decisions had reasoning scores below 3.5 and may need review:</p>
            <div class="alert-list">
                ${decisions.map(d => `
                    <div class="alert-item">
                        <div class="alert-header">
                            <span class="alert-score">Score: ${d.overall_score.toFixed(1)}</span>
                            <span class="alert-time">${formatTimestamp(d.timestamp)}</span>
                        </div>
                        <div class="alert-feedback">${d.feedback}</div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

function getScoreColor(score) {
    if (score >= 4.0) return '#28a745';  // green
    if (score >= 3.5) return '#ffc107';  // yellow
    if (score >= 3.0) return '#fd7e14';  // orange
    return '#dc3545';  // red
}

function getTrendIcon(direction) {
    if (direction === 'improving') return '📈';
    if (direction === 'declining') return '📉';
    return '➡️';
}

function formatTrend(trend) {
    if (trend.direction === 'stable') {
        return 'Stable';
    }

    const change = Math.abs(trend.recent_avg - trend.previous_avg).toFixed(2);
    return `${trend.direction === 'improving' ? 'Improving' : 'Declining'} (${change} pts)`;
}

function getInsightText(stats) {
    const avg = stats.average_scores.overall;

    if (avg >= 4.0) {
        return 'Excellent reasoning quality! The AI is providing well-thought-out decisions.';
    } else if (avg >= 3.5) {
        return 'Good reasoning quality with room for improvement in some areas.';
    } else if (avg >= 3.0) {
        return 'Fair reasoning quality. Consider reviewing decision prompts or model configuration.';
    } else {
        return 'Reasoning quality needs improvement. Review recent low-quality decisions.';
    }
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return `${Math.floor(diffMins / 1440)}d ago`;
}

// Refresh button handler
document.addEventListener('DOMContentLoaded', () => {
    const refreshBtn = document.getElementById('refreshReasoningBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            if (currentModelId) {
                loadReasoningQuality(currentModelId);
                if (typeof showToast === 'function') {
                    showToast('Refreshing reasoning quality...', 'info');
                }
            }
        });
    }
});

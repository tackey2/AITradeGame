// ============================================
// MULTI-MODEL COMPARISON
// ============================================

let comparisonChart = null;
let selectedModelsForComparison = [];
let allAvailableModels = [];

// Initialize comparison system
function initModelComparison() {
    const compareBtn = document.getElementById('compareModelsBtn');
    if (compareBtn) {
        compareBtn.addEventListener('click', openCompareModelsModal);
    }
}

// Open comparison modal
async function openCompareModelsModal() {
    const modal = document.getElementById('compareModelsModal');
    if (!modal) return;

    // Load available models
    await loadAvailableModelsForComparison();

    // Use class-based toggling instead of inline styles
    modal.classList.add('active');

    // Initialize chart if not already done
    if (!comparisonChart) {
        const chartDom = document.getElementById('comparisonChart');
        if (chartDom && typeof echarts !== 'undefined') {
            comparisonChart = echarts.init(chartDom);
        }
    }
}

// Close comparison modal
function closeCompareModelsModal() {
    const modal = document.getElementById('compareModelsModal');
    if (modal) {
        // Use class-based toggling instead of inline styles
        modal.classList.remove('active');
    }
}

// Load available models for comparison
async function loadAvailableModelsForComparison() {
    try {
        const response = await fetch('/api/models');
        const models = await response.json();

        allAvailableModels = models;

        // Render model checkboxes
        const container = document.getElementById('comparisonModelCheckboxes');
        if (!container) return;

        container.innerHTML = models.map(model => `
            <label class="model-checkbox-label">
                <input type="checkbox"
                       class="model-checkbox"
                       value="${model.id}"
                       onchange="handleModelSelectionChange(${model.id}, this.checked)">
                <span class="model-checkbox-text">
                    <strong>${model.name}</strong>
                    <small>ID: ${model.id}</small>
                </span>
            </label>
        `).join('');

        // Show compare button if multiple models exist
        const compareBtn = document.getElementById('compareModelsBtn');
        if (compareBtn && models.length >= 2) {
            compareBtn.style.display = 'inline-flex';
        }

    } catch (error) {
        console.error('Failed to load models for comparison:', error);
    }
}

// Handle model selection change
function handleModelSelectionChange(modelId, isChecked) {
    if (isChecked) {
        if (selectedModelsForComparison.length < 5) {
            selectedModelsForComparison.push(modelId);
        } else {
            // Uncheck if trying to select more than 5
            event.target.checked = false;
            showToast('Maximum 5 models can be compared', 'warning');
            return;
        }
    } else {
        selectedModelsForComparison = selectedModelsForComparison.filter(id => id !== modelId);
    }

    // Update comparison if at least 2 models selected
    if (selectedModelsForComparison.length >= 2) {
        loadComparisonData();
    } else {
        clearComparisonDisplay();
    }
}

// Load comparison data for selected models
async function loadComparisonData() {
    try {
        // Fetch data for all selected models in parallel
        const promises = selectedModelsForComparison.map(async modelId => {
            const [portfolio, analytics] = await Promise.all([
                fetch(`/api/models/${modelId}/portfolio`).then(r => r.json()),
                fetch(`/api/models/${modelId}/performance-analytics`).then(r => r.json())
            ]);

            const model = allAvailableModels.find(m => m.id === modelId);

            return {
                id: modelId,
                name: model ? model.name : `Model ${modelId}`,
                portfolio: portfolio,
                analytics: analytics,
                history: portfolio.account_value_history || []
            };
        });

        const modelData = await Promise.all(promises);

        // Render comparison
        renderComparisonChart(modelData);
        renderComparisonTable(modelData);

    } catch (error) {
        console.error('Failed to load comparison data:', error);
        showToast('Failed to load comparison data', 'error');
    }
}

// Render comparison chart
function renderComparisonChart(modelData) {
    if (!comparisonChart) return;

    const colors = ['#3370ff', '#ff6b35', '#00b96b', '#722ed1', '#fa8c16'];

    // Collect all timestamps
    const allTimestamps = new Set();
    modelData.forEach(model => {
        model.history.forEach(point => {
            allTimestamps.add(point.timestamp);
        });
    });

    // Sort timestamps
    const timeAxis = Array.from(allTimestamps).sort((a, b) => {
        return new Date(a).getTime() - new Date(b).getTime();
    });

    // Format time labels
    const formattedTimeAxis = timeAxis.map(timestamp => {
        const date = new Date(timestamp);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    });

    // Prepare series data
    const series = modelData.map((model, index) => {
        // Create value map for this model
        const valueMap = {};
        model.history.forEach(point => {
            valueMap[point.timestamp] = point.total_value;
        });

        // Map to time axis
        const data = timeAxis.map(timestamp => valueMap[timestamp] || null);

        return {
            name: model.name,
            type: 'line',
            smooth: true,
            data: data,
            connectNulls: true,
            lineStyle: {
                color: colors[index % colors.length],
                width: 2
            },
            itemStyle: {
                color: colors[index % colors.length]
            },
            emphasis: {
                focus: 'series'
            }
        };
    });

    const option = {
        backgroundColor: 'transparent',
        tooltip: {
            trigger: 'axis',
            backgroundColor: '#1a1f2e',
            borderColor: '#3c4556',
            textStyle: { color: '#e8eaed' },
            formatter: function(params) {
                let result = params[0].axisValue + '<br/>';
                params.forEach(param => {
                    if (param.value !== null) {
                        result += `${param.marker} ${param.seriesName}: $${param.value.toLocaleString()}<br/>`;
                    }
                });
                return result;
            }
        },
        legend: {
            data: modelData.map(m => m.name),
            bottom: 0,
            textStyle: { color: '#9aa0a6' }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '15%',
            top: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: formattedTimeAxis,
            axisLine: { lineStyle: { color: '#3c4556' } },
            axisLabel: {
                color: '#9aa0a6',
                rotate: 45
            }
        },
        yAxis: {
            type: 'value',
            scale: true,
            axisLine: { lineStyle: { color: '#3c4556' } },
            axisLabel: {
                color: '#9aa0a6',
                formatter: '${value}'
            },
            splitLine: { lineStyle: { color: '#252d3d' } }
        },
        series: series
    };

    comparisonChart.setOption(option);
}

// Render comparison table
function renderComparisonTable(modelData) {
    const tbody = document.getElementById('comparisonTableBody');
    if (!tbody) return;

    tbody.innerHTML = modelData.map(model => {
        const totalValue = model.portfolio.portfolio.total_value;
        const initialCapital = model.portfolio.portfolio.initial_capital || totalValue;
        const totalReturn = totalValue - initialCapital;
        const totalReturnPct = (totalReturn / initialCapital * 100);

        const winRate = model.analytics.win_rate || 0;
        const sharpeRatio = model.analytics.sharpe_ratio || 0;
        const maxDrawdown = model.analytics.max_drawdown_pct || 0;
        const totalTrades = model.analytics.total_trades || 0;

        const returnClass = totalReturn >= 0 ? 'positive' : 'negative';

        return `
            <tr>
                <td><strong>${model.name}</strong></td>
                <td>$${totalValue.toFixed(2)}</td>
                <td class="${returnClass}">
                    ${totalReturn >= 0 ? '+' : ''}$${totalReturn.toFixed(2)}
                    (${totalReturnPct >= 0 ? '+' : ''}${totalReturnPct.toFixed(2)}%)
                </td>
                <td>${winRate.toFixed(1)}%</td>
                <td>${sharpeRatio.toFixed(2)}</td>
                <td class="negative">-${maxDrawdown.toFixed(2)}%</td>
                <td>${totalTrades}</td>
            </tr>
        `;
    }).join('');
}

// Clear comparison display
function clearComparisonDisplay() {
    const tbody = document.getElementById('comparisonTableBody');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="7">Select at least 2 models to compare</td></tr>';
    }

    if (comparisonChart) {
        comparisonChart.clear();
    }
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initModelComparison);
} else {
    initModelComparison();
}

// Export for global access
window.openCompareModelsModal = openCompareModelsModal;
window.closeCompareModelsModal = closeCompareModelsModal;
window.handleModelSelectionChange = handleModelSelectionChange;

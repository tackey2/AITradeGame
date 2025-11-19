// Enhanced Dashboard - Analytics Module
// Asset allocation, performance analytics, AI conversations

// ============================================
// ANALYTICS VARIABLES
// ============================================

let assetAllocationChart = null;
let conversationsData = [];

// ============================================
// ASSET ALLOCATION CHART
// ============================================

function initAssetAllocationChart() {
    const chartDom = document.getElementById('assetAllocationChart');
    if (!chartDom) return;

    // Safety check: Ensure ECharts library is loaded
    if (typeof echarts === 'undefined') {
        console.error('ECharts library not loaded yet. Retrying in 500ms...');
        setTimeout(initAssetAllocationChart, 500);
        return;
    }

    // Dispose existing chart first to prevent memory leak
    if (assetAllocationChart) {
        assetAllocationChart.dispose();
    }

    assetAllocationChart = echarts.init(chartDom);

    const option = {
        tooltip: {
            trigger: 'item',
            formatter: '{b}: ${c} ({d}%)',
            backgroundColor: 'rgba(0, 0, 0, 0.9)',
            borderColor: '#333',
            textStyle: {
                color: '#fff'
            }
        },
        series: [{
            name: 'Asset Allocation',
            type: 'pie',
            radius: ['45%', '70%'],
            avoidLabelOverlap: true,
            itemStyle: {
                borderRadius: 8,
                borderColor: '#1a1a1a',
                borderWidth: 2
            },
            label: {
                show: false
            },
            emphasis: {
                label: {
                    show: true,
                    fontSize: 16,
                    fontWeight: 'bold'
                },
                itemStyle: {
                    shadowBlur: 10,
                    shadowOffsetX: 0,
                    shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
            },
            data: []
        }]
    };

    assetAllocationChart.setOption(option);

    // Resize chart on window resize
    window.addEventListener('resize', () => {
        assetAllocationChart?.resize();
    });
}

async function loadAssetAllocation() {
    if (!currentModelId) return;

    try {
        const response = await fetch(`/api/models/${currentModelId}/asset-allocation`);
        if (!response.ok) throw new Error('Failed to load asset allocation');

        const data = await response.json();

        // Update chart
        if (assetAllocationChart) {
            const chartData = data.allocations.map(item => ({
                name: item.name,
                value: item.value,
                itemStyle: {
                    color: item.color
                }
            }));

            assetAllocationChart.setOption({
                series: [{
                    data: chartData
                }]
            });
        }

        // Update legend
        updateAllocationLegend(data.allocations);

        // Update timestamp
        const timestamp = new Date(data.timestamp);
        document.getElementById('allocationTimestamp').textContent =
            `Updated: ${timestamp.toLocaleTimeString()}`;

    } catch (error) {
        console.error('Error loading asset allocation:', error);
        showToast('Failed to load asset allocation', 'error');
    }
}

function updateAllocationLegend(allocations) {
    const legendContainer = document.getElementById('allocationLegend');
    if (!legendContainer) return;

    if (allocations.length === 0) {
        legendContainer.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-pie-chart"></i>
                <p>No allocations yet</p>
            </div>
        `;
        return;
    }

    legendContainer.innerHTML = allocations.map(item => `
        <div class="allocation-legend-item">
            <div class="allocation-legend-left">
                <div class="allocation-color-dot" style="background: ${item.color}"></div>
                <span class="allocation-name">${item.name}</span>
            </div>
            <div class="allocation-legend-right">
                <span class="allocation-percentage">${item.percentage.toFixed(1)}%</span>
                <span class="allocation-value">$${item.value.toFixed(2)}</span>
            </div>
        </div>
    `).join('');
}

// ============================================
// PERFORMANCE ANALYTICS
// ============================================

async function loadPerformanceAnalytics() {
    if (!currentModelId) return;

    try {
        const response = await fetch(`/api/models/${currentModelId}/performance-analytics`);
        if (!response.ok) throw new Error('Failed to load performance analytics');

        const data = await response.json();

        // Update Sharpe Ratio
        const sharpeEl = document.getElementById('sharpeRatio');
        if (sharpeEl) {
            sharpeEl.textContent = data.sharpe_ratio.toFixed(2);
            sharpeEl.className = 'perf-metric-value';
            if (data.sharpe_ratio > 1) sharpeEl.classList.add('positive');
            else if (data.sharpe_ratio < 0) sharpeEl.classList.add('negative');
        }

        // Update Max Drawdown
        const drawdownEl = document.getElementById('maxDrawdown');
        if (drawdownEl) {
            drawdownEl.textContent = `-${data.max_drawdown_pct.toFixed(2)}%`;
            drawdownEl.className = 'perf-metric-value negative';
        }

        // Update Win Streak
        const winStreakEl = document.getElementById('winStreak');
        if (winStreakEl) {
            winStreakEl.textContent = data.win_streak;
            winStreakEl.className = 'perf-metric-value';
            if (data.current_win_streak > 0) {
                winStreakEl.textContent += ` (${data.current_win_streak} current)`;
                winStreakEl.classList.add('positive');
            }
        }

        // Update Loss Streak
        const lossStreakEl = document.getElementById('lossStreak');
        if (lossStreakEl) {
            lossStreakEl.textContent = data.loss_streak;
            lossStreakEl.className = 'perf-metric-value';
            if (data.current_loss_streak > 0) {
                lossStreakEl.textContent += ` (${data.current_loss_streak} current)`;
                lossStreakEl.classList.add('negative');
            }
        }

        // Update Best Trade
        const bestTradeEl = document.getElementById('bestTrade');
        if (bestTradeEl) {
            bestTradeEl.textContent = `$${data.best_trade.toFixed(2)}`;
            bestTradeEl.className = 'perf-metric-value positive';
        }

        // Update Worst Trade
        const worstTradeEl = document.getElementById('worstTrade');
        if (worstTradeEl) {
            worstTradeEl.textContent = `$${data.worst_trade.toFixed(2)}`;
            worstTradeEl.className = 'perf-metric-value negative';
        }

        // Update Avg Win
        const avgWinEl = document.getElementById('avgWin');
        if (avgWinEl) {
            avgWinEl.textContent = `$${data.avg_win.toFixed(2)}`;
            avgWinEl.className = 'perf-metric-value positive';
        }

        // Update Avg Loss
        const avgLossEl = document.getElementById('avgLoss');
        if (avgLossEl) {
            avgLossEl.textContent = `$${data.avg_loss.toFixed(2)}`;
            avgLossEl.className = 'perf-metric-value negative';
        }

        // Update Profit Factor
        const profitFactorEl = document.getElementById('profitFactor');
        if (profitFactorEl) {
            profitFactorEl.textContent = data.profit_factor.toFixed(2);
            profitFactorEl.className = 'perf-metric-value';
            if (data.profit_factor > 1) profitFactorEl.classList.add('positive');
            else if (data.profit_factor < 1) profitFactorEl.classList.add('negative');
        }

        // Update Win Rate
        const winRateEl = document.getElementById('winRate');
        if (winRateEl) {
            winRateEl.textContent = `${data.win_rate.toFixed(1)}%`;
            winRateEl.className = 'perf-metric-value';
            if (data.win_rate >= 50) winRateEl.classList.add('positive');
            else winRateEl.classList.add('negative');
        }

        // Update Total Return
        const totalReturnEl = document.getElementById('totalReturn');
        if (totalReturnEl) {
            totalReturnEl.textContent = `$${data.total_return.toFixed(2)} (${data.total_return_pct >= 0 ? '+' : ''}${data.total_return_pct.toFixed(2)}%)`;
            totalReturnEl.className = 'perf-metric-value';
            if (data.total_return > 0) totalReturnEl.classList.add('positive');
            else if (data.total_return < 0) totalReturnEl.classList.add('negative');
        }

    } catch (error) {
        console.error('Error loading performance analytics:', error);
        showToast('Failed to load performance analytics', 'error');
    }
}

// ============================================
// ANALYTICS REFRESH
// ============================================

function setupAnalyticsRefresh() {
    const refreshBtn = document.getElementById('refreshAnalyticsBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
            refreshBtn.classList.add('refreshing');
            await Promise.all([
                loadAssetAllocation(),
                loadPerformanceAnalytics()
            ]);
            setTimeout(() => refreshBtn.classList.remove('refreshing'), 1000);
        });
    }
}

// Update auto-refresh to include analytics
if (window.setupAutoRefresh) {
    const originalSetupAutoRefresh = window.setupAutoRefresh;
    window.setupAutoRefresh = function() {
        originalSetupAutoRefresh();

        // Add analytics refresh intervals
        const refreshWhenVisible = (fn, interval) => {
            const id = setInterval(() => {
                if (!document.hidden && currentModelId) {
                    fn();
                }
            }, interval);
            return id;
        };

        window.autoRefreshIntervals = window.autoRefreshIntervals || {};
        window.autoRefreshIntervals.allocation = refreshWhenVisible(loadAssetAllocation, 120000); // 2 min
        window.autoRefreshIntervals.analytics = refreshWhenVisible(loadPerformanceAnalytics, 180000); // 3 min
    };
}

// ============================================
// AI CONVERSATIONS
// ============================================

async function loadAIConversations() {
    if (!currentModelId) return;

    try {
        const response = await fetch(`/api/models/${currentModelId}/conversations?limit=50`);
        if (!response.ok) throw new Error('Failed to load conversations');

        conversationsData = await response.json();
        renderConversations(conversationsData);

    } catch (error) {
        console.error('Error loading conversations:', error);
        const container = document.getElementById('conversationsContainer');
        if (container) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-chat-dots"></i>
                    <p>Failed to load conversations</p>
                </div>
            `;
        }
    }
}

function renderConversations(conversations) {
    const container = document.getElementById('conversationsContainer');
    if (!container) return;

    if (conversations.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-chat-dots"></i>
                <p>No conversations yet</p>
            </div>
        `;
        return;
    }

    container.innerHTML = conversations.map((conv, index) => {
        const timestamp = new Date(conv.timestamp);
        const action = conv.decision?.action || 'unknown';
        const reasoning = conv.reasoning || 'No reasoning provided';

        return `
            <div class="conversation-item" data-action="${action.toLowerCase()}" data-index="${index}">
                <div class="conversation-header">
                    <span class="conversation-action ${action.toLowerCase()}">${action.toUpperCase()}</span>
                    <span class="conversation-timestamp">${timestamp.toLocaleString()}</span>
                </div>
                <div class="conversation-body" id="convBody${index}">
                    ${reasoning.substring(0, 150)}${reasoning.length > 150 ? '...' : ''}
                </div>
                ${reasoning.length > 150 ? `
                    <button class="conversation-expand" onclick="toggleConversation(${index})">
                        <span id="convToggle${index}">Show more</span>
                    </button>
                ` : ''}
            </div>
        `;
    }).join('');
}

function toggleConversation(index) {
    const bodyEl = document.getElementById(`convBody${index}`);
    const toggleEl = document.getElementById(`convToggle${index}`);
    const conv = conversationsData[index];

    if (!bodyEl || !toggleEl || !conv) return;

    if (bodyEl.classList.contains('expanded')) {
        bodyEl.classList.remove('expanded');
        bodyEl.textContent = conv.reasoning.substring(0, 150) +
            (conv.reasoning.length > 150 ? '...' : '');
        toggleEl.textContent = 'Show more';
    } else {
        bodyEl.classList.add('expanded');
        bodyEl.textContent = conv.reasoning;
        toggleEl.textContent = 'Show less';
    }
}

function setupConversationFilters() {
    const searchInput = document.getElementById('conversationSearch');
    const filterSelect = document.getElementById('conversationFilter');
    const sortSelect = document.getElementById('conversationSort');

    if (searchInput) {
        searchInput.addEventListener('input', filterConversations);
    }

    if (filterSelect) {
        filterSelect.addEventListener('change', filterConversations);
    }

    if (sortSelect) {
        sortSelect.addEventListener('change', sortAndFilterConversations);
    }
}

function filterConversations() {
    const searchTerm = document.getElementById('conversationSearch')?.value.toLowerCase() || '';
    const actionFilter = document.getElementById('conversationFilter')?.value || 'all';

    const items = document.querySelectorAll('.conversation-item');
    items.forEach(item => {
        const action = item.dataset.action;
        const text = item.textContent.toLowerCase();

        const matchesSearch = text.includes(searchTerm);
        const matchesAction = actionFilter === 'all' || action === actionFilter;

        if (matchesSearch && matchesAction) {
            item.classList.remove('filtered-out');
        } else {
            item.classList.add('filtered-out');
        }
    });
}

function sortAndFilterConversations() {
    const sortOrder = document.getElementById('conversationSort')?.value || 'newest';

    let sortedConversations = [...conversationsData];
    if (sortOrder === 'oldest') {
        sortedConversations.reverse();
    }

    renderConversations(sortedConversations);
    filterConversations(); // Reapply filters after sorting
}

function viewConversation(id) {
    showToast('View full conversation - Coming soon!', 'info');
}

console.log('✓ Enhanced Analytics Module Loaded');

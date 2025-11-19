// Enhanced Dashboard - Dashboard Module
// Portfolio metrics, charts, positions, trades, market ticker

// ============================================
// DASHBOARD VARIABLES
// ============================================

let portfolioChart = null;
let currentTimeRange = '24h';
let tradesCurrentPage = 1;
let tradesPerPage = 10;
let autoRefreshIntervals = {};

// ============================================
// DASHBOARD DATA LOADING
// ============================================

async function loadDashboardData() {
    // FIX: Use parallel loading like classic view for better performance
    try {
        // Load core data first (critical)
        await Promise.all([
            loadRiskStatus(),
            loadPendingDecisions()
        ]);

        // Load all dashboard features in parallel (faster!)
        await Promise.all([
            loadPortfolioMetrics().catch(e => console.error('Portfolio metrics:', e)),
            initPortfolioChart().catch(e => console.error('Portfolio chart:', e)),
            loadPositionsTable().catch(e => console.error('Positions:', e)),
            loadTradeHistory().catch(e => console.error('Trade history:', e)),
            updateMarketTicker().catch(e => console.error('Market ticker:', e)),
            loadAIConversations().catch(e => console.error('AI conversations:', e)),
            loadAssetAllocation().catch(e => console.error('Asset allocation:', e)),
            loadPerformanceAnalytics().catch(e => console.error('Performance analytics:', e)),
            (typeof loadTradeAnalytics === 'function' ? loadTradeAnalytics() : Promise.resolve()).catch(e => console.error('Trade analytics:', e)),
            (typeof loadModelSettingsWidget === 'function' ? loadModelSettingsWidget() : Promise.resolve()).catch(e => console.error('Model settings:', e)),
            (typeof loadGraduationStatus === 'function' ? loadGraduationStatus(currentModelId) : Promise.resolve()).catch(e => console.error('Graduation status:', e)),
            (typeof loadBenchmarkComparison === 'function' ? loadBenchmarkComparison(currentModelId) : Promise.resolve()).catch(e => console.error('Benchmark comparison:', e))
        ]);
    } catch (error) {
        console.error('Failed to load dashboard data:', error);
        showToast('Failed to load some dashboard data', 'error');
    }
}

// ============================================
// PORTFOLIO METRICS
// ============================================

async function loadPortfolioMetrics() {
    if (!currentModelId) return;

    try {
        // Simplified approach like classic view - use basic portfolio endpoint
        const [portfolioResp, modelResp, tradesResp] = await Promise.all([
            fetch(`/api/models/${currentModelId}/portfolio`),
            fetch(`/api/models/${currentModelId}`),
            fetch(`/api/models/${currentModelId}/trades?limit=1000`)
        ]);

        if (!portfolioResp.ok) {
            console.error(`Portfolio endpoint failed: ${portfolioResp.status}`);
            document.getElementById('totalValue').textContent = 'Error loading';
            document.getElementById('totalPnL').textContent = 'Error loading';
            document.getElementById('todayPnL').textContent = 'Error loading';
            showToast('Failed to load portfolio data', 'error');
            return;
        }

        const data = await portfolioResp.json();
        const portfolio = data.portfolio;
        const model = await modelResp.json();
        const trades = await tradesResp.json();

        const initialCapital = model.initial_capital || 10000;
        const totalValue = portfolio.total_value || initialCapital;
        const totalPnL = totalValue - initialCapital;
        const totalPnLPct = (totalPnL / initialCapital) * 100;

        // Calculate win rate and trades
        const totalTrades = trades.length;
        const wins = trades.filter(t => t.pnl > 0).length;
        const winRate = totalTrades > 0 ? (wins / totalTrades) * 100 : 0;

        // Calculate today's P&L from trades
        const today = new Date().toISOString().split('T')[0];
        const todayTrades = trades.filter(t => t.exit_time && t.exit_time.startsWith(today));
        const todayPnL = todayTrades.reduce((sum, t) => sum + (t.pnl || 0), 0);
        const todayPnLPct = totalValue > 0 ? (todayPnL / totalValue) * 100 : 0;

        // Update UI - Total Value
        document.getElementById('totalValue').textContent = formatCurrency(totalValue);
        const valueChange = totalValue - initialCapital;
        updateMetricChange('totalValueChange', valueChange, (valueChange / initialCapital) * 100);

        // Update Total P&L
        document.getElementById('totalPnL').textContent = formatCurrency(totalPnL);
        document.getElementById('totalPnLPercent').textContent = formatPercent(totalPnLPct);
        document.getElementById('totalPnLPercent').className = `metric-change ${totalPnL >= 0 ? 'positive' : 'negative'}`;

        // Update Today's P&L
        document.getElementById('todayPnL').textContent = formatCurrency(todayPnL);
        document.getElementById('todayPnLPercent').textContent = formatPercent(todayPnLPct);
        document.getElementById('todayPnLPercent').className = `metric-change ${todayPnL >= 0 ? 'positive' : 'negative'}`;

        // Update Win Rate
        document.getElementById('winRate').textContent = `${winRate.toFixed(1)}%`;
        document.getElementById('winRateDetails').textContent = `${wins} wins / ${totalTrades} trades`;

        // Update Total Trades
        document.getElementById('totalTrades').textContent = totalTrades;
        document.getElementById('tradesBreakdown').textContent = `${wins} wins, ${totalTrades - wins} losses`;

        // Update Open Positions
        const openPositions = portfolio.positions ? portfolio.positions.length : 0;
        document.getElementById('openPositionsCount').textContent = openPositions;
        document.getElementById('positionsValue').textContent = formatCurrency(portfolio.positions_value || 0);

    } catch (error) {
        console.error('Failed to load portfolio metrics:', error);
        showToast('Failed to load portfolio data', 'error');
    }
}

function updateMetricChange(elementId, value, percent) {
    const el = document.getElementById(elementId);
    const sign = value >= 0 ? '+' : '';
    el.textContent = `${sign}${formatCurrency(value)} (${sign}${percent.toFixed(2)}%)`;
    el.className = `metric-change ${value >= 0 ? 'positive' : 'negative'}`;
}

// ============================================
// PORTFOLIO CHART
// ============================================

async function initPortfolioChart() {
    if (!currentModelId) return;

    // Safety check: Ensure ECharts library is loaded
    if (typeof echarts === 'undefined') {
        console.error('ECharts library not loaded yet. Retrying in 500ms...');
        setTimeout(initPortfolioChart, 500);
        return;
    }

    const chartDom = document.getElementById('portfolioChart');
    if (!chartDom) return;

    // Dispose existing chart first to prevent memory leak
    if (portfolioChart) {
        portfolioChart.dispose();
    }

    // Initialize chart
    portfolioChart = echarts.init(chartDom);

    // Load initial data
    await loadPortfolioChartData(currentTimeRange);

    // Setup time range buttons
    document.querySelectorAll('.time-range-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            document.querySelectorAll('.time-range-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentTimeRange = btn.dataset.range;
            await loadPortfolioChartData(currentTimeRange);
        });
    });
}

async function loadPortfolioChartData(range) {
    if (!currentModelId || !portfolioChart) return;

    try {
        // Use simple portfolio endpoint which includes account_value_history
        // Pass the range parameter to filter data by time
        const url = range && range !== 'all'
            ? `/api/models/${currentModelId}/portfolio?range=${range}`
            : `/api/models/${currentModelId}/portfolio`;
        const response = await fetch(url);
        if (!response.ok) {
            console.warn('Portfolio endpoint failed');
            return;
        }

        const data = await response.json();
        const history = data.account_value_history || [];

        if (history.length === 0) {
            console.warn('No historical data available');
            return;
        }

        // Add current value to history
        const currentValue = data.portfolio.total_value;
        const chartData = [...history];

        // Format data for chart
        const timestamps = chartData.map(h => {
            const date = new Date(h.timestamp);
            return date.toLocaleString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        });

        const values = chartData.map(h => h.total_value);

        // Add current value if we have it
        if (currentValue && values.length > 0) {
            timestamps.push('Now');
            values.push(currentValue);
        }

        const firstValue = values[0];
        const lastValue = values[values.length - 1];
        const isProfit = lastValue >= firstValue;

        const option = {
            backgroundColor: 'transparent',
            tooltip: {
                trigger: 'axis',
                backgroundColor: '#1a1f2e',
                borderColor: '#3c4556',
                textStyle: { color: '#e8eaed' },
                formatter: function(params) {
                    const point = params[0];
                    return `${point.axisValue}<br/>Value: $${point.value.toLocaleString()}`;
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                top: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: timestamps,
                axisLine: { lineStyle: { color: '#3c4556' } },
                axisLabel: { color: '#9aa0a6' }
            },
            yAxis: {
                type: 'value',
                scale: true,  // Dynamic scaling to show value changes more clearly
                axisLine: { lineStyle: { color: '#3c4556' } },
                axisLabel: {
                    color: '#9aa0a6',
                    formatter: '${value}'
                },
                splitLine: { lineStyle: { color: '#252d3d' } }
            },
            series: [{
                data: values,
                type: 'line',
                smooth: true,
                lineStyle: {
                    color: isProfit ? '#4caf50' : '#f44336',
                    width: 2
                },
                areaStyle: {
                    color: {
                        type: 'linear',
                        x: 0, y: 0, x2: 0, y2: 1,
                        colorStops: [{
                            offset: 0,
                            color: isProfit ? 'rgba(76, 175, 80, 0.3)' : 'rgba(244, 67, 54, 0.3)'
                        }, {
                            offset: 1,
                            color: 'rgba(0, 0, 0, 0)'
                        }]
                    }
                },
                itemStyle: {
                    color: isProfit ? '#4caf50' : '#f44336'
                }
            }]
        };

        portfolioChart.setOption(option);

    } catch (error) {
        console.error('Failed to load portfolio chart data:', error);
    }
}

// ============================================
// POSITIONS TABLE
// ============================================

async function loadPositionsTable() {
    if (!currentModelId) return;

    try {
        const response = await fetch(`/api/models/${currentModelId}/portfolio`);
        if (!response.ok) return;

        const data = await response.json();
        const positions = data.portfolio.positions || [];

        const tbody = document.getElementById('positionsTableBody');

        if (positions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No open positions</td></tr>';
            return;
        }

        tbody.innerHTML = positions.map(pos => {
            const pnl = pos.unrealized_pnl || 0;
            const pnlPct = pos.unrealized_pnl_pct || 0;
            const pnlClass = pnl >= 0 ? 'pnl-positive' : 'pnl-negative';

            return `
                <tr>
                    <td><strong>${pos.coin}</strong></td>
                    <td>${pos.amount.toFixed(4)}</td>
                    <td>$${pos.avg_buy_price.toFixed(2)}</td>
                    <td>$${pos.current_price.toFixed(2)}</td>
                    <td class="${pnlClass}">
                        ${pnl >= 0 ? '+' : ''}$${pnl.toFixed(2)}<br>
                        <small>(${pnl >= 0 ? '+' : ''}${pnlPct.toFixed(2)}%)</small>
                    </td>
                    <td>
                        <button class="btn-secondary btn-small" onclick="closePosition('${pos.coin}')">
                            Close
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

    } catch (error) {
        console.error('Failed to load positions:', error);
    }
}

function closePosition(coin) {
    showToast(`Close position for ${coin} - Coming soon!`, 'info');
}

// ============================================
// TRADE HISTORY
// ============================================

async function loadTradeHistory(page = 1) {
    if (!currentModelId) return;

    tradesCurrentPage = page;

    try {
        const response = await fetch(`/api/models/${currentModelId}/trades?limit=1000`);
        if (!response.ok) {
            console.error(`Failed to load trades: ${response.status} ${response.statusText}`);
            const tbody = document.getElementById('tradesTableBody');
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state" style="color: #f44336;">Failed to load trades. Please try again.</td></tr>';
            return;
        }

        const allTrades = await response.json();

        const tbody = document.getElementById('tradesTableBody');

        if (allTrades.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No trades yet</td></tr>';
            document.getElementById('tradesPagination').style.display = 'none';
            return;
        }

        // Pagination
        const totalPages = Math.ceil(allTrades.length / tradesPerPage);
        const startIdx = (page - 1) * tradesPerPage;
        const endIdx = startIdx + tradesPerPage;
        const pageTrades = allTrades.slice(startIdx, endIdx);

        tbody.innerHTML = pageTrades.map(trade => {
            const pnl = trade.pnl || 0;
            const pnlClass = pnl > 0 ? 'pnl-positive' : pnl < 0 ? 'pnl-negative' : '';
            const actionClass = trade.action === 'buy' ? 'trade-buy' : 'trade-sell';

            return `
                <tr>
                    <td>${formatDate(trade.timestamp)}</td>
                    <td><strong>${trade.coin}</strong></td>
                    <td class="${actionClass}">${trade.action.toUpperCase()}</td>
                    <td>${trade.amount.toFixed(4)}</td>
                    <td>$${trade.price.toFixed(2)}</td>
                    <td class="${pnlClass}">
                        ${pnl !== 0 ? (pnl > 0 ? '+' : '') + '$' + pnl.toFixed(2) : '-'}
                    </td>
                </tr>
            `;
        }).join('');

        // Update pagination
        document.getElementById('paginationInfo').textContent = `Page ${page} of ${totalPages}`;
        document.getElementById('prevPageBtn').disabled = page === 1;
        document.getElementById('nextPageBtn').disabled = page === totalPages;
        document.getElementById('tradesPagination').style.display = 'flex';

    } catch (error) {
        console.error('Failed to load trade history:', error);
    }
}

// Pagination event listeners
document.getElementById('prevPageBtn')?.addEventListener('click', () => {
    loadTradeHistory(tradesCurrentPage - 1);
});

document.getElementById('nextPageBtn')?.addEventListener('click', () => {
    loadTradeHistory(tradesCurrentPage + 1);
});

// ============================================
// MARKET TICKER
// ============================================

async function updateMarketTicker() {
    try {
        const response = await fetch('/api/market/prices?symbols=BTC,ETH,BNB,SOL,XRP,DOGE');
        if (!response.ok) return;

        const prices = await response.json();

        const ticker = document.getElementById('marketTicker');

        const items = Object.entries(prices).map(([coin, data]) => {
            const change = data.change_24h || 0;
            const changeClass = change >= 0 ? 'positive' : 'negative';
            const sign = change >= 0 ? '+' : '';

            return `
                <div class="ticker-item">
                    <span class="ticker-coin">${coin}</span>
                    <span class="ticker-price">$${data.price.toLocaleString()}</span>
                    <span class="ticker-change ${changeClass}">${sign}${change.toFixed(2)}%</span>
                </div>
            `;
        }).join('');

        // Duplicate items for seamless scroll
        ticker.innerHTML = items + items;

    } catch (error) {
        console.error('Failed to update market ticker:', error);
    }
}

// ============================================
// AUTO-REFRESH SETUP
// ============================================

function setupAutoRefresh() {
    // Clear existing intervals
    Object.values(autoRefreshIntervals).forEach(clearInterval);
    autoRefreshIntervals = {};

    // Only refresh when tab is visible
    const refreshWhenVisible = (fn, interval) => {
        const id = setInterval(() => {
            if (!document.hidden && currentModelId) {
                fn();
            }
        }, interval);
        return id;
    };

    // Set up intervals (gentle, not harsh)
    autoRefreshIntervals.ticker = refreshWhenVisible(updateMarketTicker, 30000); // 30s
    autoRefreshIntervals.metrics = refreshWhenVisible(loadPortfolioMetrics, 60000); // 1min
    autoRefreshIntervals.positions = refreshWhenVisible(loadPositionsTable, 45000); // 45s
    autoRefreshIntervals.conversations = refreshWhenVisible(loadAIConversations, 60000); // 1min
}

// ============================================
// EXPORT TRADES
// ============================================

document.getElementById('exportTradesBtn')?.addEventListener('click', async () => {
    if (!currentModelId) {
        showToast('Please select a model first', 'error');
        return;
    }

    try {
        const response = await fetch(`/api/models/${currentModelId}/trades?limit=10000`);
        const trades = await response.json();

        // Convert to CSV
        const headers = ['Date', 'Coin', 'Action', 'Amount', 'Price', 'P&L'];
        const rows = trades.map(t => [
            t.timestamp,
            t.coin,
            t.action,
            t.amount,
            t.price,
            t.pnl || ''
        ]);

        const csv = [headers, ...rows].map(row => row.join(',')).join('\n');

        // Download
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `trades_model_${currentModelId}_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();

        showToast('Trades exported successfully', 'success');
    } catch (error) {
        console.error('Export failed:', error);
        showToast('Failed to export trades', 'error');
    }
});

// Toggle conversations
document.getElementById('toggleConversations')?.addEventListener('click', () => {
    const container = document.getElementById('conversationsContainer');
    const icon = document.querySelector('#toggleConversations i');

    if (container.style.display === 'none') {
        container.style.display = 'block';
        icon.className = 'bi bi-chevron-down';
    } else {
        container.style.display = 'none';
        icon.className = 'bi bi-chevron-up';
    }
});

console.log('✓ Enhanced Dashboard Module Loaded');

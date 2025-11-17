// ============================================
// TRADE ANALYTICS & INSIGHTS
// ============================================

// Load trade analytics
async function loadTradeAnalytics() {
    if (!currentModelId) return;

    try {
        const response = await fetch(`/api/models/${currentModelId}/trades?limit=1000`);
        if (!response.ok) throw new Error('Failed to load trades');

        const trades = await response.json();

        if (trades.length === 0) {
            return; // Keep empty state
        }

        // Calculate analytics
        const coinPerformance = calculateCoinPerformance(trades);
        const tradingHours = calculateTradingHours(trades);
        const tradeSize = calculateTradeSize(trades);

        // Render insights
        renderTopPerformers(coinPerformance.top);
        renderWorstPerformers(coinPerformance.worst);
        renderTradingHours(tradingHours);
        renderTradeSize(tradeSize);

    } catch (error) {
        console.error('Failed to load trade analytics:', error);
    }
}

// Calculate coin performance
function calculateCoinPerformance(trades) {
    const coinStats = {};

    trades.forEach(trade => {
        if (!coinStats[trade.coin]) {
            coinStats[trade.coin] = {
                coin: trade.coin,
                totalPnl: 0,
                tradeCount: 0,
                wins: 0,
                losses: 0
            };
        }

        const pnl = trade.pnl || 0;
        coinStats[trade.coin].totalPnl += pnl;
        coinStats[trade.coin].tradeCount++;

        if (pnl > 0) coinStats[trade.coin].wins++;
        else if (pnl < 0) coinStats[trade.coin].losses++;
    });

    // Sort by total PnL
    const sortedCoins = Object.values(coinStats).sort((a, b) => b.totalPnl - a.totalPnl);

    return {
        top: sortedCoins.slice(0, 5),
        worst: sortedCoins.slice(-5).reverse()
    };
}

// Calculate trading hours distribution
function calculateTradingHours(trades) {
    const hourlyTrades = new Array(24).fill(0);

    trades.forEach(trade => {
        const date = new Date(trade.timestamp);
        const hour = date.getHours();
        hourlyTrades[hour]++;
    });

    // Find peak hour
    const peakHour = hourlyTrades.indexOf(Math.max(...hourlyTrades));
    const totalTrades = hourlyTrades.reduce((a, b) => a + b, 0);

    return {
        hourly: hourlyTrades,
        peakHour: peakHour,
        peakCount: hourlyTrades[peakHour],
        totalTrades: totalTrades
    };
}

// Calculate trade size statistics
function calculateTradeSize(trades) {
    const sizes = trades.map(t => t.amount * t.price);

    const avgSize = sizes.reduce((a, b) => a + b, 0) / sizes.length;
    const maxSize = Math.max(...sizes);
    const minSize = Math.min(...sizes);

    return {
        average: avgSize,
        max: maxSize,
        min: minSize,
        total: sizes.reduce((a, b) => a + b, 0)
    };
}

// Render top performers
function renderTopPerformers(topCoins) {
    const container = document.getElementById('topPerformersContent');
    if (!container || topCoins.length === 0) return;

    container.innerHTML = topCoins.map(coin => {
        const winRate = coin.tradeCount > 0 ? (coin.wins / coin.tradeCount * 100) : 0;

        return `
            <div class="performer-item">
                <div class="performer-header">
                    <span class="performer-coin">${coin.coin}</span>
                    <span class="performer-pnl positive">+$${coin.totalPnl.toFixed(2)}</span>
                </div>
                <div class="performer-stats">
                    <span>${coin.tradeCount} trades</span>
                    <span>${winRate.toFixed(0)}% win rate</span>
                </div>
            </div>
        `;
    }).join('');
}

// Render worst performers
function renderWorstPerformers(worstCoins) {
    const container = document.getElementById('worstPerformersContent');
    if (!container || worstCoins.length === 0) return;

    container.innerHTML = worstCoins.map(coin => {
        const winRate = coin.tradeCount > 0 ? (coin.wins / coin.tradeCount * 100) : 0;

        return `
            <div class="performer-item">
                <div class="performer-header">
                    <span class="performer-coin">${coin.coin}</span>
                    <span class="performer-pnl negative">${coin.totalPnl.toFixed(2)}</span>
                </div>
                <div class="performer-stats">
                    <span>${coin.tradeCount} trades</span>
                    <span>${winRate.toFixed(0)}% win rate</span>
                </div>
            </div>
        `;
    }).join('');
}

// Render trading hours
function renderTradingHours(hoursData) {
    const container = document.getElementById('tradingHoursContent');
    if (!container) return;

    const peakTimeStr = `${hoursData.peakHour}:00 - ${hoursData.peakHour + 1}:00`;

    container.innerHTML = `
        <div class="trading-hours-summary">
            <div class="hours-stat">
                <div class="hours-label">Peak Trading Hour</div>
                <div class="hours-value">${peakTimeStr}</div>
            </div>
            <div class="hours-stat">
                <div class="hours-label">Trades in Peak Hour</div>
                <div class="hours-value">${hoursData.peakCount}</div>
            </div>
            <div class="hours-stat">
                <div class="hours-label">Total Trades</div>
                <div class="hours-value">${hoursData.totalTrades}</div>
            </div>
        </div>
        <div class="hours-chart">
            ${hoursData.hourly.map((count, hour) => {
                const heightPct = hoursData.peakCount > 0 ? (count / hoursData.peakCount * 100) : 0;
                return `
                    <div class="hour-bar" title="${hour}:00 - ${count} trades">
                        <div class="hour-bar-fill" style="height: ${heightPct}%"></div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

// Render trade size
function renderTradeSize(sizeData) {
    const container = document.getElementById('tradeSizeContent');
    if (!container) return;

    container.innerHTML = `
        <div class="trade-size-stats">
            <div class="size-stat">
                <div class="size-label">Average Trade</div>
                <div class="size-value">$${sizeData.average.toFixed(2)}</div>
            </div>
            <div class="size-stat">
                <div class="size-label">Largest Trade</div>
                <div class="size-value">$${sizeData.max.toFixed(2)}</div>
            </div>
            <div class="size-stat">
                <div class="size-label">Smallest Trade</div>
                <div class="size-value">$${sizeData.min.toFixed(2)}</div>
            </div>
            <div class="size-stat">
                <div class="size-label">Total Volume</div>
                <div class="size-value">$${sizeData.total.toFixed(2)}</div>
            </div>
        </div>
    `;
}

// Initialize analytics on model change
if (typeof window !== 'undefined') {
    window.loadTradeAnalytics = loadTradeAnalytics;
}

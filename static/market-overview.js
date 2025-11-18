// ============================================
// MARKET OVERVIEW
// ============================================

let marketPricesCache = {};

// Load market overview
async function loadMarketOverview() {
    try {
        const response = await fetch('/api/market/prices?symbols=BTC,ETH,BNB,SOL,XRP,DOGE');
        if (!response.ok) throw new Error('Failed to load market prices');

        const prices = await response.json();
        marketPricesCache = prices;

        renderMarketOverview(prices);

    } catch (error) {
        console.error('Failed to load market overview:', error);
    }
}

// Render market overview
function renderMarketOverview(prices) {
    // Calculate market sentiment based on average change
    const changes = Object.values(prices).map(p => p.change_24h || 0);
    const avgChange = changes.reduce((a, b) => a + b, 0) / changes.length;

    const sentimentEl = document.getElementById('marketSentiment');
    if (sentimentEl) {
        let sentiment = 'Neutral';
        let sentimentClass = '';

        if (avgChange > 2) {
            sentiment = '🚀 Bullish';
            sentimentClass = 'positive';
        } else if (avgChange < -2) {
            sentiment = '🐻 Bearish';
            sentimentClass = 'negative';
        } else if (avgChange > 0) {
            sentiment = '📈 Slightly Bullish';
            sentimentClass = 'positive';
        } else if (avgChange < 0) {
            sentiment = '📉 Slightly Bearish';
            sentimentClass = 'negative';
        }

        sentimentEl.textContent = sentiment;
        sentimentEl.className = `overview-value ${sentimentClass}`;
    }

    // Find top gainer
    let topGainer = { coin: '', change: -Infinity };
    let topLoser = { coin: '', change: Infinity };

    Object.entries(prices).forEach(([coin, data]) => {
        const change = data.change_24h || 0;
        if (change > topGainer.change) {
            topGainer = { coin, change, price: data.price };
        }
        if (change < topLoser.change) {
            topLoser = { coin, change, price: data.price };
        }
    });

    // Update top gainer
    const topGainerEl = document.getElementById('topGainer');
    if (topGainerEl && topGainer.coin) {
        topGainerEl.innerHTML = `
            ${topGainer.coin}
            <small style="font-size: 12px; font-weight: normal;">
                +${topGainer.change.toFixed(2)}%
            </small>
        `;
    }

    // Update top loser
    const topLoserEl = document.getElementById('topLoser');
    if (topLoserEl && topLoser.coin) {
        topLoserEl.innerHTML = `
            ${topLoser.coin}
            <small style="font-size: 12px; font-weight: normal;">
                ${topLoser.change.toFixed(2)}%
            </small>
        `;
    }

    // Tracked coins count
    const trackedCoinsEl = document.getElementById('trackedCoins');
    if (trackedCoinsEl) {
        trackedCoinsEl.textContent = Object.keys(prices).length;
    }
}

// Setup refresh button
function setupMarketOverviewRefresh() {
    const refreshBtn = document.getElementById('refreshMarketBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
            refreshBtn.classList.add('refreshing');
            await loadMarketOverview();
            setTimeout(() => refreshBtn.classList.remove('refreshing'), 1000);
            showToast('Market data refreshed', 'success');
        });
    }
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setupMarketOverviewRefresh();
        loadMarketOverview();
    });
} else {
    setupMarketOverviewRefresh();
    loadMarketOverview();
}

// Auto-refresh every 60 seconds
setInterval(loadMarketOverview, 60000);

// Export for global access
window.loadMarketOverview = loadMarketOverview;

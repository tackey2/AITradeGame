// ============================================
// EXPORT FEATURES
// ============================================

// Export trades to CSV
async function exportTradesToCSV() {
    if (!currentModelId) {
        showToast('Please select a model first', 'warning');
        return;
    }

    try {
        const response = await fetch(`/api/models/${currentModelId}/trades?limit=10000`);
        if (!response.ok) throw new Error('Failed to fetch trades');

        const trades = await response.json();

        if (trades.length === 0) {
            showToast('No trades to export', 'info');
            return;
        }

        // Create CSV content
        const headers = ['Timestamp', 'Coin', 'Action', 'Amount', 'Price', 'Total Value', 'P&L', 'Leverage'];
        const rows = trades.map(trade => [
            trade.timestamp,
            trade.coin,
            trade.action.toUpperCase(),
            trade.amount.toFixed(4),
            trade.price.toFixed(2),
            (trade.amount * trade.price).toFixed(2),
            trade.pnl ? trade.pnl.toFixed(2) : '0.00',
            trade.leverage || '1'
        ]);

        const csvContent = [
            headers.join(','),
            ...rows.map(row => row.join(','))
        ].join('\n');

        const timestamp = new Date().toISOString().split('T')[0];
        // Download CSV
        downloadFile(csvContent, `trade-history-${currentModelId}-${timestamp}.csv`, 'text/csv');
        showToast('Trades exported successfully', 'success');

        // Add notification
        if (typeof addNotification === 'function') {
            addNotification('success', '📊 Export Complete', `${trades.length} trades exported to CSV`, null, null);
        }
    } catch (error) {
        console.error('Failed to export trades:', error);
        showToast('Failed to export trades', 'error');
    }
}

// Export positions to CSV
async function exportPositionsToCSV() {
    if (!currentModelId) {
        showToast('Please select a model first', 'warning');
        return;
    }

    try {
        const response = await fetch(`/api/models/${currentModelId}/portfolio`);
        if (!response.ok) throw new Error('Failed to fetch portfolio');

        const data = await response.json();
        const positions = data.portfolio.positions || [];

        if (positions.length === 0) {
            showToast('No positions to export', 'info');
            return;
        }

        // Create CSV content
        const headers = ['Coin', 'Amount', 'Avg Buy Price', 'Current Price', 'Total Value', 'Unrealized P&L', 'P&L %'];
        const rows = positions.map(pos => [
            pos.coin,
            pos.amount.toFixed(4),
            pos.avg_buy_price.toFixed(2),
            pos.current_price.toFixed(2),
            (pos.amount * pos.current_price).toFixed(2),
            (pos.unrealized_pnl || 0).toFixed(2),
            (pos.unrealized_pnl_pct || 0).toFixed(2)
        ]);

        const csvContent = [
            headers.join(','),
            ...rows.map(row => row.join(','))
        ].join('\n');

        const timestamp = new Date().toISOString().split('T')[0];
        // Download CSV
        downloadFile(csvContent, `positions-${currentModelId}-${timestamp}.csv`, 'text/csv');
        showToast('Positions exported successfully', 'success');
    } catch (error) {
        console.error('Failed to export positions:', error);
        showToast('Failed to export positions', 'error');
    }
}

// Export performance report to JSON
async function exportPerformanceReport() {
    if (!currentModelId) {
        showToast('Please select a model first', 'warning');
        return;
    }

    try {
        // Fetch all data in parallel
        const [portfolio, trades, analytics, riskStatus] = await Promise.all([
            fetch(`/api/models/${currentModelId}/portfolio`).then(r => r.json()),
            fetch(`/api/models/${currentModelId}/trades?limit=10000`).then(r => r.json()),
            fetch(`/api/models/${currentModelId}/performance-analytics`).then(r => r.json()),
            fetch(`/api/models/${currentModelId}/risk-status`).then(r => r.json())
        ]);

        const report = {
            export_date: new Date().toISOString(),
            model_id: currentModelId,
            portfolio_summary: {
                total_value: portfolio.portfolio.total_value,
                cash: portfolio.portfolio.cash,
                positions_value: portfolio.portfolio.positions_value,
                total_positions: portfolio.portfolio.positions.length
            },
            performance_metrics: analytics,
            risk_status: riskStatus,
            trade_count: trades.length,
            positions: portfolio.portfolio.positions,
            recent_trades: trades.slice(0, 100) // Last 100 trades
        };

        // Download JSON
        const jsonContent = JSON.stringify(report, null, 2);
        const timestamp = new Date().toISOString().split('T')[0];
        downloadFile(jsonContent, `performance-report-${currentModelId}-${timestamp}.json`, 'application/json');
        showToast('Performance report exported', 'success');

        // Add notification
        if (typeof addNotification === 'function') {
            addNotification('success', '📋 Report Generated', 'Complete performance report exported', null, null);
        }
    } catch (error) {
        console.error('Failed to export performance report:', error);
        showToast('Failed to export report', 'error');
    }
}

// Generic download file function
function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

// Setup export button listeners
function setupExportButtons() {
    const exportTradesBtn = document.getElementById('exportTradesBtn');
    if (exportTradesBtn) {
        exportTradesBtn.addEventListener('click', exportTradesToCSV);
    }

    const exportPositionsBtn = document.getElementById('exportPositionsBtn');
    if (exportPositionsBtn) {
        exportPositionsBtn.addEventListener('click', exportPositionsToCSV);
    }

    const exportReportBtn = document.getElementById('exportReportBtn');
    if (exportReportBtn) {
        exportReportBtn.addEventListener('click', exportPerformanceReport);
    }
}

// Call setupExportButtons after DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupExportButtons);
} else {
    setupExportButtons();
}

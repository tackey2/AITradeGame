"""
Analytics and Portfolio Routes Blueprint
Handles portfolio, analytics, metrics, and market data endpoints
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import numpy as np
import math

# Create blueprints for different route groups
models_analytics_bp = Blueprint('models_analytics', __name__, url_prefix='/api/models')
aggregated_bp = Blueprint('aggregated', __name__, url_prefix='/api/aggregated')
market_bp = Blueprint('market', __name__, url_prefix='/api/market')

# Shared resources (will be injected via init_app)
db = None
enhanced_db = None
market_fetcher = None


def init_app(database, enhanced_database, market_data_fetcher):
    """Initialize analytics blueprints with shared resources"""
    global db, enhanced_db, market_fetcher
    db = database
    enhanced_db = enhanced_database
    market_fetcher = market_data_fetcher


# ============ Helper Functions ============

def generateVerdict(model_return, benchmarks):
    """Generate a verdict on whether AI is worth using"""
    valid_benchmarks = [b for b in benchmarks if b['return_pct'] is not None]

    if not valid_benchmarks:
        return {
            'recommendation': 'insufficient_data',
            'message': 'Not enough price data to compare. Continue testing.'
        }

    best_benchmark = max(valid_benchmarks, key=lambda x: x['return_pct'])
    outperformed_count = sum(1 for b in valid_benchmarks if b.get('outperformed'))

    if model_return > best_benchmark['return_pct']:
        return {
            'recommendation': 'use_ai',
            'message': f"✅ AI is outperforming all benchmarks! ({model_return:.1f}% vs {best_benchmark['return_pct']:.1f}% best)",
            'icon': '🎉'
        }
    elif outperformed_count >= len(valid_benchmarks) / 2:
        return {
            'recommendation': 'use_ai_conditional',
            'message': f"⚠️ AI beats {outperformed_count}/{len(valid_benchmarks)} benchmarks. Consider risk-adjusted performance.",
            'icon': '📊'
        }
    else:
        return {
            'recommendation': 'use_passive',
            'message': f"❌ Passive strategy is winning. Best: {best_benchmark['name']} ({best_benchmark['return_pct']:.1f}%)",
            'icon': '💡'
        }


# ============ Model Analytics Routes ============

@models_analytics_bp.route('/<int:model_id>/portfolio', methods=['GET'])
def get_portfolio(model_id):
    prices_data = market_fetcher.get_current_prices(['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE'])
    current_prices = {coin: prices_data[coin]['price'] for coin in prices_data}

    # Get time range from query parameters
    time_range = request.args.get('range', None)

    portfolio = db.get_portfolio(model_id, current_prices)
    account_value = db.get_account_value_history(model_id, limit=1000, time_range=time_range)

    return jsonify({
        'portfolio': portfolio,
        'account_value_history': account_value
    })


@models_analytics_bp.route('/<int:model_id>/trades', methods=['GET'])
def get_trades(model_id):
    limit = request.args.get('limit', 50, type=int)
    trades = enhanced_db.get_trades(model_id, limit=limit)
    return jsonify(trades)


@models_analytics_bp.route('/<int:model_id>/conversations', methods=['GET'])
def get_conversations(model_id):
    limit = request.args.get('limit', 20, type=int)
    conversations = enhanced_db.get_conversations(model_id, limit=limit)
    return jsonify(conversations)


@models_analytics_bp.route('/<int:model_id>/portfolio-metrics', methods=['GET'])
def get_portfolio_metrics(model_id):
    """Get aggregated portfolio metrics for dashboard"""
    try:
        # Get current portfolio
        prices_data = market_fetcher.get_current_prices(['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE'])
        current_prices = {coin: prices_data[coin]['price'] for coin in prices_data}
        portfolio = db.get_portfolio(model_id, current_prices)

        # Get model data
        model = db.get_model(model_id)
        if not model:
            return jsonify({'error': 'Model not found'}), 404

        initial_capital = model['initial_capital']
        total_value = portfolio.get('total_value', initial_capital)

        # Calculate total P&L
        total_pnl = total_value - initial_capital
        total_pnl_pct = (total_pnl / initial_capital * 100) if initial_capital > 0 else 0

        # Get trades for win rate and today's P&L
        all_trades = enhanced_db.get_trades(model_id, limit=1000)

        # Calculate win rate
        profitable_trades = [t for t in all_trades if t.get('pnl', 0) > 0]
        total_trades_count = len(all_trades)
        win_rate = (len(profitable_trades) / total_trades_count * 100) if total_trades_count > 0 else 0

        # Calculate today's P&L
        today = datetime.now().date()
        today_trades = [t for t in all_trades if datetime.fromisoformat(t['timestamp'].replace('Z', '+00:00')).date() == today]
        today_pnl = sum(t.get('pnl', 0) for t in today_trades)
        today_pnl_pct = (today_pnl / initial_capital * 100) if initial_capital > 0 else 0

        # Count open positions
        positions = portfolio.get('positions', [])
        open_positions = len(positions)
        positions_value = sum(p.get('value', 0) for p in positions)

        # Calculate yesterday's value for change
        history = db.get_account_value_history(model_id, limit=2)
        yesterday_value = history[1]['value'] if len(history) > 1 else initial_capital
        value_change = total_value - yesterday_value
        value_change_pct = (value_change / yesterday_value * 100) if yesterday_value > 0 else 0

        return jsonify({
            'total_value': total_value,
            'value_change': value_change,
            'value_change_pct': value_change_pct,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct,
            'today_pnl': today_pnl,
            'today_pnl_pct': today_pnl_pct,
            'win_rate': win_rate,
            'wins': len(profitable_trades),
            'total_trades': total_trades_count,
            'open_positions': open_positions,
            'positions_value': positions_value,
            'initial_capital': initial_capital
        })
    except Exception as e:
        import traceback
        print(f"[ERROR] Portfolio metrics failed: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@models_analytics_bp.route('/<int:model_id>/portfolio-history', methods=['GET'])
def get_portfolio_history(model_id):
    """Get portfolio value history for chart"""
    try:
        time_range = request.args.get('range', '24h')

        # Determine limit based on time range
        limits = {
            '1h': 12,      # 5-minute intervals
            '24h': 96,     # 15-minute intervals
            '7d': 168,     # Hourly
            '30d': 720,    # Every 4 hours
            '90d': 2160,   # Every 4 hours
            'all': 10000   # All data
        }

        limit = limits.get(time_range, 96)

        # Get account value history
        history = db.get_account_value_history(model_id, limit=limit)

        # Format for ECharts
        chart_data = {
            'timestamps': [h['timestamp'] for h in history],
            'values': [h['value'] for h in history],
            'range': time_range
        }

        return jsonify(chart_data)
    except Exception as e:
        import traceback
        print(f"[ERROR] Portfolio history failed: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@models_analytics_bp.route('/<int:model_id>/asset-allocation', methods=['GET'])
def get_asset_allocation(model_id):
    """Get current asset allocation for donut chart"""
    try:
        # Get current market prices
        prices_data = market_fetcher.get_current_prices(['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE'])
        current_prices = {coin: prices_data[coin]['price'] for coin in prices_data}

        # Get portfolio
        portfolio = db.get_portfolio(model_id, current_prices)

        # Get model data
        model = enhanced_db.get_model(model_id)
        if not model:
            return jsonify({'error': 'Model not found'}), 404

        # Calculate allocation
        allocations = []
        positions = portfolio.get('positions', [])
        cash = portfolio.get('cash', model['initial_capital'])
        total_value = portfolio.get('total_value', model['initial_capital'])

        # Add cash allocation
        if cash > 0:
            allocations.append({
                'name': 'Cash (USDT)',
                'value': cash,
                'percentage': (cash / total_value * 100) if total_value > 0 else 0,
                'color': '#3B82F6'  # Blue for cash
            })

        # Add position allocations
        colors = ['#10B981', '#F59E0B', '#8B5CF6', '#EF4444', '#06B6D4', '#F97316']
        for i, pos in enumerate(positions):
            if pos.get('value', 0) > 0:
                allocations.append({
                    'name': pos['coin'],
                    'value': pos['value'],
                    'percentage': (pos['value'] / total_value * 100) if total_value > 0 else 0,
                    'amount': pos['amount'],
                    'price': pos['current_price'],
                    'color': colors[i % len(colors)]
                })

        return jsonify({
            'allocations': allocations,
            'total_value': total_value,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        import traceback
        print(f"[ERROR] Asset allocation failed: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@models_analytics_bp.route('/<int:model_id>/performance-analytics', methods=['GET'])
def get_performance_analytics(model_id):
    """Get detailed performance analytics including Sharpe ratio, drawdown, streaks, etc."""
    try:
        # Get all trades for this model
        trades = enhanced_db.get_trades(model_id, limit=10000)

        # Get model data
        model = enhanced_db.get_model(model_id)
        if not model:
            return jsonify({'error': 'Model not found'}), 404

        initial_capital = model['initial_capital']

        # Initialize default values
        analytics = {
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'max_drawdown_pct': 0,
            'win_streak': 0,
            'current_win_streak': 0,
            'loss_streak': 0,
            'current_loss_streak': 0,
            'best_trade': 0,
            'best_trade_pct': 0,
            'worst_trade': 0,
            'worst_trade_pct': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'profit_factor': 0,
            'win_rate': 0,
            'total_return': 0,
            'total_return_pct': 0,
            'total_trades': len(trades)
        }

        if len(trades) == 0:
            return jsonify(analytics)

        # Separate winning and losing trades
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl', 0) < 0]

        # Calculate win rate
        if len(trades) > 0:
            analytics['win_rate'] = (len(winning_trades) / len(trades)) * 100

        # Calculate total return
        total_pnl = sum(t.get('pnl', 0) for t in trades)
        analytics['total_return'] = total_pnl
        analytics['total_return_pct'] = (total_pnl / initial_capital * 100) if initial_capital > 0 else 0

        # Calculate best and worst trades
        if trades:
            pnls = [t.get('pnl', 0) for t in trades]
            analytics['best_trade'] = max(pnls)
            analytics['worst_trade'] = min(pnls)

            # Best/worst trade percentages
            if trades:
                for t in trades:
                    if t.get('pnl', 0) == analytics['best_trade']:
                        analytics['best_trade_pct'] = (t.get('pnl', 0) / initial_capital * 100)
                    if t.get('pnl', 0) == analytics['worst_trade']:
                        analytics['worst_trade_pct'] = (t.get('pnl', 0) / initial_capital * 100)

        # Calculate average win/loss
        if winning_trades:
            analytics['avg_win'] = sum(t.get('pnl', 0) for t in winning_trades) / len(winning_trades)
        if losing_trades:
            analytics['avg_loss'] = sum(t.get('pnl', 0) for t in losing_trades) / len(losing_trades)

        # Calculate profit factor (gross profit / gross loss)
        gross_profit = sum(t.get('pnl', 0) for t in winning_trades)
        gross_loss = abs(sum(t.get('pnl', 0) for t in losing_trades))
        if gross_loss > 0:
            analytics['profit_factor'] = gross_profit / gross_loss

        # Calculate win/loss streaks
        current_streak = 0
        max_win_streak = 0
        max_loss_streak = 0
        last_was_win = None

        for trade in trades:
            pnl = trade.get('pnl', 0)
            is_win = pnl > 0

            if last_was_win is None or last_was_win == is_win:
                current_streak += 1
            else:
                if last_was_win:
                    max_win_streak = max(max_win_streak, current_streak)
                else:
                    max_loss_streak = max(max_loss_streak, current_streak)
                current_streak = 1

            last_was_win = is_win

        # Final streak check
        if last_was_win:
            max_win_streak = max(max_win_streak, current_streak)
            analytics['current_win_streak'] = current_streak
        else:
            max_loss_streak = max(max_loss_streak, current_streak)
            analytics['current_loss_streak'] = current_streak

        analytics['win_streak'] = max_win_streak
        analytics['loss_streak'] = max_loss_streak

        # Calculate Sharpe Ratio (simplified - using trade returns)
        if len(trades) > 1:
            returns = [(t.get('pnl', 0) / initial_capital) for t in trades]
            if returns:
                mean_return = np.mean(returns)
                std_return = np.std(returns)
                if std_return > 0:
                    # Annualized Sharpe (assuming 252 trading days)
                    analytics['sharpe_ratio'] = (mean_return / std_return) * np.sqrt(252)

        # Calculate Maximum Drawdown
        # Get account value history
        history = db.get_account_value_history(model_id, limit=10000)
        if history:
            values = [h['value'] for h in history]
            peak = values[0]
            max_dd = 0

            for value in values:
                if value > peak:
                    peak = value
                dd = peak - value
                if dd > max_dd:
                    max_dd = dd

            analytics['max_drawdown'] = max_dd
            analytics['max_drawdown_pct'] = (max_dd / peak * 100) if peak > 0 else 0

        return jsonify(analytics)
    except Exception as e:
        import traceback
        print(f"[ERROR] Performance analytics failed: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@models_analytics_bp.route('/all-summary', methods=['GET'])
def get_all_models_summary():
    """Get comprehensive summary of all models for the Models page"""
    try:
        prices_data = market_fetcher.get_current_prices(['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE'])
        current_prices = {coin: prices_data[coin]['price'] for coin in prices_data}

        models = db.get_all_models()
        models_summary = []

        total_capital = 0
        total_value = 0
        total_trades = 0
        active_count = 0

        for model in models:
            # Get portfolio
            portfolio = db.get_portfolio(model['id'], current_prices)

            # Get model status (active/paused)
            # For now, assume all models are active
            is_active = True
            if is_active:
                active_count += 1

            # Get trades for statistics
            trades = enhanced_db.get_trades(model['id'], limit=1000)

            # Calculate stats
            initial_capital = model['initial_capital']
            model_value = portfolio.get('total_value', initial_capital)
            pnl = model_value - initial_capital
            pnl_pct = (pnl / initial_capital * 100) if initial_capital > 0 else 0

            # Win rate
            profitable_trades = [t for t in trades if t.get('pnl', 0) > 0]
            win_rate = (len(profitable_trades) / len(trades) * 100) if len(trades) > 0 else 0

            # Get provider name
            provider = db.get_provider(model['provider_id'])
            provider_name = provider['name'] if provider else 'Unknown'

            model_summary = {
                'id': model['id'],
                'name': model['name'],
                'provider_name': provider_name,
                'model_name': model['model_name'],
                'initial_capital': initial_capital,
                'current_value': model_value,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'win_rate': win_rate,
                'total_trades': len(trades),
                'wins': len(profitable_trades),
                'losses': len(trades) - len(profitable_trades),
                'open_positions': len(portfolio.get('positions', [])),
                'is_active': is_active,
                'status': 'active' if is_active else 'paused'
            }

            models_summary.append(model_summary)

            # Aggregate totals
            total_capital += initial_capital
            total_value += model_value
            total_trades += len(trades)

        # Calculate aggregated metrics
        total_pnl = total_value - total_capital
        total_pnl_pct = (total_pnl / total_capital * 100) if total_capital > 0 else 0

        # Average win rate across all models
        avg_win_rate = sum(m['win_rate'] for m in models_summary) / len(models_summary) if models_summary else 0

        return jsonify({
            'models': models_summary,
            'aggregated': {
                'total_capital': total_capital,
                'total_value': total_value,
                'total_pnl': total_pnl,
                'total_pnl_pct': total_pnl_pct,
                'active_models': active_count,
                'total_models': len(models),
                'total_trades': total_trades,
                'avg_win_rate': avg_win_rate
            }
        })

    except Exception as e:
        import traceback
        print(f"[ERROR] All models summary failed: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@models_analytics_bp.route('/chart-data', methods=['GET'])
def get_models_chart_data():
    """Get chart data for all models"""
    limit = request.args.get('limit', 100, type=int)
    chart_data = db.get_multi_model_chart_data(limit=limit)
    return jsonify(chart_data)


@models_analytics_bp.route('/<int:model_id>/graduation-status', methods=['GET'])
def get_model_graduation_status(model_id):
    """Get model graduation status against criteria"""
    try:
        # Get graduation settings
        settings = db.get_graduation_settings()
        if not settings:
            return jsonify({'error': 'Graduation settings not configured'}), 400

        # Get model info
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM models WHERE id = ?', (model_id,))
        model = cursor.fetchone()
        if not model:
            conn.close()
            return jsonify({'error': 'Model not found'}), 404

        # Get trades count and first trade date
        cursor.execute('''
            SELECT COUNT(*) as count, MIN(timestamp) as first_trade
            FROM trades WHERE model_id = ?
        ''', (model_id,))
        trade_info = cursor.fetchone()
        total_trades = trade_info['count']
        first_trade_date = trade_info['first_trade']

        # Calculate testing days
        testing_days = 0
        if first_trade_date:
            first_date = datetime.fromisoformat(first_trade_date)
            testing_days = (datetime.now() - first_date).days

        # Get win rate
        cursor.execute('''
            SELECT
                COUNT(CASE WHEN pnl > 0 THEN 1 END) as wins,
                COUNT(*) as total
            FROM trades WHERE model_id = ?
        ''', (model_id,))
        win_data = cursor.fetchone()
        win_rate = (win_data['wins'] / win_data['total'] * 100) if win_data['total'] > 0 else 0

        # Calculate Sharpe ratio (simplified - using trade returns)
        cursor.execute('''
            SELECT pnl FROM trades WHERE model_id = ? ORDER BY timestamp
        ''', (model_id,))
        trades = cursor.fetchall()

        sharpe_ratio = 0
        if len(trades) > 1:
            returns = [t['pnl'] for t in trades]
            avg_return = sum(returns) / len(returns)
            std_return = math.sqrt(sum([(r - avg_return)**2 for r in returns]) / len(returns))
            sharpe_ratio = (avg_return / std_return) if std_return > 0 else 0

        # Calculate max drawdown
        cursor.execute('''
            SELECT total_value, timestamp FROM account_values
            WHERE model_id = ? ORDER BY timestamp
        ''', (model_id,))
        account_values = cursor.fetchall()

        max_drawdown = 0
        if len(account_values) > 0:
            peak = account_values[0]['total_value']
            for av in account_values:
                if av['total_value'] > peak:
                    peak = av['total_value']
                drawdown = ((peak - av['total_value']) / peak * 100) if peak > 0 else 0
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

        conn.close()

        # Calculate statistical confidence
        # Using simplified formula: confidence increases with sample size
        confidence_level = min(99, int(total_trades / settings['min_trades'] * settings['confidence_level']))

        # Build criteria results
        criteria = []
        passed_count = 0

        # Trades criterion
        trades_met = total_trades >= settings['min_trades']
        if trades_met:
            passed_count += 1
        criteria.append({
            'name': 'Minimum Trades',
            'required': settings['min_trades'],
            'actual': total_trades,
            'met': trades_met,
            'display': f"{total_trades}/{settings['min_trades']} trades"
        })

        # Days criterion
        days_met = testing_days >= settings['min_testing_days']
        if days_met:
            passed_count += 1
        criteria.append({
            'name': 'Testing Duration',
            'required': settings['min_testing_days'],
            'actual': testing_days,
            'met': days_met,
            'display': f"{testing_days}/{settings['min_testing_days']} days"
        })

        # Win rate criterion
        if settings['min_win_rate'] is not None:
            win_rate_met = win_rate >= settings['min_win_rate']
            if win_rate_met:
                passed_count += 1
            criteria.append({
                'name': 'Win Rate',
                'required': settings['min_win_rate'],
                'actual': round(win_rate, 1),
                'met': win_rate_met,
                'display': f"{round(win_rate, 1)}% ≥ {settings['min_win_rate']}%"
            })

        # Sharpe ratio criterion
        if settings['min_sharpe_ratio'] is not None:
            sharpe_met = sharpe_ratio >= settings['min_sharpe_ratio']
            if sharpe_met:
                passed_count += 1
            criteria.append({
                'name': 'Sharpe Ratio',
                'required': settings['min_sharpe_ratio'],
                'actual': round(sharpe_ratio, 2),
                'met': sharpe_met,
                'display': f"{round(sharpe_ratio, 2)} ≥ {settings['min_sharpe_ratio']}"
            })

        # Max drawdown criterion
        if settings['max_drawdown_pct'] is not None:
            drawdown_met = max_drawdown <= settings['max_drawdown_pct']
            if drawdown_met:
                passed_count += 1
            criteria.append({
                'name': 'Max Drawdown',
                'required': settings['max_drawdown_pct'],
                'actual': round(max_drawdown, 1),
                'met': drawdown_met,
                'display': f"{round(max_drawdown, 1)}% ≤ {settings['max_drawdown_pct']}%"
            })

        total_criteria = len(criteria)
        readiness_pct = int((passed_count / total_criteria * 100)) if total_criteria > 0 else 0

        return jsonify({
            'model_id': model_id,
            'strategy_preset': settings['strategy_preset'],
            'confidence_level': confidence_level,
            'criteria': criteria,
            'passed_count': passed_count,
            'total_criteria': total_criteria,
            'readiness_percentage': readiness_pct,
            'is_ready': passed_count == total_criteria
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@models_analytics_bp.route('/<int:model_id>/benchmark-comparison', methods=['GET'])
def get_benchmark_comparison(model_id):
    """Compare model performance against buy & hold benchmarks"""
    try:
        # Get model info and first trade date
        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM models WHERE id = ?', (model_id,))
        model = cursor.fetchone()
        if not model:
            conn.close()
            return jsonify({'error': 'Model not found'}), 404

        # Get first and last trade dates
        cursor.execute('''
            SELECT MIN(timestamp) as first_trade, MAX(timestamp) as last_trade
            FROM trades WHERE model_id = ?
        ''', (model_id,))
        trade_dates = cursor.fetchone()
        first_trade_date = trade_dates['first_trade']
        last_trade_date = trade_dates['last_trade']

        if not first_trade_date:
            conn.close()
            return jsonify({
                'error': 'No trades found',
                'message': 'Model has no trading history to compare'
            }), 400

        # Get model's performance
        cursor.execute('''
            SELECT
                COUNT(*) as total_trades,
                COUNT(CASE WHEN pnl > 0 THEN 1 END) as wins,
                COALESCE(SUM(pnl), 0) as total_pnl
            FROM trades WHERE model_id = ?
        ''', (model_id,))
        model_stats = cursor.fetchone()

        win_rate = (model_stats['wins'] / model_stats['total_trades'] * 100) if model_stats['total_trades'] > 0 else 0

        # Get model's current total value
        cursor.execute('''
            SELECT total_value FROM account_values
            WHERE model_id = ? ORDER BY timestamp DESC LIMIT 1
        ''', (model_id,))
        latest_value_row = cursor.fetchone()
        current_value = latest_value_row['total_value'] if latest_value_row else model['initial_capital']

        model_return_pct = ((current_value - model['initial_capital']) / model['initial_capital'] * 100)

        conn.close()

        # Calculate benchmarks
        benchmarks = []

        # Get price at start and end
        coins = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE']

        for coin in ['BTC', 'ETH']:
            start_price = db.get_price_at_timestamp(coin, first_trade_date)
            end_price = db.get_price_at_timestamp(coin, last_trade_date)

            if start_price and end_price:
                benchmark_return = ((end_price - start_price) / start_price * 100)
                benchmarks.append({
                    'name': f'Buy & Hold {coin}',
                    'return_pct': round(benchmark_return, 2),
                    'outperformed': model_return_pct > benchmark_return
                })
            else:
                benchmarks.append({
                    'name': f'Buy & Hold {coin}',
                    'return_pct': None,
                    'outperformed': None,
                    'note': 'Insufficient price data'
                })

        # Calculate 50/50 BTC/ETH
        btc_start = db.get_price_at_timestamp('BTC', first_trade_date)
        btc_end = db.get_price_at_timestamp('BTC', last_trade_date)
        eth_start = db.get_price_at_timestamp('ETH', first_trade_date)
        eth_end = db.get_price_at_timestamp('ETH', last_trade_date)

        if all([btc_start, btc_end, eth_start, eth_end]):
            btc_return = ((btc_end - btc_start) / btc_start * 100)
            eth_return = ((eth_end - eth_start) / eth_start * 100)
            balanced_return = (btc_return + eth_return) / 2

            benchmarks.append({
                'name': '50/50 BTC/ETH',
                'return_pct': round(balanced_return, 2),
                'outperformed': model_return_pct > balanced_return
            })

        # Calculate equal weight all coins
        equal_weight_returns = []
        for coin in coins:
            start_price = db.get_price_at_timestamp(coin, first_trade_date)
            end_price = db.get_price_at_timestamp(coin, last_trade_date)
            if start_price and end_price:
                coin_return = ((end_price - start_price) / start_price * 100)
                equal_weight_returns.append(coin_return)

        if len(equal_weight_returns) >= 4:
            avg_return = sum(equal_weight_returns) / len(equal_weight_returns)
            benchmarks.append({
                'name': f'Equal Weight ({len(equal_weight_returns)} coins)',
                'return_pct': round(avg_return, 2),
                'outperformed': model_return_pct > avg_return
            })

        return jsonify({
            'model_id': model_id,
            'model_name': model['name'],
            'testing_period': {
                'start': first_trade_date,
                'end': last_trade_date
            },
            'model_performance': {
                'initial_capital': model['initial_capital'],
                'current_value': current_value,
                'return_pct': round(model_return_pct, 2),
                'total_pnl': round(model_stats['total_pnl'], 2),
                'total_trades': model_stats['total_trades'],
                'win_rate': round(win_rate, 1)
            },
            'benchmarks': benchmarks,
            'verdict': generateVerdict(model_return_pct, benchmarks)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ Aggregated Portfolio Routes ============

@aggregated_bp.route('/portfolio', methods=['GET'])
def get_aggregated_portfolio():
    """Get aggregated portfolio data across all models"""
    prices_data = market_fetcher.get_current_prices(['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE'])
    current_prices = {coin: prices_data[coin]['price'] for coin in prices_data}

    # Get aggregated data
    models = db.get_all_models()
    total_portfolio = {
        'total_value': 0,
        'cash': 0,
        'positions_value': 0,
        'realized_pnl': 0,
        'unrealized_pnl': 0,
        'initial_capital': 0,
        'positions': []
    }

    all_positions = {}

    for model in models:
        portfolio = db.get_portfolio(model['id'], current_prices)
        if portfolio:
            total_portfolio['total_value'] += portfolio.get('total_value', 0)
            total_portfolio['cash'] += portfolio.get('cash', 0)
            total_portfolio['positions_value'] += portfolio.get('positions_value', 0)
            total_portfolio['realized_pnl'] += portfolio.get('realized_pnl', 0)
            total_portfolio['unrealized_pnl'] += portfolio.get('unrealized_pnl', 0)
            total_portfolio['initial_capital'] += portfolio.get('initial_capital', 0)

            # Aggregate positions by coin and side
            for pos in portfolio.get('positions', []):
                key = f"{pos['coin']}_{pos['side']}"
                if key not in all_positions:
                    all_positions[key] = {
                        'coin': pos['coin'],
                        'side': pos['side'],
                        'quantity': 0,
                        'avg_price': 0,
                        'total_cost': 0,
                        'leverage': pos['leverage'],
                        'current_price': pos['current_price'],
                        'pnl': 0
                    }

                # Weighted average calculation
                current_pos = all_positions[key]
                current_cost = current_pos['quantity'] * current_pos['avg_price']
                new_cost = pos['quantity'] * pos['avg_price']
                total_quantity = current_pos['quantity'] + pos['quantity']

                if total_quantity > 0:
                    current_pos['avg_price'] = (current_cost + new_cost) / total_quantity
                    current_pos['quantity'] = total_quantity
                    current_pos['total_cost'] = current_cost + new_cost
                    current_pos['pnl'] = (pos['current_price'] - current_pos['avg_price']) * total_quantity

    total_portfolio['positions'] = list(all_positions.values())

    # Get multi-model chart data
    chart_data = db.get_multi_model_chart_data(limit=100)

    return jsonify({
        'portfolio': total_portfolio,
        'chart_data': chart_data,
        'model_count': len(models)
    })


# ============ Market Data Routes ============

@market_bp.route('/prices', methods=['GET'])
def get_market_prices():
    coins = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE']
    prices = market_fetcher.get_current_prices(coins)
    return jsonify(prices)

"""
Model API Blueprint
Handles all model-related API endpoints including CRUD operations,
portfolio management, trading execution, and performance analytics.
"""
from flask import Blueprint, request, jsonify
import time
import threading
import json
import re
from datetime import datetime, timedelta
import numpy as np
from routes import app_context
from trading_engine import TradingEngine
from ai_trader import AITrader
from market_data import MarketDataFetcher
from version import __version__, __github_owner__, __repo__, GITHUB_REPO_URL, LATEST_RELEASE_URL

models_bp = Blueprint('models', __name__)


# ============ Model CRUD Endpoints ============

@models_bp.route('/api/models', methods=['GET'])
def get_models():
    db = app_context['db']
    models = db.get_all_models()
    return jsonify(models)


@models_bp.route('/api/models', methods=['POST'])
def add_model():
    db = app_context['db']
    market_fetcher = app_context['market_fetcher']
    trading_engines = app_context['trading_engines']
    TRADE_FEE_RATE = app_context['TRADE_FEE_RATE']

    data = request.json
    try:
        # Get provider info
        provider = db.get_provider(data['provider_id'])
        if not provider:
            return jsonify({'error': 'Provider not found'}), 404

        model_id = db.add_model(
            name=data['name'],
            provider_id=data['provider_id'],
            model_name=data['model_name'],
            initial_capital=float(data.get('initial_capital', 100000))
        )

        model = db.get_model(model_id)
        trading_engines[model_id] = TradingEngine(
            model_id=model_id,
            db=db,
            market_fetcher=market_fetcher,
            ai_trader=AITrader(
                api_key=model['api_key'],
                api_url=model['api_url'],
                model_name=model['model_name']
            ),
            trade_fee_rate=TRADE_FEE_RATE  # 新增：传入费率
        )
        print(f"[INFO] Model {model_id} ({data['name']}) initialized")

        return jsonify({'id': model_id, 'message': 'Model added successfully'})

    except Exception as e:
        print(f"[ERROR] Failed to add model: {e}")
        return jsonify({'error': str(e)}), 500


@models_bp.route('/api/models/<int:model_id>', methods=['PUT'])
def update_model(model_id):
    """Update model information"""
    db = app_context['db']
    market_fetcher = app_context['market_fetcher']
    trading_engines = app_context['trading_engines']
    TRADE_FEE_RATE = app_context['TRADE_FEE_RATE']

    data = request.json
    try:
        db.update_model(
            model_id=model_id,
            name=data.get('name'),
            provider_id=data.get('provider_id'),
            model_name=data.get('model_name'),
            initial_capital=data.get('initial_capital')
        )

        # If model is in trading_engines and provider/model_name changed, reinitialize
        if model_id in trading_engines and (data.get('provider_id') or data.get('model_name')):
            model = db.get_model(model_id)
            trading_engines[model_id] = TradingEngine(
                model_id=model_id,
                db=db,
                market_fetcher=market_fetcher,
                ai_trader=AITrader(
                    api_key=model['api_key'],
                    api_url=model['api_url'],
                    model_name=model['model_name']
                ),
                trade_fee_rate=TRADE_FEE_RATE
            )
            print(f"[INFO] Model {model_id} ({model['name']}) reinitialized")

        return jsonify({'message': 'Model updated successfully'})
    except Exception as e:
        print(f"[ERROR] Update model {model_id} failed: {e}")
        return jsonify({'error': str(e)}), 500


@models_bp.route('/api/models/<int:model_id>', methods=['DELETE'])
def delete_model(model_id):
    db = app_context['db']
    trading_engines = app_context['trading_engines']

    try:
        model = db.get_model(model_id)
        model_name = model['name'] if model else f"ID-{model_id}"

        db.delete_model(model_id)
        if model_id in trading_engines:
            del trading_engines[model_id]

        print(f"[INFO] Model {model_id} ({model_name}) deleted")
        return jsonify({'message': 'Model deleted successfully'})
    except Exception as e:
        print(f"[ERROR] Delete model {model_id} failed: {e}")
        return jsonify({'error': str(e)}), 500


# ============ Portfolio Management Endpoints ============

@models_bp.route('/api/models/<int:model_id>/portfolio', methods=['GET'])
def get_portfolio(model_id):
    db = app_context['db']
    market_fetcher = app_context['market_fetcher']

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


@models_bp.route('/api/models/<int:model_id>/portfolio-metrics', methods=['GET'])
def get_portfolio_metrics(model_id):
    """Get aggregated portfolio metrics for dashboard"""
    db = app_context['db']
    enhanced_db = app_context['enhanced_db']
    market_fetcher = app_context['market_fetcher']

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


@models_bp.route('/api/models/<int:model_id>/portfolio-history', methods=['GET'])
def get_portfolio_history(model_id):
    """Get portfolio value history for chart"""
    db = app_context['db']

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


@models_bp.route('/api/models/<int:model_id>/asset-allocation', methods=['GET'])
def get_asset_allocation(model_id):
    """Get current asset allocation for donut chart"""
    db = app_context['db']
    enhanced_db = app_context['enhanced_db']
    market_fetcher = app_context['market_fetcher']

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


# ============ Trade History Endpoints ============

@models_bp.route('/api/models/<int:model_id>/trades', methods=['GET'])
def get_trades(model_id):
    enhanced_db = app_context['enhanced_db']

    limit = request.args.get('limit', 50, type=int)
    trades = enhanced_db.get_trades(model_id, limit=limit)
    return jsonify(trades)


@models_bp.route('/api/models/<int:model_id>/conversations', methods=['GET'])
def get_conversations(model_id):
    enhanced_db = app_context['enhanced_db']

    limit = request.args.get('limit', 20, type=int)
    conversations = enhanced_db.get_conversations(model_id, limit=limit)
    return jsonify(conversations)


# ============ Performance Analytics Endpoints ============

@models_bp.route('/api/models/<int:model_id>/performance-analytics', methods=['GET'])
def get_performance_analytics(model_id):
    """Get detailed performance analytics including Sharpe ratio, drawdown, streaks, etc."""
    db = app_context['db']
    enhanced_db = app_context['enhanced_db']

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


# ============ All Models Summary Endpoints ============

@models_bp.route('/api/models/all-summary', methods=['GET'])
def get_all_models_summary():
    """Get comprehensive summary of all models for the Models page"""
    db = app_context['db']
    enhanced_db = app_context['enhanced_db']
    market_fetcher = app_context['market_fetcher']

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


# ============ Aggregated Portfolio Endpoints ============

@models_bp.route('/api/aggregated/portfolio', methods=['GET'])
def get_aggregated_portfolio():
    """Get aggregated portfolio data across all models"""
    db = app_context['db']
    market_fetcher = app_context['market_fetcher']

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


@models_bp.route('/api/models/chart-data', methods=['GET'])
def get_models_chart_data():
    """Get chart data for all models"""
    db = app_context['db']

    limit = request.args.get('limit', 100, type=int)
    chart_data = db.get_multi_model_chart_data(limit=limit)
    return jsonify(chart_data)


# ============ Market Data Endpoints ============

@models_bp.route('/api/market/prices', methods=['GET'])
def get_market_prices():
    market_fetcher = app_context['market_fetcher']

    coins = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE']
    prices = market_fetcher.get_current_prices(coins)
    return jsonify(prices)


# ============ Trading Execution Endpoints ============

@models_bp.route('/api/models/<int:model_id>/execute', methods=['POST'])
def execute_trading(model_id):
    db = app_context['db']
    market_fetcher = app_context['market_fetcher']
    trading_engines = app_context['trading_engines']
    TRADE_FEE_RATE = app_context['TRADE_FEE_RATE']

    if model_id not in trading_engines:
        model = db.get_model(model_id)
        if not model:
            return jsonify({'error': 'Model not found'}), 404

        # Get provider info
        provider = db.get_provider(model['provider_id'])
        if not provider:
            return jsonify({'error': 'Provider not found'}), 404

        trading_engines[model_id] = TradingEngine(
            model_id=model_id,
            db=db,
            market_fetcher=market_fetcher,
            ai_trader=AITrader(
                api_key=provider['api_key'],
                api_url=provider['api_url'],
                model_name=model['model_name']
            ),
            trade_fee_rate=TRADE_FEE_RATE  # 新增：传入费率
        )

    try:
        result = trading_engines[model_id].execute_trading_cycle()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ Leaderboard Endpoints ============

@models_bp.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    db = app_context['db']
    market_fetcher = app_context['market_fetcher']

    models = db.get_all_models()
    leaderboard = []

    prices_data = market_fetcher.get_current_prices(['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE'])
    current_prices = {coin: prices_data[coin]['price'] for coin in prices_data}

    for model in models:
        portfolio = db.get_portfolio(model['id'], current_prices)
        account_value = portfolio.get('total_value', model['initial_capital'])
        returns = ((account_value - model['initial_capital']) / model['initial_capital']) * 100

        leaderboard.append({
            'model_id': model['id'],
            'model_name': model['name'],
            'account_value': account_value,
            'returns': returns,
            'initial_capital': model['initial_capital']
        })

    leaderboard.sort(key=lambda x: x['returns'], reverse=True)
    return jsonify(leaderboard)


# ============ Settings Endpoints ============

@models_bp.route('/api/settings', methods=['GET'])
def get_settings():
    """Get system settings"""
    db = app_context['db']

    try:
        settings = db.get_settings()
        return jsonify(settings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@models_bp.route('/api/settings', methods=['PUT'])
def update_settings():
    """Update system settings"""
    db = app_context['db']

    try:
        data = request.json
        trading_frequency_minutes = int(data.get('trading_frequency_minutes', 60))
        trading_fee_rate = float(data.get('trading_fee_rate', 0.001))

        success = db.update_settings(trading_frequency_minutes, trading_fee_rate)

        if success:
            return jsonify({'success': True, 'message': 'Settings updated successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to update settings'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ Version Check Endpoints ============

@models_bp.route('/api/version', methods=['GET'])
def get_version():
    """Get current version information"""
    return jsonify({
        'current_version': __version__,
        'github_repo': GITHUB_REPO_URL,
        'latest_release_url': LATEST_RELEASE_URL
    })


@models_bp.route('/api/check-update', methods=['GET'])
def check_update():
    """Check for GitHub updates"""
    try:
        import requests

        # Get latest release from GitHub
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'AITradeGame/1.0'
        }

        # Try to get latest release
        try:
            response = requests.get(
                f"https://api.github.com/repos/{__github_owner__}/{__repo__}/releases/latest",
                headers=headers,
                timeout=5
            )

            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data.get('tag_name', '').lstrip('v')
                release_url = release_data.get('html_url', '')
                release_notes = release_data.get('body', '')

                # Compare versions
                is_update_available = compare_versions(latest_version, __version__) > 0

                return jsonify({
                    'update_available': is_update_available,
                    'current_version': __version__,
                    'latest_version': latest_version,
                    'release_url': release_url,
                    'release_notes': release_notes,
                    'repo_url': GITHUB_REPO_URL
                })
            else:
                # If API fails, still return current version info
                return jsonify({
                    'update_available': False,
                    'current_version': __version__,
                    'error': 'Could not check for updates'
                })
        except Exception as e:
            print(f"[WARN] GitHub API error: {e}")
            return jsonify({
                'update_available': False,
                'current_version': __version__,
                'error': 'Network error checking updates'
            })

    except Exception as e:
        print(f"[ERROR] Check update failed: {e}")
        return jsonify({
            'update_available': False,
            'current_version': __version__,
            'error': str(e)
        }), 500


# ============ Helper Functions ============

def trading_loop():
    """
    Main trading loop that executes trading cycles for all active models.
    This function runs in a separate thread when auto-trading is enabled.
    """
    print("[INFO] Trading loop started")

    auto_trading = app_context['auto_trading']
    trading_engines = app_context['trading_engines']

    while auto_trading:
        try:
            if not trading_engines:
                time.sleep(30)
                continue

            print(f"\n{'='*60}")
            print(f"[CYCLE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"[INFO] Active models: {len(trading_engines)}")
            print(f"{'='*60}")

            for model_id, engine in list(trading_engines.items()):
                try:
                    print(f"\n[EXEC] Model {model_id}")
                    result = engine.execute_trading_cycle()

                    if result.get('success'):
                        print(f"[OK] Model {model_id} completed")
                        if result.get('executions'):
                            for exec_result in result['executions']:
                                signal = exec_result.get('signal', 'unknown')
                                coin = exec_result.get('coin', 'unknown')

                                # Check for error first
                                if 'error' in exec_result:
                                    print(f"  [ERROR] {coin}: {exec_result['error']}")
                                elif signal != 'hold':
                                    msg = exec_result.get('message', '')
                                    print(f"  [TRADE] {coin}: {msg}")
                    else:
                        error = result.get('error', 'Unknown error')
                        print(f"[WARN] Model {model_id} failed: {error}")

                except Exception as e:
                    print(f"[ERROR] Model {model_id} exception: {e}")
                    import traceback
                    print(traceback.format_exc())
                    continue

            print(f"\n{'='*60}")
            print(f"[SLEEP] Waiting 3 minutes for next cycle")
            print(f"{'='*60}\n")

            time.sleep(180)

        except Exception as e:
            print(f"\n[CRITICAL] Trading loop error: {e}")
            import traceback
            print(traceback.format_exc())
            print("[RETRY] Retrying in 60 seconds\n")
            time.sleep(60)

    print("[INFO] Trading loop stopped")


def init_trading_engines():
    """
    Initialize trading engines for all existing models.
    This is called during application startup.
    """
    db = app_context['db']
    market_fetcher = app_context['market_fetcher']
    trading_engines = app_context['trading_engines']
    TRADE_FEE_RATE = app_context['TRADE_FEE_RATE']

    models = db.get_all_models()
    for model in models:
        try:
            trading_engines[model['id']] = TradingEngine(
                model_id=model['id'],
                db=db,
                market_fetcher=market_fetcher,
                ai_trader=AITrader(
                    api_key=model['api_key'],
                    api_url=model['api_url'],
                    model_name=model['model_name']
                ),
                trade_fee_rate=TRADE_FEE_RATE
            )
            print(f"[INFO] Model {model['id']} ({model['name']}) initialized")
        except Exception as e:
            print(f"[ERROR] Failed to initialize model {model['id']}: {e}")


def compare_versions(version1, version2):
    """Compare two version strings.

    Returns:
        1 if version1 > version2
        0 if version1 == version2
        -1 if version1 < version2
    """
    def normalize(v):
        # Extract numeric parts from version string
        parts = re.findall(r'\d+', v)
        # Pad with zeros to make them comparable
        return [int(p) for p in parts]

    v1_parts = normalize(version1)
    v2_parts = normalize(version2)

    # Pad shorter version with zeros
    max_len = max(len(v1_parts), len(v2_parts))
    v1_parts.extend([0] * (max_len - len(v1_parts)))
    v2_parts.extend([0] * (max_len - len(v2_parts)))

    # Compare
    if v1_parts > v2_parts:
        return 1
    elif v1_parts < v2_parts:
        return -1
    else:
        return 0

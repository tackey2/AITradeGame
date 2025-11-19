"""
Graduation and Benchmark API Blueprint.
Handles model graduation criteria, status tracking, and benchmark comparisons.
"""

from flask import Blueprint, request, jsonify
from routes import app_context
from datetime import datetime, timedelta
import math

graduation_bp = Blueprint('graduation', __name__)


# ============ Graduation & Benchmark Settings API ============

@graduation_bp.route('/api/graduation-settings', methods=['GET'])
def get_graduation_settings_api():
    """Get graduation criteria settings"""
    try:
        db = app_context['db']
        settings = db.get_graduation_settings()
        return jsonify(settings if settings else {})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@graduation_bp.route('/api/graduation-settings', methods=['POST'])
def update_graduation_settings_api():
    """Update graduation criteria settings"""
    try:
        db = app_context['db']
        settings = request.json
        db.update_graduation_settings(settings)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@graduation_bp.route('/api/benchmark-settings', methods=['GET'])
def get_benchmark_settings_api():
    """Get benchmark settings"""
    try:
        db = app_context['db']
        settings = db.get_benchmark_settings()
        return jsonify(settings if settings else {})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@graduation_bp.route('/api/benchmark-settings', methods=['POST'])
def update_benchmark_settings_api():
    """Update benchmark settings"""
    try:
        db = app_context['db']
        settings = request.json
        db.update_benchmark_settings(settings)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@graduation_bp.route('/api/cost-tracking-settings', methods=['GET'])
def get_cost_tracking_settings_api():
    """Get cost tracking settings"""
    try:
        db = app_context['db']
        settings = db.get_cost_tracking_settings()
        return jsonify(settings if settings else {})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@graduation_bp.route('/api/cost-tracking-settings', methods=['POST'])
def update_cost_tracking_settings_api():
    """Update cost tracking settings"""
    try:
        db = app_context['db']
        settings = request.json
        db.update_cost_tracking_settings(settings)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ Model Graduation Status API ============

@graduation_bp.route('/api/models/<int:model_id>/graduation-status', methods=['GET'])
def get_model_graduation_status(model_id):
    """Get model graduation status against criteria"""
    try:
        db = app_context['db']

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

        # Get trades count and first trade date (exclude 'hold' signals)
        cursor.execute('''
            SELECT COUNT(*) as count, MIN(timestamp) as first_trade
            FROM trades WHERE model_id = ? AND signal != 'hold'
        ''', (model_id,))
        trade_info = cursor.fetchone()
        total_trades = trade_info['count']
        first_trade_date = trade_info['first_trade']

        # Calculate testing duration in both days and minutes
        testing_days = 0
        testing_minutes = 0
        if first_trade_date:
            first_date = datetime.fromisoformat(first_trade_date)
            time_delta = datetime.now() - first_date
            testing_days = time_delta.days
            testing_minutes = int(time_delta.total_seconds() / 60)

        # Get win rate (exclude 'hold' signals)
        cursor.execute('''
            SELECT
                COUNT(CASE WHEN pnl > 0 THEN 1 END) as wins,
                COUNT(*) as total
            FROM trades WHERE model_id = ? AND signal != 'hold'
        ''', (model_id,))
        win_data = cursor.fetchone()
        win_rate = (win_data['wins'] / win_data['total'] * 100) if win_data['total'] > 0 else 0

        # Calculate Sharpe ratio (simplified - using trade returns, exclude 'hold' signals)
        cursor.execute('''
            SELECT pnl FROM trades WHERE model_id = ? AND signal != 'hold' ORDER BY timestamp
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

        # Duration criterion - support both minutes and days
        # If min_testing_minutes is set and > 0, use minutes; otherwise use days
        use_minutes = settings.get('min_testing_minutes', 0) > 0

        if use_minutes:
            min_duration = settings['min_testing_minutes']
            actual_duration = testing_minutes
            duration_met = testing_minutes >= min_duration

            # Format display based on duration
            if testing_minutes < 60:
                actual_display = f"{testing_minutes} min"
            elif testing_minutes < 1440:
                actual_display = f"{testing_minutes // 60}h {testing_minutes % 60}m"
            else:
                actual_display = f"{testing_minutes // 1440}d {(testing_minutes % 1440) // 60}h"

            if min_duration < 60:
                required_display = f"{min_duration} min"
            elif min_duration < 1440:
                required_display = f"{min_duration // 60}h {min_duration % 60}m"
            else:
                required_display = f"{min_duration // 1440}d {(min_duration % 1440) // 60}h"

            display_text = f"{actual_display} / {required_display}"
        else:
            # Use days (legacy mode)
            min_duration = settings.get('min_testing_days', 14)
            actual_duration = testing_days
            duration_met = testing_days >= min_duration
            display_text = f"{testing_days}/{min_duration} days"

        if duration_met:
            passed_count += 1
        criteria.append({
            'name': 'Testing Duration',
            'required': min_duration,
            'actual': actual_duration,
            'met': duration_met,
            'display': display_text
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


# ============ Benchmark Comparison API ============

@graduation_bp.route('/api/models/<int:model_id>/benchmark-comparison', methods=['GET'])
def get_benchmark_comparison(model_id):
    """Compare model performance against buy & hold benchmarks"""
    try:
        db = app_context['db']

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

        # Get model's performance (exclude 'hold' signals)
        cursor.execute('''
            SELECT
                COUNT(*) as total_trades,
                COUNT(CASE WHEN pnl > 0 THEN 1 END) as wins,
                COALESCE(SUM(pnl), 0) as total_pnl
            FROM trades WHERE model_id = ? AND signal != 'hold'
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
            'verdict': generate_verdict(model_return_pct, benchmarks)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ Helper Functions ============

def generate_verdict(model_return, benchmarks):
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

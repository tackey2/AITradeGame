"""
Risk management routes for AI Trade Game.
Includes risk profiles, risk status, readiness assessment, and incidents logging.
"""
from flask import Blueprint, request, jsonify
from datetime import datetime

# Create blueprints
risk_bp = Blueprint('risk', __name__, url_prefix='/api')

# Shared resources will be injected via init_app
db = None
enhanced_db = None
market_fetcher = None
risk_managers = None


def init_app(database, enhanced_database, market_data_fetcher, risk_manager_dict):
    """Initialize blueprint with shared resources"""
    global db, enhanced_db, market_fetcher, risk_managers
    db = database
    enhanced_db = enhanced_database
    market_fetcher = market_data_fetcher
    risk_managers = risk_manager_dict


# ==================== Helper Functions ====================

def _calculate_risk_score(profile):
    """Calculate a risk score (0-100) for a profile"""
    score = 0
    score += profile['max_position_size_pct'] * 2  # Weight: 2
    score += profile['max_open_positions'] * 3  # Weight: 3
    score += (100 - profile['min_cash_reserve_pct']) * 0.5  # Weight: 0.5
    score += profile['max_daily_loss_pct'] * 5  # Weight: 5
    score += profile['max_drawdown_pct'] * 2  # Weight: 2
    return min(100, score)


def _classify_market_condition(metrics: dict) -> str:
    """Classify overall market condition"""
    if metrics['drawdown_pct'] < -15 or metrics['recent_win_rate'] < 30:
        return 'adverse'
    elif metrics['win_rate'] > 60 and metrics['drawdown_pct'] > -5:
        return 'favorable'
    elif metrics['volatility'] > 150:
        return 'volatile'
    else:
        return 'normal'


def _assess_risk_level(metrics: dict) -> str:
    """Assess current risk level"""
    risk_score = 0

    if metrics['drawdown_pct'] < -10:
        risk_score += 3
    if metrics['consecutive_losses'] >= 4:
        risk_score += 2
    if metrics['volatility'] > 150:
        risk_score += 2
    if metrics['recent_win_rate'] < 40:
        risk_score += 2

    if risk_score >= 5:
        return 'high'
    elif risk_score >= 3:
        return 'elevated'
    elif risk_score >= 1:
        return 'moderate'
    else:
        return 'low'


def _assess_trading_suitability(metrics: dict) -> str:
    """Assess if conditions are suitable for trading"""
    if metrics['drawdown_pct'] < -15:
        return 'not_recommended'
    elif metrics['consecutive_losses'] >= 5:
        return 'pause_recommended'
    elif metrics['win_rate'] > 55 and metrics['total_trades'] >= 15:
        return 'excellent'
    elif metrics['total_trades'] < 5:
        return 'insufficient_data'
    else:
        return 'proceed_with_caution'


def _get_suitability_label(score: float) -> str:
    """Convert suitability score to label"""
    if score >= 80:
        return 'Highly Recommended'
    elif score >= 60:
        return 'Recommended'
    elif score >= 40:
        return 'Suitable'
    elif score >= 20:
        return 'Not Ideal'
    else:
        return 'Not Recommended'


# ==================== Risk Status Routes ====================

@risk_bp.route('/models/<int:model_id>/risk-status', methods=['GET'])
def get_risk_status(model_id):
    """Get current risk status for a model"""
    try:
        # Check if model exists first
        model = enhanced_db.get_model(model_id)
        if not model:
            return jsonify({'error': f'Model {model_id} not found'}), 404

        # Initialize risk manager for this model if needed
        if model_id not in risk_managers:
            from risk_manager import RiskManager
            risk_managers[model_id] = RiskManager(enhanced_db)

        # Get portfolio
        prices_data = market_fetcher.get_current_prices(['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE'])
        portfolio = enhanced_db.get_portfolio(model_id, prices_data)

        # Get settings (with defaults if not set)
        settings = enhanced_db.get_model_settings(model_id)
        if not settings:
            settings = {}

        # Calculate risk metrics
        total_value = portfolio['total_value']
        initial_capital = model['initial_capital']

        # Position size usage
        position_value = portfolio['positions_value']
        max_position_size = total_value * (settings.get('max_position_size_pct', 10.0) / 100)
        position_usage = (position_value / max_position_size * 100) if max_position_size > 0 else 0

        # Daily loss
        daily_loss_pct = ((total_value - initial_capital) / initial_capital * 100)
        max_daily_loss = settings.get('max_daily_loss_pct', 3.0)

        # Open positions
        open_positions = len(portfolio['positions'])
        max_open_positions = settings.get('max_open_positions', 5)

        # Cash reserve
        cash_reserve_pct = (portfolio['cash'] / total_value * 100) if total_value > 0 else 0
        min_cash_reserve = settings.get('min_cash_reserve_pct', 20.0)

        # Recent trades
        recent_trades = enhanced_db.get_trades(model_id, limit=10)
        trades_today = len([t for t in recent_trades if t['timestamp'].startswith(datetime.now().strftime('%Y-%m-%d'))])
        max_daily_trades = settings.get('max_daily_trades', 20)

        risk_status = {
            'position_size': {
                'current': position_value,
                'max': max_position_size,
                'usage_pct': position_usage,
                'status': 'ok' if position_usage < 80 else 'warning' if position_usage < 100 else 'critical'
            },
            'daily_loss': {
                'current_pct': daily_loss_pct,
                'max_pct': max_daily_loss,
                'status': 'ok' if daily_loss_pct > -max_daily_loss else 'critical'
            },
            'open_positions': {
                'current': open_positions,
                'max': max_open_positions,
                'status': 'ok' if open_positions < max_open_positions else 'critical'
            },
            'cash_reserve': {
                'current_pct': cash_reserve_pct,
                'min_pct': min_cash_reserve,
                'status': 'ok' if cash_reserve_pct >= min_cash_reserve else 'warning'
            },
            'daily_trades': {
                'current': trades_today,
                'max': max_daily_trades,
                'status': 'ok' if trades_today < max_daily_trades else 'critical'
            }
        }

        return jsonify(risk_status)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] Risk status endpoint failed for model {model_id}:")
        print(error_trace)
        return jsonify({'error': str(e), 'details': error_trace}), 500


# ==================== Risk Profiles Management Routes ====================

@risk_bp.route('/risk-profiles', methods=['GET'])
def get_all_risk_profiles():
    """Get all risk profiles (system and custom)"""
    try:
        profiles = enhanced_db.get_all_risk_profiles()
        return jsonify(profiles)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@risk_bp.route('/risk-profiles/<int:profile_id>', methods=['GET'])
def get_risk_profile(profile_id):
    """Get a specific risk profile"""
    try:
        profile = enhanced_db.get_risk_profile(profile_id)
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        return jsonify(profile)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@risk_bp.route('/risk-profiles', methods=['POST'])
def create_custom_risk_profile():
    """Create a custom risk profile"""
    try:
        data = request.json

        name = data.get('name')
        description = data.get('description', '')
        color = data.get('color', '#64748b')
        icon = data.get('icon', '⭐')

        if not name:
            return jsonify({'error': 'Profile name is required'}), 400

        # Extract risk parameters
        parameters = {
            'max_position_size_pct': data.get('max_position_size_pct', 10.0),
            'max_open_positions': data.get('max_open_positions', 5),
            'min_cash_reserve_pct': data.get('min_cash_reserve_pct', 20.0),
            'max_daily_loss_pct': data.get('max_daily_loss_pct', 3.0),
            'max_drawdown_pct': data.get('max_drawdown_pct', 15.0),
            'max_daily_trades': data.get('max_daily_trades', 20),
            'trading_interval_minutes': data.get('trading_interval_minutes', 60),
            'auto_pause_consecutive_losses': data.get('auto_pause_consecutive_losses', 5),
            'auto_pause_win_rate_threshold': data.get('auto_pause_win_rate_threshold', 40.0),
            'auto_pause_volatility_multiplier': data.get('auto_pause_volatility_multiplier', 3.0),
            'trading_fee_rate': data.get('trading_fee_rate', 0.1),
            'ai_temperature': data.get('ai_temperature', 0.7),
            'ai_strategy': data.get('ai_strategy', 'day_trading_mean_reversion')
        }

        profile_id = enhanced_db.create_custom_risk_profile(
            name=name,
            description=description,
            parameters=parameters,
            color=color,
            icon=icon
        )

        return jsonify({
            'success': True,
            'profile_id': profile_id,
            'message': f'Custom profile "{name}" created successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@risk_bp.route('/risk-profiles/<int:profile_id>', methods=['PUT'])
def update_risk_profile(profile_id):
    """Update a custom risk profile"""
    try:
        data = request.json
        enhanced_db.update_risk_profile(profile_id, data)
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully'
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@risk_bp.route('/risk-profiles/<int:profile_id>', methods=['DELETE'])
def delete_risk_profile(profile_id):
    """Delete a custom risk profile"""
    try:
        enhanced_db.delete_risk_profile(profile_id)
        return jsonify({
            'success': True,
            'message': 'Profile deleted successfully'
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Profile Application Routes ====================

@risk_bp.route('/models/<int:model_id>/apply-profile', methods=['POST'])
def apply_risk_profile(model_id):
    """Apply a risk profile to a model"""
    try:
        data = request.json
        profile_id = data.get('profile_id')

        if not profile_id:
            return jsonify({'error': 'profile_id is required'}), 400

        enhanced_db.apply_risk_profile(model_id, profile_id)

        profile = enhanced_db.get_risk_profile(profile_id)

        return jsonify({
            'success': True,
            'message': f'Profile "{profile["name"]}" applied successfully',
            'profile': profile
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@risk_bp.route('/models/<int:model_id>/active-profile', methods=['GET'])
def get_active_profile(model_id):
    """Get the active risk profile for a model"""
    try:
        settings = enhanced_db.get_model_settings(model_id)
        profile_id = settings.get('active_profile_id')

        if not profile_id:
            return jsonify({
                'active_profile': None,
                'message': 'No profile active, using custom settings'
            })

        profile = enhanced_db.get_risk_profile(profile_id)
        return jsonify({
            'active_profile': profile
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Profile Performance and History Routes ====================

@risk_bp.route('/risk-profiles/<int:profile_id>/performance', methods=['GET'])
def get_profile_performance(profile_id):
    """Get performance metrics for a risk profile"""
    try:
        performance = enhanced_db.get_profile_performance(profile_id)
        return jsonify(performance)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@risk_bp.route('/models/<int:model_id>/profile-history', methods=['GET'])
def get_model_profile_history(model_id):
    """Get profile usage history for a model"""
    try:
        limit = request.args.get('limit', 10, type=int)
        history = enhanced_db.get_model_profile_history(model_id, limit)
        return jsonify(history)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@risk_bp.route('/risk-profiles/compare', methods=['POST'])
def compare_risk_profiles():
    """Compare multiple risk profiles"""
    try:
        data = request.json
        profile_ids = data.get('profile_ids', [])

        if not profile_ids or len(profile_ids) < 2:
            return jsonify({'error': 'At least 2 profile IDs required for comparison'}), 400

        profiles = []
        for profile_id in profile_ids:
            profile = enhanced_db.get_risk_profile(profile_id)
            if profile:
                performance = enhanced_db.get_profile_performance(profile_id)
                profile['performance'] = performance
                profiles.append(profile)

        return jsonify({
            'profiles': profiles,
            'comparison': {
                'risk_levels': {p['name']: _calculate_risk_score(p) for p in profiles},
                'performance': {p['name']: p['performance']['avg_pnl_pct'] for p in profiles}
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Profile Recommendations Routes ====================

@risk_bp.route('/models/<int:model_id>/recommend-profile', methods=['GET'])
def recommend_profile(model_id):
    """
    Analyze current performance and recommend optimal risk profile
    Uses existing trade data - no external APIs required
    """
    try:
        from market_analyzer import MarketAnalyzer
        analyzer = MarketAnalyzer(enhanced_db)
        recommendation = analyzer.recommend_profile(model_id)

        # Get full profile details for recommended profile
        recommended_profile_data = enhanced_db.get_risk_profile_by_name(
            recommendation['recommended_profile']
        )

        return jsonify({
            'success': True,
            'recommendation': {
                'profile_name': recommendation['recommended_profile'],
                'profile_id': recommended_profile_data['id'] if recommended_profile_data else None,
                'profile_icon': recommended_profile_data['icon'] if recommended_profile_data else '⭐',
                'current_profile': recommendation['current_profile'],
                'should_switch': recommendation['should_switch'],
                'reason': recommendation['reason'],
                'all_reasons': recommendation['all_reasons'],
                'confidence': recommendation['confidence']
            },
            'metrics': recommendation['metrics'],
            'alternatives': recommendation['alternatives']
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@risk_bp.route('/models/<int:model_id>/market-metrics', methods=['GET'])
def get_market_metrics(model_id):
    """Get detailed market condition metrics"""
    try:
        from market_analyzer import MarketAnalyzer
        analyzer = MarketAnalyzer(enhanced_db)
        metrics = analyzer.get_market_metrics(model_id)

        return jsonify({
            'success': True,
            'metrics': metrics,
            'analysis': {
                'condition': _classify_market_condition(metrics),
                'risk_level': _assess_risk_level(metrics),
                'trading_suitability': _assess_trading_suitability(metrics)
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@risk_bp.route('/models/<int:model_id>/profile-suitability', methods=['GET'])
def get_profile_suitability(model_id):
    """Get suitability scores for all profiles"""
    try:
        from market_analyzer import MarketAnalyzer
        analyzer = MarketAnalyzer(enhanced_db)
        suitability = analyzer.get_profile_suitability(model_id)

        # Get all profiles with their suitability scores
        all_profiles = enhanced_db.get_all_risk_profiles()

        profiles_with_scores = []
        for profile in all_profiles:
            if profile['name'] in suitability:
                profiles_with_scores.append({
                    'id': profile['id'],
                    'name': profile['name'],
                    'icon': profile['icon'],
                    'description': profile['description'],
                    'suitability_score': suitability[profile['name']],
                    'suitability_label': _get_suitability_label(suitability[profile['name']])
                })

        # Sort by suitability score
        profiles_with_scores.sort(key=lambda x: x['suitability_score'], reverse=True)

        return jsonify({
            'success': True,
            'profiles': profiles_with_scores
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Readiness Assessment Routes ====================

@risk_bp.route('/models/<int:model_id>/readiness', methods=['GET'])
def get_readiness_assessment(model_id):
    """Get readiness assessment for switching to full auto"""
    try:
        # Get recent trades
        trades = enhanced_db.get_trades(model_id, limit=50)

        if len(trades) < 10:
            return jsonify({
                'ready': False,
                'score': 0,
                'message': 'Need at least 10 trades for assessment',
                'metrics': {}
            })

        # Calculate metrics
        wins = sum(1 for t in trades if t['pnl'] > 0)
        total = len(trades)
        win_rate = (wins / total * 100) if total > 0 else 0

        # Get approval data (for semi-auto)
        conn = enhanced_db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN approved = 1 THEN 1 ELSE 0 END) as approved,
                   SUM(CASE WHEN modified = 1 THEN 1 ELSE 0 END) as modified
            FROM approval_events
            WHERE model_id = ?
        ''', (model_id,))
        approval_data = dict(cursor.fetchone())
        conn.close()

        approval_rate = (approval_data['approved'] / approval_data['total'] * 100) if approval_data['total'] > 0 else 0
        modification_rate = (approval_data['modified'] / approval_data['total'] * 100) if approval_data['total'] > 0 else 0

        # Get risk violations
        cursor = conn = enhanced_db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM incidents
            WHERE model_id = ? AND incident_type = 'TRADE_REJECTED'
        ''', (model_id,))
        risk_violations = dict(cursor.fetchone())['count']
        conn.close()

        # Calculate returns
        model = enhanced_db.get_model(model_id)
        prices_data = market_fetcher.get_current_prices(['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE'])
        portfolio = enhanced_db.get_portfolio(model_id, prices_data)
        total_return = ((portfolio['total_value'] - model['initial_capital']) / model['initial_capital'] * 100)

        # Calculate return volatility (std dev of returns)
        returns = [t['pnl'] / model['initial_capital'] * 100 for t in trades[:20]]
        if len(returns) > 1:
            mean_return = sum(returns) / len(returns)
            variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
            return_volatility = variance ** 0.5
        else:
            return_volatility = 0

        # Scoring criteria
        score = 0
        max_score = 100

        # 1. Win rate (30 points)
        if win_rate >= 55:
            score += 30
        elif win_rate >= 50:
            score += 20
        elif win_rate >= 45:
            score += 10

        # 2. Approval rate (20 points)
        if approval_rate >= 90:
            score += 20
        elif approval_rate >= 80:
            score += 15
        elif approval_rate >= 70:
            score += 10

        # 3. Modification rate (lower is better, 15 points)
        if modification_rate <= 5:
            score += 15
        elif modification_rate <= 10:
            score += 10
        elif modification_rate <= 20:
            score += 5

        # 4. Risk violations (lower is better, 15 points)
        if risk_violations == 0:
            score += 15
        elif risk_violations <= 3:
            score += 10
        elif risk_violations <= 5:
            score += 5

        # 5. Total return (10 points)
        if total_return >= 5:
            score += 10
        elif total_return >= 2:
            score += 5
        elif total_return >= 0:
            score += 2

        # 6. Return volatility (lower is better, 10 points)
        if return_volatility <= 2:
            score += 10
        elif return_volatility <= 4:
            score += 5
        elif return_volatility <= 6:
            score += 2

        # Ready if score >= 70
        ready = score >= 70

        metrics = {
            'total_trades': total,
            'win_rate': win_rate,
            'approval_rate': approval_rate,
            'modification_rate': modification_rate,
            'risk_violations': risk_violations,
            'total_return': total_return,
            'return_volatility': return_volatility
        }

        # Generate recommendation
        if ready:
            message = "✅ Ready for Full Automation"
        elif score >= 50:
            message = "⚠️ Approaching Readiness - Continue monitoring"
        else:
            message = "❌ Not Ready - More learning needed"

        return jsonify({
            'ready': ready,
            'score': score,
            'max_score': max_score,
            'message': message,
            'metrics': metrics
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Incidents Log Routes ====================

@risk_bp.route('/models/<int:model_id>/incidents', methods=['GET'])
def get_model_incidents(model_id):
    """Get incidents log for a model"""
    try:
        limit = request.args.get('limit', 50, type=int)
        incidents = enhanced_db.get_recent_incidents(model_id=model_id, limit=limit)
        return jsonify(incidents)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@risk_bp.route('/incidents', methods=['GET'])
def get_all_incidents():
    """Get all incidents across all models"""
    try:
        limit = request.args.get('limit', 100, type=int)
        incidents = enhanced_db.get_recent_incidents(model_id=None, limit=limit)
        return jsonify(incidents)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

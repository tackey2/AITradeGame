"""
Risk Management API Blueprint
Handles all risk-related endpoints including profiles, status, and recommendations.
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import traceback
from routes import app_context
from market_analyzer import MarketAnalyzer
from risk_manager import RiskManager
from notifier import Notifier
from explainer import AIExplainer

risk_bp = Blueprint('risk', __name__)


# Helper function to initialize enhanced components for a model
def init_enhanced_components(model_id):
    """Initialize risk manager, notifier, explainer, and executor for a model"""
    enhanced_db = app_context['enhanced_db']
    risk_managers = app_context['risk_managers']
    notifiers = app_context['notifiers']
    explainers = app_context['explainers']

    if model_id not in risk_managers:
        risk_managers[model_id] = RiskManager(enhanced_db)

    if model_id not in notifiers:
        notifiers[model_id] = Notifier(enhanced_db)

    if model_id not in explainers:
        # Get model to access AI configuration
        model = enhanced_db.get_model(model_id)
        if model:
            explainers[model_id] = AIExplainer(
                enhanced_db,
                api_url=model.get('api_url'),
                api_key=model.get('api_key'),
                model_name=model.get('model_name')
            )


# -------- Risk Status --------

@risk_bp.route('/api/models/<int:model_id>/risk-status', methods=['GET'])
def get_risk_status(model_id):
    """Get current risk status for a model"""
    try:
        enhanced_db = app_context['enhanced_db']
        market_fetcher = app_context['market_fetcher']

        # Check if model exists first
        model = enhanced_db.get_model(model_id)
        if not model:
            return jsonify({'error': f'Model {model_id} not found'}), 404

        init_enhanced_components(model_id)

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
        error_trace = traceback.format_exc()
        print(f"[ERROR] Risk status endpoint failed for model {model_id}:")
        print(error_trace)
        return jsonify({'error': str(e), 'details': error_trace}), 500


# -------- Risk Profiles Management --------

@risk_bp.route('/api/risk-profiles', methods=['GET'])
def get_all_risk_profiles():
    """Get all risk profiles (system and custom)"""
    try:
        enhanced_db = app_context['enhanced_db']
        profiles = enhanced_db.get_all_risk_profiles()
        return jsonify(profiles)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@risk_bp.route('/api/risk-profiles/<int:profile_id>', methods=['GET'])
def get_risk_profile(profile_id):
    """Get a specific risk profile"""
    try:
        enhanced_db = app_context['enhanced_db']
        profile = enhanced_db.get_risk_profile(profile_id)
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        return jsonify(profile)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@risk_bp.route('/api/risk-profiles', methods=['POST'])
def create_custom_risk_profile():
    """Create a custom risk profile"""
    try:
        enhanced_db = app_context['enhanced_db']
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


@risk_bp.route('/api/risk-profiles/<int:profile_id>', methods=['PUT'])
def update_risk_profile(profile_id):
    """Update a custom risk profile"""
    try:
        enhanced_db = app_context['enhanced_db']
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


@risk_bp.route('/api/risk-profiles/<int:profile_id>', methods=['DELETE'])
def delete_risk_profile(profile_id):
    """Delete a custom risk profile"""
    try:
        enhanced_db = app_context['enhanced_db']
        enhanced_db.delete_risk_profile(profile_id)
        return jsonify({
            'success': True,
            'message': 'Profile deleted successfully'
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@risk_bp.route('/api/models/<int:model_id>/apply-profile', methods=['POST'])
def apply_risk_profile(model_id):
    """Apply a risk profile to a model"""
    try:
        enhanced_db = app_context['enhanced_db']
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


@risk_bp.route('/api/models/<int:model_id>/active-profile', methods=['GET'])
def get_active_profile(model_id):
    """Get the active risk profile for a model"""
    try:
        enhanced_db = app_context['enhanced_db']
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


@risk_bp.route('/api/risk-profiles/<int:profile_id>/performance', methods=['GET'])
def get_profile_performance(profile_id):
    """Get performance metrics for a risk profile"""
    try:
        enhanced_db = app_context['enhanced_db']
        performance = enhanced_db.get_profile_performance(profile_id)
        return jsonify(performance)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@risk_bp.route('/api/models/<int:model_id>/profile-history', methods=['GET'])
def get_model_profile_history(model_id):
    """Get profile usage history for a model"""
    try:
        enhanced_db = app_context['enhanced_db']
        limit = request.args.get('limit', 10, type=int)
        history = enhanced_db.get_model_profile_history(model_id, limit)
        return jsonify(history)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@risk_bp.route('/api/risk-profiles/compare', methods=['POST'])
def compare_risk_profiles():
    """Compare multiple risk profiles"""
    try:
        enhanced_db = app_context['enhanced_db']
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


def _calculate_risk_score(profile):
    """Calculate a risk score (0-100) for a profile"""
    score = 0
    score += profile['max_position_size_pct'] * 2  # Weight: 2
    score += profile['max_open_positions'] * 3  # Weight: 3
    score += (100 - profile['min_cash_reserve_pct']) * 0.5  # Weight: 0.5
    score += profile['max_daily_loss_pct'] * 5  # Weight: 5
    score += profile['max_drawdown_pct'] * 2  # Weight: 2
    return min(100, score)


# -------- Profile Recommendations (Phase 3) --------

@risk_bp.route('/api/models/<int:model_id>/recommend-profile', methods=['GET'])
def recommend_profile(model_id):
    """
    Analyze current performance and recommend optimal risk profile
    Uses existing trade data - no external APIs required
    """
    try:
        enhanced_db = app_context['enhanced_db']
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


@risk_bp.route('/api/models/<int:model_id>/market-metrics', methods=['GET'])
def get_market_metrics(model_id):
    """Get detailed market condition metrics"""
    try:
        enhanced_db = app_context['enhanced_db']
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


@risk_bp.route('/api/models/<int:model_id>/profile-suitability', methods=['GET'])
def get_profile_suitability(model_id):
    """Get suitability scores for all profiles"""
    try:
        enhanced_db = app_context['enhanced_db']
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

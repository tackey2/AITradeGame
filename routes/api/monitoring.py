"""
Monitoring and Emergency Controls API Blueprint
Handles incidents logging, emergency controls (pause/stop), and enhanced trading execution.
"""
from flask import Blueprint, request, jsonify
from routes import app_context
from ai_trader import AITrader
from risk_manager import RiskManager
from notifier import Notifier
from explainer import AIExplainer
from trading_modes import TradingExecutor

monitoring_bp = Blueprint('monitoring', __name__)


# ============ Helper Functions ============

def init_enhanced_components(model_id):
    """Initialize risk manager, notifier, explainer, and executor for a model"""
    enhanced_db = app_context['enhanced_db']
    risk_managers = app_context['risk_managers']
    notifiers = app_context['notifiers']
    explainers = app_context['explainers']
    trading_executors = app_context['trading_executors']

    if model_id not in risk_managers:
        risk_managers[model_id] = RiskManager(enhanced_db)

    if model_id not in notifiers:
        notifiers[model_id] = Notifier(enhanced_db)

    if model_id not in explainers:
        # Get model to access AI configuration
        model = enhanced_db.get_model(model_id)
        provider = enhanced_db.get_provider(model['provider_id'])

        ai_trader = AITrader(
            api_key=provider['api_key'],
            api_url=provider['api_url'],
            model_name=model['model_name']
        )
        explainers[model_id] = AIExplainer(ai_trader)

    if model_id not in trading_executors:
        # Create executor with all components
        trading_executors[model_id] = TradingExecutor(
            db=enhanced_db,
            risk_manager=risk_managers[model_id],
            notifier=notifiers[model_id],
            explainer=explainers[model_id]
        )


# ============ Incidents Log Endpoints ============

@monitoring_bp.route('/api/models/<int:model_id>/incidents', methods=['GET'])
def get_model_incidents(model_id):
    """Get incidents log for a model"""
    enhanced_db = app_context['enhanced_db']

    try:
        limit = request.args.get('limit', 50, type=int)
        incidents = enhanced_db.get_recent_incidents(model_id=model_id, limit=limit)
        return jsonify(incidents)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/api/incidents', methods=['GET'])
def get_all_incidents():
    """Get all incidents across all models"""
    enhanced_db = app_context['enhanced_db']

    try:
        limit = request.args.get('limit', 100, type=int)
        incidents = enhanced_db.get_recent_incidents(model_id=None, limit=limit)
        return jsonify(incidents)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ Emergency Controls Endpoints ============

@monitoring_bp.route('/api/models/<int:model_id>/pause', methods=['POST'])
def pause_model(model_id):
    """Emergency pause - switch to semi-auto mode"""
    enhanced_db = app_context['enhanced_db']

    try:
        data = request.json or {}
        reason = data.get('reason', 'User-initiated emergency pause')

        # Get current mode
        current_mode = enhanced_db.get_model_mode(model_id)

        if current_mode == 'fully_automated':
            # Switch to semi-auto
            enhanced_db.set_model_mode(model_id, 'semi_automated')

            # Log incident
            enhanced_db.log_incident(
                model_id=model_id,
                incident_type='EMERGENCY_PAUSE',
                severity='high',
                message=reason
            )

            return jsonify({
                'success': True,
                'previous_mode': current_mode,
                'new_mode': 'semi_automated',
                'message': 'Model paused successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Model is already in {current_mode} mode'
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/api/emergency-stop-all', methods=['POST'])
def emergency_stop_all():
    """Emergency stop ALL models - switch all to simulation"""
    enhanced_db = app_context['enhanced_db']

    try:
        data = request.json or {}
        reason = data.get('reason', 'User-initiated emergency stop for all models')

        models = enhanced_db.get_all_models()
        switched = []

        for model in models:
            model_id = model['id']
            current_mode = enhanced_db.get_model_mode(model_id)

            if current_mode != 'simulation':
                enhanced_db.set_model_mode(model_id, 'simulation')

                enhanced_db.log_incident(
                    model_id=model_id,
                    incident_type='EMERGENCY_STOP_ALL',
                    severity='critical',
                    message=reason
                )

                switched.append({
                    'model_id': model_id,
                    'model_name': model['name'],
                    'previous_mode': current_mode
                })

        return jsonify({
            'success': True,
            'switched_count': len(switched),
            'switched_models': switched,
            'message': f'All {len(switched)} models switched to simulation mode'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ Enhanced Trading Execution Endpoints ============

@monitoring_bp.route('/api/models/<int:model_id>/execute-enhanced', methods=['POST'])
def execute_enhanced_trading(model_id):
    """Execute trading cycle with enhanced system (mode-aware)"""
    enhanced_db = app_context['enhanced_db']
    market_fetcher = app_context['market_fetcher']
    trading_executors = app_context['trading_executors']

    try:
        # Initialize components
        init_enhanced_components(model_id)

        # Get market data
        coins = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE']
        market_data = market_fetcher.get_current_prices(coins)

        # Get AI decisions
        model = enhanced_db.get_model(model_id)
        provider = enhanced_db.get_provider(model['provider_id'])

        ai_trader = AITrader(
            api_key=provider['api_key'],
            api_url=provider['api_url'],
            model_name=model['model_name']
        )

        # Get portfolio and account info
        portfolio = enhanced_db.get_portfolio(model_id, market_data)
        account_info = {
            'initial_capital': model['initial_capital'],
            'total_return': ((portfolio['total_value'] - model['initial_capital']) / model['initial_capital'] * 100)
        }

        # Get AI decisions
        ai_decisions = ai_trader.make_decision(market_data, portfolio, account_info)

        # Execute with trading executor (mode-aware)
        result = trading_executors[model_id].execute_trading_cycle(
            model_id=model_id,
            market_data=market_data,
            ai_decisions=ai_decisions
        )

        return jsonify({
            'success': True,
            'result': result
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

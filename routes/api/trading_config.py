"""
Trading Configuration API Blueprint
Handles trading mode, environment, automation, exchange credentials, and pending decisions.
"""
from flask import Blueprint, request, jsonify
import json
from routes import app_context

# Import required components for initialization
from risk_manager import RiskManager
from notifier import Notifier
from explainer import AIExplainer
from trading_modes import TradingExecutor
from ai_trader import AITrader

trading_config_bp = Blueprint('trading_config', __name__)


# -------- Helper Functions --------

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


# -------- Trading Mode Management --------

@trading_config_bp.route('/api/models/<int:model_id>/mode', methods=['GET'])
def get_trading_mode(model_id):
    """Get current trading mode for a model"""
    try:
        enhanced_db = app_context['enhanced_db']
        mode = enhanced_db.get_model_mode(model_id)
        return jsonify({'mode': mode})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_config_bp.route('/api/models/<int:model_id>/mode', methods=['POST'])
def set_trading_mode(model_id):
    """Set trading mode for a model"""
    try:
        enhanced_db = app_context['enhanced_db']
        data = request.json
        mode = data.get('mode')

        if mode not in ['simulation', 'semi_automated', 'fully_automated']:
            return jsonify({'error': 'Invalid mode'}), 400

        enhanced_db.set_model_mode(model_id, mode)

        # Log incident
        enhanced_db.log_incident(
            model_id=model_id,
            incident_type='MODE_CHANGE',
            severity='low',
            message=f'Trading mode changed to {mode}'
        )

        return jsonify({'success': True, 'mode': mode})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# -------- Environment & Automation Management (NEW ARCHITECTURE) --------

@trading_config_bp.route('/api/models/<int:model_id>/environment', methods=['GET'])
def get_trading_environment(model_id):
    """Get trading environment (simulation or live)"""
    try:
        enhanced_db = app_context['enhanced_db']
        environment = enhanced_db.get_trading_environment(model_id)
        return jsonify({'environment': environment})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_config_bp.route('/api/models/<int:model_id>/environment', methods=['POST'])
def set_trading_environment(model_id):
    """Set trading environment (simulation or live)"""
    try:
        enhanced_db = app_context['enhanced_db']
        data = request.json
        environment = data.get('environment')

        if environment not in ['simulation', 'live']:
            return jsonify({'error': 'Invalid environment. Must be "simulation" or "live"'}), 400

        enhanced_db.set_trading_environment(model_id, environment)

        return jsonify({
            'success': True,
            'environment': environment
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_config_bp.route('/api/models/<int:model_id>/automation', methods=['GET'])
def get_automation_level(model_id):
    """Get automation level (manual, semi_automated, fully_automated)"""
    try:
        enhanced_db = app_context['enhanced_db']
        automation = enhanced_db.get_automation_level(model_id)
        return jsonify({'automation': automation})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_config_bp.route('/api/models/<int:model_id>/automation', methods=['POST'])
def set_automation_level(model_id):
    """Set automation level (manual, semi_automated, fully_automated)"""
    try:
        enhanced_db = app_context['enhanced_db']
        data = request.json
        automation = data.get('automation')

        if automation not in ['manual', 'semi_automated', 'fully_automated']:
            return jsonify({'error': 'Invalid automation level'}), 400

        enhanced_db.set_automation_level(model_id, automation)

        return jsonify({
            'success': True,
            'automation': automation
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# -------- Model Settings Management --------

@trading_config_bp.route('/api/models/<int:model_id>/config', methods=['GET'])
def get_model_config(model_id):
    """Get complete model configuration (environment + automation + exchange)"""
    try:
        enhanced_db = app_context['enhanced_db']
        config = {
            'environment': enhanced_db.get_trading_environment(model_id),
            'automation': enhanced_db.get_automation_level(model_id),
            'exchange_environment': enhanced_db.get_exchange_environment(model_id)
        }
        return jsonify(config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_config_bp.route('/api/models/<int:model_id>/settings', methods=['GET'])
def get_model_settings(model_id):
    """Get all settings for a model"""
    try:
        enhanced_db = app_context['enhanced_db']
        settings = enhanced_db.get_model_settings(model_id)
        return jsonify(settings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_config_bp.route('/api/models/<int:model_id>/settings', methods=['POST'])
def update_model_settings(model_id):
    """Update model settings"""
    try:
        enhanced_db = app_context['enhanced_db']
        data = request.json

        # Initialize settings if not exists
        enhanced_db.init_model_settings(model_id)

        # Update settings
        enhanced_db.update_model_settings(model_id, data)

        # Log changes
        for key, value in data.items():
            enhanced_db.conn = enhanced_db.get_connection()
            cursor = enhanced_db.conn.cursor()
            cursor.execute('''
                INSERT INTO setting_changes (model_id, setting_key, new_value)
                VALUES (?, ?, ?)
            ''', (model_id, key, str(value)))
            enhanced_db.conn.commit()
            enhanced_db.conn.close()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# -------- Exchange Credentials Management --------

@trading_config_bp.route('/api/models/<int:model_id>/exchange/credentials', methods=['GET'])
def get_exchange_credentials(model_id):
    """Get exchange credentials status (without exposing secrets)"""
    try:
        enhanced_db = app_context['enhanced_db']
        credentials = enhanced_db.get_exchange_credentials(model_id)

        if not credentials:
            return jsonify({
                'configured': False,
                'has_mainnet': False,
                'has_testnet': False
            })

        # Return status without exposing API secrets
        return jsonify({
            'configured': True,
            'has_mainnet': bool(credentials.get('api_key')),
            'has_testnet': bool(credentials.get('testnet_api_key')),
            'exchange_type': credentials.get('exchange_type', 'binance'),
            'last_validated': credentials.get('last_validated'),
            'is_active': credentials.get('is_active', True)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_config_bp.route('/api/models/<int:model_id>/exchange/credentials', methods=['POST'])
def set_exchange_credentials(model_id):
    """Set exchange credentials for a model"""
    try:
        enhanced_db = app_context['enhanced_db']
        data = request.json

        api_key = data.get('api_key')
        api_secret = data.get('api_secret')
        testnet_api_key = data.get('testnet_api_key')
        testnet_api_secret = data.get('testnet_api_secret')
        exchange_type = data.get('exchange_type', 'binance')

        if not api_key or not api_secret:
            return jsonify({'error': 'API key and secret are required'}), 400

        # Store credentials
        enhanced_db.set_exchange_credentials(
            model_id=model_id,
            api_key=api_key,
            api_secret=api_secret,
            testnet_api_key=testnet_api_key,
            testnet_api_secret=testnet_api_secret,
            exchange_type=exchange_type
        )

        return jsonify({
            'success': True,
            'message': 'Exchange credentials saved successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_config_bp.route('/api/models/<int:model_id>/exchange/credentials', methods=['DELETE'])
def delete_exchange_credentials(model_id):
    """Delete exchange credentials for a model"""
    try:
        enhanced_db = app_context['enhanced_db']
        enhanced_db.delete_exchange_credentials(model_id)

        return jsonify({
            'success': True,
            'message': 'Exchange credentials deleted'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_config_bp.route('/api/models/<int:model_id>/exchange/validate', methods=['POST'])
def validate_exchange_credentials(model_id):
    """Validate exchange credentials by testing connection"""
    try:
        enhanced_db = app_context['enhanced_db']
        is_valid = enhanced_db.validate_exchange_credentials(model_id)

        return jsonify({
            'valid': is_valid,
            'message': 'Credentials are valid' if is_valid else 'Credentials validation failed'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_config_bp.route('/api/models/<int:model_id>/exchange/environment', methods=['GET'])
def get_exchange_environment(model_id):
    """Get exchange environment (testnet or mainnet)"""
    try:
        enhanced_db = app_context['enhanced_db']
        exchange_env = enhanced_db.get_exchange_environment(model_id)
        return jsonify({'exchange_environment': exchange_env})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_config_bp.route('/api/models/<int:model_id>/exchange/environment', methods=['POST'])
def set_exchange_environment(model_id):
    """Set exchange environment (testnet or mainnet)"""
    try:
        enhanced_db = app_context['enhanced_db']
        data = request.json
        exchange_env = data.get('exchange_environment')

        if exchange_env not in ['testnet', 'mainnet']:
            return jsonify({'error': 'Invalid exchange environment. Must be "testnet" or "mainnet"'}), 400

        enhanced_db.set_exchange_environment(model_id, exchange_env)

        return jsonify({
            'success': True,
            'exchange_environment': exchange_env
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# -------- Pending Decisions (Semi-Auto Workflow) --------

@trading_config_bp.route('/api/pending-decisions', methods=['GET'])
def get_all_pending_decisions():
    """Get all pending decisions across all models"""
    try:
        enhanced_db = app_context['enhanced_db']
        model_id = request.args.get('model_id', type=int)

        if model_id:
            decisions = enhanced_db.get_pending_decisions(model_id, status='pending')
        else:
            # Get all pending decisions
            conn = enhanced_db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM pending_decisions
                WHERE status = 'pending'
                ORDER BY created_at DESC
            ''')
            rows = cursor.fetchall()
            conn.close()

            decisions = []
            for row in rows:
                data = dict(row)
                data['decision_data'] = json.loads(data['decision_data'])
                if data['explanation_data']:
                    data['explanation_data'] = json.loads(data['explanation_data'])
                decisions.append(data)

        return jsonify(decisions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_config_bp.route('/api/decision-history', methods=['GET'])
def get_decision_history():
    """Get decision history with filtering options"""
    try:
        enhanced_db = app_context['enhanced_db']
        model_id = request.args.get('model_id', type=int)
        status_filter = request.args.get('status', None)  # 'pending', 'approved', 'rejected', 'expired', or None for all
        limit = request.args.get('limit', 100, type=int)

        conn = enhanced_db.get_connection()
        cursor = conn.cursor()

        # Build query with filters
        query = 'SELECT * FROM pending_decisions WHERE 1=1'
        params = []

        if model_id:
            query += ' AND model_id = ?'
            params.append(model_id)

        if status_filter:
            query += ' AND status = ?'
            params.append(status_filter)

        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        decisions = []
        for row in rows:
            data = dict(row)
            data['decision_data'] = json.loads(data['decision_data'])
            if data['explanation_data']:
                data['explanation_data'] = json.loads(data['explanation_data'])
            decisions.append(data)

        return jsonify(decisions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_config_bp.route('/api/pending-decisions/<int:decision_id>/approve', methods=['POST'])
def approve_pending_decision(decision_id):
    """Approve a pending decision"""
    try:
        enhanced_db = app_context['enhanced_db']
        trading_executors = app_context['trading_executors']

        data = request.json or {}
        modified = data.get('modified', False)
        modifications = data.get('modifications', None)

        # Initialize components if needed
        decisions = enhanced_db.get_pending_decisions(model_id=None, status='pending')
        decision = next((d for d in decisions if d['id'] == decision_id), None)

        if not decision:
            return jsonify({'error': 'Decision not found'}), 404

        model_id = decision['model_id']
        init_enhanced_components(model_id)

        # Execute approval
        result = trading_executors[model_id].approve_decision(
            decision_id=decision_id,
            modified=modified,
            modifications=modifications
        )

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trading_config_bp.route('/api/pending-decisions/<int:decision_id>/reject', methods=['POST'])
def reject_pending_decision(decision_id):
    """Reject a pending decision"""
    try:
        enhanced_db = app_context['enhanced_db']
        trading_executors = app_context['trading_executors']

        data = request.json or {}
        reason = data.get('reason', 'User rejected')

        # Initialize components if needed
        decisions = enhanced_db.get_pending_decisions(model_id=None, status='pending')
        decision = next((d for d in decisions if d['id'] == decision_id), None)

        if not decision:
            return jsonify({'error': 'Decision not found'}), 404

        model_id = decision['model_id']
        init_enhanced_components(model_id)

        # Execute rejection
        result = trading_executors[model_id].reject_decision(
            decision_id=decision_id,
            reason=reason
        )

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

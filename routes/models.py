from flask import Blueprint, request, jsonify
from ai_trader import AITrader
from trading_engine import TradingEngine

models_bp = Blueprint('models', __name__, url_prefix='/api/models')

# Global variables to store injected dependencies
db = None
enhanced_db = None
market_fetcher = None
trading_engines = None
TRADE_FEE_RATE = None


def init_app(database, enhanced_database, market_fetcher_instance, trading_engines_dict, trade_fee_rate):
    """Initialize the blueprint with shared resources"""
    global db, enhanced_db, market_fetcher, trading_engines, TRADE_FEE_RATE
    db = database
    enhanced_db = enhanced_database
    market_fetcher = market_fetcher_instance
    trading_engines = trading_engines_dict
    TRADE_FEE_RATE = trade_fee_rate


# -------- Models Management --------

@models_bp.route('', methods=['GET'])
def get_models():
    models = db.get_all_models()
    return jsonify(models)


@models_bp.route('', methods=['POST'])
def add_model():
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


@models_bp.route('/<int:model_id>', methods=['PUT'])
def update_model(model_id):
    """Update model information"""
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


@models_bp.route('/<int:model_id>', methods=['DELETE'])
def delete_model(model_id):
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


# -------- Trading Mode Management --------

@models_bp.route('/<int:model_id>/mode', methods=['GET'])
def get_trading_mode(model_id):
    """Get current trading mode for a model"""
    try:
        mode = enhanced_db.get_model_mode(model_id)
        return jsonify({'mode': mode})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@models_bp.route('/<int:model_id>/mode', methods=['POST'])
def set_trading_mode(model_id):
    """Set trading mode for a model"""
    try:
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


# -------- Environment & Automation Management --------

@models_bp.route('/<int:model_id>/environment', methods=['GET'])
def get_trading_environment(model_id):
    """Get trading environment (simulation or live)"""
    try:
        environment = enhanced_db.get_trading_environment(model_id)
        return jsonify({'environment': environment})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@models_bp.route('/<int:model_id>/environment', methods=['POST'])
def set_trading_environment(model_id):
    """Set trading environment (simulation or live)"""
    try:
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


@models_bp.route('/<int:model_id>/automation', methods=['GET'])
def get_automation_level(model_id):
    """Get automation level (manual, semi_automated, fully_automated)"""
    try:
        automation = enhanced_db.get_automation_level(model_id)
        return jsonify({'automation': automation})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@models_bp.route('/<int:model_id>/automation', methods=['POST'])
def set_automation_level(model_id):
    """Set automation level (manual, semi_automated, fully_automated)"""
    try:
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


@models_bp.route('/<int:model_id>/config', methods=['GET'])
def get_model_config(model_id):
    """Get complete model configuration (environment + automation + exchange)"""
    try:
        config = {
            'environment': enhanced_db.get_trading_environment(model_id),
            'automation': enhanced_db.get_automation_level(model_id),
            'exchange_environment': enhanced_db.get_exchange_environment(model_id)
        }
        return jsonify(config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# -------- Model Settings Management --------

@models_bp.route('/<int:model_id>/settings', methods=['GET'])
def get_model_settings(model_id):
    """Get all settings for a model"""
    try:
        settings = enhanced_db.get_model_settings(model_id)
        return jsonify(settings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@models_bp.route('/<int:model_id>/settings', methods=['POST'])
def update_model_settings(model_id):
    """Update model settings"""
    try:
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

@models_bp.route('/<int:model_id>/exchange/credentials', methods=['GET'])
def get_exchange_credentials(model_id):
    """Get exchange credentials status (without exposing secrets)"""
    try:
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


@models_bp.route('/<int:model_id>/exchange/credentials', methods=['POST'])
def set_exchange_credentials(model_id):
    """Set exchange credentials for a model"""
    try:
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


@models_bp.route('/<int:model_id>/exchange/credentials', methods=['DELETE'])
def delete_exchange_credentials(model_id):
    """Delete exchange credentials for a model"""
    try:
        enhanced_db.delete_exchange_credentials(model_id)

        return jsonify({
            'success': True,
            'message': 'Exchange credentials deleted'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@models_bp.route('/<int:model_id>/exchange/validate', methods=['POST'])
def validate_exchange_credentials(model_id):
    """Validate exchange credentials by testing connection"""
    try:
        is_valid = enhanced_db.validate_exchange_credentials(model_id)

        return jsonify({
            'valid': is_valid,
            'message': 'Credentials are valid' if is_valid else 'Credentials validation failed'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@models_bp.route('/<int:model_id>/exchange/environment', methods=['GET'])
def get_exchange_environment(model_id):
    """Get exchange environment (testnet or mainnet)"""
    try:
        exchange_env = enhanced_db.get_exchange_environment(model_id)
        return jsonify({'exchange_environment': exchange_env})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@models_bp.route('/<int:model_id>/exchange/environment', methods=['POST'])
def set_exchange_environment(model_id):
    """Set exchange environment (testnet or mainnet)"""
    try:
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

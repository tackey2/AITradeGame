from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import time
import threading
import json
import re
from datetime import datetime
from trading_engine import TradingEngine
from market_data import MarketDataFetcher
from ai_trader import AITrader
from database import Database
from version import __version__, __github_owner__, __repo__, GITHUB_REPO_URL, LATEST_RELEASE_URL

# NEW - Enhanced system imports
from database_enhanced import EnhancedDatabase
from trading_modes import TradingExecutor
from risk_manager import RiskManager
from notifier import Notifier
from explainer import AIExplainer
from market_analyzer import MarketAnalyzer

app = Flask(__name__)
CORS(app)

# Initialize databases (keep both for backward compatibility)
db = Database('AITradeGame.db')
enhanced_db = EnhancedDatabase('AITradeGame.db')

# Initialize enhanced database schema
enhanced_db.init_db()

# Initialize system risk profiles
enhanced_db.init_system_risk_profiles()

# Market data fetcher
market_fetcher = MarketDataFetcher()

# Trading engines (original system)
trading_engines = {}

# NEW - Enhanced system components
risk_managers = {}  # model_id -> RiskManager
notifiers = {}  # model_id -> Notifier
explainers = {}  # model_id -> AIExplainer
trading_executors = {}  # model_id -> TradingExecutor

auto_trading = True
TRADE_FEE_RATE = 0.001  # 默认交易费率

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/enhanced')
def enhanced():
    return render_template('enhanced.html')

@app.route('/test_ui_debug.html')
def test_ui_debug():
    with open('test_ui_debug.html', 'r') as f:
        return f.read()

@app.route('/test-profiles')
def test_profiles():
    return render_template('test_profiles.html')

# ============ Provider API Endpoints ============

@app.route('/api/providers', methods=['GET'])
def get_providers():
    """Get all API providers"""
    providers = db.get_all_providers()
    return jsonify(providers)

@app.route('/api/providers', methods=['POST'])
def add_provider():
    """Add new API provider"""
    data = request.json
    try:
        provider_id = db.add_provider(
            name=data['name'],
            api_url=data['api_url'],
            api_key=data['api_key'],
            models=data.get('models', '')
        )
        return jsonify({'id': provider_id, 'message': 'Provider added successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/providers/<int:provider_id>', methods=['PUT'])
def update_provider(provider_id):
    """Update API provider"""
    data = request.json
    try:
        db.update_provider(
            provider_id=provider_id,
            name=data['name'],
            api_url=data['api_url'],
            api_key=data['api_key'],
            models=data.get('models', '')
        )
        return jsonify({'message': 'Provider updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/providers/<int:provider_id>', methods=['DELETE'])
def delete_provider(provider_id):
    """Delete API provider"""
    try:
        db.delete_provider(provider_id)
        return jsonify({'message': 'Provider deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/providers/models', methods=['POST'])
def fetch_provider_models():
    """Fetch available models from provider's API"""
    data = request.json
    api_url = data.get('api_url')
    api_key = data.get('api_key')

    if not api_url or not api_key:
        return jsonify({'error': 'API URL and key are required'}), 400

    try:
        import requests
        models = []

        # Try to detect provider type and call appropriate API
        if 'openai.com' in api_url.lower():
            # OpenAI API call
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            response = requests.get(f'{api_url}/models', headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                models = [m['id'] for m in result.get('data', []) if 'gpt' in m['id'].lower()]
        elif 'deepseek' in api_url.lower():
            # DeepSeek API
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            response = requests.get(f'{api_url}/models', headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                models = [m['id'] for m in result.get('data', [])]
        elif 'openrouter.ai' in api_url.lower():
            # OpenRouter API - fetch available models
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            response = requests.get('https://openrouter.ai/api/v1/models', headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                models = [m['id'] for m in result.get('data', [])]
        else:
            # Generic OpenAI-compatible API
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            # Try standard /models endpoint
            try:
                response = requests.get(f'{api_url}/models', headers=headers, timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    if 'data' in result:
                        models = [m['id'] for m in result.get('data', [])]
                    else:
                        # Fallback to common model names
                        models = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo']
                else:
                    # Fallback to common model names
                    models = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo']
            except:
                # Fallback to common model names
                models = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo']

        return jsonify({'models': models})
    except Exception as e:
        print(f"[ERROR] Fetch models failed: {e}")
        return jsonify({'error': f'Failed to fetch models: {str(e)}'}), 500

# ============ Model API Endpoints ============

@app.route('/api/models', methods=['GET'])
def get_models():
    models = db.get_all_models()
    return jsonify(models)

@app.route('/api/models', methods=['POST'])
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

@app.route('/api/models/<int:model_id>', methods=['PUT'])
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

@app.route('/api/models/<int:model_id>', methods=['DELETE'])
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

@app.route('/api/models/<int:model_id>/portfolio', methods=['GET'])
def get_portfolio(model_id):
    prices_data = market_fetcher.get_current_prices(['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE'])
    current_prices = {coin: prices_data[coin]['price'] for coin in prices_data}
    
    portfolio = db.get_portfolio(model_id, current_prices)
    account_value = db.get_account_value_history(model_id, limit=100)
    
    return jsonify({
        'portfolio': portfolio,
        'account_value_history': account_value
    })

@app.route('/api/models/<int:model_id>/trades', methods=['GET'])
def get_trades(model_id):
    limit = request.args.get('limit', 50, type=int)
    trades = db.get_trades(model_id, limit=limit)
    return jsonify(trades)

@app.route('/api/models/<int:model_id>/conversations', methods=['GET'])
def get_conversations(model_id):
    limit = request.args.get('limit', 20, type=int)
    conversations = db.get_conversations(model_id, limit=limit)
    return jsonify(conversations)

@app.route('/api/aggregated/portfolio', methods=['GET'])
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

@app.route('/api/models/chart-data', methods=['GET'])
def get_models_chart_data():
    """Get chart data for all models"""
    limit = request.args.get('limit', 100, type=int)
    chart_data = db.get_multi_model_chart_data(limit=limit)
    return jsonify(chart_data)

@app.route('/api/market/prices', methods=['GET'])
def get_market_prices():
    coins = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE']
    prices = market_fetcher.get_current_prices(coins)
    return jsonify(prices)

@app.route('/api/models/<int:model_id>/execute', methods=['POST'])
def execute_trading(model_id):
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

def trading_loop():
    print("[INFO] Trading loop started")
    
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
                                msg = exec_result.get('message', '')
                                if signal != 'hold':
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

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
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

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get system settings"""
    try:
        settings = db.get_settings()
        return jsonify(settings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['PUT'])
def update_settings():
    """Update system settings"""
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

@app.route('/api/version', methods=['GET'])
def get_version():
    """Get current version information"""
    return jsonify({
        'current_version': __version__,
        'github_repo': GITHUB_REPO_URL,
        'latest_release_url': LATEST_RELEASE_URL
    })

@app.route('/api/check-update', methods=['GET'])
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

# ============ ENHANCED SYSTEM API ENDPOINTS ============

# Helper function to initialize enhanced components for a model
def init_enhanced_components(model_id):
    """Initialize risk manager, notifier, explainer, and executor for a model"""
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

@app.route('/api/models/<int:model_id>/mode', methods=['GET'])
def get_trading_mode(model_id):
    """Get current trading mode for a model"""
    try:
        mode = enhanced_db.get_model_mode(model_id)
        return jsonify({'mode': mode})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models/<int:model_id>/mode', methods=['POST'])
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

# -------- Environment & Automation Management (NEW ARCHITECTURE) --------

@app.route('/api/models/<int:model_id>/environment', methods=['GET'])
def get_trading_environment(model_id):
    """Get trading environment (simulation or live)"""
    try:
        environment = enhanced_db.get_trading_environment(model_id)
        return jsonify({'environment': environment})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models/<int:model_id>/environment', methods=['POST'])
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

@app.route('/api/models/<int:model_id>/automation', methods=['GET'])
def get_automation_level(model_id):
    """Get automation level (manual, semi_automated, fully_automated)"""
    try:
        automation = enhanced_db.get_automation_level(model_id)
        return jsonify({'automation': automation})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models/<int:model_id>/automation', methods=['POST'])
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

@app.route('/api/models/<int:model_id>/config', methods=['GET'])
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

@app.route('/api/models/<int:model_id>/settings', methods=['GET'])
def get_model_settings(model_id):
    """Get all settings for a model"""
    try:
        settings = enhanced_db.get_model_settings(model_id)
        return jsonify(settings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models/<int:model_id>/settings', methods=['POST'])
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

@app.route('/api/models/<int:model_id>/exchange/credentials', methods=['GET'])
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

@app.route('/api/models/<int:model_id>/exchange/credentials', methods=['POST'])
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

@app.route('/api/models/<int:model_id>/exchange/credentials', methods=['DELETE'])
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

@app.route('/api/models/<int:model_id>/exchange/validate', methods=['POST'])
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

@app.route('/api/models/<int:model_id>/exchange/environment', methods=['GET'])
def get_exchange_environment(model_id):
    """Get exchange environment (testnet or mainnet)"""
    try:
        exchange_env = enhanced_db.get_exchange_environment(model_id)
        return jsonify({'exchange_environment': exchange_env})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models/<int:model_id>/exchange/environment', methods=['POST'])
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

# -------- Pending Decisions (Semi-Auto Workflow) --------

@app.route('/api/pending-decisions', methods=['GET'])
def get_all_pending_decisions():
    """Get all pending decisions across all models"""
    try:
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

@app.route('/api/pending-decisions/<int:decision_id>/approve', methods=['POST'])
def approve_pending_decision(decision_id):
    """Approve a pending decision"""
    try:
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

@app.route('/api/pending-decisions/<int:decision_id>/reject', methods=['POST'])
def reject_pending_decision(decision_id):
    """Reject a pending decision"""
    try:
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

# -------- Risk Status --------

@app.route('/api/models/<int:model_id>/risk-status', methods=['GET'])
def get_risk_status(model_id):
    """Get current risk status for a model"""
    try:
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
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] Risk status endpoint failed for model {model_id}:")
        print(error_trace)
        return jsonify({'error': str(e), 'details': error_trace}), 500

# -------- Risk Profiles Management --------

@app.route('/api/risk-profiles', methods=['GET'])
def get_all_risk_profiles():
    """Get all risk profiles (system and custom)"""
    try:
        profiles = enhanced_db.get_all_risk_profiles()
        return jsonify(profiles)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/risk-profiles/<int:profile_id>', methods=['GET'])
def get_risk_profile(profile_id):
    """Get a specific risk profile"""
    try:
        profile = enhanced_db.get_risk_profile(profile_id)
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        return jsonify(profile)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/risk-profiles', methods=['POST'])
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

@app.route('/api/risk-profiles/<int:profile_id>', methods=['PUT'])
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

@app.route('/api/risk-profiles/<int:profile_id>', methods=['DELETE'])
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

@app.route('/api/models/<int:model_id>/apply-profile', methods=['POST'])
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

@app.route('/api/models/<int:model_id>/active-profile', methods=['GET'])
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

@app.route('/api/risk-profiles/<int:profile_id>/performance', methods=['GET'])
def get_profile_performance(profile_id):
    """Get performance metrics for a risk profile"""
    try:
        performance = enhanced_db.get_profile_performance(profile_id)
        return jsonify(performance)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models/<int:model_id>/profile-history', methods=['GET'])
def get_model_profile_history(model_id):
    """Get profile usage history for a model"""
    try:
        limit = request.args.get('limit', 10, type=int)
        history = enhanced_db.get_model_profile_history(model_id, limit)
        return jsonify(history)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/risk-profiles/compare', methods=['POST'])
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

@app.route('/api/models/<int:model_id>/recommend-profile', methods=['GET'])
def recommend_profile(model_id):
    """
    Analyze current performance and recommend optimal risk profile
    Uses existing trade data - no external APIs required
    """
    try:
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

@app.route('/api/models/<int:model_id>/market-metrics', methods=['GET'])
def get_market_metrics(model_id):
    """Get detailed market condition metrics"""
    try:
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

@app.route('/api/models/<int:model_id>/profile-suitability', methods=['GET'])
def get_profile_suitability(model_id):
    """Get suitability scores for all profiles"""
    try:
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

# -------- Readiness Assessment --------

@app.route('/api/models/<int:model_id>/readiness', methods=['GET'])
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

# -------- Incidents Log --------

@app.route('/api/models/<int:model_id>/incidents', methods=['GET'])
def get_model_incidents(model_id):
    """Get incidents log for a model"""
    try:
        limit = request.args.get('limit', 50, type=int)
        incidents = enhanced_db.get_recent_incidents(model_id=model_id, limit=limit)
        return jsonify(incidents)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/incidents', methods=['GET'])
def get_all_incidents():
    """Get all incidents across all models"""
    try:
        limit = request.args.get('limit', 100, type=int)
        incidents = enhanced_db.get_recent_incidents(model_id=None, limit=limit)
        return jsonify(incidents)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# -------- Emergency Controls --------

@app.route('/api/models/<int:model_id>/pause', methods=['POST'])
def pause_model(model_id):
    """Emergency pause - switch to semi-auto mode"""
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

@app.route('/api/emergency-stop-all', methods=['POST'])
def emergency_stop_all():
    """Emergency stop ALL models - switch all to simulation"""
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

# -------- Enhanced Trading Execution --------

@app.route('/api/models/<int:model_id>/execute-enhanced', methods=['POST'])
def execute_enhanced_trading(model_id):
    """Execute trading cycle with enhanced system (mode-aware)"""
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

def init_trading_engines():
    try:
        models = db.get_all_models()

        if not models:
            print("[WARN] No trading models found")
            return

        print(f"\n[INIT] Initializing trading engines...")
        for model in models:
            model_id = model['id']
            model_name = model['name']

            try:
                # Get provider info
                provider = db.get_provider(model['provider_id'])
                if not provider:
                    print(f"  [WARN] Model {model_id} ({model_name}): Provider not found")
                    continue

                trading_engines[model_id] = TradingEngine(
                    model_id=model_id,
                    db=db,
                    market_fetcher=market_fetcher,
                    ai_trader=AITrader(
                        api_key=provider['api_key'],
                        api_url=provider['api_url'],
                        model_name=model['model_name']
                    ),
                    trade_fee_rate=TRADE_FEE_RATE
                )
                print(f"  [OK] Model {model_id} ({model_name})")
            except Exception as e:
                print(f"  [ERROR] Model {model_id} ({model_name}): {e}")
                continue

        print(f"[INFO] Initialized {len(trading_engines)} engine(s)\n")

    except Exception as e:
        print(f"[ERROR] Init engines failed: {e}\n")

if __name__ == '__main__':
    import webbrowser
    import os
    
    print("\n" + "=" * 60)
    print("AITradeGame - Starting...")
    print("=" * 60)
    print("[INFO] Initializing database...")
    
    db.init_db()
    
    print("[INFO] Database initialized")
    print("[INFO] Initializing trading engines...")
    
    init_trading_engines()
    
    if auto_trading:
        trading_thread = threading.Thread(target=trading_loop, daemon=True)
        trading_thread.start()
        print("[INFO] Auto-trading enabled")
    
    print("\n" + "=" * 60)
    print("AITradeGame is running!")
    print("Server: http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("=" * 60 + "\n")
    
    # 自动打开浏览器
    def open_browser():
        time.sleep(1.5)  # 等待服务器启动
        url = "http://localhost:5000"
        try:
            webbrowser.open(url)
            print(f"[INFO] Browser opened: {url}")
        except Exception as e:
            print(f"[WARN] Could not open browser: {e}")
    
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)

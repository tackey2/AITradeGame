"""
Trading execution routes blueprint
Handles all trading execution, control, and monitoring endpoints
"""
from flask import Blueprint, request, jsonify
import time
from datetime import datetime

# Import trading components
from trading_engine import TradingEngine
from ai_trader import AITrader
from risk_manager import RiskManager
from notifier import Notifier
from explainer import AIExplainer
from trading_modes import TradingExecutor
from market_analyzer import MarketAnalyzer

# Create blueprint
trading_bp = Blueprint('trading', __name__, url_prefix='/api')

# Shared resources (injected via init_app)
_db = None
_enhanced_db = None
_market_fetcher = None
_trading_engines = None
_risk_managers = None
_notifiers = None
_explainers = None
_trading_executors = None
_trade_fee_rate = None
_auto_trading_flag = None  # Reference to auto_trading flag


def init_app(db, enhanced_db, market_fetcher, trading_engines, risk_managers,
             notifiers, explainers, trading_executors, trade_fee_rate, auto_trading_flag=None):
    """
    Initialize blueprint with shared resources

    Args:
        db: Database instance
        enhanced_db: EnhancedDatabase instance
        market_fetcher: MarketDataFetcher instance
        trading_engines: Dict of model_id -> TradingEngine
        risk_managers: Dict of model_id -> RiskManager
        notifiers: Dict of model_id -> Notifier
        explainers: Dict of model_id -> AIExplainer
        trading_executors: Dict of model_id -> TradingExecutor
        trade_fee_rate: Trading fee rate (float)
        auto_trading_flag: Reference to auto_trading boolean (optional, for trading_loop)
    """
    global _db, _enhanced_db, _market_fetcher, _trading_engines
    global _risk_managers, _notifiers, _explainers, _trading_executors
    global _trade_fee_rate, _auto_trading_flag

    _db = db
    _enhanced_db = enhanced_db
    _market_fetcher = market_fetcher
    _trading_engines = trading_engines
    _risk_managers = risk_managers
    _notifiers = notifiers
    _explainers = explainers
    _trading_executors = trading_executors
    _trade_fee_rate = trade_fee_rate
    _auto_trading_flag = auto_trading_flag


# ============ HELPER FUNCTIONS ============

def init_enhanced_components(model_id):
    """Initialize risk manager, notifier, explainer, and executor for a model"""
    if model_id not in _risk_managers:
        _risk_managers[model_id] = RiskManager(_enhanced_db)

    if model_id not in _notifiers:
        _notifiers[model_id] = Notifier(_enhanced_db)

    if model_id not in _explainers:
        # Get model to access AI configuration
        model = _enhanced_db.get_model(model_id)
        provider = _enhanced_db.get_provider(model['provider_id'])

        ai_trader = AITrader(
            api_key=provider['api_key'],
            api_url=provider['api_url'],
            model_name=model['model_name']
        )
        _explainers[model_id] = AIExplainer(ai_trader)

    if model_id not in _trading_executors:
        # Create executor with all components
        _trading_executors[model_id] = TradingExecutor(
            db=_enhanced_db,
            risk_manager=_risk_managers[model_id],
            notifier=_notifiers[model_id],
            explainer=_explainers[model_id]
        )


def trading_loop(auto_trading_check=None):
    """
    Background trading loop for automated trading

    Args:
        auto_trading_check: Callable that returns True if auto trading should continue
                          If None, uses _auto_trading_flag or defaults to lambda: True
    """
    print("[INFO] Trading loop started")

    # Determine which auto_trading check to use
    if auto_trading_check is None:
        if _auto_trading_flag is not None:
            auto_trading_check = _auto_trading_flag
        else:
            # Default: always return True (caller must handle stopping)
            auto_trading_check = lambda: True

    while auto_trading_check():
        try:
            if not _trading_engines:
                time.sleep(30)
                continue

            print(f"\n{'='*60}")
            print(f"[CYCLE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"[INFO] Active models: {len(_trading_engines)}")
            print(f"{'='*60}")

            for model_id, engine in list(_trading_engines.items()):
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


# ============ TRADING EXECUTION ROUTES ============

@trading_bp.route('/models/<int:model_id>/execute', methods=['POST'])
def execute_trading(model_id):
    """Execute trading cycle for a model (original system)"""
    if model_id not in _trading_engines:
        model = _db.get_model(model_id)
        if not model:
            return jsonify({'error': 'Model not found'}), 404

        # Get provider info
        provider = _db.get_provider(model['provider_id'])
        if not provider:
            return jsonify({'error': 'Provider not found'}), 404

        _trading_engines[model_id] = TradingEngine(
            model_id=model_id,
            db=_db,
            market_fetcher=_market_fetcher,
            ai_trader=AITrader(
                api_key=provider['api_key'],
                api_url=provider['api_url'],
                model_name=model['model_name']
            ),
            trade_fee_rate=_trade_fee_rate
        )

    try:
        result = _trading_engines[model_id].execute_trading_cycle()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@trading_bp.route('/models/<int:model_id>/execute-enhanced', methods=['POST'])
def execute_enhanced_trading(model_id):
    """Execute trading cycle with enhanced system (mode-aware)"""
    try:
        # Initialize components
        init_enhanced_components(model_id)

        # Get market data
        coins = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE']
        market_data = _market_fetcher.get_current_prices(coins)

        # Get AI decisions
        model = _enhanced_db.get_model(model_id)
        provider = _enhanced_db.get_provider(model['provider_id'])

        ai_trader = AITrader(
            api_key=provider['api_key'],
            api_url=provider['api_url'],
            model_name=model['model_name']
        )

        # Get portfolio and account info
        portfolio = _enhanced_db.get_portfolio(model_id, market_data)
        account_info = {
            'initial_capital': model['initial_capital'],
            'total_return': ((portfolio['total_value'] - model['initial_capital']) / model['initial_capital'] * 100)
        }

        # Get AI decisions
        ai_decisions = ai_trader.make_decision(market_data, portfolio, account_info)

        # Execute with trading executor (mode-aware)
        result = _trading_executors[model_id].execute_trading_cycle(
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


@trading_bp.route('/models/<int:model_id>/pause', methods=['POST'])
def pause_model(model_id):
    """Emergency pause - switch to semi-auto mode"""
    try:
        data = request.json or {}
        reason = data.get('reason', 'User-initiated emergency pause')

        # Get current mode
        current_mode = _enhanced_db.get_model_mode(model_id)

        if current_mode == 'fully_automated':
            # Switch to semi-auto
            _enhanced_db.set_model_mode(model_id, 'semi_automated')

            # Log incident
            _enhanced_db.log_incident(
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


@trading_bp.route('/emergency-stop-all', methods=['POST'])
def emergency_stop_all():
    """Emergency stop ALL models - switch all to simulation"""
    try:
        data = request.json or {}
        reason = data.get('reason', 'User-initiated emergency stop for all models')

        models = _enhanced_db.get_all_models()
        switched = []

        for model in models:
            model_id = model['id']
            current_mode = _enhanced_db.get_model_mode(model_id)

            if current_mode != 'simulation':
                _enhanced_db.set_model_mode(model_id, 'simulation')

                _enhanced_db.log_incident(
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

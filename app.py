"""
AITradeGame - Main Application Entry Point (Modularized)

This file now uses Flask blueprints for better code organization.
Routes are organized in the 'routes' package by functionality.
"""
from flask import Flask
from flask_cors import CORS
import time
import threading

# Core system imports
from database import Database
from database_enhanced import EnhancedDatabase
from market_data import MarketDataFetcher
from ai_trader import AITrader
from trading_engine import TradingEngine

# Enhanced system imports
from trading_modes import TradingExecutor
from risk_manager import RiskManager
from notifier import Notifier
from explainer import AIExplainer
from market_analyzer import MarketAnalyzer

# Import all blueprints
from routes.views import views_bp
from routes.providers import providers_bp
from routes.models import models_bp
from routes.analytics import models_analytics_bp, aggregated_bp, market_bp
from routes.trading import trading_bp
from routes.risk import risk_bp
from routes.decisions import decisions_bp
from routes.system import system_bp

# Import blueprint initialization functions
import routes.providers as providers_routes
import routes.models as models_routes
import routes.analytics as analytics_routes
import routes.trading as trading_routes
import routes.risk as risk_routes
import routes.decisions as decisions_routes
import routes.system as system_routes

# ============ Flask App Creation ============
app = Flask(__name__)
CORS(app)

# ============ Initialize Databases ============
db = Database('AITradeGame.db')
enhanced_db = EnhancedDatabase('AITradeGame.db')

# Initialize enhanced database schema
enhanced_db.init_db()

# Initialize system risk profiles
enhanced_db.init_system_risk_profiles()

# ============ Initialize Core Components ============
# Market data fetcher (pass db for price snapshot storage)
market_fetcher = MarketDataFetcher(db=db)

# Trading engines (original system)
trading_engines = {}

# Enhanced system components
risk_managers = {}  # model_id -> RiskManager
notifiers = {}  # model_id -> Notifier
explainers = {}  # model_id -> AIExplainer
trading_executors = {}  # model_id -> TradingExecutor

# Global settings
auto_trading = True
TRADE_FEE_RATE = 0.001  # Default trade fee rate


def init_trading_engines():
    """Initialize trading engines for all models in database"""
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


# ============ Register Blueprints ============

# Initialize blueprints with shared resources
providers_routes.init_app(db)
models_routes.init_app(db, enhanced_db, market_fetcher, trading_engines, TRADE_FEE_RATE)
analytics_routes.init_app(db, enhanced_db, market_fetcher)
trading_routes.init_app(
    db, enhanced_db, market_fetcher, trading_engines,
    risk_managers, notifiers, explainers, trading_executors,
    TRADE_FEE_RATE, lambda: auto_trading
)
risk_routes.init_app(db, enhanced_db, market_fetcher, risk_managers)
decisions_routes.init_app(enhanced_db, trading_executors, risk_managers, notifiers, explainers)
system_routes.init_app(db, enhanced_db, market_fetcher, lambda: auto_trading)

# Register all blueprints
app.register_blueprint(views_bp)
app.register_blueprint(providers_bp)
app.register_blueprint(models_bp)
app.register_blueprint(models_analytics_bp)
app.register_blueprint(aggregated_bp)
app.register_blueprint(market_bp)
app.register_blueprint(trading_bp)
app.register_blueprint(risk_bp)
app.register_blueprint(decisions_bp)
app.register_blueprint(system_bp)

print("[INFO] All blueprints registered successfully")


# ============ Main Entry Point ============
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

    # Start trading loop if auto-trading is enabled
    if auto_trading:
        # Import and start trading loop from trading routes
        from routes.trading import trading_loop
        trading_thread = threading.Thread(
            target=trading_loop,
            args=(lambda: auto_trading,),
            daemon=True
        )
        trading_thread.start()
        print("[INFO] Auto-trading enabled")

    print("\n" + "=" * 60)
    print("AITradeGame is running!")
    print("Server: http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("=" * 60 + "\n")

    # Auto-open browser
    def open_browser():
        time.sleep(1.5)  # Wait for server to start
        url = "http://localhost:5000"
        try:
            webbrowser.open(url)
            print(f"[INFO] Browser opened: {url}")
        except Exception as e:
            print(f"[WARN] Could not open browser: {e}")

    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)

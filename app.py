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

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize databases (keep both for backward compatibility)
db = Database('AITradeGame.db')
enhanced_db = EnhancedDatabase('AITradeGame.db')

# Initialize enhanced database schema
enhanced_db.init_db()

# Initialize system risk profiles
enhanced_db.init_system_risk_profiles()

# Market data fetcher (pass db for price snapshot storage)
market_fetcher = MarketDataFetcher(db=db)

# Trading engines (original system)
trading_engines = {}

# NEW - Enhanced system components
risk_managers = {}  # model_id -> RiskManager
notifiers = {}  # model_id -> Notifier
explainers = {}  # model_id -> AIExplainer
trading_executors = {}  # model_id -> TradingExecutor

auto_trading = True
TRADE_FEE_RATE = 0.001  # 默认交易费率

# ============ Import Blueprints ============
from routes.pages import pages_bp
from routes.api.providers import providers_bp
from routes.api.models import models_bp, init_trading_engines, trading_loop
from routes.api.trading_config import trading_config_bp
from routes.api.risk import risk_bp
from routes.api.graduation import graduation_bp
from routes.api.monitoring import monitoring_bp
from routes.api.reports import reports_bp

# Initialize shared context for all blueprints
from routes import init_context

init_context(
    db=db,
    enhanced_db=enhanced_db,
    market_fetcher=market_fetcher,
    trading_engines=trading_engines,
    risk_managers=risk_managers,
    notifiers=notifiers,
    explainers=explainers,
    trading_executors=trading_executors,
    auto_trading=auto_trading,
    trade_fee_rate=TRADE_FEE_RATE
)

# ============ Register Blueprints ============
app.register_blueprint(pages_bp)
app.register_blueprint(providers_bp)
app.register_blueprint(models_bp)
app.register_blueprint(trading_config_bp)
app.register_blueprint(risk_bp)
app.register_blueprint(graduation_bp)
app.register_blueprint(monitoring_bp)
app.register_blueprint(reports_bp)

# ============ Application Entry Point ============
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

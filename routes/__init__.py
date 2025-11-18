"""
Routes package for AITradeGame.
Contains all Flask blueprints for modular API organization.
"""

# This will be populated by app.py during initialization
app_context = {
    'db': None,
    'enhanced_db': None,
    'market_fetcher': None,
    'trading_engines': None,
    'risk_managers': None,
    'notifiers': None,
    'explainers': None,
    'trading_executors': None,
    'auto_trading': None,
    'TRADE_FEE_RATE': None
}

def init_context(db, enhanced_db, market_fetcher, trading_engines,
                 risk_managers, notifiers, explainers, trading_executors,
                 auto_trading, trade_fee_rate):
    """Initialize the shared context for all blueprints."""
    app_context['db'] = db
    app_context['enhanced_db'] = enhanced_db
    app_context['market_fetcher'] = market_fetcher
    app_context['trading_engines'] = trading_engines
    app_context['risk_managers'] = risk_managers
    app_context['notifiers'] = notifiers
    app_context['explainers'] = explainers
    app_context['trading_executors'] = trading_executors
    app_context['auto_trading'] = auto_trading
    app_context['TRADE_FEE_RATE'] = trade_fee_rate

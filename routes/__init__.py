"""
Routes package for AITradeGame application.
Contains all Flask blueprints organized by functionality.
"""

from .views import views_bp
from .providers import providers_bp
from .models import models_bp
from .analytics import models_analytics_bp, aggregated_bp, market_bp
from .trading import trading_bp
from .risk import risk_bp
from .decisions import decisions_bp
from .system import system_bp

__all__ = [
    'views_bp',
    'providers_bp',
    'models_bp',
    'models_analytics_bp',
    'aggregated_bp',
    'market_bp',
    'trading_bp',
    'risk_bp',
    'decisions_bp',
    'system_bp'
]

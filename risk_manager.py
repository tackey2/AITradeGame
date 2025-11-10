"""
Risk Management Module
Pre-trade validation to ensure all trades comply with risk limits
"""
from typing import Dict, Tuple
from datetime import datetime, timedelta


class RiskManager:
    """Pre-execution risk validation"""

    def __init__(self, db):
        """
        Args:
            db: Database instance (EnhancedDatabase)
        """
        self.db = db

    def validate_trade(self, model_id: int, coin: str, decision: Dict,
                      market_data: Dict) -> Tuple[bool, str]:
        """
        Validate a trade against all risk limits

        Args:
            model_id: Model ID
            coin: Trading pair (e.g., 'BTC')
            decision: AI decision dict
            market_data: Current market data for the coin

        Returns:
            (is_valid, reason) - True if trade passes all checks
        """
        settings = self.db.get_model_settings(model_id)
        portfolio = self.db.get_portfolio(model_id, {coin: market_data})
        model = self.db.get_model(model_id)

        signal = decision.get('signal', 'hold')
        quantity = decision.get('quantity', 0)
        price = market_data.get('price', 0)

        # Skip hold signals
        if signal == 'hold':
            return True, "Hold signal"

        # Check 1: Max position size
        is_valid, reason = self._check_position_size(
            settings, portfolio, quantity, price
        )
        if not is_valid:
            return False, reason

        # Check 2: Daily loss limit (circuit breaker)
        is_valid, reason = self._check_daily_loss_limit(
            settings, model, portfolio
        )
        if not is_valid:
            return False, reason

        # Check 3: Max daily trades
        is_valid, reason = self._check_daily_trade_limit(
            settings, model_id
        )
        if not is_valid:
            return False, reason

        # Check 4: Max open positions
        is_valid, reason = self._check_max_positions(
            settings, portfolio, signal
        )
        if not is_valid:
            return False, reason

        # Check 5: Cash reserve
        is_valid, reason = self._check_cash_reserve(
            settings, portfolio, quantity, price, signal
        )
        if not is_valid:
            return False, reason

        # Check 6: Max drawdown (for full auto mode only)
        automation = self.db.get_automation_level(model_id)
        if automation == 'fully_automated':
            is_valid, reason = self._check_max_drawdown(
                settings, model_id, model, portfolio
            )
            if not is_valid:
                return False, reason

        # Check 7: Live trading specific checks
        environment = self.db.get_trading_environment(model_id)
        if environment == 'live':
            # Additional live trading validations can go here
            # For now, we use the same checks
            pass

        # All checks passed
        return True, "✅ All risk checks passed"

    def _check_position_size(self, settings: Dict, portfolio: Dict,
                            quantity: float, price: float) -> Tuple[bool, str]:
        """Check if position size is within limits"""
        position_value = quantity * price
        max_size_pct = settings.get('max_position_size_pct', 10.0)
        max_size = portfolio['total_value'] * (max_size_pct / 100)

        if position_value > max_size:
            return False, f"Position size ${position_value:,.0f} exceeds limit ${max_size:,.0f} ({max_size_pct}%)"

        return True, ""

    def _check_daily_loss_limit(self, settings: Dict, model: Dict,
                                portfolio: Dict) -> Tuple[bool, str]:
        """Check if daily loss limit exceeded (CIRCUIT BREAKER)"""
        initial_capital = model['initial_capital']
        current_value = portfolio['total_value']

        daily_loss_pct = ((current_value - initial_capital) / initial_capital) * 100
        max_loss_pct = settings.get('max_daily_loss_pct', 3.0)

        if daily_loss_pct < -max_loss_pct:
            return False, f"🚨 CIRCUIT BREAKER: Daily loss {daily_loss_pct:.2f}% exceeds limit ({max_loss_pct}%)"

        return True, ""

    def _check_daily_trade_limit(self, settings: Dict, model_id: int) -> Tuple[bool, str]:
        """Check if daily trade limit exceeded"""
        # Count trades today
        trades_today = self._count_trades_today(model_id)
        max_trades = settings.get('max_daily_trades', 20)

        if trades_today >= max_trades:
            return False, f"Daily trade limit reached ({trades_today}/{max_trades})"

        return True, ""

    def _check_max_positions(self, settings: Dict, portfolio: Dict,
                            signal: str) -> Tuple[bool, str]:
        """Check if max open positions limit exceeded"""
        # Only check for entry signals
        if signal not in ['buy_to_enter', 'sell_to_enter']:
            return True, ""

        current_positions = len(portfolio['positions'])
        max_positions = settings.get('max_open_positions', 5)

        if current_positions >= max_positions:
            return False, f"Max positions reached ({current_positions}/{max_positions})"

        return True, ""

    def _check_cash_reserve(self, settings: Dict, portfolio: Dict,
                           quantity: float, price: float, signal: str) -> Tuple[bool, str]:
        """Check if trade would violate minimum cash reserve"""
        # Only check for entry signals
        if signal not in ['buy_to_enter', 'sell_to_enter']:
            return True, ""

        required_cash = quantity * price  # Simplified, doesn't account for leverage
        new_cash = portfolio['cash'] - required_cash

        min_reserve_pct = settings.get('min_cash_reserve_pct', 20.0)
        min_reserve = portfolio['total_value'] * (min_reserve_pct / 100)

        if new_cash < min_reserve:
            return False, f"Insufficient cash reserve (would have ${new_cash:,.0f}, need ${min_reserve:,.0f} ({min_reserve_pct}%))"

        return True, ""

    def _check_max_drawdown(self, settings: Dict, model_id: int, model: Dict,
                           portfolio: Dict) -> Tuple[bool, str]:
        """Check if max drawdown exceeded (full auto only)"""
        # Get peak equity (highest total_value ever reached)
        peak_equity = self._get_peak_equity(model_id, model['initial_capital'])

        current_value = portfolio['total_value']
        drawdown_pct = ((current_value - peak_equity) / peak_equity) * 100

        max_drawdown = settings.get('max_drawdown_pct', 15.0)

        if drawdown_pct < -max_drawdown:
            return False, f"Max drawdown exceeded: {drawdown_pct:.2f}% from peak ${peak_equity:,.0f} (limit: {max_drawdown}%)"

        return True, ""

    def _count_trades_today(self, model_id: int) -> int:
        """Count trades executed today"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        today = datetime.now().date()
        cursor.execute('''
            SELECT COUNT(*) as count FROM trades
            WHERE model_id = ?
            AND DATE(timestamp) = DATE(?)
        ''', (model_id, today))

        row = cursor.fetchone()
        conn.close()

        return row['count'] if row else 0

    def _get_peak_equity(self, model_id: int, initial_capital: float) -> float:
        """Get the highest account value ever reached"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT MAX(total_value) as peak FROM account_values
            WHERE model_id = ?
        ''', (model_id,))

        row = cursor.fetchone()
        conn.close()

        if row and row['peak']:
            return max(row['peak'], initial_capital)
        return initial_capital

    def get_risk_status(self, model_id: int) -> Dict:
        """
        Get current risk status for a model

        Returns:
            Dict with risk metrics and status
        """
        settings = self.db.get_model_settings(model_id)
        portfolio = self.db.get_portfolio(model_id)
        model = self.db.get_model(model_id)

        # Calculate metrics
        initial_capital = model['initial_capital']
        current_value = portfolio['total_value']
        daily_pnl_pct = ((current_value - initial_capital) / initial_capital) * 100

        trades_today = self._count_trades_today(model_id)
        peak_equity = self._get_peak_equity(model_id, initial_capital)
        drawdown_pct = ((current_value - peak_equity) / peak_equity) * 100

        # Check limits
        max_daily_loss = settings.get('max_daily_loss_pct', 3.0)
        max_trades = settings.get('max_daily_trades', 20)
        max_positions = settings.get('max_open_positions', 5)
        max_drawdown = settings.get('max_drawdown_pct', 15.0)

        return {
            'daily_pnl_pct': daily_pnl_pct,
            'daily_loss_used_pct': (abs(daily_pnl_pct) / max_daily_loss) * 100 if daily_pnl_pct < 0 else 0,
            'trades_today': trades_today,
            'trades_limit': max_trades,
            'trades_used_pct': (trades_today / max_trades) * 100,
            'open_positions': len(portfolio['positions']),
            'positions_limit': max_positions,
            'positions_used_pct': (len(portfolio['positions']) / max_positions) * 100,
            'drawdown_pct': drawdown_pct,
            'drawdown_used_pct': (abs(drawdown_pct) / max_drawdown) * 100 if drawdown_pct < 0 else 0,
            'circuit_breaker_triggered': daily_pnl_pct < -max_daily_loss,
            'status': 'ok' if daily_pnl_pct > -max_daily_loss else 'circuit_breaker'
        }

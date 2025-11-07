"""
Trading Modes System
Handles execution logic for different trading modes:
- Simulation: Fake execution for testing
- Semi-Automated: Real APIs, requires user approval
- Fully Automated: Real APIs, autonomous execution
"""
from enum import Enum
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import json


class TradingMode(Enum):
    """Trading modes"""
    SIMULATION = "simulation"
    SEMI_AUTO = "semi_automated"
    FULL_AUTO = "fully_automated"


class TradingExecutor:
    """Unified executor for all trading modes"""

    def __init__(self, db, exchange, risk_manager, notifier=None, explainer=None):
        """
        Args:
            db: Database instance (EnhancedDatabase)
            exchange: Exchange interface (BinanceExchange, etc.)
            risk_manager: RiskManager instance
            notifier: Notification system (optional)
            explainer: AI explainability system (optional)
        """
        self.db = db
        self.exchange = exchange
        self.risk_manager = risk_manager
        self.notifier = notifier
        self.explainer = explainer

    def execute_trading_cycle(self, model_id: int, market_data: Dict,
                             ai_decisions: Dict) -> Dict:
        """
        Main trading cycle - handles all modes

        Args:
            model_id: Model ID
            market_data: Current market data
            ai_decisions: AI trading decisions

        Returns:
            Dict with execution results
        """
        # Get model and mode
        model = self.db.get_model(model_id)
        mode = TradingMode(self.db.get_model_mode(model_id))

        print(f"[{mode.value.upper()}] Executing trading cycle for model {model['name']}")

        # Get portfolio
        portfolio = self.db.get_portfolio(model_id, market_data)

        # Generate explanations for all decisions
        explanations = {}
        if self.explainer:
            for coin, decision in ai_decisions.items():
                explanations[coin] = self.explainer.create_explanation(
                    coin=coin,
                    decision=decision,
                    market_data=market_data.get(coin, {}),
                    portfolio=portfolio
                )

        # Log AI conversation
        self.db.add_conversation(
            model_id=model_id,
            user_prompt="Market analysis request",
            ai_response=json.dumps(ai_decisions)
        )

        # Mode-specific execution
        if mode == TradingMode.SIMULATION:
            return self._execute_simulation(model_id, ai_decisions, market_data, explanations)

        elif mode == TradingMode.SEMI_AUTO:
            return self._request_approvals(model_id, ai_decisions, market_data, explanations)

        elif mode == TradingMode.FULL_AUTO:
            return self._execute_fully_auto(model_id, ai_decisions, market_data, explanations)

    def _execute_simulation(self, model_id: int, decisions: Dict,
                           market_data: Dict, explanations: Dict) -> Dict:
        """Execute in simulation mode (fake execution)"""
        results = {
            'mode': 'simulation',
            'executed': [],
            'skipped': []
        }

        for coin, decision in decisions.items():
            signal = decision.get('signal', 'hold')

            if signal == 'hold':
                continue

            # Validate with risk manager
            is_valid, reason = self.risk_manager.validate_trade(
                model_id=model_id,
                coin=coin,
                decision=decision,
                market_data=market_data.get(coin, {})
            )

            if not is_valid:
                results['skipped'].append({
                    'coin': coin,
                    'reason': reason
                })
                continue

            # Simulate execution (no real API call)
            trade_result = self._simulate_trade(model_id, coin, decision, market_data[coin])
            results['executed'].append(trade_result)

        return results

    def _request_approvals(self, model_id: int, decisions: Dict,
                          market_data: Dict, explanations: Dict) -> Dict:
        """Request user approval for each decision (semi-auto mode)"""
        results = {
            'mode': 'semi_automated',
            'pending': [],
            'skipped': []
        }

        for coin, decision in decisions.items():
            signal = decision.get('signal', 'hold')

            if signal == 'hold':
                continue

            # Validate with risk manager
            is_valid, reason = self.risk_manager.validate_trade(
                model_id=model_id,
                coin=coin,
                decision=decision,
                market_data=market_data.get(coin, {})
            )

            if not is_valid:
                results['skipped'].append({
                    'coin': coin,
                    'reason': reason
                })
                continue

            # Create pending decision
            decision_id = self.db.create_pending_decision(
                model_id=model_id,
                coin=coin,
                decision=decision,
                explanation=explanations.get(coin, {}),
                expires_in_hours=1
            )

            results['pending'].append({
                'decision_id': decision_id,
                'coin': coin,
                'signal': signal,
                'quantity': decision.get('quantity')
            })

            # Send notification
            if self.notifier:
                self.notifier.send_notification(
                    title=f"🔔 Trade Approval Needed: {coin}",
                    message=f"AI wants to {signal.upper()} {decision.get('quantity')} {coin}",
                    priority="medium",
                    model_id=model_id
                )

        return results

    def _execute_fully_auto(self, model_id: int, decisions: Dict,
                           market_data: Dict, explanations: Dict) -> Dict:
        """Execute automatically without approval (full-auto mode)"""
        results = {
            'mode': 'fully_automated',
            'executed': [],
            'skipped': []
        }

        # Check auto-pause triggers first
        should_pause, pause_reason = self._check_auto_pause_triggers(model_id)
        if should_pause:
            # Pause full auto, switch to semi-auto
            self.db.set_model_mode(model_id, TradingMode.SEMI_AUTO.value)

            self.db.log_incident(
                model_id=model_id,
                incident_type='AUTO_PAUSE',
                severity='high',
                message=f'Full auto paused: {pause_reason}'
            )

            if self.notifier:
                self.notifier.send_notification(
                    title="🚨 FULL AUTO PAUSED",
                    message=f"Switched to semi-auto: {pause_reason}",
                    priority="critical",
                    model_id=model_id
                )

            return {
                'mode': 'paused',
                'reason': pause_reason,
                'executed': [],
                'skipped': []
            }

        # Execute trades
        for coin, decision in decisions.items():
            signal = decision.get('signal', 'hold')

            if signal == 'hold':
                continue

            # Validate with risk manager
            is_valid, reason = self.risk_manager.validate_trade(
                model_id=model_id,
                coin=coin,
                decision=decision,
                market_data=market_data.get(coin, {})
            )

            if not is_valid:
                results['skipped'].append({
                    'coin': coin,
                    'reason': reason
                })

                # Log risk rejection
                self.db.log_incident(
                    model_id=model_id,
                    incident_type='TRADE_REJECTED',
                    severity='low',
                    message=f'Trade rejected: {coin} - {reason}'
                )
                continue

            # Execute trade
            try:
                trade_result = self._execute_trade_live(
                    model_id=model_id,
                    coin=coin,
                    decision=decision,
                    market_data=market_data[coin]
                )

                results['executed'].append(trade_result)

                # Send informational notification
                if self.notifier:
                    self.notifier.send_notification(
                        title=f"✅ Trade Executed: {coin}",
                        message=f"{signal.upper()} {decision.get('quantity')} @ ${market_data[coin]['price']}",
                        priority="low",
                        model_id=model_id
                    )

            except Exception as e:
                error_msg = f"Execution failed: {str(e)}"
                results['skipped'].append({
                    'coin': coin,
                    'reason': error_msg
                })

                self.db.log_incident(
                    model_id=model_id,
                    incident_type='EXECUTION_ERROR',
                    severity='high',
                    message=f'Failed to execute {coin}: {str(e)}'
                )

                if self.notifier:
                    self.notifier.send_notification(
                        title=f"❌ Trade Failed: {coin}",
                        message=error_msg,
                        priority="high",
                        model_id=model_id
                    )

        return results

    def approve_decision(self, decision_id: int, modified: bool = False,
                        modifications: Dict = None) -> Dict:
        """
        Approve a pending decision (semi-auto mode)

        Args:
            decision_id: Pending decision ID
            modified: Whether user modified the decision
            modifications: Modified parameters if any

        Returns:
            Execution result
        """
        # Get pending decision
        decisions = self.db.get_pending_decisions(model_id=None, status='pending')
        decision_data = next((d for d in decisions if d['id'] == decision_id), None)

        if not decision_data:
            return {'success': False, 'error': 'Decision not found or already processed'}

        # Check expiration
        if datetime.now() > datetime.fromisoformat(decision_data['expires_at']):
            self.db.update_pending_decision(decision_id, status='expired')
            return {'success': False, 'error': 'Decision expired'}

        model_id = decision_data['model_id']
        coin = decision_data['coin']
        decision = decision_data['decision_data']

        # Apply modifications if any
        if modified and modifications:
            decision.update(modifications)
            self.db.update_pending_decision(
                decision_id,
                status='approved',
                modified_data=modifications
            )
        else:
            self.db.update_pending_decision(decision_id, status='approved')

        # Get current market data
        from market_data import MarketDataFetcher
        market_fetcher = MarketDataFetcher()
        market_data = market_fetcher.get_current_prices([coin])

        # Execute the trade
        try:
            result = self._execute_trade_live(model_id, coin, decision, market_data[coin])

            # Log approval event
            self.db.conn = self.db.get_connection()
            cursor = self.db.conn.cursor()
            cursor.execute('''
                INSERT INTO approval_events
                (decision_id, model_id, approved, modified, modification_details, execution_result)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (decision_id, model_id, True, modified,
                  json.dumps(modifications) if modifications else None,
                  json.dumps(result)))
            self.db.conn.commit()
            self.db.conn.close()

            return {'success': True, 'result': result}

        except Exception as e:
            error_msg = f"Execution failed: {str(e)}"

            # Log error
            cursor = self.db.conn.cursor()
            cursor.execute('''
                INSERT INTO approval_events
                (decision_id, model_id, approved, modified, execution_result)
                VALUES (?, ?, ?, ?, ?)
            ''', (decision_id, model_id, True, modified, json.dumps({'error': error_msg})))
            self.db.conn.commit()
            self.db.conn.close()

            return {'success': False, 'error': error_msg}

    def reject_decision(self, decision_id: int, reason: str = None) -> Dict:
        """Reject a pending decision"""
        self.db.update_pending_decision(
            decision_id,
            status='rejected',
            rejection_reason=reason
        )

        # Log rejection
        decisions = self.db.get_pending_decisions(model_id=None, status='rejected')
        decision_data = next((d for d in decisions if d['id'] == decision_id), None)

        if decision_data:
            cursor = self.db.conn = self.db.get_connection()
            cursor = self.db.conn.cursor()
            cursor.execute('''
                INSERT INTO approval_events
                (decision_id, model_id, approved, rejection_reason)
                VALUES (?, ?, ?, ?)
            ''', (decision_id, decision_data['model_id'], False, reason))
            self.db.conn.commit()
            self.db.conn.close()

        return {'success': True}

    def _simulate_trade(self, model_id: int, coin: str, decision: Dict,
                       market_data: Dict) -> Dict:
        """Simulate trade execution (no real API)"""
        # Use existing trading engine logic
        from trading_engine import TradingEngine
        engine = TradingEngine(self.db)

        # Execute the signal
        signal = decision.get('signal')
        quantity = decision.get('quantity', 0)
        leverage = decision.get('leverage', 1)

        current_price = market_data.get('price', 0)

        if signal == 'buy_to_enter':
            engine._execute_buy(model_id, coin, quantity, current_price, leverage)
        elif signal == 'sell_to_enter':
            engine._execute_sell(model_id, coin, quantity, current_price, leverage)
        elif signal == 'close_position':
            engine._execute_close(model_id, coin, current_price)

        return {
            'coin': coin,
            'signal': signal,
            'quantity': quantity,
            'price': current_price,
            'status': 'simulated'
        }

    def _execute_trade_live(self, model_id: int, coin: str, decision: Dict,
                           market_data: Dict) -> Dict:
        """Execute trade on real exchange"""
        # TODO: Implement real exchange execution
        # For now, use simulation
        return self._simulate_trade(model_id, coin, decision, market_data)

    def _check_auto_pause_triggers(self, model_id: int) -> Tuple[bool, str]:
        """
        Check if any auto-pause triggers are hit

        Returns:
            (should_pause, reason)
        """
        settings = self.db.get_model_settings(model_id)

        if not settings.get('auto_pause_enabled', True):
            return False, ""

        # Trigger 1: Consecutive losses
        recent_trades = self.db.get_trades(model_id, limit=20)
        consecutive_losses = 0
        for trade in recent_trades:
            if trade['pnl'] < 0:
                consecutive_losses += 1
            else:
                break

        threshold = settings.get('auto_pause_consecutive_losses', 5)
        if consecutive_losses >= threshold:
            return True, f"{consecutive_losses} consecutive losses (threshold: {threshold})"

        # Trigger 2: Win rate drop
        if len(recent_trades) >= 10:
            wins = sum(1 for t in recent_trades[:10] if t['pnl'] > 0)
            win_rate = wins / 10 * 100
            threshold = settings.get('auto_pause_win_rate_threshold', 40.0)

            if win_rate < threshold:
                return True, f"Win rate dropped to {win_rate:.1f}% (threshold: {threshold}%)"

        # Trigger 3: Daily loss limit (checked in risk manager, but double-check here)
        portfolio = self.db.get_portfolio(model_id)
        model = self.db.get_model(model_id)
        initial_capital = model['initial_capital']

        daily_loss_pct = (portfolio['total_value'] - initial_capital) / initial_capital * 100
        threshold = settings.get('max_daily_loss_pct', 3.0)

        if daily_loss_pct < -threshold:
            return True, f"Daily loss {daily_loss_pct:.2f}% exceeds limit ({threshold}%)"

        return False, ""

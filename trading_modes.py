"""
Trading System Architecture - REFACTORED
Properly separates Trading Environment from Automation Level

Architecture:
  Environment (Where): Simulation vs Live Trading
  Automation (How): Manual, Semi-Automated, Fully Automated

This matches the real-world mental model and allows for:
  - Simulation + Manual (learning)
  - Simulation + Semi-Auto (practicing approval workflow)
  - Live + Semi-Auto (real money with approval)
  - Live + Full-Auto (autonomous trading)
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
import json


# ============ Enums ============

class TradingEnvironment(Enum):
    """Where trades are executed"""
    SIMULATION = "simulation"  # Paper trading, no real money
    LIVE = "live"              # Real exchange, real money


class AutomationLevel(Enum):
    """How much control/automation"""
    MANUAL = "manual"                      # View only, no execution
    SEMI_AUTOMATED = "semi_automated"      # Execute with approval
    FULLY_AUTOMATED = "fully_automated"    # Autonomous execution


# ============ Environment Executors ============

class EnvironmentExecutor(ABC):
    """Abstract base class for environment-specific execution"""

    def __init__(self, db):
        self.db = db

    @abstractmethod
    def execute_trade(self, model_id: int, coin: str, decision: Dict,
                     market_data: Dict) -> Dict:
        """Execute a trade in this environment"""
        pass


class SimulationExecutor(EnvironmentExecutor):
    """Simulated execution - updates database only, no real API calls"""

    def execute_trade(self, model_id: int, coin: str, decision: Dict,
                     market_data: Dict) -> Dict:
        """Simulate trade execution"""
        from trading_engine import TradingEngine
        engine = TradingEngine(self.db)

        signal = decision.get('signal')
        quantity = decision.get('quantity', 0)
        leverage = decision.get('leverage', 1)
        current_price = market_data.get('price', 0)

        # Execute in simulation (database only)
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
            'status': 'simulated',
            'environment': 'simulation'
        }


class LiveExecutor(EnvironmentExecutor):
    """Live execution - real exchange API calls"""

    def __init__(self, db, exchange):
        super().__init__(db)
        self.exchange = exchange

    def execute_trade(self, model_id: int, coin: str, decision: Dict,
                     market_data: Dict) -> Dict:
        """Execute trade on real exchange"""
        from binance.exceptions import BinanceAPIException

        if not self.exchange:
            # No exchange configured - log error and fall back to simulation
            self.db.log_incident(
                model_id=model_id,
                incident_type='EXCHANGE_NOT_CONFIGURED',
                severity='critical',
                message='Live mode enabled but no exchange client configured'
            )

            print("[LIVE] ERROR: No exchange configured - falling back to simulation")
            sim_executor = SimulationExecutor(self.db)
            result = sim_executor.execute_trade(model_id, coin, decision, market_data)
            result['environment'] = 'live'
            result['status'] = 'failed_no_exchange'
            return result

        signal = decision.get('signal')
        quantity = decision.get('quantity', 0)
        current_price = market_data.get('price', 0)

        # Convert coin to Binance symbol format (e.g., BTC -> BTCUSDT)
        symbol = f"{coin}USDT"

        print(f"[LIVE] Executing on real exchange: {symbol} {signal} {quantity}")

        try:
            # Execute based on signal type
            if signal == 'buy_to_enter':
                # Place market buy order
                order = self.exchange.place_market_order(
                    symbol=symbol,
                    side='BUY',
                    quantity=quantity,
                    test=False  # Real execution
                )

                # Update database (positions)
                from trading_engine import TradingEngine
                engine = TradingEngine(self.db)
                engine._execute_buy(model_id, coin, quantity, current_price,
                                   decision.get('leverage', 1))

                return {
                    'coin': coin,
                    'signal': signal,
                    'quantity': quantity,
                    'price': order.get('price') or current_price,
                    'status': 'executed',
                    'environment': 'live',
                    'order_id': order.get('order_id'),
                    'exchange_response': order
                }

            elif signal == 'sell_to_enter':
                # Place market sell order (short)
                order = self.exchange.place_market_order(
                    symbol=symbol,
                    side='SELL',
                    quantity=quantity,
                    test=False
                )

                # Update database
                from trading_engine import TradingEngine
                engine = TradingEngine(self.db)
                engine._execute_sell(model_id, coin, quantity, current_price,
                                    decision.get('leverage', 1))

                return {
                    'coin': coin,
                    'signal': signal,
                    'quantity': quantity,
                    'price': order.get('price') or current_price,
                    'status': 'executed',
                    'environment': 'live',
                    'order_id': order.get('order_id'),
                    'exchange_response': order
                }

            elif signal == 'close_position':
                # Get current position to determine order side
                portfolio = self.db.get_portfolio(model_id)
                position = portfolio.get('positions', {}).get(coin)

                if not position or position['quantity'] == 0:
                    return {
                        'coin': coin,
                        'signal': signal,
                        'quantity': 0,
                        'price': current_price,
                        'status': 'skipped',
                        'environment': 'live',
                        'reason': 'No position to close'
                    }

                # Determine side (close long = sell, close short = buy)
                close_side = 'SELL' if position['quantity'] > 0 else 'BUY'
                close_quantity = abs(position['quantity'])

                order = self.exchange.place_market_order(
                    symbol=symbol,
                    side=close_side,
                    quantity=close_quantity,
                    test=False
                )

                # Update database
                from trading_engine import TradingEngine
                engine = TradingEngine(self.db)
                engine._execute_close(model_id, coin, current_price)

                return {
                    'coin': coin,
                    'signal': signal,
                    'quantity': close_quantity,
                    'price': order.get('price') or current_price,
                    'status': 'executed',
                    'environment': 'live',
                    'order_id': order.get('order_id'),
                    'exchange_response': order
                }

            else:
                # Unknown signal
                return {
                    'coin': coin,
                    'signal': signal,
                    'quantity': 0,
                    'price': current_price,
                    'status': 'skipped',
                    'environment': 'live',
                    'reason': f'Unknown signal: {signal}'
                }

        except BinanceAPIException as e:
            # Binance API error
            error_msg = f"Binance API error: {e.message} (code: {e.code})"

            self.db.log_incident(
                model_id=model_id,
                incident_type='EXCHANGE_API_ERROR',
                severity='high',
                message=error_msg,
                details={
                    'coin': coin,
                    'signal': signal,
                    'error_code': e.code,
                    'error_message': e.message
                }
            )

            print(f"[LIVE] API Error: {error_msg}")

            return {
                'coin': coin,
                'signal': signal,
                'quantity': quantity,
                'price': current_price,
                'status': 'failed',
                'environment': 'live',
                'error': error_msg
            }

        except Exception as e:
            # Generic error
            error_msg = f"Execution error: {str(e)}"

            self.db.log_incident(
                model_id=model_id,
                incident_type='EXECUTION_ERROR',
                severity='critical',
                message=error_msg,
                details={
                    'coin': coin,
                    'signal': signal,
                    'error': str(e)
                }
            )

            print(f"[LIVE] Execution Error: {error_msg}")

            return {
                'coin': coin,
                'signal': signal,
                'quantity': quantity,
                'price': current_price,
                'status': 'failed',
                'environment': 'live',
                'error': error_msg
            }


# ============ Automation Handlers ============

class AutomationHandler(ABC):
    """Abstract base class for automation-specific logic"""

    def __init__(self, db, notifier=None):
        self.db = db
        self.notifier = notifier

    @abstractmethod
    def process_decisions(self, model_id: int, decisions: Dict, market_data: Dict,
                         explanations: Dict, risk_manager) -> Dict:
        """Process AI decisions according to automation level"""
        pass


class ManualHandler(AutomationHandler):
    """Manual mode - display only, no execution"""

    def process_decisions(self, model_id: int, decisions: Dict, market_data: Dict,
                         explanations: Dict, risk_manager) -> Dict:
        """Display decisions but don't execute"""
        results = {
            'automation': 'manual',
            'displayed': [],
            'skipped': []
        }

        for coin, decision in decisions.items():
            signal = decision.get('signal', 'hold')

            if signal == 'hold':
                continue

            # Validate with risk manager
            is_valid, reason = risk_manager.validate_trade(
                model_id=model_id,
                coin=coin,
                decision=decision,
                market_data=market_data.get(coin, {})
            )

            if not is_valid:
                results['skipped'].append({
                    'coin': coin,
                    'reason': reason,
                    'decision': decision
                })
                continue

            # Display decision (don't execute)
            results['displayed'].append({
                'coin': coin,
                'signal': signal,
                'decision': decision,
                'explanation': explanations.get(coin, {}),
                'action': 'displayed_only'
            })

        return results


class SemiAutomatedHandler(AutomationHandler):
    """Semi-automated mode - create pending decisions for approval"""

    def process_decisions(self, model_id: int, decisions: Dict, market_data: Dict,
                         explanations: Dict, risk_manager) -> Dict:
        """Create pending decisions for user approval"""
        results = {
            'automation': 'semi_automated',
            'pending': [],
            'skipped': []
        }

        for coin, decision in decisions.items():
            signal = decision.get('signal', 'hold')

            if signal == 'hold':
                continue

            # Validate with risk manager
            is_valid, reason = risk_manager.validate_trade(
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


class FullyAutomatedHandler(AutomationHandler):
    """Fully automated mode - execute automatically after risk checks"""

    def __init__(self, db, notifier=None, auto_pause_checker=None):
        super().__init__(db, notifier)
        self.auto_pause_checker = auto_pause_checker

    def process_decisions(self, model_id: int, decisions: Dict, market_data: Dict,
                         explanations: Dict, risk_manager) -> Dict:
        """Auto-execute after risk validation"""
        results = {
            'automation': 'fully_automated',
            'auto_approved': [],
            'skipped': []
        }

        # Check auto-pause triggers first
        if self.auto_pause_checker:
            should_pause, pause_reason = self.auto_pause_checker(model_id)
            if should_pause:
                # Return special result indicating pause needed
                return {
                    'automation': 'paused',
                    'reason': pause_reason,
                    'auto_approved': [],
                    'skipped': []
                }

        for coin, decision in decisions.items():
            signal = decision.get('signal', 'hold')

            if signal == 'hold':
                continue

            # Validate with risk manager
            is_valid, reason = risk_manager.validate_trade(
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

            # Auto-approve
            results['auto_approved'].append({
                'coin': coin,
                'signal': signal,
                'decision': decision
            })

        return results


# ============ Unified Trading Executor ============

class TradingExecutor:
    """
    Unified trading executor using composition

    Separates concerns:
      - Environment Executor: Where to execute (Sim vs Live)
      - Automation Handler: How to process (Manual/Semi/Full)
      - Risk Manager: What's safe to execute
    """

    def __init__(self, db, risk_manager, notifier=None, explainer=None):
        """
        Args:
            db: EnhancedDatabase instance
            risk_manager: RiskManager instance
            notifier: Notifier instance (optional)
            explainer: AIExplainer instance (optional)
        """
        self.db = db
        self.risk_manager = risk_manager
        self.notifier = notifier
        self.explainer = explainer

        # Environment executors (LiveExecutor exchange client loaded per-model)
        self.executors = {
            TradingEnvironment.SIMULATION: SimulationExecutor(db),
            TradingEnvironment.LIVE: None  # Created dynamically per model
        }

        # Automation handlers
        self.handlers = {
            AutomationLevel.MANUAL: ManualHandler(db, notifier),
            AutomationLevel.SEMI_AUTOMATED: SemiAutomatedHandler(db, notifier),
            AutomationLevel.FULLY_AUTOMATED: FullyAutomatedHandler(
                db, notifier, auto_pause_checker=self._check_auto_pause_triggers
            )
        }

    def execute_trading_cycle(self, model_id: int, market_data: Dict,
                             ai_decisions: Dict) -> Dict:
        """
        Main trading cycle - mode-aware execution

        Args:
            model_id: Model ID
            market_data: Current market data
            ai_decisions: AI trading decisions

        Returns:
            Execution results
        """
        # Get environment and automation level
        environment = TradingEnvironment(self.db.get_trading_environment(model_id))
        automation = AutomationLevel(self.db.get_automation_level(model_id))

        model = self.db.get_model(model_id)
        print(f"[{environment.value.upper()}|{automation.value.upper()}] Trading cycle for {model['name']}")

        # Load exchange client for live environment
        if environment == TradingEnvironment.LIVE:
            exchange_client = self.db.get_exchange_client(model_id)
            if not exchange_client:
                print("[LIVE] WARNING: No exchange client configured - will fall back to simulation")
                self.db.log_incident(
                    model_id=model_id,
                    incident_type='EXCHANGE_NOT_CONFIGURED',
                    severity='high',
                    message='Live trading enabled but no exchange credentials configured'
                )
            # Create LiveExecutor with the exchange client
            self.executors[TradingEnvironment.LIVE] = LiveExecutor(self.db, exchange_client)

        # Get portfolio
        portfolio = self.db.get_portfolio(model_id, market_data)

        # Generate explanations
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

        # STEP 1: Automation layer processes decisions
        automation_handler = self.handlers[automation]
        processed = automation_handler.process_decisions(
            model_id=model_id,
            decisions=ai_decisions,
            market_data=market_data,
            explanations=explanations,
            risk_manager=self.risk_manager
        )

        # Handle auto-pause
        if processed.get('automation') == 'paused':
            # Pause full auto, switch to semi-auto
            self.db.set_automation_level(model_id, AutomationLevel.SEMI_AUTOMATED.value)

            self.db.log_incident(
                model_id=model_id,
                incident_type='AUTO_PAUSE',
                severity='high',
                message=f'Full auto paused: {processed["reason"]}'
            )

            if self.notifier:
                self.notifier.send_notification(
                    title="🚨 FULL AUTO PAUSED",
                    message=f'Switched to semi-auto: {processed["reason"]}',
                    priority="critical",
                    model_id=model_id
                )

            return processed

        # STEP 2: Environment layer executes approved decisions
        environment_executor = self.executors[environment]
        executed_trades = []

        # Execute auto-approved trades (full auto) or displayed trades (manual)
        trades_to_execute = processed.get('auto_approved', [])

        for trade_info in trades_to_execute:
            coin = trade_info['coin']
            decision = trade_info['decision']

            try:
                result = environment_executor.execute_trade(
                    model_id=model_id,
                    coin=coin,
                    decision=decision,
                    market_data=market_data[coin]
                )

                executed_trades.append(result)

                # Send notification
                if self.notifier and automation == AutomationLevel.FULLY_AUTOMATED:
                    self.notifier.send_notification(
                        title=f"✅ Trade Executed: {coin}",
                        message=f"{decision.get('signal').upper()} {decision.get('quantity')} @ ${market_data[coin]['price']}",
                        priority="low",
                        model_id=model_id
                    )

            except Exception as e:
                error_msg = f"Execution failed: {str(e)}"
                processed.setdefault('skipped', []).append({
                    'coin': coin,
                    'reason': error_msg
                })

                self.db.log_incident(
                    model_id=model_id,
                    incident_type='EXECUTION_ERROR',
                    severity='high',
                    message=f'Failed to execute {coin}: {str(e)}'
                )

        # Combine results
        final_result = {
            'environment': environment.value,
            'automation': automation.value,
            'executed': executed_trades,
            **processed  # Include pending, skipped, etc.
        }

        return final_result

    def approve_decision(self, decision_id: int, modified: bool = False,
                        modifications: Dict = None) -> Dict:
        """Approve a pending decision (semi-auto workflow)"""
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

        # Apply modifications
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

        # Execute using appropriate environment executor
        environment = TradingEnvironment(self.db.get_trading_environment(model_id))
        executor = self.executors[environment]

        try:
            result = executor.execute_trade(model_id, coin, decision, market_data[coin])

            # Log approval event
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO approval_events
                (decision_id, model_id, approved, modified, modification_details, execution_result)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (decision_id, model_id, True, modified,
                  json.dumps(modifications) if modifications else None,
                  json.dumps(result)))
            conn.commit()
            conn.close()

            return {'success': True, 'result': result}

        except Exception as e:
            error_msg = f"Execution failed: {str(e)}"

            # Log error
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO approval_events
                (decision_id, model_id, approved, modified, execution_result)
                VALUES (?, ?, ?, ?, ?)
            ''', (decision_id, model_id, True, modified, json.dumps({'error': error_msg})))
            conn.commit()
            conn.close()

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
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO approval_events
                (decision_id, model_id, approved, rejection_reason)
                VALUES (?, ?, ?, ?)
            ''', (decision_id, decision_data['model_id'], False, reason))
            conn.commit()
            conn.close()

        return {'success': True}

    def _check_auto_pause_triggers(self, model_id: int) -> Tuple[bool, str]:
        """Check if any auto-pause triggers are hit (for full auto)"""
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

        # Trigger 3: Daily loss limit
        portfolio = self.db.get_portfolio(model_id)
        model = self.db.get_model(model_id)
        initial_capital = model['initial_capital']

        daily_loss_pct = (portfolio['total_value'] - initial_capital) / initial_capital * 100
        threshold = settings.get('max_daily_loss_pct', 3.0)

        if daily_loss_pct < -threshold:
            return True, f"Daily loss {daily_loss_pct:.2f}% exceeds limit ({threshold}%)"

        return False, ""

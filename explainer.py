"""
AI Explainability Module
Generates human-readable explanations for AI trading decisions
"""
from typing import Dict


class AIExplainer:
    """Generate explanations for AI decisions"""

    def __init__(self, explanation_level: str = 'intermediate'):
        """
        Args:
            explanation_level: Level of detail (beginner, intermediate, advanced)
        """
        self.explanation_level = explanation_level

    def create_explanation(self, coin: str, decision: Dict,
                          market_data: Dict, portfolio: Dict) -> Dict:
        """
        Generate explanation for a trading decision

        Args:
            coin: Trading pair (e.g., 'BTC')
            decision: AI decision dict
            market_data: Current market data
            portfolio: Current portfolio state

        Returns:
            Dict with explanation components
        """
        signal = decision.get('signal', 'hold')
        quantity = decision.get('quantity', 0)
        price = market_data.get('price', 0)
        confidence = decision.get('confidence', 0)

        explanation = {
            'coin': coin,
            'decision_summary': self._format_decision_summary(coin, signal, quantity, price),
            'confidence': confidence,
            'market_analysis': self._analyze_market(coin, market_data),
            'technical_indicators': self._explain_indicators(market_data),
            'risk_assessment': self._assess_risk(decision, market_data, portfolio),
            'position_sizing': self._explain_position_sizing(decision, market_data, portfolio),
            'justification': decision.get('justification', 'No justification provided'),
            'timestamp': market_data.get('timestamp', '')
        }

        return explanation

    def _format_decision_summary(self, coin: str, signal: str,
                                 quantity: float, price: float) -> str:
        """Format decision summary string"""
        if signal == 'hold':
            return f"HOLD {coin} (no action)"
        elif signal == 'buy_to_enter':
            return f"BUY {quantity} {coin} @ ${price:,.2f}"
        elif signal == 'sell_to_enter':
            return f"SHORT {quantity} {coin} @ ${price:,.2f}"
        elif signal == 'close_position':
            return f"CLOSE {coin} position @ ${price:,.2f}"
        return f"{signal.upper()} {quantity} {coin} @ ${price:,.2f}"

    def _analyze_market(self, coin: str, market_data: Dict) -> Dict:
        """Analyze current market conditions"""
        price = market_data.get('price', 0)
        change_24h = market_data.get('change_24h', 0)

        indicators = market_data.get('indicators', {})
        sma_7 = indicators.get('sma_7', 0)
        sma_14 = indicators.get('sma_14', 0)

        analysis = {
            'current_price': price,
            'change_24h': change_24h,
            'trend': 'bullish' if change_24h > 0 else 'bearish',
            'price_vs_sma7': self._calc_percentage_diff(price, sma_7),
            'price_vs_sma14': self._calc_percentage_diff(price, sma_14)
        }

        return analysis

    def _explain_indicators(self, market_data: Dict) -> Dict:
        """Explain technical indicators"""
        indicators = market_data.get('indicators', {})

        rsi = indicators.get('rsi_14', 50)
        sma_7 = indicators.get('sma_7', 0)
        sma_14 = indicators.get('sma_14', 0)

        explanations = {
            'rsi': {
                'value': rsi,
                'interpretation': self._interpret_rsi(rsi),
                'signal': 'oversold' if rsi < 30 else 'overbought' if rsi > 70 else 'neutral'
            },
            'moving_averages': {
                'sma_7': sma_7,
                'sma_14': sma_14,
                'crossover': 'bullish' if sma_7 > sma_14 else 'bearish',
                'interpretation': 'Short-term trend is above long-term' if sma_7 > sma_14 else 'Short-term trend is below long-term'
            }
        }

        return explanations

    def _assess_risk(self, decision: Dict, market_data: Dict, portfolio: Dict) -> Dict:
        """Assess risk for this decision"""
        quantity = decision.get('quantity', 0)
        price = market_data.get('price', 0)
        stop_loss = decision.get('stop_loss', 0)
        take_profit = decision.get('profit_target', 0)

        position_value = quantity * price
        portfolio_value = portfolio.get('total_value', 10000)

        # Calculate risk
        if stop_loss and price:
            risk_per_unit = abs(price - stop_loss)
            total_risk = risk_per_unit * quantity
            risk_pct = (total_risk / portfolio_value) * 100
        else:
            risk_pct = 2.0  # Default assumption

        # Calculate reward
        if take_profit and price:
            reward_per_unit = abs(take_profit - price)
            total_reward = reward_per_unit * quantity
            reward_pct = (total_reward / portfolio_value) * 100
        else:
            reward_pct = 4.0  # Default assumption

        risk_reward_ratio = reward_pct / risk_pct if risk_pct > 0 else 0

        return {
            'position_size': position_value,
            'position_size_pct': (position_value / portfolio_value) * 100,
            'risk_amount': total_risk if stop_loss else position_value * 0.02,
            'risk_pct': risk_pct,
            'potential_reward': total_reward if take_profit else position_value * 0.04,
            'reward_pct': reward_pct,
            'risk_reward_ratio': risk_reward_ratio,
            'stop_loss': stop_loss,
            'take_profit': take_profit
        }

    def _explain_position_sizing(self, decision: Dict, market_data: Dict,
                                 portfolio: Dict) -> Dict:
        """Explain position sizing logic"""
        quantity = decision.get('quantity', 0)
        price = market_data.get('price', 0)
        position_value = quantity * price
        portfolio_value = portfolio.get('total_value', 10000)

        return {
            'portfolio_value': portfolio_value,
            'position_value': position_value,
            'position_pct': (position_value / portfolio_value) * 100,
            'quantity': quantity,
            'price': price,
            'explanation': f"Position size of ${position_value:,.0f} is {(position_value/portfolio_value)*100:.1f}% of portfolio"
        }

    def _interpret_rsi(self, rsi: float) -> str:
        """Interpret RSI value"""
        if rsi < 30:
            return f"RSI at {rsi:.1f} indicates oversold conditions. Price may bounce up."
        elif rsi > 70:
            return f"RSI at {rsi:.1f} indicates overbought conditions. Price may pull back."
        else:
            return f"RSI at {rsi:.1f} is in neutral zone. No extreme conditions."

    def _calc_percentage_diff(self, price: float, reference: float) -> float:
        """Calculate percentage difference"""
        if reference == 0:
            return 0
        return ((price - reference) / reference) * 100

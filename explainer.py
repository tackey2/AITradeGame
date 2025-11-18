"""
AI Explainability Module
Generates human-readable explanations for AI trading decisions
With chain-of-thought tracking and AI-as-judge reasoning evaluation
"""
from typing import Dict, Optional
import json


class AIExplainer:
    """Generate explanations for AI decisions with reasoning evaluation"""

    def __init__(self, ai_trader=None, explanation_level: str = 'intermediate'):
        """
        Args:
            ai_trader: AITrader instance for AI-powered evaluation (optional)
            explanation_level: Level of detail (beginner, intermediate, advanced)
        """
        self.ai_trader = ai_trader
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

    def evaluate_reasoning(self, decision: Dict, cot_trace: str, market_data: Dict) -> Dict:
        """
        Use AI to evaluate the quality of reasoning in a trading decision

        Args:
            decision: The trading decision dict
            cot_trace: Chain of thought reasoning trace
            market_data: Market data context

        Returns:
            Dict with reasoning quality scores and feedback
        """
        # If no AI trader available, fall back to rule-based scoring
        if not self.ai_trader or not cot_trace:
            return self._rule_based_scoring(decision, cot_trace, market_data)

        try:
            # Prepare evaluation prompt for AI
            eval_prompt = self._create_evaluation_prompt(decision, cot_trace, market_data)

            # Call AI to evaluate reasoning
            response = self.ai_trader._call_llm(eval_prompt, 'reasoning_evaluation')

            # Parse AI evaluation response
            evaluation = self._parse_evaluation_response(response)

            return evaluation

        except Exception as e:
            print(f"AI evaluation failed, using rule-based: {e}")
            return self._rule_based_scoring(decision, cot_trace, market_data)

    def _create_evaluation_prompt(self, decision: Dict, cot_trace: str, market_data: Dict) -> str:
        """Create prompt for AI to evaluate reasoning quality"""

        signal = decision.get('signal', 'unknown')
        coin = decision.get('coin', 'unknown')
        price = market_data.get('price', 0)

        prompt = f"""You are an expert trading analyst evaluating the quality of AI trading reasoning.

TRADING DECISION:
- Coin: {coin}
- Signal: {signal}
- Price: ${price:,.2f}
- Confidence: {decision.get('confidence', 0)}

MARKET CONTEXT:
- 24h Change: {market_data.get('change_24h', 0):.2f}%
- RSI: {market_data.get('indicators', {}).get('rsi_14', 'N/A')}
- Volume: {market_data.get('volume_24h', 'N/A')}

REASONING PROVIDED:
{cot_trace}

EVALUATION TASK:
Evaluate this trading reasoning on a scale of 1-5 for each dimension:

1. **Logical Consistency** (1-5): Does the reasoning flow logically? Are there contradictions?
2. **Evidence Usage** (1-5): Does it reference market data and indicators properly?
3. **Risk Awareness** (1-5): Does it consider potential downsides and risks?
4. **Clarity** (1-5): Is the explanation clear and understandable?

Provide your evaluation in this EXACT JSON format:
{{
    "logical_consistency": <score 1-5>,
    "evidence_usage": <score 1-5>,
    "risk_awareness": <score 1-5>,
    "clarity": <score 1-5>,
    "overall_score": <average score>,
    "feedback": "<brief 1-2 sentence evaluation>",
    "strengths": "<what was done well>",
    "weaknesses": "<what could be improved>"
}}

IMPORTANT: Return ONLY the JSON, no other text."""

        return prompt

    def _parse_evaluation_response(self, response: str) -> Dict:
        """Parse AI evaluation response into structured format"""
        try:
            # Try to extract JSON from response
            response_text = response
            if hasattr(response, 'choices'):
                response_text = response.choices[0].message.content

            # Clean up response - remove markdown code blocks if present
            response_text = response_text.strip()
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])

            # Parse JSON
            evaluation = json.loads(response_text)

            # Validate scores are in range
            for key in ['logical_consistency', 'evidence_usage', 'risk_awareness', 'clarity']:
                score = evaluation.get(key, 3)
                evaluation[key] = max(1, min(5, score))

            # Calculate overall score if not provided
            if 'overall_score' not in evaluation:
                scores = [
                    evaluation.get('logical_consistency', 3),
                    evaluation.get('evidence_usage', 3),
                    evaluation.get('risk_awareness', 3),
                    evaluation.get('clarity', 3)
                ]
                evaluation['overall_score'] = sum(scores) / len(scores)

            return evaluation

        except Exception as e:
            print(f"Failed to parse AI evaluation: {e}")
            # Return default neutral evaluation
            return {
                'logical_consistency': 3,
                'evidence_usage': 3,
                'risk_awareness': 3,
                'clarity': 3,
                'overall_score': 3.0,
                'feedback': 'Could not evaluate reasoning automatically.',
                'strengths': 'N/A',
                'weaknesses': 'N/A'
            }

    def _rule_based_scoring(self, decision: Dict, cot_trace: str, market_data: Dict) -> Dict:
        """
        Fallback rule-based scoring when AI evaluation is not available
        Simple heuristics based on reasoning length and keyword presence
        """
        if not cot_trace:
            return {
                'logical_consistency': 1,
                'evidence_usage': 1,
                'risk_awareness': 1,
                'clarity': 1,
                'overall_score': 1.0,
                'feedback': 'No reasoning provided.',
                'strengths': 'N/A',
                'weaknesses': 'No chain of thought trace available'
            }

        cot_lower = cot_trace.lower()
        cot_length = len(cot_trace)

        # Logical consistency - based on length and structure
        logical_score = 3
        if cot_length > 500:
            logical_score += 1
        if any(word in cot_lower for word in ['because', 'therefore', 'thus', 'since']):
            logical_score += 1
        logical_score = min(5, logical_score)

        # Evidence usage - check for data references
        evidence_score = 2
        evidence_keywords = ['price', 'rsi', 'volume', 'trend', 'indicator', 'moving average', 'support', 'resistance']
        evidence_count = sum(1 for keyword in evidence_keywords if keyword in cot_lower)
        evidence_score = min(5, 2 + evidence_count // 2)

        # Risk awareness - check for risk mentions
        risk_score = 2
        risk_keywords = ['risk', 'loss', 'stop', 'downside', 'volatility', 'drawdown']
        risk_count = sum(1 for keyword in risk_keywords if keyword in cot_lower)
        risk_score = min(5, 2 + risk_count)

        # Clarity - based on length and readability
        clarity_score = 3
        if 200 < cot_length < 1000:  # Not too short, not too long
            clarity_score += 1
        if cot_lower.count('.') > 2:  # Multiple sentences
            clarity_score += 1
        clarity_score = min(5, clarity_score)

        overall_score = (logical_score + evidence_score + risk_score + clarity_score) / 4

        # Generate feedback
        feedback_parts = []
        if overall_score >= 4:
            feedback_parts.append("Strong reasoning quality.")
        elif overall_score >= 3:
            feedback_parts.append("Adequate reasoning provided.")
        else:
            feedback_parts.append("Reasoning could be improved.")

        if evidence_score < 3:
            feedback_parts.append("Lacks market data references.")
        if risk_score < 3:
            feedback_parts.append("Risk assessment needed.")

        return {
            'logical_consistency': logical_score,
            'evidence_usage': evidence_score,
            'risk_awareness': risk_score,
            'clarity': clarity_score,
            'overall_score': round(overall_score, 2),
            'feedback': ' '.join(feedback_parts),
            'strengths': 'Rule-based evaluation',
            'weaknesses': 'Consider adding more detail and market analysis'
        }

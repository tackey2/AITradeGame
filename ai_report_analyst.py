"""
AI Report Analyst
Uses AI to generate narrative analysis from report metrics
"""
import requests
import json
from typing import Dict, List, Optional


class AIReportAnalyst:
    """Generate AI-powered narrative analysis for reports"""

    def __init__(self, provider: str = 'anthropic', model: str = 'claude-sonnet-3.5',
                 api_key: str = None, api_url: str = None):
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.api_url = api_url or self._get_default_url(provider)

    def _get_default_url(self, provider: str) -> str:
        """Get default API URL for provider"""
        if provider == 'anthropic':
            return 'https://api.anthropic.com/v1'
        elif provider == 'openai':
            return 'https://api.openai.com/v1'
        else:
            return api_url

    def generate_executive_summary(self, report_data: Dict) -> str:
        """Generate executive summary with AI recommendation"""

        top_model = report_data['models'][0] if report_data['models'] else None

        if not top_model:
            return "No models available for analysis."

        prompt = f"""You are a professional trading analyst reviewing AI trading models.

Analyze these metrics and provide a clear, concise executive summary:

Model: {top_model['model_name']}
Period: {report_data['period_start']} to {report_data['period_end']}

Performance Metrics:
- Net ROI: {top_model['performance']['net_roi']}%
- Win Rate: {top_model['performance']['win_rate']}%
- Sharpe Ratio: {top_model['performance']['sharpe_ratio']}
- Max Drawdown: {top_model['performance']['max_drawdown']}%
- Total Trades: {top_model['performance']['total_trades']}

Risk & Compliance:
- Risk Violations: {top_model['risk']['total_violations']}
- Compliance Rate: {top_model['risk']['compliance_rate']}%

Costs:
- Total Trading Costs: ${top_model['performance']['costs']['total']}
- Cost Impact: {top_model['performance']['costs']['impact_pct']}%

Market Context:
- BTC Performance: {report_data['market_context']['btc_performance']['change_pct']}%
- Market Regime: {report_data['market_context']['market_regime']}

Generate a 4-5 paragraph executive summary that:
1. Opens with a clear recommendation (Ready for Live Trading / Continue Testing / Not Ready)
2. Explains WHY this is the recommendation based on the metrics
3. Highlights key strengths
4. Mentions any concerns or risks
5. Provides specific, actionable next steps

Write in a professional but conversational tone. Focus on insights, not just repeating numbers."""

        analysis = self._call_ai(prompt)
        return analysis if analysis else self._fallback_executive_summary(top_model, report_data)

    def generate_comparative_analysis(self, models: List[Dict]) -> str:
        """Generate head-to-head comparative analysis"""

        if len(models) < 2:
            return "Insufficient models for comparison."

        prompt = f"""You are a professional trading analyst comparing multiple AI trading models.

Compare these {len(models)} models and explain which is best and why:

"""
        for i, model in enumerate(models[:3], 1):  # Top 3 models
            prompt += f"""
Model #{i}: {model['model_name']} (Score: {model['score']}/100, Rank: {model['rank']})
- Net ROI: {model['performance']['net_roi']}%
- Win Rate: {model['performance']['win_rate']}%
- Sharpe Ratio: {model['performance']['sharpe_ratio']}
- Risk Violations: {model['risk']['total_violations']}
"""

        prompt += """
Provide a 2-3 paragraph comparative analysis that:
1. Explains why Model #1 ranks highest
2. Compares Model #1 to the alternatives (strengths vs weaknesses)
3. Identifies the best use case for each model (e.g., "Model #1 for returns, Model #2 for safety")

Be specific and insightful, not just stating obvious differences."""

        analysis = self._call_ai(prompt)
        return analysis if analysis else self._fallback_comparative_analysis(models)

    def generate_risk_assessment(self, top_model: Dict, market_context: Dict) -> str:
        """Generate risk assessment and what could go wrong"""

        prompt = f"""You are a professional risk analyst reviewing an AI trading model.

Model: {top_model['model_name']}

Performance:
- Net ROI: {top_model['performance']['net_roi']}%
- Max Drawdown: {top_model['performance']['max_drawdown']}%
- Total Trades: {top_model['performance']['total_trades']}
- Win Rate: {top_model['performance']['win_rate']}%

Market Context:
- Tested in: {market_context['market_regime']}
- BTC Performance: {market_context['btc_performance']['change_pct']}%
- Market Volatility: {market_context['btc_performance']['volatility']}%

Provide a balanced risk assessment (2-3 paragraphs) that addresses:
1. What could go wrong if this model goes live?
2. Market regime dependency (will it perform differently in bear markets?)
3. Sample size concerns ({top_model['performance']['total_trades']} trades - is this enough?)
4. Any red flags in the data
5. Specific risks to monitor

Be honest and objective - don't sugarcoat risks."""

        analysis = self._call_ai(prompt)
        return analysis if analysis else self._fallback_risk_assessment(top_model, market_context)

    def generate_metrics_interpretation(self, models: List[Dict]) -> str:
        """Generate interpretation of key metrics"""

        if not models:
            return "No models available for interpretation."

        top_model = models[0]

        prompt = f"""You are explaining trading metrics to someone who understands basics but wants deeper insight.

Model: {top_model['model_name']}

Key Metrics:
- Net ROI: {top_model['performance']['net_roi']}% (after all costs)
- Win Rate: {top_model['performance']['win_rate']}%
- Sharpe Ratio: {top_model['performance']['sharpe_ratio']}
- Max Drawdown: {top_model['performance']['max_drawdown']}%
- Risk Violations: {top_model['risk']['total_violations']}

Explain in 1-2 paragraphs what these numbers MEAN in plain English:
- Why is this performance good/bad?
- What do the numbers tell us about the model's decision-making?
- Is the model profitable AND safe, or just one or the other?

Don't just define the metrics - explain what they reveal about THIS specific model."""

        analysis = self._call_ai(prompt)
        return analysis if analysis else self._fallback_metrics_interpretation(top_model)

    def _call_ai(self, prompt: str) -> Optional[str]:
        """Make API call to AI provider"""
        try:
            if not self.api_key:
                print("[WARN] No API key configured for AI analyst")
                return None

            if self.provider == 'anthropic':
                return self._call_anthropic(prompt)
            elif self.provider == 'openai':
                return self._call_openai(prompt)
            else:
                return self._call_generic(prompt)

        except Exception as e:
            print(f"[ERROR] AI analysis failed: {e}")
            return None

    def _call_anthropic(self, prompt: str) -> Optional[str]:
        """Call Anthropic Claude API"""
        headers = {
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        }

        payload = {
            'model': self.model,
            'max_tokens': 1024,
            'messages': [
                {'role': 'user', 'content': prompt}
            ]
        }

        response = requests.post(
            f'{self.api_url}/messages',
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()['content'][0]['text']
        else:
            print(f"[ERROR] Anthropic API error: {response.status_code}")
            return None

    def _call_openai(self, prompt: str) -> Optional[str]:
        """Call OpenAI API"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': self.model,
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 1024,
            'temperature': 0.7
        }

        response = requests.post(
            f'{self.api_url}/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            print(f"[ERROR] OpenAI API error: {response.status_code}")
            return None

    def _call_generic(self, prompt: str) -> Optional[str]:
        """Call generic OpenAI-compatible API"""
        return self._call_openai(prompt)  # Same format

    # Fallback methods when AI is unavailable

    def _fallback_executive_summary(self, model: Dict, report_data: Dict) -> str:
        """Template-based executive summary"""
        roi = model['performance']['net_roi']
        violations = model['risk']['total_violations']
        win_rate = model['performance']['win_rate']

        if roi > 10 and violations == 0 and win_rate > 55:
            recommendation = "✅ READY FOR LIVE TRADING"
            explanation = f"{model['model_name']} demonstrates strong performance with {roi}% net ROI, {win_rate}% win rate, and zero risk violations. This model is ready for live trading with appropriate safeguards."
        elif roi > 5 and violations <= 2:
            recommendation = "⚠️ CONTINUE TESTING"
            explanation = f"{model['model_name']} shows promising results with {roi}% net ROI, but needs more validation before going live."
        else:
            recommendation = "❌ NOT READY"
            explanation = f"{model['model_name']} requires further optimization before live trading. Key concerns: ROI {roi}%, {violations} violations."

        return f"""{recommendation}

{explanation}

Key Highlights:
• Net ROI: {roi}% after all costs
• Win Rate: {win_rate}%
• Risk Violations: {violations}
• Market Conditions: {report_data['market_context']['market_regime']}

The model has executed {model['performance']['total_trades']} trades during this period with consistent risk management."""

    def _fallback_comparative_analysis(self, models: List[Dict]) -> str:
        """Template-based comparative analysis"""
        if len(models) < 2:
            return "Insufficient models for comparison."

        model1 = models[0]
        model2 = models[1]

        return f"""{model1['model_name']} ranks #1 with a score of {model1['score']}/100, outperforming {model2['model_name']} (score: {model2['score']}/100).

The key differentiator is performance: {model1['model_name']} achieved {model1['performance']['net_roi']}% net ROI compared to {model2['model_name']}'s {model2['performance']['net_roi']}%. Additionally, {model1['model_name']} has {'zero' if model1['risk']['total_violations'] == 0 else model1['risk']['total_violations']} risk violations, demonstrating better risk discipline.

For risk-averse traders, {model2['model_name']} may be preferable if it has lower drawdown. For growth-focused traders, {model1['model_name']} is the clear choice."""

    def _fallback_risk_assessment(self, model: Dict, market_context: Dict) -> str:
        """Template-based risk assessment"""
        return f"""This model was tested during {market_context['market_regime']} conditions. Performance may differ in other market environments.

Key Risks:
• Limited sample size: {model['performance']['total_trades']} trades provides good initial data but more validation is recommended
• Max drawdown of {model['performance']['max_drawdown']}% indicates potential volatility
• Market regime dependency: Tested primarily in {'bullish' if market_context['btc_performance']['change_pct'] > 0 else 'bearish'} conditions

Recommendation: Start with small capital ($500-1000) and monitor daily for the first 2 weeks."""

    def _fallback_metrics_interpretation(self, model: Dict) -> str:
        """Template-based metrics interpretation"""
        return f"""The {model['performance']['net_roi']}% net ROI indicates this model is profitable after accounting for all costs. The {model['performance']['win_rate']}% win rate means the model makes profitable decisions more often than not.

The Sharpe ratio of {model['performance']['sharpe_ratio']} suggests {'good' if model['performance']['sharpe_ratio'] > 1.5 else 'moderate'} risk-adjusted returns. With {model['risk']['total_violations']} risk violations, the model demonstrates {'excellent' if model['risk']['total_violations'] == 0 else 'acceptable'} discipline in following risk parameters."""


# For testing
if __name__ == '__main__':
    # Test with sample data
    analyst = AIReportAnalyst()

    sample_data = {
        'period_start': '2024-11-11',
        'period_end': '2024-11-17',
        'models': [{
            'model_name': 'GPT-4 Trader',
            'score': 87,
            'rank': 1,
            'performance': {
                'net_roi': 12.3,
                'win_rate': 58,
                'sharpe_ratio': 1.8,
                'max_drawdown': 15.2,
                'total_trades': 42,
                'costs': {'total': 42, 'impact_pct': 2.1}
            },
            'risk': {
                'total_violations': 0,
                'compliance_rate': 100
            }
        }],
        'market_context': {
            'btc_performance': {'change_pct': 12.5, 'volatility': 3.2},
            'market_regime': 'Bullish with moderate volatility'
        }
    }

    print("Executive Summary:")
    print(analyst.generate_executive_summary(sample_data))

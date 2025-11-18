import json
from typing import Dict, Optional
from openai import OpenAI, APIConnectionError, APIError

class AITrader:
    def __init__(self, api_key: str, api_url: str, model_name: str,
                 db=None, model_id: Optional[int] = None):
        self.api_key = api_key
        self.api_url = api_url
        self.model_name = model_name
        self.db = db
        self.model_id = model_id

        # OpenRouter pricing (per 1M tokens) - Update as needed
        self.pricing = {
            'z-ai/glm-4.6': {'input': 1.0, 'output': 1.0},  # $1 per 1M tokens (estimate)
            'minimax/minimax-m2': {'input': 0.5, 'output': 0.5},  # $0.5 per 1M tokens (estimate)
            'default': {'input': 2.0, 'output': 2.0}  # Default fallback pricing
        }
    
    def make_decision(self, market_state: Dict, portfolio: Dict,
                     account_info: Dict, include_reasoning: bool = True) -> Dict:
        """
        Make trading decision with optional chain-of-thought reasoning

        Args:
            market_state: Current market data
            portfolio: Current portfolio state
            account_info: Account information
            include_reasoning: Whether to request chain-of-thought reasoning

        Returns:
            Dict with decisions and optional 'reasoning' field
        """
        prompt = self._build_prompt(market_state, portfolio, account_info, include_reasoning)

        response = self._call_llm(prompt, cost_type='decision')

        # Parse response and extract reasoning if included
        result = self._parse_response_with_reasoning(response, include_reasoning)

        return result
    
    def _build_prompt(self, market_state: Dict, portfolio: Dict,
                     account_info: Dict, include_reasoning: bool = True) -> str:
        """Build prompt with optional chain-of-thought reasoning"""

        prompt = f"""You are a professional cryptocurrency trader. Analyze the market and make trading decisions.

MARKET DATA:
"""
        for coin, data in market_state.items():
            prompt += f"{coin}: ${data['price']:.2f} ({data['change_24h']:+.2f}%)\n"
            if 'indicators' in data and data['indicators']:
                indicators = data['indicators']
                prompt += f"  SMA7: ${indicators.get('sma_7', 0):.2f}, SMA14: ${indicators.get('sma_14', 0):.2f}, RSI: {indicators.get('rsi_14', 0):.1f}\n"

        prompt += f"""
ACCOUNT STATUS:
- Initial Capital: ${account_info['initial_capital']:.2f}
- Total Value: ${portfolio['total_value']:.2f}
- Cash: ${portfolio['cash']:.2f}
- Total Return: {account_info['total_return']:.2f}%

CURRENT POSITIONS:
"""
        if portfolio['positions']:
            for pos in portfolio['positions']:
                prompt += f"- {pos['coin']} {pos['side']}: {pos['quantity']:.4f} @ ${pos['avg_price']:.2f} ({pos['leverage']}x)\n"
        else:
            prompt += "None\n"

        prompt += """
TRADING RULES:
1. Signals: buy_to_enter (long), sell_to_enter (short), close_position, hold
2. Risk Management:
   - Max 3 positions
   - Risk 1-5% per trade
   - Use appropriate leverage (1-20x)
3. Position Sizing:
   - Conservative: 1-2% risk
   - Moderate: 2-4% risk
   - Aggressive: 4-5% risk
4. Exit Strategy:
   - Close losing positions quickly
   - Let winners run
   - Use technical indicators
"""

        if include_reasoning:
            prompt += """
REASONING PROCESS:
Before making your decision, think through the following:
1. What are the key market signals I'm seeing? (trend, momentum, volume)
2. What risks do I see in each potential trade?
3. Why is this the right position size given current portfolio state?
4. How confident am I in this decision and why?
5. What's my exit strategy if the trade goes against me?

Provide your reasoning, then output your decisions.

OUTPUT FORMAT:
```json
{
  "reasoning": "Your step-by-step thought process (2-4 sentences explaining your analysis and decision logic)",
  "decisions": {
    "COIN": {
      "signal": "buy_to_enter|sell_to_enter|hold|close_position",
      "quantity": 0.5,
      "leverage": 10,
      "profit_target": 45000.0,
      "stop_loss": 42000.0,
      "confidence": 0.75,
      "justification": "Brief reason"
    }
  }
}
```
"""
        else:
            prompt += """
OUTPUT FORMAT (JSON only):
```json
{
  "COIN": {
    "signal": "buy_to_enter|sell_to_enter|hold|close_position",
    "quantity": 0.5,
    "leverage": 10,
    "profit_target": 45000.0,
    "stop_loss": 42000.0,
    "confidence": 0.75,
    "justification": "Brief reason"
  }
}
```
"""

        prompt += "\nAnalyze and output JSON only."

        return prompt
    
    def _call_llm(self, prompt: str, cost_type: str = 'other') -> str:
        """
        Call LLM API with cost tracking

        Args:
            prompt: The prompt to send
            cost_type: Type of operation for cost tracking (decision, evaluation, etc.)

        Returns:
            Response text from LLM
        """
        try:
            base_url = self.api_url.rstrip('/')
            if not base_url.endswith('/v1'):
                if '/v1' in base_url:
                    base_url = base_url.split('/v1')[0] + '/v1'
                else:
                    base_url = base_url + '/v1'

            client = OpenAI(
                api_key=self.api_key,
                base_url=base_url
            )

            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional cryptocurrency trader. Output JSON format only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )

            # Track AI costs if database is available
            if self.db and self.model_id:
                self._track_cost(response, cost_type)

            return response.choices[0].message.content

        except APIConnectionError as e:
            error_msg = f"API connection failed: {str(e)}"
            print(f"[ERROR] {error_msg}")
            raise Exception(error_msg)
        except APIError as e:
            error_msg = f"API error ({e.status_code}): {e.message}"
            print(f"[ERROR] {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"LLM call failed: {str(e)}"
            print(f"[ERROR] {error_msg}")
            import traceback
            print(traceback.format_exc())
            raise Exception(error_msg)
    
    def _parse_response(self, response: str) -> Dict:
        response = response.strip()

        if '```json' in response:
            response = response.split('```json')[1].split('```')[0]
        elif '```' in response:
            response = response.split('```')[1].split('```')[0]

        try:
            decisions = json.loads(response.strip())
            return decisions
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON parse failed: {e}")
            print(f"[DATA] Response:\n{response}")
            return {}

    def _parse_response_with_reasoning(self, response: str, include_reasoning: bool) -> Dict:
        """
        Parse response and extract chain-of-thought reasoning if present

        Args:
            response: Raw LLM response
            include_reasoning: Whether reasoning was requested

        Returns:
            Dict with 'decisions' and optional 'reasoning' field
        """
        parsed = self._parse_response(response)

        if not include_reasoning or not parsed:
            # Return decisions in expected format
            return parsed if parsed else {}

        # Check if response has the new format with reasoning
        if 'reasoning' in parsed and 'decisions' in parsed:
            # New format: {"reasoning": "...", "decisions": {...}}
            return {
                'reasoning': parsed.get('reasoning', ''),
                **parsed.get('decisions', {})
            }
        else:
            # Old format or no reasoning provided - return as-is
            return parsed

    def _track_cost(self, response, cost_type: str):
        """Track AI API costs in database"""
        try:
            # Extract token usage from response
            usage = response.usage
            if not usage:
                return

            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens

            # Get pricing for this model
            pricing = self.pricing.get(self.model_name, self.pricing['default'])

            # Calculate cost (pricing is per 1M tokens)
            input_cost = (prompt_tokens / 1_000_000) * pricing['input']
            output_cost = (completion_tokens / 1_000_000) * pricing['output']
            total_cost = input_cost + output_cost

            # Determine provider from API URL
            provider = 'openrouter' if 'openrouter' in self.api_url.lower() else 'openai'

            # Store in database
            self.db.add_ai_cost(
                model_id=self.model_id,
                cost_type=cost_type,
                tokens_used=total_tokens,
                cost_usd=total_cost,
                provider=provider,
                model_name=self.model_name
            )

            print(f"[COST] AI API: {total_tokens} tokens, ${total_cost:.6f} ({cost_type})")

        except Exception as e:
            # Don't fail the trading decision if cost tracking fails
            print(f"[WARN] Failed to track AI cost: {e}")

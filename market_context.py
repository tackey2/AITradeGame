"""
Market Context Fetcher for Report Generation
Fetches real market data from CoinGecko API with rate limiting
"""
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

class MarketContextFetcher:
    """Fetch market context data from CoinGecko API"""

    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.last_request_time = 0
        self.min_request_interval = 1.5  # 1.5 seconds between requests (free tier: ~30 calls/min)

        # Coin ID mapping
        self.coin_ids = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'SOL': 'solana',
            'BNB': 'binancecoin',
            'XRP': 'ripple',
            'DOGE': 'dogecoin'
        }

    def _rate_limit(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)

        self.last_request_time = time.time()

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make rate-limited API request"""
        self._rate_limit()

        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Too Many Requests
                print("[WARN] CoinGecko rate limit hit, waiting 60 seconds...")
                time.sleep(60)
                return self._make_request(endpoint, params)  # Retry once
            else:
                print(f"[ERROR] CoinGecko API error: {response.status_code}")
                return None

        except Exception as e:
            print(f"[ERROR] CoinGecko request failed: {e}")
            return None

    def get_current_prices(self, coins: List[str] = None) -> Dict:
        """
        Get current prices for coins

        Args:
            coins: List of coin symbols (e.g., ['BTC', 'ETH'])

        Returns:
            Dict with coin symbols as keys and price data as values
        """
        if coins is None:
            coins = list(self.coin_ids.keys())

        coin_ids = [self.coin_ids[coin] for coin in coins if coin in self.coin_ids]
        if not coin_ids:
            return {}

        params = {
            'ids': ','.join(coin_ids),
            'vs_currencies': 'usd',
            'include_market_cap': 'true',
            'include_24hr_vol': 'true',
            'include_24hr_change': 'true'
        }

        data = self._make_request('simple/price', params)

        if not data:
            return {}

        # Convert to our format
        result = {}
        for coin_symbol, coin_id in self.coin_ids.items():
            if coin_symbol in coins and coin_id in data:
                result[coin_symbol] = {
                    'price': data[coin_id]['usd'],
                    'market_cap': data[coin_id].get('usd_market_cap', 0),
                    'volume_24h': data[coin_id].get('usd_24h_vol', 0),
                    'change_24h': data[coin_id].get('usd_24h_change', 0)
                }

        return result

    def get_historical_price(self, coin: str, date: datetime) -> Optional[float]:
        """
        Get historical price for a specific date

        Args:
            coin: Coin symbol (e.g., 'BTC')
            date: Date for historical price

        Returns:
            Price in USD or None if not found
        """
        if coin not in self.coin_ids:
            return None

        coin_id = self.coin_ids[coin]
        date_str = date.strftime('%d-%m-%Y')

        params = {
            'date': date_str,
            'localization': 'false'
        }

        data = self._make_request(f'coins/{coin_id}/history', params)

        if data and 'market_data' in data:
            return data['market_data']['current_price'].get('usd')

        return None

    def get_price_range(self, coin: str, days: int) -> Optional[Dict]:
        """
        Get price data for the last N days

        Args:
            coin: Coin symbol (e.g., 'BTC')
            days: Number of days to fetch (1-90 for free tier)

        Returns:
            Dict with prices, market caps, and volumes
        """
        if coin not in self.coin_ids:
            return None

        coin_id = self.coin_ids[coin]

        params = {
            'vs_currency': 'usd',
            'days': min(days, 90),  # Free tier limit
            'interval': 'daily'
        }

        data = self._make_request(f'coins/{coin_id}/market_chart', params)

        if not data:
            return None

        return {
            'prices': data.get('prices', []),
            'market_caps': data.get('market_caps', []),
            'total_volumes': data.get('total_volumes', [])
        }

    def get_market_context(self, period_start: str, period_end: str) -> Dict:
        """
        Get comprehensive market context for a period

        Args:
            period_start: Start date (YYYY-MM-DD)
            period_end: End date (YYYY-MM-DD)

        Returns:
            Dict with market performance and regime analysis
        """
        try:
            start_date = datetime.strptime(period_start, '%Y-%m-%d')
            end_date = datetime.strptime(period_end, '%Y-%m-%d')
            days = (end_date - start_date).days + 1

            # Get BTC and ETH data (main market indicators)
            btc_data = self.get_price_range('BTC', days + 1)
            eth_data = self.get_price_range('ETH', days + 1)

            if not btc_data or not eth_data:
                return self._get_fallback_context()

            # Calculate BTC performance
            btc_prices = [p[1] for p in btc_data['prices']]
            btc_start = btc_prices[0]
            btc_end = btc_prices[-1]
            btc_change_pct = ((btc_end - btc_start) / btc_start * 100) if btc_start > 0 else 0
            btc_high = max(btc_prices)
            btc_low = min(btc_prices)

            # Calculate ETH performance
            eth_prices = [p[1] for p in eth_data['prices']]
            eth_start = eth_prices[0]
            eth_end = eth_prices[-1]
            eth_change_pct = ((eth_end - eth_start) / eth_start * 100) if eth_start > 0 else 0

            # Calculate volatility (standard deviation of daily changes)
            btc_daily_changes = [(btc_prices[i] - btc_prices[i-1]) / btc_prices[i-1] * 100
                                 for i in range(1, len(btc_prices))]
            btc_volatility = self._calculate_std_dev(btc_daily_changes)

            # Determine market regime
            regime = self._determine_market_regime(btc_change_pct, btc_volatility)

            # Fear & Greed approximation (simplified)
            fear_greed = self._estimate_fear_greed(btc_change_pct, btc_volatility)

            return {
                'btc_performance': {
                    'start_price': btc_start,
                    'end_price': btc_end,
                    'change_pct': round(btc_change_pct, 2),
                    'high': btc_high,
                    'low': btc_low,
                    'volatility': round(btc_volatility, 2)
                },
                'eth_performance': {
                    'start_price': eth_start,
                    'end_price': eth_end,
                    'change_pct': round(eth_change_pct, 2)
                },
                'market_regime': regime,
                'fear_greed_estimate': fear_greed,
                'period_days': days
            }

        except Exception as e:
            print(f"[ERROR] Failed to get market context: {e}")
            return self._get_fallback_context()

    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if not values:
            return 0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    def _determine_market_regime(self, btc_change: float, volatility: float) -> str:
        """Determine market regime based on BTC performance and volatility"""
        if btc_change > 5 and volatility < 3:
            return "Bullish with low volatility"
        elif btc_change > 5:
            return "Bullish with high volatility"
        elif btc_change < -5 and volatility < 3:
            return "Bearish with low volatility"
        elif btc_change < -5:
            return "Bearish with high volatility"
        elif volatility > 5:
            return "Sideways with high volatility"
        else:
            return "Sideways with moderate volatility"

    def _estimate_fear_greed(self, btc_change: float, volatility: float) -> int:
        """Estimate fear & greed index (0-100) based on price and volatility"""
        # Simplified calculation
        base_score = 50  # Neutral

        # Price component (+/- 30)
        price_score = min(max(btc_change * 3, -30), 30)

        # Volatility component (-20 for high vol, +10 for low vol)
        if volatility > 5:
            vol_score = -20
        elif volatility < 2:
            vol_score = 10
        else:
            vol_score = 0

        score = base_score + price_score + vol_score
        return int(min(max(score, 0), 100))

    def _get_fallback_context(self) -> Dict:
        """Return fallback context when API fails"""
        return {
            'btc_performance': {
                'start_price': 0,
                'end_price': 0,
                'change_pct': 0,
                'high': 0,
                'low': 0,
                'volatility': 0
            },
            'eth_performance': {
                'start_price': 0,
                'end_price': 0,
                'change_pct': 0
            },
            'market_regime': 'Unknown (API unavailable)',
            'fear_greed_estimate': 50,
            'period_days': 0,
            'error': 'Failed to fetch market data'
        }


# For testing
if __name__ == '__main__':
    fetcher = MarketContextFetcher()

    # Test current prices
    print("Testing current prices...")
    prices = fetcher.get_current_prices(['BTC', 'ETH'])
    print(json.dumps(prices, indent=2))

    # Test market context
    print("\nTesting market context...")
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    context = fetcher.get_market_context(
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )
    print(json.dumps(context, indent=2))

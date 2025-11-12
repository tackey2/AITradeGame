"""
Binance Exchange Client

Handles all interactions with Binance exchange (both Testnet and Mainnet).
Supports spot trading with market and limit orders.

Safety Features:
- Testnet mode for safe testing
- Comprehensive error handling
- Order validation
- Position tracking
- Balance monitoring
"""

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from typing import Dict, List, Optional, Tuple
import time
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExchangeClient:
    """
    Binance Exchange Client

    Supports both Testnet and Mainnet trading.
    Default is Testnet for safety.
    """

    # Testnet URLs
    TESTNET_API_URL = 'https://testnet.binance.vision/api'
    TESTNET_STREAM_URL = 'wss://testnet.binance.vision/ws'

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = True,
        timeout: int = 30
    ):
        """
        Initialize Binance client

        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: If True, use testnet (default: True for safety)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.timeout = timeout

        # Initialize client
        if testnet:
            logger.info("🔧 Initializing Binance TESTNET client")
            self.client = Client(
                api_key=api_key,
                api_secret=api_secret,
                testnet=True,
                requests_params={'timeout': timeout}
            )
            # Set testnet URLs
            self.client.API_URL = self.TESTNET_API_URL
        else:
            logger.warning("⚠️ Initializing Binance MAINNET client - REAL MONEY!")
            self.client = Client(
                api_key=api_key,
                api_secret=api_secret,
                requests_params={'timeout': timeout}
            )

        # Verify connection
        self._verify_connection()

    def _verify_connection(self) -> bool:
        """Verify API connection and permissions"""
        try:
            # Test connectivity
            status = self.client.get_system_status()
            logger.info(f"✅ Exchange status: {status}")

            # Test authentication
            account = self.client.get_account()
            logger.info(f"✅ Account authenticated: {account.get('canTrade', False)}")

            # Check permissions
            permissions = account.get('permissions', [])
            logger.info(f"📋 Permissions: {permissions}")

            if 'SPOT' not in permissions:
                logger.warning("⚠️ SPOT trading not enabled!")
                return False

            return True

        except BinanceAPIException as e:
            logger.error(f"❌ API Error: {e.message}")
            raise
        except Exception as e:
            logger.error(f"❌ Connection failed: {str(e)}")
            raise

    # ==================== ACCOUNT INFO ====================

    def get_account_info(self) -> Dict:
        """
        Get account information

        Returns:
            Dict with account details, balances, permissions
        """
        try:
            account = self.client.get_account()

            # Parse balances (only non-zero)
            balances = {}
            for balance in account.get('balances', []):
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked

                if total > 0:
                    balances[balance['asset']] = {
                        'free': free,
                        'locked': locked,
                        'total': total
                    }

            return {
                'can_trade': account.get('canTrade', False),
                'can_withdraw': account.get('canWithdraw', False),
                'can_deposit': account.get('canDeposit', False),
                'permissions': account.get('permissions', []),
                'balances': balances,
                'update_time': account.get('updateTime', 0)
            }

        except BinanceAPIException as e:
            logger.error(f"❌ Failed to get account info: {e.message}")
            raise

    def get_balance(self, asset: str = 'USDT') -> Dict:
        """
        Get balance for specific asset

        Args:
            asset: Asset symbol (e.g., 'USDT', 'BTC')

        Returns:
            Dict with free, locked, and total amounts
        """
        try:
            balance = self.client.get_asset_balance(asset=asset)

            free = float(balance['free'])
            locked = float(balance['locked'])

            return {
                'asset': asset,
                'free': free,
                'locked': locked,
                'total': free + locked
            }

        except BinanceAPIException as e:
            logger.error(f"❌ Failed to get balance for {asset}: {e.message}")
            raise

    # ==================== MARKET DATA ====================

    def get_ticker_price(self, symbol: str) -> float:
        """
        Get current price for symbol

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')

        Returns:
            Current price as float
        """
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])

        except BinanceAPIException as e:
            logger.error(f"❌ Failed to get price for {symbol}: {e.message}")
            raise

    def get_symbol_info(self, symbol: str) -> Dict:
        """
        Get trading rules for symbol

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')

        Returns:
            Dict with lot size, price filters, etc.
        """
        try:
            exchange_info = self.client.get_exchange_info()

            for s in exchange_info['symbols']:
                if s['symbol'] == symbol:
                    # Extract key filters
                    filters = {}
                    for f in s['filters']:
                        if f['filterType'] == 'LOT_SIZE':
                            filters['min_qty'] = float(f['minQty'])
                            filters['max_qty'] = float(f['maxQty'])
                            filters['step_size'] = float(f['stepSize'])
                        elif f['filterType'] == 'PRICE_FILTER':
                            filters['min_price'] = float(f['minPrice'])
                            filters['max_price'] = float(f['maxPrice'])
                            filters['tick_size'] = float(f['tickSize'])
                        elif f['filterType'] == 'MIN_NOTIONAL':
                            filters['min_notional'] = float(f['minNotional'])

                    return {
                        'symbol': symbol,
                        'status': s['status'],
                        'base_asset': s['baseAsset'],
                        'quote_asset': s['quoteAsset'],
                        'filters': filters
                    }

            raise ValueError(f"Symbol {symbol} not found")

        except BinanceAPIException as e:
            logger.error(f"❌ Failed to get symbol info for {symbol}: {e.message}")
            raise

    # ==================== ORDER PLACEMENT ====================

    def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        test: bool = False
    ) -> Dict:
        """
        Place market order

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL'
            quantity: Amount to trade
            test: If True, test order without execution

        Returns:
            Order details
        """
        try:
            logger.info(f"{'🧪 TEST' if test else '💰'} Market {side}: {quantity} {symbol}")

            # Validate inputs
            if side not in ['BUY', 'SELL']:
                raise ValueError(f"Invalid side: {side}. Must be 'BUY' or 'SELL'")

            if quantity <= 0:
                raise ValueError(f"Invalid quantity: {quantity}. Must be > 0")

            # Place order
            if test:
                order = self.client.create_test_order(
                    symbol=symbol,
                    side=side,
                    type='MARKET',
                    quantity=quantity
                )
                logger.info("✅ Test order successful")
                return {'status': 'TEST', 'symbol': symbol, 'side': side, 'quantity': quantity}
            else:
                order = self.client.create_order(
                    symbol=symbol,
                    side=side,
                    type='MARKET',
                    quantity=quantity
                )
                logger.info(f"✅ Order placed: {order['orderId']}")
                return self._parse_order_response(order)

        except BinanceAPIException as e:
            logger.error(f"❌ Order failed: {e.message}")
            raise

    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        time_in_force: str = 'GTC',
        test: bool = False
    ) -> Dict:
        """
        Place limit order

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL'
            quantity: Amount to trade
            price: Limit price
            time_in_force: 'GTC' (Good Till Cancel), 'IOC', 'FOK'
            test: If True, test order without execution

        Returns:
            Order details
        """
        try:
            logger.info(f"{'🧪 TEST' if test else '💰'} Limit {side}: {quantity} {symbol} @ {price}")

            # Validate inputs
            if side not in ['BUY', 'SELL']:
                raise ValueError(f"Invalid side: {side}")

            if quantity <= 0:
                raise ValueError(f"Invalid quantity: {quantity}")

            if price <= 0:
                raise ValueError(f"Invalid price: {price}")

            # Place order
            if test:
                order = self.client.create_test_order(
                    symbol=symbol,
                    side=side,
                    type='LIMIT',
                    timeInForce=time_in_force,
                    quantity=quantity,
                    price=price
                )
                logger.info("✅ Test order successful")
                return {
                    'status': 'TEST',
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity,
                    'price': price
                }
            else:
                order = self.client.create_order(
                    symbol=symbol,
                    side=side,
                    type='LIMIT',
                    timeInForce=time_in_force,
                    quantity=quantity,
                    price=price
                )
                logger.info(f"✅ Order placed: {order['orderId']}")
                return self._parse_order_response(order)

        except BinanceAPIException as e:
            logger.error(f"❌ Order failed: {e.message}")
            raise

    def _parse_order_response(self, order: Dict) -> Dict:
        """Parse Binance order response into standardized format"""
        return {
            'order_id': order.get('orderId'),
            'symbol': order.get('symbol'),
            'side': order.get('side'),
            'type': order.get('type'),
            'status': order.get('status'),
            'quantity': float(order.get('origQty', 0)),
            'executed_qty': float(order.get('executedQty', 0)),
            'price': float(order.get('price', 0)) if order.get('price') else None,
            'time_in_force': order.get('timeInForce'),
            'time': order.get('transactTime', 0)
        }

    # ==================== ORDER MANAGEMENT ====================

    def get_order(self, symbol: str, order_id: int) -> Dict:
        """
        Get order status

        Args:
            symbol: Trading pair
            order_id: Order ID

        Returns:
            Order details
        """
        try:
            order = self.client.get_order(symbol=symbol, orderId=order_id)
            return self._parse_order_response(order)

        except BinanceAPIException as e:
            logger.error(f"❌ Failed to get order {order_id}: {e.message}")
            raise

    def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """
        Cancel open order

        Args:
            symbol: Trading pair
            order_id: Order ID

        Returns:
            Cancellation result
        """
        try:
            logger.info(f"🚫 Canceling order {order_id} for {symbol}")
            result = self.client.cancel_order(symbol=symbol, orderId=order_id)
            logger.info(f"✅ Order {order_id} canceled")
            return {
                'order_id': result.get('orderId'),
                'symbol': result.get('symbol'),
                'status': result.get('status'),
                'canceled': True
            }

        except BinanceAPIException as e:
            logger.error(f"❌ Failed to cancel order {order_id}: {e.message}")
            raise

    def cancel_all_orders(self, symbol: str) -> List[Dict]:
        """
        Cancel all open orders for symbol

        Args:
            symbol: Trading pair

        Returns:
            List of canceled orders
        """
        try:
            logger.warning(f"🚫 Canceling ALL orders for {symbol}")
            results = self.client.cancel_open_orders(symbol=symbol)
            logger.info(f"✅ Canceled {len(results)} orders")
            return results

        except BinanceAPIException as e:
            logger.error(f"❌ Failed to cancel all orders: {e.message}")
            raise

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get all open orders

        Args:
            symbol: Trading pair (optional, None for all)

        Returns:
            List of open orders
        """
        try:
            if symbol:
                orders = self.client.get_open_orders(symbol=symbol)
            else:
                orders = self.client.get_open_orders()

            return [self._parse_order_response(order) for order in orders]

        except BinanceAPIException as e:
            logger.error(f"❌ Failed to get open orders: {e.message}")
            raise

    # ==================== POSITIONS ====================

    def get_positions(self) -> Dict[str, float]:
        """
        Get current positions (non-zero balances)

        Returns:
            Dict of {asset: amount}
        """
        try:
            account = self.get_account_info()
            positions = {}

            for asset, balance in account['balances'].items():
                if balance['total'] > 0:
                    positions[asset] = balance['total']

            return positions

        except Exception as e:
            logger.error(f"❌ Failed to get positions: {str(e)}")
            raise

    # ==================== UTILITY ====================

    def get_server_time(self) -> int:
        """Get Binance server time in milliseconds"""
        try:
            return self.client.get_server_time()['serverTime']
        except Exception as e:
            logger.error(f"❌ Failed to get server time: {str(e)}")
            raise

    def ping(self) -> bool:
        """
        Test connectivity to exchange

        Returns:
            True if connected
        """
        try:
            self.client.ping()
            return True
        except Exception:
            return False

    # ==================== SAFETY ====================

    def emergency_cancel_all(self) -> Dict:
        """
        EMERGENCY: Cancel all open orders on all symbols

        Returns:
            Dict with cancellation results
        """
        try:
            logger.warning("🚨 EMERGENCY: Canceling ALL open orders on ALL symbols!")

            # Get all open orders
            all_orders = self.get_open_orders()

            if not all_orders:
                logger.info("✅ No open orders to cancel")
                return {'canceled_count': 0, 'orders': []}

            # Group by symbol
            symbols = set(order['symbol'] for order in all_orders)

            # Cancel all orders for each symbol
            canceled = []
            for symbol in symbols:
                try:
                    results = self.cancel_all_orders(symbol)
                    canceled.extend(results)
                except Exception as e:
                    logger.error(f"❌ Failed to cancel orders for {symbol}: {str(e)}")

            logger.warning(f"🚨 Emergency canceled {len(canceled)} orders")

            return {
                'canceled_count': len(canceled),
                'symbols': list(symbols),
                'orders': canceled
            }

        except Exception as e:
            logger.error(f"❌ Emergency cancel failed: {str(e)}")
            raise

    def __repr__(self):
        mode = "TESTNET" if self.testnet else "⚠️ MAINNET"
        return f"<BinanceClient mode={mode}>"


# ==================== HELPER FUNCTIONS ====================

def format_quantity(quantity: float, step_size: float) -> float:
    """
    Format quantity according to step size rules

    Args:
        quantity: Raw quantity
        step_size: Minimum step size from symbol info

    Returns:
        Formatted quantity
    """
    precision = len(str(step_size).rstrip('0').split('.')[-1])
    return round(quantity - (quantity % step_size), precision)


def format_price(price: float, tick_size: float) -> float:
    """
    Format price according to tick size rules

    Args:
        price: Raw price
        tick_size: Minimum tick size from symbol info

    Returns:
        Formatted price
    """
    precision = len(str(tick_size).rstrip('0').split('.')[-1])
    return round(price - (price % tick_size), precision)

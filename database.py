"""
Database management module
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path: str = 'AITradeGame.db'):
        self.db_path = db_path
        
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Providers table (API提供方)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS providers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                api_url TEXT NOT NULL,
                api_key TEXT NOT NULL,
                models TEXT,  -- JSON string or comma-separated list of models
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Models table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                provider_id INTEGER,
                model_name TEXT NOT NULL,
                initial_capital REAL DEFAULT 10000,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (provider_id) REFERENCES providers(id)
            )
        ''')
        
        # Portfolios table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER NOT NULL,
                coin TEXT NOT NULL,
                quantity REAL NOT NULL,
                avg_price REAL NOT NULL,
                leverage INTEGER DEFAULT 1,
                side TEXT DEFAULT 'long',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (model_id) REFERENCES models(id),
                UNIQUE(model_id, coin, side)
            )
        ''')
        
        # Trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER NOT NULL,
                coin TEXT NOT NULL,
                signal TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                leverage INTEGER DEFAULT 1,
                side TEXT DEFAULT 'long',
                pnl REAL DEFAULT 0,
                fee REAL DEFAULT 0,
                slippage REAL DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (model_id) REFERENCES models(id)
            )
        ''')
        
        # Conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER NOT NULL,
                user_prompt TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                cot_trace TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (model_id) REFERENCES models(id)
            )
        ''')
        
        # Account values history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS account_values (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER NOT NULL,
                total_value REAL NOT NULL,
                cash REAL NOT NULL,
                positions_value REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (model_id) REFERENCES models(id)
            )
        ''')

        # Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trading_frequency_minutes INTEGER DEFAULT 60,
                trading_fee_rate REAL DEFAULT 0.001,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Insert default settings if no settings exist
        cursor.execute('SELECT COUNT(*) FROM settings')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO settings (trading_frequency_minutes, trading_fee_rate)
                VALUES (60, 0.001)
            ''')

        # Price snapshots table (for benchmark calculations)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coin TEXT NOT NULL,
                price REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create index for price snapshots
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_coin_timestamp
            ON price_snapshots (coin, timestamp)
        ''')

        # Graduation settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS graduation_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_preset TEXT DEFAULT 'quick_test',
                min_trades INTEGER DEFAULT 20,
                confidence_level INTEGER DEFAULT 80,
                min_testing_days INTEGER DEFAULT 14,
                min_win_rate REAL DEFAULT 50.0,
                min_sharpe_ratio REAL DEFAULT 0.8,
                max_drawdown_pct REAL DEFAULT 25.0,
                min_reasoning_quality REAL DEFAULT 3.5,
                require_beats_benchmark BOOLEAN DEFAULT 0,
                require_bear_market_test BOOLEAN DEFAULT 0,
                require_consistency_check BOOLEAN DEFAULT 0,
                require_net_profit_positive BOOLEAN DEFAULT 1,
                min_roi_after_costs REAL DEFAULT 5.0,
                require_beats_benchmark_after_costs BOOLEAN DEFAULT 0,
                show_warnings BOOLEAN DEFAULT 1,
                show_readiness_percentage BOOLEAN DEFAULT 1,
                highlight_missing_criteria BOOLEAN DEFAULT 1,
                send_notification_when_ready BOOLEAN DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Benchmark settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS benchmark_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                track_btc_hold BOOLEAN DEFAULT 1,
                track_eth_hold BOOLEAN DEFAULT 1,
                track_50_50 BOOLEAN DEFAULT 1,
                track_equal_weight BOOLEAN DEFAULT 1,
                custom_allocation TEXT,
                trading_fee_pct REAL DEFAULT 0.1,
                slippage_pct REAL DEFAULT 0.05,
                calc_method TEXT DEFAULT 'match_model',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Cost tracking settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cost_tracking_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                maker_fee_pct REAL DEFAULT 0.1,
                taker_fee_pct REAL DEFAULT 0.1,
                fee_assumption TEXT DEFAULT 'taker',
                slippage_pct REAL DEFAULT 0.05,
                track_ai_costs BOOLEAN DEFAULT 1,
                track_evaluation_costs BOOLEAN DEFAULT 1,
                show_gross_profit BOOLEAN DEFAULT 1,
                show_itemized_costs BOOLEAN DEFAULT 1,
                show_net_profit BOOLEAN DEFAULT 1,
                show_roi_pct BOOLEAN DEFAULT 1,
                compare_to_benchmark_net BOOLEAN DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # AI costs tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_costs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER NOT NULL,
                cost_type TEXT NOT NULL,
                tokens_used INTEGER,
                cost_usd REAL NOT NULL,
                provider TEXT,
                model_name TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (model_id) REFERENCES models(id)
            )
        ''')

        # Insert default graduation settings if none exist
        cursor.execute('SELECT COUNT(*) FROM graduation_settings')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO graduation_settings (strategy_preset) VALUES ('quick_test')
            ''')

        # Insert default benchmark settings if none exist
        cursor.execute('SELECT COUNT(*) FROM benchmark_settings')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO benchmark_settings DEFAULT VALUES
            ''')

        # Insert default cost tracking settings if none exist
        cursor.execute('SELECT COUNT(*) FROM cost_tracking_settings')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO cost_tracking_settings DEFAULT VALUES
            ''')

        conn.commit()
        conn.close()
    
    # ============ Model Management (Moved) ============
    
    def delete_model(self, model_id: int):
        """Delete model and related data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM models WHERE id = ?', (model_id,))
        cursor.execute('DELETE FROM portfolios WHERE model_id = ?', (model_id,))
        cursor.execute('DELETE FROM trades WHERE model_id = ?', (model_id,))
        cursor.execute('DELETE FROM conversations WHERE model_id = ?', (model_id,))
        cursor.execute('DELETE FROM account_values WHERE model_id = ?', (model_id,))
        conn.commit()
        conn.close()
    
    # ============ Portfolio Management ============
    
    def update_position(self, model_id: int, coin: str, quantity: float, 
                       avg_price: float, leverage: int = 1, side: str = 'long'):
        """Update position"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO portfolios (model_id, coin, quantity, avg_price, leverage, side, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(model_id, coin, side) DO UPDATE SET
                quantity = excluded.quantity,
                avg_price = excluded.avg_price,
                leverage = excluded.leverage,
                updated_at = CURRENT_TIMESTAMP
        ''', (model_id, coin, quantity, avg_price, leverage, side))
        conn.commit()
        conn.close()
    
    def get_portfolio(self, model_id: int, current_prices: Dict = None) -> Dict:
        """Get portfolio with positions and P&L
        
        Args:
            model_id: Model ID
            current_prices: Current market prices {coin: price} for unrealized P&L calculation
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get positions
        cursor.execute('''
            SELECT * FROM portfolios WHERE model_id = ? AND quantity > 0
        ''', (model_id,))
        positions = [dict(row) for row in cursor.fetchall()]
        
        # Get initial capital
        cursor.execute('SELECT initial_capital FROM models WHERE id = ?', (model_id,))
        initial_capital = cursor.fetchone()['initial_capital']
        
        # Calculate realized P&L (sum of all trade P&L)
        cursor.execute('''
            SELECT COALESCE(SUM(pnl), 0) as total_pnl FROM trades WHERE model_id = ?
        ''', (model_id,))
        realized_pnl = cursor.fetchone()['total_pnl']
        
        # Calculate margin used
        margin_used = sum([p['quantity'] * p['avg_price'] / p['leverage'] for p in positions])
        
        # Calculate unrealized P&L (if prices provided)
        unrealized_pnl = 0
        if current_prices:
            for pos in positions:
                coin = pos['coin']
                if coin in current_prices:
                    current_price = current_prices[coin]
                    entry_price = pos['avg_price']
                    quantity = pos['quantity']
                    
                    # Add current price to position
                    pos['current_price'] = current_price
                    
                    # Calculate position P&L
                    if pos['side'] == 'long':
                        pos_pnl = (current_price - entry_price) * quantity
                    else:  # short
                        pos_pnl = (entry_price - current_price) * quantity
                    
                    pos['pnl'] = pos_pnl
                    unrealized_pnl += pos_pnl
                else:
                    pos['current_price'] = None
                    pos['pnl'] = 0
        else:
            for pos in positions:
                pos['current_price'] = None
                pos['pnl'] = 0
        
        # Cash = initial capital + realized P&L - margin used
        cash = initial_capital + realized_pnl - margin_used
        
        # Position value = quantity * entry price (not margin!)
        positions_value = sum([p['quantity'] * p['avg_price'] for p in positions])
        
        # Total account value = initial capital + realized P&L + unrealized P&L
        total_value = initial_capital + realized_pnl + unrealized_pnl
        
        conn.close()
        
        return {
            'model_id': model_id,
            'cash': cash,
            'positions': positions,
            'positions_value': positions_value,
            'margin_used': margin_used,
            'total_value': total_value,
            'realized_pnl': realized_pnl,
            'unrealized_pnl': unrealized_pnl
        }
    
    def close_position(self, model_id: int, coin: str, side: str = 'long'):
        """Close position"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM portfolios WHERE model_id = ? AND coin = ? AND side = ?
        ''', (model_id, coin, side))
        conn.commit()
        conn.close()
    
    # ============ Trade Records ============
    
    def add_trade(self, model_id: int, coin: str, signal: str, quantity: float,
              price: float, leverage: int = 1, side: str = 'long', pnl: float = 0,
              fee: float = 0, slippage: float = 0):
        """Add trade record with fee and slippage"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO trades (model_id, coin, signal, quantity, price, leverage, side, pnl, fee, slippage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (model_id, coin, signal, quantity, price, leverage, side, pnl, fee, slippage))
        conn.commit()
        conn.close()
    
    def get_trades(self, model_id: int, limit: int = 50) -> List[Dict]:
        """Get trade history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM trades WHERE model_id = ?
            ORDER BY timestamp DESC LIMIT ?
        ''', (model_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    # ============ Conversation History ============
    
    def add_conversation(self, model_id: int, user_prompt: str, 
                        ai_response: str, cot_trace: str = ''):
        """Add conversation record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO conversations (model_id, user_prompt, ai_response, cot_trace)
            VALUES (?, ?, ?, ?)
        ''', (model_id, user_prompt, ai_response, cot_trace))
        conn.commit()
        conn.close()
    
    def get_conversations(self, model_id: int, limit: int = 20) -> List[Dict]:
        """Get conversation history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM conversations WHERE model_id = ?
            ORDER BY timestamp DESC LIMIT ?
        ''', (model_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    # ============ Account Value History ============
    
    def record_account_value(self, model_id: int, total_value: float, 
                            cash: float, positions_value: float):
        """Record account value snapshot"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO account_values (model_id, total_value, cash, positions_value)
            VALUES (?, ?, ?, ?)
        ''', (model_id, total_value, cash, positions_value))
        conn.commit()
        conn.close()
    
    def get_account_value_history(self, model_id: int, limit: int = 100, time_range: str = None) -> List[Dict]:
        """Get account value history with optional time range filtering"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Calculate time threshold based on range
        time_filter = ""
        if time_range:
            from datetime import datetime, timedelta
            now = datetime.now()

            if time_range == '24h':
                threshold = now - timedelta(hours=24)
            elif time_range == '7d':
                threshold = now - timedelta(days=7)
            elif time_range == '30d':
                threshold = now - timedelta(days=30)
            elif time_range == '90d':
                threshold = now - timedelta(days=90)
            else:  # 'all' or any other value
                threshold = None

            if threshold:
                time_filter = f" AND timestamp >= '{threshold.strftime('%Y-%m-%d %H:%M:%S')}'"

        cursor.execute(f'''
            SELECT * FROM account_values WHERE model_id = ?{time_filter}
            ORDER BY timestamp DESC LIMIT ?
        ''', (model_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_aggregated_account_value_history(self, limit: int = 100) -> List[Dict]:
        """Get aggregated account value history across all models"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get the most recent timestamp for each time point across all models
        cursor.execute('''
            SELECT timestamp,
                   SUM(total_value) as total_value,
                   SUM(cash) as cash,
                   SUM(positions_value) as positions_value,
                   COUNT(DISTINCT model_id) as model_count
            FROM (
                SELECT timestamp,
                       total_value,
                       cash,
                       positions_value,
                       model_id,
                       ROW_NUMBER() OVER (PARTITION BY model_id, DATE(timestamp) ORDER BY timestamp DESC) as rn
                FROM account_values
            ) grouped
            WHERE rn <= 10  -- Keep up to 10 records per model per day for aggregation
            GROUP BY DATE(timestamp), HOUR(timestamp)
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            result.append({
                'timestamp': row['timestamp'],
                'total_value': row['total_value'],
                'cash': row['cash'],
                'positions_value': row['positions_value'],
                'model_count': row['model_count']
            })

        return result

    def get_multi_model_chart_data(self, limit: int = 100) -> List[Dict]:
        """Get chart data for all models to display in multi-line chart"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get all models
        cursor.execute('SELECT id, name FROM models')
        models = cursor.fetchall()

        chart_data = []

        for model in models:
            model_id = model['id']
            model_name = model['name']

            # Get account value history for this model
            cursor.execute('''
                SELECT timestamp, total_value FROM account_values
                WHERE model_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (model_id, limit))

            history = cursor.fetchall()

            if history:
                # Convert to list of dicts with model info
                model_data = {
                    'model_id': model_id,
                    'model_name': model_name,
                    'data': [
                        {
                            'timestamp': row['timestamp'],
                            'value': row['total_value']
                        } for row in history
                    ]
                }
                chart_data.append(model_data)

        conn.close()
        return chart_data

    # ============ Settings Management ============

    def get_settings(self) -> Dict:
        """Get system settings"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT trading_frequency_minutes, trading_fee_rate
            FROM settings
            ORDER BY id DESC
            LIMIT 1
        ''')

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'trading_frequency_minutes': row['trading_frequency_minutes'],
                'trading_fee_rate': row['trading_fee_rate']
            }
        else:
            # Return default settings if none exist
            return {
                'trading_frequency_minutes': 60,
                'trading_fee_rate': 0.001
            }

    def update_settings(self, trading_frequency_minutes: int, trading_fee_rate: float) -> bool:
        """Update system settings"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                UPDATE settings
                SET trading_frequency_minutes = ?,
                    trading_fee_rate = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = (
                    SELECT id FROM settings ORDER BY id DESC LIMIT 1
                )
            ''', (trading_frequency_minutes, trading_fee_rate))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating settings: {e}")
            conn.close()
            return False

    # ============ Provider Management ============

    def add_provider(self, name: str, api_url: str, api_key: str, models: str = '') -> int:
        """Add new API provider"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO providers (name, api_url, api_key, models)
            VALUES (?, ?, ?, ?)
        ''', (name, api_url, api_key, models))
        provider_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return provider_id

    def get_provider(self, provider_id: int) -> Optional[Dict]:
        """Get provider information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM providers WHERE id = ?', (provider_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_all_providers(self) -> List[Dict]:
        """Get all API providers"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM providers ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def delete_provider(self, provider_id: int):
        """Delete provider"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM providers WHERE id = ?', (provider_id,))
        conn.commit()
        conn.close()

    def update_provider(self, provider_id: int, name: str, api_url: str, api_key: str, models: str):
        """Update provider information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE providers
            SET name = ?, api_url = ?, api_key = ?, models = ?
            WHERE id = ?
        ''', (name, api_url, api_key, models, provider_id))
        conn.commit()
        conn.close()

    # ============ Model Management (Updated) ============

    def add_model(self, name: str, provider_id: int, model_name: str, initial_capital: float = 10000) -> int:
        """Add new trading model"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO models (name, provider_id, model_name, initial_capital)
            VALUES (?, ?, ?, ?)
        ''', (name, provider_id, model_name, initial_capital))
        model_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return model_id

    def get_model(self, model_id: int) -> Optional[Dict]:
        """Get model information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.*, p.api_key, p.api_url
            FROM models m
            LEFT JOIN providers p ON m.provider_id = p.id
            WHERE m.id = ?
        ''', (model_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_all_models(self) -> List[Dict]:
        """Get all trading models"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.*, p.name as provider_name
            FROM models m
            LEFT JOIN providers p ON m.provider_id = p.id
            ORDER BY m.created_at DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def update_model(self, model_id: int, name: str = None, provider_id: int = None, model_name: str = None, initial_capital: float = None):
        """Update model information"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Build dynamic UPDATE query based on provided parameters
        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if provider_id is not None:
            updates.append("provider_id = ?")
            params.append(provider_id)
        if model_name is not None:
            updates.append("model_name = ?")
            params.append(model_name)
        if initial_capital is not None:
            updates.append("initial_capital = ?")
            params.append(initial_capital)

        if not updates:
            conn.close()
            return

        params.append(model_id)
        query = f"UPDATE models SET {', '.join(updates)} WHERE id = ?"

        cursor.execute(query, params)
        conn.commit()
        conn.close()

    # ============ Price Snapshots (for benchmarks) ============

    def store_price_snapshot(self, coin: str, price: float):
        """Store price snapshot for benchmark calculations"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO price_snapshots (coin, price) VALUES (?, ?)
        ''', (coin, price))
        conn.commit()
        conn.close()

    def get_price_at_timestamp(self, coin: str, timestamp: str) -> Optional[float]:
        """Get closest price to a given timestamp"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT price FROM price_snapshots
            WHERE coin = ? AND timestamp <= ?
            ORDER BY timestamp DESC LIMIT 1
        ''', (coin, timestamp))
        row = cursor.fetchone()
        conn.close()
        return row['price'] if row else None

    def get_earliest_price_snapshot(self, coin: str) -> Optional[Dict]:
        """Get earliest price snapshot for a coin"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT price, timestamp FROM price_snapshots
            WHERE coin = ?
            ORDER BY timestamp ASC LIMIT 1
        ''', (coin,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    # ============ Graduation Settings ============

    def get_graduation_settings(self) -> Dict:
        """Get graduation settings"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM graduation_settings ORDER BY id DESC LIMIT 1')
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_graduation_settings(self, settings: Dict):
        """Update graduation settings"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get existing settings ID
        cursor.execute('SELECT id FROM graduation_settings ORDER BY id DESC LIMIT 1')
        row = cursor.fetchone()
        settings_id = row['id'] if row else None

        if settings_id:
            # Update existing
            updates = ', '.join([f"{key} = ?" for key in settings.keys()])
            values = list(settings.values()) + [settings_id]
            cursor.execute(f'''
                UPDATE graduation_settings SET {updates}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', values)
        else:
            # Insert new
            columns = ', '.join(settings.keys())
            placeholders = ', '.join(['?' for _ in settings])
            cursor.execute(f'''
                INSERT INTO graduation_settings ({columns}) VALUES ({placeholders})
            ''', list(settings.values()))

        conn.commit()
        conn.close()

    # ============ Benchmark Settings ============

    def get_benchmark_settings(self) -> Dict:
        """Get benchmark settings"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM benchmark_settings ORDER BY id DESC LIMIT 1')
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_benchmark_settings(self, settings: Dict):
        """Update benchmark settings"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM benchmark_settings ORDER BY id DESC LIMIT 1')
        row = cursor.fetchone()
        settings_id = row['id'] if row else None

        if settings_id:
            updates = ', '.join([f"{key} = ?" for key in settings.keys()])
            values = list(settings.values()) + [settings_id]
            cursor.execute(f'''
                UPDATE benchmark_settings SET {updates}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', values)
        else:
            columns = ', '.join(settings.keys())
            placeholders = ', '.join(['?' for _ in settings])
            cursor.execute(f'''
                INSERT INTO benchmark_settings ({columns}) VALUES ({placeholders})
            ''', list(settings.values()))

        conn.commit()
        conn.close()

    # ============ Cost Tracking Settings ============

    def get_cost_tracking_settings(self) -> Dict:
        """Get cost tracking settings"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cost_tracking_settings ORDER BY id DESC LIMIT 1')
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_cost_tracking_settings(self, settings: Dict):
        """Update cost tracking settings"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM cost_tracking_settings ORDER BY id DESC LIMIT 1')
        row = cursor.fetchone()
        settings_id = row['id'] if row else None

        if settings_id:
            updates = ', '.join([f"{key} = ?" for key in settings.keys()])
            values = list(settings.values()) + [settings_id]
            cursor.execute(f'''
                UPDATE cost_tracking_settings SET {updates}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', values)
        else:
            columns = ', '.join(settings.keys())
            placeholders = ', '.join(['?' for _ in settings])
            cursor.execute(f'''
                INSERT INTO cost_tracking_settings ({columns}) VALUES ({placeholders})
            ''', list(settings.values()))

        conn.commit()
        conn.close()

    # ============ AI Costs Tracking ============

    def store_ai_cost(self, model_id: int, cost_type: str, cost_usd: float,
                     tokens_used: int = None, provider: str = None, model_name: str = None):
        """Store AI API cost"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ai_costs (model_id, cost_type, tokens_used, cost_usd, provider, model_name)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (model_id, cost_type, tokens_used, cost_usd, provider, model_name))
        conn.commit()
        conn.close()

    def get_ai_costs(self, model_id: int, start_date: str = None, end_date: str = None) -> List[Dict]:
        """Get AI costs for a model"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = 'SELECT * FROM ai_costs WHERE model_id = ?'
        params = [model_id]

        if start_date:
            query += ' AND timestamp >= ?'
            params.append(start_date)
        if end_date:
            query += ' AND timestamp <= ?'
            params.append(end_date)

        query += ' ORDER BY timestamp DESC'

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_total_ai_costs(self, model_id: int) -> float:
        """Get total AI costs for a model"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COALESCE(SUM(cost_usd), 0) as total FROM ai_costs WHERE model_id = ?
        ''', (model_id,))
        row = cursor.fetchone()
        conn.close()
        return row['total']


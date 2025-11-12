"""
Enhanced Database Schema for Personal Trading System
Extends the original database with new tables for:
- Trading modes (Simulation, Semi-Auto, Full-Auto)
- Comprehensive settings management
- Risk parameters
- Pending decisions (for semi-auto)
- Approval history
- Incidents/alerts log
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from database import Database  # Inherit from original

class EnhancedDatabase(Database):
    """Enhanced database with additional tables for personal trading"""

    def init_db(self):
        """Initialize all database tables (original + enhanced)"""
        # Call parent init first
        super().init_db()

        # Now add enhanced tables
        conn = self.get_connection()
        cursor = conn.cursor()

        # ============ Enhanced Models Table ============
        # Add new columns to models table if they don't exist
        cursor.execute("PRAGMA table_info(models)")
        columns = [col[1] for col in cursor.fetchall()]

        # NEW ARCHITECTURE: Separate environment from automation
        if 'trading_environment' not in columns:
            cursor.execute('ALTER TABLE models ADD COLUMN trading_environment TEXT DEFAULT "simulation"')
        if 'automation_level' not in columns:
            cursor.execute('ALTER TABLE models ADD COLUMN automation_level TEXT DEFAULT "manual"')
        if 'exchange_environment' not in columns:
            cursor.execute('ALTER TABLE models ADD COLUMN exchange_environment TEXT DEFAULT "testnet"')

        # Legacy column for migration (will be removed later)
        if 'trading_mode' not in columns:
            cursor.execute('ALTER TABLE models ADD COLUMN trading_mode TEXT DEFAULT "simulation"')

        # Other columns
        if 'status' not in columns:
            cursor.execute('ALTER TABLE models ADD COLUMN status TEXT DEFAULT "active"')
        if 'exchange_type' not in columns:
            cursor.execute('ALTER TABLE models ADD COLUMN exchange_type TEXT DEFAULT "binance"')

        # ============ Enhanced Settings Table ============
        # Comprehensive settings for each model
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER UNIQUE NOT NULL,

                -- Risk Management
                max_position_size_pct REAL DEFAULT 10.0,
                max_daily_loss_pct REAL DEFAULT 3.0,
                max_daily_trades INTEGER DEFAULT 20,
                max_open_positions INTEGER DEFAULT 5,
                min_cash_reserve_pct REAL DEFAULT 20.0,
                max_drawdown_pct REAL DEFAULT 15.0,

                -- Trading
                trading_interval_minutes INTEGER DEFAULT 60,
                trading_fee_rate REAL DEFAULT 0.1,

                -- Auto-Pause Triggers
                auto_pause_enabled BOOLEAN DEFAULT 1,
                auto_pause_consecutive_losses INTEGER DEFAULT 5,
                auto_pause_win_rate_threshold REAL DEFAULT 40.0,
                auto_pause_volatility_multiplier REAL DEFAULT 3.0,
                auto_pause_api_errors INTEGER DEFAULT 3,

                -- AI Settings
                ai_temperature REAL DEFAULT 0.7,
                ai_strategy TEXT DEFAULT 'day_trading_mean_reversion',
                explanation_level TEXT DEFAULT 'intermediate',

                -- Notifications
                email_enabled BOOLEAN DEFAULT 0,
                email_address TEXT,
                email_frequency TEXT DEFAULT 'digest',
                notify_trades BOOLEAN DEFAULT 1,
                notify_approvals BOOLEAN DEFAULT 1,
                notify_daily_summary BOOLEAN DEFAULT 1,
                notify_risk_triggers BOOLEAN DEFAULT 1,
                notify_auto_pause BOOLEAN DEFAULT 1,
                notify_errors BOOLEAN DEFAULT 1,

                -- Exchange
                use_testnet BOOLEAN DEFAULT 0,
                supported_assets TEXT DEFAULT '["BTC","ETH","SOL","BNB","XRP","DOGE"]',

                -- Metadata
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
            )
        ''')

        # ============ Pending Decisions Table (Semi-Auto) ============
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER NOT NULL,
                coin TEXT NOT NULL,
                decision_data TEXT NOT NULL,  -- JSON: full decision object
                explanation_data TEXT,  -- JSON: full explanation object
                status TEXT DEFAULT 'pending',  -- pending, approved, rejected, expired
                expires_at TIMESTAMP,
                rejection_reason TEXT,
                modified_data TEXT,  -- JSON: if user modified before executing
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,

                FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
            )
        ''')

        # ============ Approval Events Table ============
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS approval_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id INTEGER NOT NULL,
                model_id INTEGER NOT NULL,
                approved BOOLEAN NOT NULL,
                modified BOOLEAN DEFAULT 0,
                modification_details TEXT,  -- JSON: what was changed
                rejection_reason TEXT,
                execution_result TEXT,  -- JSON: trade execution result
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (decision_id) REFERENCES pending_decisions(id) ON DELETE CASCADE,
                FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
            )
        ''')

        # ============ Incidents/Alerts Log ============
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER,
                incident_type TEXT NOT NULL,  -- CIRCUIT_BREAKER, AUTO_PAUSE, API_ERROR, etc.
                severity TEXT NOT NULL,  -- low, medium, high, critical
                message TEXT NOT NULL,
                details TEXT,  -- JSON: additional details
                resolved BOOLEAN DEFAULT 0,
                resolved_at TIMESTAMP,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
            )
        ''')

        # ============ Readiness Metrics Table ============
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS readiness_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER NOT NULL,
                total_trades INTEGER DEFAULT 0,
                approval_rate REAL DEFAULT 0,
                win_rate REAL DEFAULT 0,
                total_return REAL DEFAULT 0,
                risk_violations INTEGER DEFAULT 0,
                modification_rate REAL DEFAULT 0,
                return_volatility REAL DEFAULT 0,
                readiness_score REAL DEFAULT 0,
                calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
            )
        ''')

        # ============ Setting Change Audit Log ============
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS setting_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER,
                setting_key TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                changed_by TEXT DEFAULT 'user',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
            )
        ''')

        # ============ Exchange Credentials Table ============
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exchange_credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER UNIQUE NOT NULL,
                exchange_type TEXT DEFAULT 'binance',
                api_key TEXT NOT NULL,
                api_secret TEXT NOT NULL,
                testnet_api_key TEXT,
                testnet_api_secret TEXT,
                is_active BOOLEAN DEFAULT 1,
                last_validated TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
            )
        ''')

        # ============ Risk Profiles Table ============
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                color TEXT,
                icon TEXT,
                is_system_preset BOOLEAN DEFAULT 0,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,

                -- Risk parameters
                max_position_size_pct REAL NOT NULL,
                max_open_positions INTEGER NOT NULL,
                min_cash_reserve_pct REAL NOT NULL,
                max_daily_loss_pct REAL NOT NULL,
                max_drawdown_pct REAL NOT NULL,
                max_daily_trades INTEGER NOT NULL,
                trading_interval_minutes INTEGER NOT NULL,
                auto_pause_consecutive_losses INTEGER NOT NULL,
                auto_pause_win_rate_threshold REAL NOT NULL,
                auto_pause_volatility_multiplier REAL NOT NULL,
                trading_fee_rate REAL NOT NULL,

                -- AI settings
                ai_temperature REAL DEFAULT 0.7,
                ai_strategy TEXT DEFAULT 'day_trading_mean_reversion'
            )
        ''')

        # ============ Profile Sessions Table ============
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS profile_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER NOT NULL,
                profile_id INTEGER NOT NULL,
                profile_name TEXT NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                trades_executed INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                total_pnl REAL DEFAULT 0,
                total_pnl_pct REAL DEFAULT 0,
                win_rate REAL DEFAULT 0,
                max_drawdown_pct REAL DEFAULT 0,
                avg_profit_per_trade REAL DEFAULT 0,
                sharpe_ratio REAL,

                FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
                FOREIGN KEY (profile_id) REFERENCES risk_profiles(id) ON DELETE SET NULL
            )
        ''')

        # Add active_profile_id column to model_settings if not exists
        cursor.execute("PRAGMA table_info(model_settings)")
        settings_columns = [col[1] for col in cursor.fetchall()]
        if 'active_profile_id' not in settings_columns:
            cursor.execute('ALTER TABLE model_settings ADD COLUMN active_profile_id INTEGER REFERENCES risk_profiles(id)')

        conn.commit()
        conn.close()

        print("✅ Enhanced database schema initialized")

    # ============ Model Settings Management ============

    def init_model_settings(self, model_id: int):
        """Initialize default settings for a new model"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR IGNORE INTO model_settings (model_id)
            VALUES (?)
        ''', (model_id,))

        conn.commit()
        conn.close()

    def get_model_settings(self, model_id: int) -> Dict:
        """Get all settings for a model"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM model_settings WHERE model_id = ?
        ''', (model_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            settings = dict(row)
            # Parse JSON fields
            if settings.get('supported_assets'):
                try:
                    settings['supported_assets'] = json.loads(settings['supported_assets'])
                except:
                    settings['supported_assets'] = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE']
            return settings
        else:
            # Return defaults if not found
            return self._get_default_settings()

    def update_model_settings(self, model_id: int, settings: Dict):
        """Update model settings"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Build dynamic UPDATE query
        fields = []
        values = []

        for key, value in settings.items():
            if key in ['model_id', 'id', 'created_at']:
                continue  # Skip these fields

            fields.append(f"{key} = ?")

            # JSON serialize if needed
            if key == 'supported_assets' and isinstance(value, list):
                values.append(json.dumps(value))
            else:
                values.append(value)

        if not fields:
            conn.close()
            return

        values.append(model_id)

        query = f'''
            UPDATE model_settings
            SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP
            WHERE model_id = ?
        '''

        cursor.execute(query, values)
        conn.commit()
        conn.close()

    def _get_default_settings(self) -> Dict:
        """Get default settings"""
        return {
            'max_position_size_pct': 10.0,
            'max_daily_loss_pct': 3.0,
            'max_daily_trades': 20,
            'max_open_positions': 5,
            'min_cash_reserve_pct': 20.0,
            'max_drawdown_pct': 15.0,
            'trading_interval_minutes': 60,
            'trading_fee_rate': 0.1,
            'auto_pause_enabled': True,
            'auto_pause_consecutive_losses': 5,
            'auto_pause_win_rate_threshold': 40.0,
            'auto_pause_volatility_multiplier': 3.0,
            'auto_pause_api_errors': 3,
            'ai_temperature': 0.7,
            'ai_strategy': 'day_trading_mean_reversion',
            'explanation_level': 'intermediate',
            'email_enabled': False,
            'email_address': '',
            'email_frequency': 'digest',
            'use_testnet': False,
            'supported_assets': ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE']
        }

    # ============ Pending Decisions Management ============

    def create_pending_decision(self, model_id: int, coin: str, decision: Dict,
                               explanation: Dict, expires_in_hours: int = 1) -> int:
        """Create a pending decision for semi-auto approval"""
        conn = self.get_connection()
        cursor = conn.cursor()

        from datetime import timedelta
        expires_at = datetime.now() + timedelta(hours=expires_in_hours)

        cursor.execute('''
            INSERT INTO pending_decisions
            (model_id, coin, decision_data, explanation_data, expires_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (model_id, coin, json.dumps(decision), json.dumps(explanation), expires_at))

        decision_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return decision_id

    def get_pending_decisions(self, model_id: int, status: str = 'pending') -> List[Dict]:
        """Get pending decisions for a model"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM pending_decisions
            WHERE model_id = ? AND status = ?
            ORDER BY created_at DESC
        ''', (model_id, status))

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            data = dict(row)
            # Parse JSON fields
            data['decision_data'] = json.loads(data['decision_data'])
            if data['explanation_data']:
                data['explanation_data'] = json.loads(data['explanation_data'])
            if data['modified_data']:
                data['modified_data'] = json.loads(data['modified_data'])
            results.append(data)

        return results

    def update_pending_decision(self, decision_id: int, status: str,
                               rejection_reason: str = None, modified_data: Dict = None):
        """Update status of a pending decision"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE pending_decisions
            SET status = ?,
                rejection_reason = ?,
                modified_data = ?,
                resolved_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, rejection_reason, json.dumps(modified_data) if modified_data else None, decision_id))

        conn.commit()
        conn.close()

    # ============ Incident Logging ============

    def log_incident(self, model_id: int, incident_type: str, message: str,
                    severity: str = 'medium', details: Dict = None):
        """Log an incident/alert"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO incidents (model_id, incident_type, severity, message, details)
            VALUES (?, ?, ?, ?, ?)
        ''', (model_id, incident_type, severity, message, json.dumps(details) if details else None))

        conn.commit()
        conn.close()

    def get_recent_incidents(self, model_id: int = None, limit: int = 50) -> List[Dict]:
        """Get recent incidents"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if model_id:
            cursor.execute('''
                SELECT * FROM incidents
                WHERE model_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (model_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM incidents
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            data = dict(row)
            if data['details']:
                data['details'] = json.loads(data['details'])
            results.append(data)

        return results

    # ============ Mode Management (NEW ARCHITECTURE) ============

    def get_trading_environment(self, model_id: int) -> str:
        """Get trading environment (simulation or live)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT trading_environment FROM models WHERE id = ?', (model_id,))
        row = cursor.fetchone()
        conn.close()

        return row['trading_environment'] if row else 'simulation'

    def set_trading_environment(self, model_id: int, environment: str):
        """Set trading environment (simulation or live)"""
        if environment not in ['simulation', 'live']:
            raise ValueError(f"Invalid environment: {environment}")

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE models
            SET trading_environment = ?
            WHERE id = ?
        ''', (environment, model_id))

        conn.commit()
        conn.close()

        # Log the environment change
        self.log_incident(
            model_id=model_id,
            incident_type='ENVIRONMENT_CHANGE',
            severity='high' if environment == 'live' else 'low',
            message=f'Trading environment changed to {environment}',
            details={'new_environment': environment}
        )

    def get_automation_level(self, model_id: int) -> str:
        """Get automation level (manual, semi_automated, fully_automated)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT automation_level FROM models WHERE id = ?', (model_id,))
        row = cursor.fetchone()
        conn.close()

        return row['automation_level'] if row else 'manual'

    def set_automation_level(self, model_id: int, level: str):
        """Set automation level (manual, semi_automated, fully_automated)"""
        if level not in ['manual', 'semi_automated', 'fully_automated']:
            raise ValueError(f"Invalid automation level: {level}")

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE models
            SET automation_level = ?
            WHERE id = ?
        ''', (level, model_id))

        conn.commit()
        conn.close()

        # Log the automation change
        self.log_incident(
            model_id=model_id,
            incident_type='AUTOMATION_CHANGE',
            severity='medium',
            message=f'Automation level changed to {level}',
            details={'new_automation_level': level}
        )

    def get_exchange_environment(self, model_id: int) -> str:
        """Get exchange environment (testnet or mainnet)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT exchange_environment FROM models WHERE id = ?', (model_id,))
        row = cursor.fetchone()
        conn.close()

        return row['exchange_environment'] if row else 'testnet'

    def set_exchange_environment(self, model_id: int, exchange_env: str):
        """Set exchange environment (testnet or mainnet)"""
        if exchange_env not in ['testnet', 'mainnet']:
            raise ValueError(f"Invalid exchange environment: {exchange_env}")

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE models
            SET exchange_environment = ?
            WHERE id = ?
        ''', (exchange_env, model_id))

        conn.commit()
        conn.close()

        # Log the exchange environment change
        self.log_incident(
            model_id=model_id,
            incident_type='EXCHANGE_ENV_CHANGE',
            severity='critical' if exchange_env == 'mainnet' else 'medium',
            message=f'Exchange environment changed to {exchange_env}',
            details={'new_exchange_environment': exchange_env}
        )

    # ============ Legacy Mode Management (For Backward Compatibility) ============

    def get_model_mode(self, model_id: int) -> str:
        """DEPRECATED: Get trading mode (use get_trading_environment + get_automation_level)"""
        environment = self.get_trading_environment(model_id)
        automation = self.get_automation_level(model_id)

        # Map to legacy mode
        if environment == 'simulation':
            return 'simulation'
        elif environment == 'live' and automation == 'semi_automated':
            return 'semi_automated'
        elif environment == 'live' and automation == 'fully_automated':
            return 'fully_automated'
        else:
            return 'simulation'

    def set_model_mode(self, model_id: int, mode: str):
        """DEPRECATED: Set trading mode (use set_trading_environment + set_automation_level)"""
        # Map legacy mode to new architecture
        if mode == 'simulation':
            self.set_trading_environment(model_id, 'simulation')
            self.set_automation_level(model_id, 'manual')
        elif mode == 'semi_automated':
            self.set_trading_environment(model_id, 'live')
            self.set_automation_level(model_id, 'semi_automated')
        elif mode == 'fully_automated':
            self.set_trading_environment(model_id, 'live')
            self.set_automation_level(model_id, 'fully_automated')
        else:
            raise ValueError(f"Invalid mode: {mode}")

    # ============ Exchange Credentials Management ============

    def set_exchange_credentials(self, model_id: int, api_key: str, api_secret: str,
                                testnet_api_key: str = None, testnet_api_secret: str = None,
                                exchange_type: str = 'binance'):
        """
        Store exchange API credentials for a model

        NOTE: In production, these should be encrypted!
        For now, storing in plaintext for simplicity.

        Args:
            model_id: Model ID
            api_key: Mainnet API key
            api_secret: Mainnet API secret
            testnet_api_key: Testnet API key (optional)
            testnet_api_secret: Testnet API secret (optional)
            exchange_type: Exchange type (default: binance)
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if credentials exist
        cursor.execute('SELECT id FROM exchange_credentials WHERE model_id = ?', (model_id,))
        exists = cursor.fetchone()

        if exists:
            # Update existing
            cursor.execute('''
                UPDATE exchange_credentials
                SET api_key = ?,
                    api_secret = ?,
                    testnet_api_key = ?,
                    testnet_api_secret = ?,
                    exchange_type = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE model_id = ?
            ''', (api_key, api_secret, testnet_api_key, testnet_api_secret, exchange_type, model_id))
        else:
            # Insert new
            cursor.execute('''
                INSERT INTO exchange_credentials
                (model_id, api_key, api_secret, testnet_api_key, testnet_api_secret, exchange_type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (model_id, api_key, api_secret, testnet_api_key, testnet_api_secret, exchange_type))

        conn.commit()
        conn.close()

        # Log credential update
        self.log_incident(
            model_id=model_id,
            incident_type='CREDENTIALS_UPDATED',
            severity='medium',
            message=f'Exchange credentials updated for {exchange_type}'
        )

    def get_exchange_credentials(self, model_id: int) -> Optional[Dict]:
        """Get exchange credentials for a model"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM exchange_credentials
            WHERE model_id = ? AND is_active = 1
        ''', (model_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def validate_exchange_credentials(self, model_id: int) -> bool:
        """
        Validate exchange credentials by testing connection

        Returns:
            True if credentials are valid, False otherwise
        """
        from exchange_client import ExchangeClient

        credentials = self.get_exchange_credentials(model_id)
        if not credentials:
            return False

        # Determine which credentials to use
        exchange_env = self.get_exchange_environment(model_id)

        if exchange_env == 'testnet':
            api_key = credentials.get('testnet_api_key')
            api_secret = credentials.get('testnet_api_secret')
            testnet = True
        else:
            api_key = credentials.get('api_key')
            api_secret = credentials.get('api_secret')
            testnet = False

        if not api_key or not api_secret:
            return False

        try:
            # Try to create client and ping
            client = ExchangeClient(api_key=api_key, api_secret=api_secret, testnet=testnet)
            is_valid = client.ping()

            if is_valid:
                # Update validation timestamp
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE exchange_credentials
                    SET last_validated = CURRENT_TIMESTAMP
                    WHERE model_id = ?
                ''', (model_id,))
                conn.commit()
                conn.close()

            return is_valid

        except Exception as e:
            print(f"Credential validation failed: {str(e)}")
            return False

    def delete_exchange_credentials(self, model_id: int):
        """Delete exchange credentials for a model"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM exchange_credentials WHERE model_id = ?', (model_id,))

        conn.commit()
        conn.close()

        self.log_incident(
            model_id=model_id,
            incident_type='CREDENTIALS_DELETED',
            severity='medium',
            message='Exchange credentials deleted'
        )

    def get_exchange_client(self, model_id: int):
        """
        Get configured ExchangeClient for a model

        Returns:
            ExchangeClient instance or None if not configured
        """
        from exchange_client import ExchangeClient

        credentials = self.get_exchange_credentials(model_id)
        if not credentials:
            return None

        # Determine which credentials to use based on exchange environment
        exchange_env = self.get_exchange_environment(model_id)

        if exchange_env == 'testnet':
            api_key = credentials.get('testnet_api_key')
            api_secret = credentials.get('testnet_api_secret')
            testnet = True
        else:
            api_key = credentials.get('api_key')
            api_secret = credentials.get('api_secret')
            testnet = False

        if not api_key or not api_secret:
            print(f"No {exchange_env} credentials configured for model {model_id}")
            return None

        try:
            client = ExchangeClient(api_key=api_key, api_secret=api_secret, testnet=testnet)
            return client
        except Exception as e:
            print(f"Failed to create exchange client: {str(e)}")
            self.log_incident(
                model_id=model_id,
                incident_type='EXCHANGE_CLIENT_ERROR',
                severity='high',
                message=f'Failed to create exchange client: {str(e)}'
            )
            return None

    # ============ Risk Profiles Management ============

    def init_system_risk_profiles(self):
        """Initialize the 5 system risk profile presets"""
        conn = self.get_connection()
        cursor = conn.cursor()

        system_profiles = [
            {
                'name': 'Ultra-Safe',
                'description': 'Minimal risk, focus on capital preservation',
                'color': '#10b981',
                'icon': '🛡️',
                'max_position_size_pct': 5.0,
                'max_open_positions': 3,
                'min_cash_reserve_pct': 40.0,
                'max_daily_loss_pct': 1.0,
                'max_drawdown_pct': 5.0,
                'max_daily_trades': 5,
                'trading_interval_minutes': 120,
                'auto_pause_consecutive_losses': 3,
                'auto_pause_win_rate_threshold': 50.0,
                'auto_pause_volatility_multiplier': 2.0,
                'trading_fee_rate': 0.1,
                'ai_temperature': 0.5,
                'ai_strategy': 'day_trading_mean_reversion'
            },
            {
                'name': 'Conservative',
                'description': 'Low risk, steady growth focus',
                'color': '#3b82f6',
                'icon': '📊',
                'max_position_size_pct': 8.0,
                'max_open_positions': 4,
                'min_cash_reserve_pct': 30.0,
                'max_daily_loss_pct': 2.0,
                'max_drawdown_pct': 10.0,
                'max_daily_trades': 10,
                'trading_interval_minutes': 90,
                'auto_pause_consecutive_losses': 4,
                'auto_pause_win_rate_threshold': 45.0,
                'auto_pause_volatility_multiplier': 2.5,
                'trading_fee_rate': 0.1,
                'ai_temperature': 0.6,
                'ai_strategy': 'day_trading_mean_reversion'
            },
            {
                'name': 'Balanced',
                'description': 'Moderate risk-reward balance',
                'color': '#f59e0b',
                'icon': '⚖️',
                'max_position_size_pct': 10.0,
                'max_open_positions': 5,
                'min_cash_reserve_pct': 20.0,
                'max_daily_loss_pct': 3.0,
                'max_drawdown_pct': 15.0,
                'max_daily_trades': 20,
                'trading_interval_minutes': 60,
                'auto_pause_consecutive_losses': 5,
                'auto_pause_win_rate_threshold': 40.0,
                'auto_pause_volatility_multiplier': 3.0,
                'trading_fee_rate': 0.1,
                'ai_temperature': 0.7,
                'ai_strategy': 'day_trading_mean_reversion'
            },
            {
                'name': 'Aggressive',
                'description': 'Higher risk for maximum growth potential',
                'color': '#ef4444',
                'icon': '🚀',
                'max_position_size_pct': 15.0,
                'max_open_positions': 8,
                'min_cash_reserve_pct': 10.0,
                'max_daily_loss_pct': 5.0,
                'max_drawdown_pct': 25.0,
                'max_daily_trades': 40,
                'trading_interval_minutes': 30,
                'auto_pause_consecutive_losses': 7,
                'auto_pause_win_rate_threshold': 35.0,
                'auto_pause_volatility_multiplier': 4.0,
                'trading_fee_rate': 0.1,
                'ai_temperature': 0.8,
                'ai_strategy': 'day_trading_mean_reversion'
            },
            {
                'name': 'Scalper',
                'description': 'High-frequency trading, small profits per trade',
                'color': '#8b5cf6',
                'icon': '⚡',
                'max_position_size_pct': 12.0,
                'max_open_positions': 10,
                'min_cash_reserve_pct': 15.0,
                'max_daily_loss_pct': 4.0,
                'max_drawdown_pct': 20.0,
                'max_daily_trades': 100,
                'trading_interval_minutes': 15,
                'auto_pause_consecutive_losses': 8,
                'auto_pause_win_rate_threshold': 38.0,
                'auto_pause_volatility_multiplier': 3.5,
                'trading_fee_rate': 0.1,
                'ai_temperature': 0.75,
                'ai_strategy': 'day_trading_mean_reversion'
            }
        ]

        for profile in system_profiles:
            cursor.execute('''
                INSERT OR IGNORE INTO risk_profiles
                (name, description, color, icon, is_system_preset,
                 max_position_size_pct, max_open_positions, min_cash_reserve_pct,
                 max_daily_loss_pct, max_drawdown_pct, max_daily_trades,
                 trading_interval_minutes, auto_pause_consecutive_losses,
                 auto_pause_win_rate_threshold, auto_pause_volatility_multiplier,
                 trading_fee_rate, ai_temperature, ai_strategy)
                VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                profile['name'], profile['description'], profile['color'], profile['icon'],
                profile['max_position_size_pct'], profile['max_open_positions'],
                profile['min_cash_reserve_pct'], profile['max_daily_loss_pct'],
                profile['max_drawdown_pct'], profile['max_daily_trades'],
                profile['trading_interval_minutes'], profile['auto_pause_consecutive_losses'],
                profile['auto_pause_win_rate_threshold'], profile['auto_pause_volatility_multiplier'],
                profile['trading_fee_rate'], profile['ai_temperature'], profile['ai_strategy']
            ))

        conn.commit()
        conn.close()
        print("✅ System risk profiles initialized")

    def get_all_risk_profiles(self, include_inactive: bool = False) -> List[Dict]:
        """Get all risk profiles (system and custom)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if include_inactive:
            cursor.execute('SELECT * FROM risk_profiles ORDER BY is_system_preset DESC, name')
        else:
            cursor.execute('SELECT * FROM risk_profiles WHERE is_active = 1 ORDER BY is_system_preset DESC, name')

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_risk_profile(self, profile_id: int) -> Optional[Dict]:
        """Get a specific risk profile by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM risk_profiles WHERE id = ?', (profile_id,))
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def get_risk_profile_by_name(self, name: str) -> Optional[Dict]:
        """Get a specific risk profile by name"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM risk_profiles WHERE name = ?', (name,))
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def create_custom_risk_profile(self, name: str, description: str, parameters: Dict,
                                   color: str = '#64748b', icon: str = '⭐') -> int:
        """Create a custom risk profile"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO risk_profiles
            (name, description, color, icon, is_system_preset,
             max_position_size_pct, max_open_positions, min_cash_reserve_pct,
             max_daily_loss_pct, max_drawdown_pct, max_daily_trades,
             trading_interval_minutes, auto_pause_consecutive_losses,
             auto_pause_win_rate_threshold, auto_pause_volatility_multiplier,
             trading_fee_rate, ai_temperature, ai_strategy)
            VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            name, description, color, icon,
            parameters['max_position_size_pct'], parameters['max_open_positions'],
            parameters['min_cash_reserve_pct'], parameters['max_daily_loss_pct'],
            parameters['max_drawdown_pct'], parameters['max_daily_trades'],
            parameters['trading_interval_minutes'], parameters['auto_pause_consecutive_losses'],
            parameters['auto_pause_win_rate_threshold'], parameters['auto_pause_volatility_multiplier'],
            parameters.get('trading_fee_rate', 0.1),
            parameters.get('ai_temperature', 0.7),
            parameters.get('ai_strategy', 'day_trading_mean_reversion')
        ))

        profile_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return profile_id

    def update_risk_profile(self, profile_id: int, parameters: Dict):
        """Update a risk profile (custom profiles only)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if it's a system preset
        cursor.execute('SELECT is_system_preset FROM risk_profiles WHERE id = ?', (profile_id,))
        row = cursor.fetchone()

        if row and row['is_system_preset']:
            conn.close()
            raise ValueError("Cannot modify system preset profiles")

        # Build dynamic UPDATE query
        fields = []
        values = []

        for key, value in parameters.items():
            if key in ['id', 'created_at', 'is_system_preset', 'created_by']:
                continue

            fields.append(f"{key} = ?")
            values.append(value)

        if not fields:
            conn.close()
            return

        values.append(profile_id)

        query = f'''
            UPDATE risk_profiles
            SET {', '.join(fields)}
            WHERE id = ?
        '''

        cursor.execute(query, values)
        conn.commit()
        conn.close()

    def delete_risk_profile(self, profile_id: int):
        """Delete a custom risk profile"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if it's a system preset
        cursor.execute('SELECT is_system_preset FROM risk_profiles WHERE id = ?', (profile_id,))
        row = cursor.fetchone()

        if row and row['is_system_preset']:
            conn.close()
            raise ValueError("Cannot delete system preset profiles")

        # Soft delete by marking inactive
        cursor.execute('UPDATE risk_profiles SET is_active = 0 WHERE id = ?', (profile_id,))

        conn.commit()
        conn.close()

    def apply_risk_profile(self, model_id: int, profile_id: int):
        """Apply a risk profile to a model"""
        profile = self.get_risk_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile {profile_id} not found")

        # End current profile session if any
        self._end_current_profile_session(model_id)

        # Update model settings with profile parameters
        settings = {
            'max_position_size_pct': profile['max_position_size_pct'],
            'max_open_positions': profile['max_open_positions'],
            'min_cash_reserve_pct': profile['min_cash_reserve_pct'],
            'max_daily_loss_pct': profile['max_daily_loss_pct'],
            'max_drawdown_pct': profile['max_drawdown_pct'],
            'max_daily_trades': profile['max_daily_trades'],
            'trading_interval_minutes': profile['trading_interval_minutes'],
            'auto_pause_consecutive_losses': profile['auto_pause_consecutive_losses'],
            'auto_pause_win_rate_threshold': profile['auto_pause_win_rate_threshold'],
            'auto_pause_volatility_multiplier': profile['auto_pause_volatility_multiplier'],
            'trading_fee_rate': profile['trading_fee_rate'],
            'ai_temperature': profile['ai_temperature'],
            'ai_strategy': profile['ai_strategy'],
            'active_profile_id': profile_id
        }

        self.update_model_settings(model_id, settings)

        # Start new profile session
        self._start_profile_session(model_id, profile_id, profile['name'])

        # Log the profile change
        self.log_incident(
            model_id=model_id,
            incident_type='PROFILE_CHANGE',
            severity='medium',
            message=f'Risk profile changed to: {profile["name"]}',
            details={'profile_id': profile_id, 'profile_name': profile['name']}
        )

    def _start_profile_session(self, model_id: int, profile_id: int, profile_name: str):
        """Start a new profile session"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO profile_sessions (model_id, profile_id, profile_name)
            VALUES (?, ?, ?)
        ''', (model_id, profile_id, profile_name))

        conn.commit()
        conn.close()

    def _end_current_profile_session(self, model_id: int):
        """End the current profile session and calculate metrics"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Find active session
            cursor.execute('''
                SELECT id, profile_id, started_at FROM profile_sessions
                WHERE model_id = ? AND ended_at IS NULL
                ORDER BY started_at DESC LIMIT 1
            ''', (model_id,))

            session = cursor.fetchone()
            if not session:
                conn.close()
                return

            session_id = session['id']
            started_at = session['started_at']

            # Calculate metrics from trades in this session
            try:
                cursor.execute('''
                    SELECT
                        COUNT(*) as total_trades,
                        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                        SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) as losing_trades,
                        SUM(pnl) as total_pnl,
                        AVG(pnl) as avg_profit_per_trade
                    FROM trades
                    WHERE model_id = ? AND timestamp >= ?
                ''', (model_id, started_at))

                metrics = cursor.fetchone()

                total_trades = metrics['total_trades'] or 0
                winning_trades = metrics['winning_trades'] or 0
                losing_trades = metrics['losing_trades'] or 0
                total_pnl = metrics['total_pnl'] or 0
                avg_profit_per_trade = metrics['avg_profit_per_trade'] or 0
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            except:
                # Trades table might not exist or have no data
                total_trades = 0
                winning_trades = 0
                losing_trades = 0
                total_pnl = 0
                avg_profit_per_trade = 0
                win_rate = 0

            # Get portfolio value at start
            try:
                cursor.execute('''
                    SELECT portfolio_value FROM portfolio_history
                    WHERE model_id = ? AND timestamp >= ?
                    ORDER BY timestamp ASC LIMIT 1
                ''', (model_id, started_at))

                start_row = cursor.fetchone()
                start_value = start_row['portfolio_value'] if start_row else 10000
            except:
                # Portfolio history table might not exist
                start_value = 10000

            total_pnl_pct = (total_pnl / start_value * 100) if start_value > 0 else 0

            # Calculate max drawdown during session
            try:
                cursor.execute('''
                    SELECT MIN(portfolio_value) as min_value, MAX(portfolio_value) as peak_value
                    FROM portfolio_history
                    WHERE model_id = ? AND timestamp >= ?
                ''', (model_id, started_at))

                dd_row = cursor.fetchone()
                if dd_row and dd_row['peak_value']:
                    max_drawdown_pct = ((dd_row['min_value'] - dd_row['peak_value']) / dd_row['peak_value'] * 100)
                else:
                    max_drawdown_pct = 0
            except:
                # Portfolio history table might not exist
                max_drawdown_pct = 0

            # Update session with metrics
            cursor.execute('''
                UPDATE profile_sessions
                SET ended_at = CURRENT_TIMESTAMP,
                    trades_executed = ?,
                    winning_trades = ?,
                    losing_trades = ?,
                    total_pnl = ?,
                    total_pnl_pct = ?,
                    win_rate = ?,
                    max_drawdown_pct = ?,
                    avg_profit_per_trade = ?
                WHERE id = ?
            ''', (total_trades, winning_trades, losing_trades, total_pnl, total_pnl_pct,
                  win_rate, max_drawdown_pct, avg_profit_per_trade, session_id))

            conn.commit()
        except Exception as e:
            # If any error occurs, just log and continue
            print(f"Warning: Could not end profile session: {e}")
        finally:
            conn.close()

    def get_profile_performance(self, profile_id: int) -> Dict:
        """Get aggregated performance metrics for a profile across all sessions"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                COUNT(*) as total_sessions,
                SUM(trades_executed) as total_trades,
                SUM(winning_trades) as total_winning_trades,
                SUM(losing_trades) as total_losing_trades,
                AVG(win_rate) as avg_win_rate,
                SUM(total_pnl) as total_pnl,
                AVG(total_pnl_pct) as avg_pnl_pct,
                AVG(max_drawdown_pct) as avg_max_drawdown,
                AVG(avg_profit_per_trade) as avg_profit_per_trade
            FROM profile_sessions
            WHERE profile_id = ? AND ended_at IS NOT NULL
        ''', (profile_id,))

        row = cursor.fetchone()
        conn.close()

        if row and row['total_sessions']:
            return dict(row)
        else:
            return {
                'total_sessions': 0,
                'total_trades': 0,
                'total_winning_trades': 0,
                'total_losing_trades': 0,
                'avg_win_rate': 0,
                'total_pnl': 0,
                'avg_pnl_pct': 0,
                'avg_max_drawdown': 0,
                'avg_profit_per_trade': 0
            }

    def get_model_profile_history(self, model_id: int, limit: int = 10) -> List[Dict]:
        """Get profile usage history for a model"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM profile_sessions
            WHERE model_id = ?
            ORDER BY started_at DESC
            LIMIT ?
        ''', (model_id, limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

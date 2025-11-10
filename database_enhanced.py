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

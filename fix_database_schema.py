#!/usr/bin/env python3
"""
Database Schema Fix Script
Re-initializes the database schema to ensure all enhanced columns exist
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_enhanced import EnhancedDatabase

def fix_database():
    print("=" * 60)
    print("DATABASE SCHEMA FIX")
    print("=" * 60)

    db = EnhancedDatabase('AITradeGame.db')

    print("\n📝 Re-initializing database schema...")
    try:
        db.init_db()
        print("✅ Database schema initialized successfully!")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n📝 Initializing system risk profiles...")
    try:
        db.init_system_risk_profiles()
        print("✅ Risk profiles initialized!")
    except Exception as e:
        print(f"❌ Error initializing risk profiles: {e}")
        import traceback
        traceback.print_exc()

    # Verify schema
    print("\n🔍 Verifying schema...")
    import sqlite3
    conn = sqlite3.connect('AITradeGame.db')
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(models)")
    columns = [col[1] for col in cursor.fetchall()]

    print(f"\nModels table columns: {', '.join(columns)}")

    required_columns = ['trading_environment', 'automation_level', 'exchange_environment']
    missing = [col for col in required_columns if col not in columns]

    if missing:
        print(f"\n⚠️  Still missing columns: {', '.join(missing)}")
        return False
    else:
        print("\n✅ All required columns present!")

    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\nAvailable tables ({len(tables)}): {', '.join(tables)}")

    conn.close()

    print("\n" + "=" * 60)
    print("Schema fix complete! You can now:")
    print("1. Restart the Flask app (python app.py)")
    print("2. Create a new trading model through the UI")
    print("3. Start trading to generate data for the dashboard")
    print("=" * 60)

    return True

if __name__ == '__main__':
    success = fix_database()
    sys.exit(0 if success else 1)

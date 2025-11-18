#!/usr/bin/env python3
"""
Database Diagnostic Script
Checks what data exists in the database for debugging dashboard issues
"""

import sqlite3
from datetime import datetime

db_path = 'AITradeGame.db'

def diagnose():
    print("=" * 60)
    print("DATABASE DIAGNOSTIC REPORT")
    print("=" * 60)
    print(f"Database: {db_path}")
    print(f"Timestamp: {datetime.now()}\n")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check models
    print("\n📋 MODELS:")
    print("-" * 60)

    # First check what columns exist
    cursor.execute("PRAGMA table_info(models)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"  Available columns: {', '.join(columns)}\n")

    cursor.execute("SELECT * FROM models")
    models = cursor.fetchall()
    if models:
        for model in models:
            print(f"  Model ID: {model['id']}")
            print(f"  Name: {model['name']}")
            if 'trading_environment' in columns:
                print(f"  Environment: {model.get('trading_environment', 'N/A')}")
            if 'automation_mode' in columns:
                print(f"  Automation: {model.get('automation_mode', 'N/A')}")
            print(f"  Initial Capital: ${model['initial_capital']:,.2f}")
            print()
    else:
        print("  ⚠️  No models found!")

    # For each model, check trades and account values
    for model in models:
        model_id = model['id']
        print(f"\n💼 DATA FOR MODEL {model_id} ({model['name']}):")
        print("-" * 60)

        # Check trades
        cursor.execute("SELECT COUNT(*) as count FROM trades WHERE model_id = ?", (model_id,))
        trade_count = cursor.fetchone()['count']
        print(f"  Trades: {trade_count}")

        if trade_count > 0:
            cursor.execute("""
                SELECT coin, signal, quantity, price, pnl, timestamp
                FROM trades WHERE model_id = ?
                ORDER BY timestamp DESC LIMIT 5
            """, (model_id,))
            recent_trades = cursor.fetchall()
            print("  Recent trades:")
            for trade in recent_trades:
                print(f"    - {trade['timestamp']}: {trade['signal']} {trade['quantity']} {trade['coin']} @ ${trade['price']:.2f} (PnL: ${trade['pnl']:.2f})")

        # Check account values
        cursor.execute("SELECT COUNT(*) as count FROM account_values WHERE model_id = ?", (model_id,))
        av_count = cursor.fetchone()['count']
        print(f"\n  Account Value Records: {av_count}")

        if av_count > 0:
            cursor.execute("""
                SELECT total_value, cash, positions_value, timestamp
                FROM account_values WHERE model_id = ?
                ORDER BY timestamp DESC LIMIT 5
            """, (model_id,))
            recent_avs = cursor.fetchall()
            print("  Recent snapshots:")
            for av in recent_avs:
                print(f"    - {av['timestamp']}: Total=${av['total_value']:,.2f} (Cash=${av['cash']:,.2f}, Positions=${av['positions_value']:,.2f})")
        else:
            print("  ⚠️  No account value records! This will cause dashboard issues.")

        # Check conversations (AI decisions)
        cursor.execute("SELECT COUNT(*) as count FROM conversations WHERE model_id = ?", (model_id,))
        conv_count = cursor.fetchone()['count']
        print(f"\n  AI Conversations: {conv_count}")

        if conv_count > 0:
            cursor.execute("""
                SELECT id, timestamp
                FROM conversations WHERE model_id = ?
                ORDER BY timestamp DESC LIMIT 3
            """, (model_id,))
            recent_convs = cursor.fetchall()
            print("  Recent conversations:")
            for conv in recent_convs:
                print(f"    - {conv['timestamp']}: Conversation #{conv['id']}")

        # Check positions
        cursor.execute("SELECT COUNT(*) as count FROM positions WHERE model_id = ? AND quantity != 0", (model_id,))
        pos_count = cursor.fetchone()['count']
        print(f"\n  Active Positions: {pos_count}")

        if pos_count > 0:
            cursor.execute("""
                SELECT coin, quantity, avg_price, side
                FROM positions WHERE model_id = ? AND quantity != 0
            """, (model_id,))
            positions = cursor.fetchall()
            for pos in positions:
                print(f"    - {pos['coin']}: {pos['quantity']} @ ${pos['avg_price']:.2f} ({pos['side']})")

    # Check graduation settings
    print("\n\n🎓 GRADUATION SETTINGS:")
    print("-" * 60)
    cursor.execute("SELECT * FROM graduation_settings LIMIT 1")
    settings = cursor.fetchone()
    if settings:
        print(f"  Strategy Preset: {settings['strategy_preset']}")
        print(f"  Min Trades: {settings['min_trades']}")
        print(f"  Min Testing Days: {settings['min_testing_days']}")
        print(f"  Min Win Rate: {settings['min_win_rate']}%")
        print(f"  Min Sharpe Ratio: {settings['min_sharpe_ratio']}")
        print(f"  Max Drawdown: {settings['max_drawdown_pct']}%")
        print(f"  Confidence Level: {settings['confidence_level']}%")
    else:
        print("  ⚠️  No graduation settings configured!")

    conn.close()

    print("\n" + "=" * 60)
    print("END OF DIAGNOSTIC REPORT")
    print("=" * 60)

if __name__ == '__main__':
    try:
        diagnose()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

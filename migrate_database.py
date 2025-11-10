"""
Migration Script: Convert Legacy trading_mode to New Architecture
Migrates from single 'trading_mode' column to separate 'trading_environment' and 'automation_level'
"""
import sqlite3
from database_enhanced import EnhancedDatabase

def migrate_database(db_path='AITradeGame.db'):
    """Migrate existing database to new architecture"""
    print("=" * 60)
    print("DATABASE MIGRATION: Legacy Mode → Environment + Automation")
    print("=" * 60)

    db = EnhancedDatabase(db_path)
    conn = db.get_connection()
    cursor = conn.cursor()

    # Check if migration is needed
    cursor.execute("PRAGMA table_info(models)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'trading_environment' not in columns or 'automation_level' not in columns:
        print("\n⚠️  New columns not found. Running init_db() first...")
        db.init_db()
        conn = db.get_connection()
        cursor = conn.cursor()

    # Get all models
    cursor.execute('SELECT id, trading_mode FROM models')
    models = cursor.fetchall()

    if not models:
        print("\n✓ No models to migrate")
        conn.close()
        return

    print(f"\n📊 Found {len(models)} model(s) to migrate")
    print("\nMigration Mapping:")
    print("  'simulation'       → environment='simulation', automation='manual'")
    print("  'semi_automated'   → environment='live',       automation='semi_automated'")
    print("  'fully_automated'  → environment='live',       automation='fully_automated'")

    migrated = 0
    skipped = 0

    for model in models:
        model_id = model['id']
        old_mode = model['trading_mode'] or 'simulation'

        # Map old mode to new architecture
        if old_mode == 'simulation':
            new_environment = 'simulation'
            new_automation = 'manual'
        elif old_mode == 'semi_automated':
            new_environment = 'live'
            new_automation = 'semi_automated'
        elif old_mode == 'fully_automated':
            new_environment = 'live'
            new_automation = 'fully_automated'
        else:
            print(f"\n⚠️  Model {model_id}: Unknown mode '{old_mode}', defaulting to simulation")
            new_environment = 'simulation'
            new_automation = 'manual'

        # Check if already migrated
        cursor.execute('''
            SELECT trading_environment, automation_level
            FROM models
            WHERE id = ?
        ''', (model_id,))
        current = cursor.fetchone()

        if current and current['trading_environment'] and current['automation_level']:
            print(f"\n  Model {model_id}: Already migrated (env={current['trading_environment']}, auto={current['automation_level']})")
            skipped += 1
            continue

        # Perform migration
        cursor.execute('''
            UPDATE models
            SET trading_environment = ?,
                automation_level = ?,
                exchange_environment = 'testnet'
            WHERE id = ?
        ''', (new_environment, new_automation, model_id))

        print(f"\n  ✓ Model {model_id}: {old_mode} → env='{new_environment}', auto='{new_automation}'")
        migrated += 1

    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE")
    print("=" * 60)
    print(f"\nResults:")
    print(f"  Migrated: {migrated}")
    print(f"  Skipped:  {skipped}")
    print(f"  Total:    {len(models)}")

    print("\n✅ Database successfully migrated to new architecture!")
    print("\nNew Architecture:")
    print("  - trading_environment: 'simulation' or 'live'")
    print("  - automation_level: 'manual', 'semi_automated', or 'fully_automated'")
    print("  - exchange_environment: 'testnet' or 'mainnet'")

    return migrated, skipped

if __name__ == '__main__':
    migrate_database()

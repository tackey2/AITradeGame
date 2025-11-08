#!/usr/bin/env python3
"""
Simple script to create a test model
"""

from database_enhanced import EnhancedDatabase

print("=" * 60)
print("CREATING TEST MODEL")
print("=" * 60)

# Initialize database
print("\n1. Initializing database...")
db = EnhancedDatabase('AITradeGame.db')
db.init_db()
print("✓ Database initialized")

# Check if models exist
conn = db.get_connection()
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) as count FROM models')
count = cursor.fetchone()['count']

print(f"\n2. Current models in database: {count}")

if count == 0:
    print("\n3. Creating test model...")
    cursor.execute('''
        INSERT INTO models (
            name,
            coins,
            capital,
            trading_environment,
            automation_level,
            exchange_environment
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        'Test Trading Model',
        'BTC,ETH,SOL',
        10000.0,
        'simulation',
        'manual',
        'testnet'
    ))
    conn.commit()
    print("✓ Created 'Test Trading Model'")
    print("  - Capital: $10,000")
    print("  - Coins: BTC, ETH, SOL")
    print("  - Environment: Simulation")
    print("  - Automation: Manual")
else:
    print("\n3. Models already exist - skipping creation")

# Show all models
print("\n4. All models in database:")
print("-" * 60)
cursor.execute('SELECT id, name, trading_environment, automation_level FROM models')
models = cursor.fetchall()

for model in models:
    print(f"\n  Model ID: {model['id']}")
    print(f"  Name: {model['name']}")
    print(f"  Environment: {model['trading_environment']}")
    print(f"  Automation: {model['automation_level']}")

print("\n" + "=" * 60)
print("DONE!")
print("=" * 60)
print("\nYou can now:")
print("1. Start server: python app.py")
print("2. Open Enhanced UI: http://localhost:5000/enhanced")
print("3. Select 'Test Trading Model' from dropdown")
print("\n")

conn.close()

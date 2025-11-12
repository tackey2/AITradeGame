#!/usr/bin/env python3
"""
Simple script to create a test model
"""

import sys
import os
# Add parent directory to path so we can import from root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database_enhanced import EnhancedDatabase
from database import Database

print("=" * 60)
print("CREATING TEST MODEL")
print("=" * 60)

# Initialize both databases
print("\n1. Initializing databases...")
db = Database('AITradeGame.db')
enhanced_db = EnhancedDatabase('AITradeGame.db')
db.init_db()
enhanced_db.init_db()
print("✓ Databases initialized")

# Check if models exist
conn = enhanced_db.get_connection()
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) as count FROM models')
count = cursor.fetchone()['count']

print(f"\n2. Current models in database: {count}")

if count == 0:
    print("\n3. Creating test model...")

    # First, check if we have a provider, if not create one
    cursor.execute('SELECT COUNT(*) FROM providers')
    provider_count = cursor.fetchone()[0]

    if provider_count == 0:
        print("  Creating default provider...")
        cursor.execute('''
            INSERT INTO providers (name, api_url, api_key, models)
            VALUES (?, ?, ?, ?)
        ''', ('Test OpenAI', 'https://api.openai.com/v1', 'test-key', 'gpt-3.5-turbo,gpt-4'))
        conn.commit()
        provider_id = cursor.lastrowid
        print(f"  ✓ Created provider (ID: {provider_id})")
    else:
        cursor.execute('SELECT id FROM providers LIMIT 1')
        provider_id = cursor.fetchone()['id']

    # Create the model with correct schema
    cursor.execute('''
        INSERT INTO models (
            name,
            provider_id,
            model_name,
            initial_capital
        ) VALUES (?, ?, ?, ?)
    ''', (
        'Test Trading Model',
        provider_id,
        'gpt-4-turbo',
        10000.0
    ))
    conn.commit()
    model_id = cursor.lastrowid

    print(f"✓ Created 'Test Trading Model' (ID: {model_id})")
    print("  - Initial Capital: $10,000")
    print("  - Model: gpt-4-turbo")

    # Set the enhanced columns (environment and automation)
    print("\n4. Setting trading configuration...")
    enhanced_db.set_trading_environment(model_id, 'simulation')
    enhanced_db.set_automation_level(model_id, 'manual')
    enhanced_db.set_exchange_environment(model_id, 'testnet')
    print("  ✓ Environment: Simulation")
    print("  ✓ Automation: Manual")
    print("  ✓ Exchange: Testnet")

    # Initialize portfolio with some cash
    cursor.execute('''
        INSERT INTO account_values (model_id, total_value, cash, positions_value)
        VALUES (?, ?, ?, ?)
    ''', (model_id, 10000.0, 10000.0, 0.0))
    conn.commit()
    print("  ✓ Portfolio initialized")

else:
    print("\n3. Models already exist - skipping creation")

# Show all models
print("\n5. All models in database:")
print("-" * 60)
cursor.execute('''
    SELECT id, name, model_name, initial_capital,
           trading_environment, automation_level, exchange_environment
    FROM models
''')
models = cursor.fetchall()

for model in models:
    print(f"\n  Model ID: {model['id']}")
    print(f"  Name: {model['name']}")
    print(f"  AI Model: {model['model_name']}")
    print(f"  Capital: ${model['initial_capital']:,.2f}")
    print(f"  Environment: {model['trading_environment']}")
    print(f"  Automation: {model['automation_level']}")
    print(f"  Exchange: {model['exchange_environment']}")

print("\n" + "=" * 60)
print("DONE!")
print("=" * 60)
print("\nYou can now:")
print("1. Start server: python app.py")
print("2. Open Enhanced UI: http://localhost:5000/enhanced")
print("3. Select 'Test Trading Model' from dropdown")
print("\n")

conn.close()

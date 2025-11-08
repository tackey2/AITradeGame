"""
Test Setup Script - Creates test data for Enhanced UI testing
"""
from database_enhanced import EnhancedDatabase

print("=" * 60)
print("ENHANCED UI TEST SETUP")
print("=" * 60)

# Initialize database
db = EnhancedDatabase('AITradeGame.db')
db.init_db()

print("\n1. Checking existing providers...")
providers = db.get_all_providers()
print(f"   Found {len(providers)} provider(s)")

# Create test provider if none exists
if len(providers) == 0:
    print("\n2. Creating test provider...")
    provider_id = db.add_provider(
        name='Test OpenAI',
        api_url='https://api.openai.com/v1',
        api_key='sk-test-key-replace-with-real-key',
        models='gpt-3.5-turbo,gpt-4'
    )
    print(f"   ✓ Provider created: ID {provider_id}")
else:
    provider_id = providers[0]['id']
    print(f"   Using existing provider: ID {provider_id}")

print("\n3. Checking existing models...")
models = db.get_all_models()
print(f"   Found {len(models)} model(s)")

# Create test model if none exists
if len(models) == 0:
    print("\n4. Creating test model...")
    model_id = db.add_model(
        name='Test Trading Model',
        provider_id=provider_id,
        model_name='gpt-3.5-turbo',
        initial_capital=10000.0
    )
    print(f"   ✓ Model created: ID {model_id}")
else:
    model_id = models[0]['id']
    print(f"   Using existing model: ID {model_id}")

print("\n5. Setting up enhanced features...")

# Set trading mode to simulation
db.set_model_mode(model_id, 'simulation')
print(f"   ✓ Trading mode: simulation")

# Initialize settings with defaults
db.init_model_settings(model_id)
print(f"   ✓ Settings initialized")

# Verify settings
settings = db.get_model_settings(model_id)
print(f"\n6. Current settings for Model {model_id}:")
print(f"   - Max Position Size: {settings['max_position_size_pct']}%")
print(f"   - Max Daily Loss: {settings['max_daily_loss_pct']}%")
print(f"   - Max Daily Trades: {settings['max_daily_trades']}")
print(f"   - Max Open Positions: {settings['max_open_positions']}")
print(f"   - Min Cash Reserve: {settings['min_cash_reserve_pct']}%")
print(f"   - Trading Interval: {settings['trading_interval_minutes']} minutes")

# Log an incident for testing
db.log_incident(
    model_id=model_id,
    incident_type='SYSTEM_INIT',
    severity='low',
    message='Test setup completed - Enhanced UI ready for testing'
)
print(f"\n   ✓ Test incident logged")

print("\n" + "=" * 60)
print("SETUP COMPLETE!")
print("=" * 60)
print(f"\nTest Model ID: {model_id}")
print(f"Initial Capital: $10,000")
print(f"Trading Mode: Simulation")
print(f"\nNext Steps:")
print(f"1. Start the Flask server: python app.py")
print(f"2. Open browser: http://localhost:5000/enhanced")
print(f"3. Select 'Test Trading Model' from dropdown")
print(f"4. Start testing!")
print("=" * 60)

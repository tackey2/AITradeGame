"""
Demo Script - Week 1 MVP Features
Demonstrates the new trading system capabilities
"""
import sys
sys.path.append('.')

from database_enhanced import EnhancedDatabase
from risk_manager import RiskManager
from notifier import Notifier
from explainer import AIExplainer
from trading_modes import TradingExecutor, TradingMode
from market_data import MarketDataFetcher


def demo_system():
    """Demonstrate the new trading system"""

    print("="*60)
    print("  AI PERSONAL TRADING SYSTEM - Week 1 MVP Demo")
    print("="*60)
    print()

    # 1. Initialize database
    print("📦 Step 1: Initializing Enhanced Database...")
    db = EnhancedDatabase()
    db.init_db()
    print("   ✅ Database initialized with enhanced schema")
    print()

    # 2. Create a provider (OpenRouter example)
    print("🔌 Step 2: Adding AI Provider (OpenRouter)...")
    provider_id = db.add_provider(
        name="OpenRouter",
        api_url="https://openrouter.ai/api/v1",
        api_key="your-api-key-here",  # Replace with real key
        models="anthropic/claude-3.5-sonnet,openai/gpt-4-turbo"
    )
    print(f"   ✅ Provider added (ID: {provider_id})")
    print()

    # 3. Create a trading model
    print("🤖 Step 3: Creating Trading Model...")
    model_id = db.add_model(
        name="Demo Crypto Trader",
        provider_id=provider_id,
        model_name="anthropic/claude-3.5-sonnet",
        initial_capital=10000
    )
    print(f"   ✅ Model created (ID: {model_id})")
    print()

    # 4. Initialize model settings with defaults
    print("⚙️  Step 4: Initializing Model Settings...")
    db.init_model_settings(model_id)
    settings = db.get_model_settings(model_id)
    print(f"   ✅ Settings initialized:")
    print(f"      - Max Position Size: {settings['max_position_size_pct']}%")
    print(f"      - Max Daily Loss: {settings['max_daily_loss_pct']}%")
    print(f"      - Max Daily Trades: {settings['max_daily_trades']}")
    print(f"      - Max Open Positions: {settings['max_open_positions']}")
    print()

    # 5. Set trading mode
    print("🎚️  Step 5: Setting Trading Mode...")
    db.set_model_mode(model_id, TradingMode.SIMULATION.value)
    mode = db.get_model_mode(model_id)
    print(f"   ✅ Trading Mode: {mode.upper()}")
    print()

    # 6. Create system components
    print("🔧 Step 6: Initializing System Components...")
    risk_manager = RiskManager(db)
    notifier = Notifier(db)
    explainer = AIExplainer(explanation_level='intermediate')
    market_fetcher = MarketDataFetcher()
    print("   ✅ Risk Manager initialized")
    print("   ✅ Notifier initialized")
    print("   ✅ AI Explainer initialized")
    print("   ✅ Market Data Fetcher initialized")
    print()

    # 7. Create trading executor
    print("🚀 Step 7: Creating Trading Executor...")
    executor = TradingExecutor(
        db=db,
        exchange=None,  # None for simulation
        risk_manager=risk_manager,
        notifier=notifier,
        explainer=explainer
    )
    print("   ✅ Trading Executor ready")
    print()

    # 8. Fetch real market data
    print("📊 Step 8: Fetching Real Market Data...")
    coins = ['BTC', 'ETH']
    market_prices = market_fetcher.get_current_prices(coins)

    market_data = {}
    for coin in coins:
        if coin in market_prices:
            # Get technical indicators
            indicators = market_fetcher.calculate_technical_indicators(coin)

            market_data[coin] = {
                'price': market_prices[coin]['price'],
                'change_24h': market_prices[coin]['change_24h'],
                'indicators': indicators
            }

            print(f"   ✅ {coin}: ${market_prices[coin]['price']:,.2f} ({market_prices[coin]['change_24h']:+.2f}%)")

    print()

    # 9. Simulate AI decision
    print("🧠 Step 9: Simulating AI Trading Decision...")
    # In real scenario, this would come from AI, but we'll create a test decision
    ai_decision = {
        'BTC': {
            'signal': 'buy_to_enter',
            'quantity': 0.1,
            'leverage': 1,
            'stop_loss': market_data['BTC']['price'] * 0.95,  # 5% stop loss
            'profit_target': market_data['BTC']['price'] * 1.10,  # 10% profit target
            'confidence': 0.75,
            'justification': 'RSI indicates oversold conditions with support bounce signal'
        }
    }
    print(f"   ✅ AI Decision: {ai_decision['BTC']['signal'].upper()}")
    print(f"      Quantity: {ai_decision['BTC']['quantity']} BTC")
    print(f"      Confidence: {ai_decision['BTC']['confidence']*100}%")
    print()

    # 10. Generate explanation
    print("💡 Step 10: Generating AI Explanation...")
    portfolio = db.get_portfolio(model_id, market_data)
    explanation = explainer.create_explanation(
        coin='BTC',
        decision=ai_decision['BTC'],
        market_data=market_data['BTC'],
        portfolio=portfolio
    )
    print(f"   ✅ Explanation generated:")
    print(f"      Decision: {explanation['decision_summary']}")
    print(f"      Market Trend: {explanation['market_analysis']['trend'].capitalize()}")
    print(f"      RSI Signal: {explanation['technical_indicators']['rsi']['signal'].capitalize()}")
    print(f"      Position Size: {explanation['position_sizing']['position_pct']:.1f}% of portfolio")
    print(f"      Risk Amount: ${explanation['risk_assessment']['risk_amount']:.2f}")
    print(f"      Risk:Reward: 1:{explanation['risk_assessment']['risk_reward_ratio']:.2f}")
    print()

    # 11. Validate with risk manager
    print("🛡️  Step 11: Running Risk Validation...")
    is_valid, reason = risk_manager.validate_trade(
        model_id=model_id,
        coin='BTC',
        decision=ai_decision['BTC'],
        market_data=market_data['BTC']
    )
    if is_valid:
        print(f"   ✅ {reason}")
    else:
        print(f"   ❌ {reason}")
    print()

    # 12. Execute trading cycle
    print("⚡ Step 12: Executing Trading Cycle...")
    result = executor.execute_trading_cycle(
        model_id=model_id,
        market_data=market_data,
        ai_decisions=ai_decision
    )
    print(f"   ✅ Execution complete:")
    print(f"      Mode: {result['mode']}")
    print(f"      Executed: {len(result['executed'])} trade(s)")
    print(f"      Skipped: {len(result['skipped'])} trade(s)")
    if result['executed']:
        for trade in result['executed']:
            print(f"         - {trade['coin']}: {trade['signal']} @ ${trade['price']:,.2f}")
    print()

    # 13. Check risk status
    print("📈 Step 13: Checking Risk Status...")
    risk_status = risk_manager.get_risk_status(model_id)
    print(f"   ✅ Risk Metrics:")
    print(f"      Daily P&L: {risk_status['daily_pnl_pct']:+.2f}%")
    print(f"      Daily Loss Used: {risk_status['daily_loss_used_pct']:.1f}% of limit")
    print(f"      Trades Today: {risk_status['trades_today']}/{risk_status['trades_limit']}")
    print(f"      Open Positions: {risk_status['open_positions']}/{risk_status['positions_limit']}")
    print(f"      Status: {risk_status['status'].upper()}")
    print()

    # 14. Get updated portfolio
    print("💰 Step 14: Getting Updated Portfolio...")
    updated_portfolio = db.get_portfolio(model_id, market_data)
    print(f"   ✅ Portfolio Status:")
    print(f"      Total Value: ${updated_portfolio['total_value']:,.2f}")
    print(f"      Cash: ${updated_portfolio['cash']:,.2f}")
    print(f"      Open Positions: {len(updated_portfolio['positions'])}")
    if updated_portfolio['positions']:
        for pos in updated_portfolio['positions']:
            pnl = pos.get('pnl', 0)
            pnl_str = f"${pnl:+,.2f}" if pnl else "N/A"
            print(f"         - {pos['coin']}: {pos['quantity']} @ ${pos['avg_price']:,.2f} (P&L: {pnl_str})")
    print()

    # 15. Demo mode switching
    print("🔄 Step 15: Demonstrating Mode Switching...")
    print("   Current mode: SIMULATION")
    print("   Switching to SEMI_AUTO...")
    db.set_model_mode(model_id, TradingMode.SEMI_AUTO.value)
    new_mode = db.get_model_mode(model_id)
    print(f"   ✅ Mode changed to: {new_mode.upper()}")
    print()

    # 16. Demo pending decision (semi-auto)
    print("⏳ Step 16: Creating Pending Decision (Semi-Auto Mode)...")
    # Execute again in semi-auto mode
    result = executor.execute_trading_cycle(
        model_id=model_id,
        market_data=market_data,
        ai_decisions={'ETH': {
            'signal': 'buy_to_enter',
            'quantity': 2.0,
            'leverage': 1,
            'confidence': 0.68,
            'justification': 'Technical breakout pattern'
        }}
    )
    print(f"   ✅ Result:")
    print(f"      Pending approvals: {len(result['pending'])}")
    if result['pending']:
        for pending in result['pending']:
            print(f"         - Decision ID {pending['decision_id']}: {pending['signal'].upper()} {pending['quantity']} {pending['coin']}")
    print()

    # 17. Get pending decisions
    print("📋 Step 17: Retrieving Pending Decisions...")
    pending_decisions = db.get_pending_decisions(model_id, status='pending')
    print(f"   ✅ Found {len(pending_decisions)} pending decision(s)")
    if pending_decisions:
        for decision in pending_decisions:
            print(f"      Decision ID: {decision['id']}")
            print(f"      Coin: {decision['coin']}")
            print(f"      Expires: {decision['expires_at']}")
    print()

    # 18. Get recent incidents
    print("🚨 Step 18: Checking Recent Incidents/Alerts...")
    incidents = db.get_recent_incidents(model_id=model_id, limit=5)
    print(f"   ✅ Found {len(incidents)} incident(s)")
    for incident in incidents:
        print(f"      [{incident['severity'].upper()}] {incident['incident_type']}: {incident['message'][:60]}...")
    print()

    print("="*60)
    print("  ✅ Demo Complete!")
    print("="*60)
    print()
    print("Summary:")
    print(f"  - Model created and configured")
    print(f"  - Trading executed in SIMULATION mode")
    print(f"  - Risk validation working")
    print(f"  - AI explanations generated")
    print(f"  - Mode switching demonstrated")
    print(f"  - Pending decisions created in SEMI-AUTO mode")
    print()
    print("Next Steps:")
    print("  1. Integrate with Flask API")
    print("  2. Connect UI from stitch_dashboard/")
    print("  3. Add Binance live trading (Week 2)")
    print("  4. Deploy with Docker")
    print()


if __name__ == "__main__":
    try:
        demo_system()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

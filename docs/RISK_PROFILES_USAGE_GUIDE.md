# Risk Profile System - Quick Start Guide

## 🚀 What You Have Now

Your trading system now includes an **intelligent risk profile management system** with:

✅ **Phase 1 & 2 COMPLETE**: Profile management with 5 system presets
✅ **Phase 3 COMPLETE**: Smart recommendations using your trade data

---

## 📊 The 5 Risk Profiles

| Profile | Icon | Best For | Risk Level | Position Size | Daily Loss Limit |
|---------|------|----------|------------|---------------|------------------|
| **Ultra-Safe** | 🛡️ | Bear markets, capital preservation | Very Low | 5% | 1% |
| **Conservative** | 📊 | Steady growth, beginners | Low | 8% | 2% |
| **Balanced** | ⚖️ | Normal conditions (default) | Medium | 10% | 3% |
| **Aggressive** | 🚀 | Bull markets, high growth | High | 15% | 5% |
| **Scalper** | ⚡ | High-frequency trading | Medium-High | 12% | 4% |

---

## 🎯 Quick Start (5 Minutes)

### Step 1: Start Your Server

```bash
cd /home/user/AITradeGame
python3 app.py
```

Server will start on: `http://localhost:5001`

### Step 2: Test the System

```bash
# Run comprehensive tests
python3 test_risk_profiles.py

# Run recommendation tests
python3 test_recommendations.py
```

### Step 3: Try the API

```bash
# Get profile recommendation for model 1
curl http://localhost:5001/api/models/1/recommend-profile

# See all available profiles
curl http://localhost:5001/api/risk-profiles

# Apply a profile
curl -X POST http://localhost:5001/api/models/1/apply-profile \
  -H "Content-Type: application/json" \
  -d '{"profile_id": 3}'
```

---

## 📡 API Endpoints (All Working!)

### Profile Management

```bash
# List all profiles
GET /api/risk-profiles

# Get specific profile
GET /api/risk-profiles/{id}

# Create custom profile
POST /api/risk-profiles
{
  "name": "My Custom Profile",
  "description": "...",
  "max_position_size_pct": 12.0,
  "max_daily_loss_pct": 2.5,
  ...
}

# Update profile (custom only)
PUT /api/risk-profiles/{id}

# Delete profile (custom only)
DELETE /api/risk-profiles/{id}
```

### Profile Application

```bash
# Apply profile to model
POST /api/models/{model_id}/apply-profile
{"profile_id": 3}

# Get active profile
GET /api/models/{model_id}/active-profile

# Get profile usage history
GET /api/models/{model_id}/profile-history
```

### Recommendations (Phase 3) ⭐

```bash
# Get AI recommendation based on your trading performance
GET /api/models/{model_id}/recommend-profile

# Response includes:
# - Recommended profile
# - Confidence level
# - Reasons why
# - Alternative options

# Get detailed market metrics
GET /api/models/{model_id}/market-metrics

# Get suitability scores for all profiles
GET /api/models/{model_id}/profile-suitability
```

### Analytics

```bash
# Compare multiple profiles
POST /api/risk-profiles/compare
{"profile_ids": [1, 3, 4]}

# Get profile performance history
GET /api/risk-profiles/{id}/performance
```

---

## 🧪 Example Use Cases

### Use Case 1: "I'm losing money - what should I do?"

```bash
# Get recommendation
curl http://localhost:5001/api/models/1/recommend-profile

# Response:
{
  "recommendation": {
    "profile_name": "Ultra-Safe",
    "confidence": 85,
    "reason": "Poor recent performance (35% win rate)",
    "should_switch": true
  }
}

# Apply Ultra-Safe profile
curl -X POST http://localhost:5001/api/models/1/apply-profile \
  -H "Content-Type: application/json" \
  -d '{"profile_id": 1}'

# Now trading with Ultra-Safe settings:
# - Max position size: 5%
# - Daily loss limit: 1%
# - Max 5 trades per day
```

### Use Case 2: "Which profile is best for me right now?"

```bash
# Get suitability scores
curl http://localhost:5001/api/models/1/profile-suitability

# Response shows ranked profiles:
{
  "profiles": [
    {
      "name": "Balanced",
      "suitability_score": 85,
      "suitability_label": "Highly Recommended"
    },
    {
      "name": "Conservative",
      "suitability_score": 72,
      "suitability_label": "Recommended"
    },
    ...
  ]
}
```

### Use Case 3: "How's my performance?"

```bash
# Get market metrics
curl http://localhost:5001/api/models/1/market-metrics

# Response:
{
  "metrics": {
    "win_rate": 58.5,
    "volatility": 42.3,
    "drawdown_pct": -4.2,
    "consecutive_losses": 0
  },
  "analysis": {
    "condition": "favorable",
    "risk_level": "low",
    "trading_suitability": "excellent"
  }
}
```

### Use Case 4: "Compare Aggressive vs Conservative"

```bash
# Compare profiles
curl -X POST http://localhost:5001/api/risk-profiles/compare \
  -H "Content-Type: application/json" \
  -d '{"profile_ids": [2, 4]}'

# See side-by-side comparison:
# - Risk levels
# - Performance history
# - Parameter differences
```

---

## 🎮 How The Recommendation System Works

The system analyzes your **existing trade data** to recommend profiles:

### Metrics Analyzed

1. **Win Rate** - Last 30 trades
2. **Recent Win Rate** - Last 10 trades
3. **Volatility** - P&L standard deviation
4. **Drawdown** - Distance from peak value
5. **Consecutive Losses** - Current losing streak
6. **Daily Performance** - Today's P&L

### Recommendation Logic

```
IF drawdown > 15% OR recent_win_rate < 30%:
    → Ultra-Safe (Emergency mode)

ELIF drawdown > 8% OR recent_win_rate < 45%:
    → Conservative (Cautious mode)

ELIF win_rate > 60% AND drawdown < 3%:
    → Aggressive (Good conditions)

ELIF trades_today > 15 AND volatility < 50:
    → Scalper (High-frequency mode)

ELSE:
    → Balanced (Normal mode)
```

### No External APIs Required!

- ✅ Uses only your trade history
- ✅ Works offline
- ✅ No API keys needed
- ✅ Instant analysis

---

## 💡 Smart Features

### 1. Automatic Performance Tracking

Every time you switch profiles, the system automatically tracks:
- Trades executed
- Win rate
- Total P&L
- Max drawdown

View performance history:
```bash
curl http://localhost:5001/api/models/1/profile-history
```

### 2. Profile Protection

System presets are **protected**:
- ✅ Can view and use
- ❌ Cannot modify
- ❌ Cannot delete

Custom profiles:
- ✅ Can create
- ✅ Can modify
- ✅ Can delete

### 3. Real-time Suitability

Get **live suitability scores** for all profiles based on current conditions:

```bash
curl http://localhost:5001/api/models/1/profile-suitability
```

Response ranks profiles 0-100:
- **80-100**: Highly Recommended
- **60-79**: Recommended
- **40-59**: Suitable
- **20-39**: Not Ideal
- **0-19**: Not Recommended

---

## 🔧 Customization

### Create Your Own Profile

```bash
curl -X POST http://localhost:5001/api/risk-profiles \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Weekend Trader",
    "description": "Low activity for weekends",
    "color": "#9333ea",
    "icon": "🌙",
    "max_position_size_pct": 6.0,
    "max_open_positions": 3,
    "min_cash_reserve_pct": 35.0,
    "max_daily_loss_pct": 1.5,
    "max_drawdown_pct": 8.0,
    "max_daily_trades": 8,
    "trading_interval_minutes": 120,
    "auto_pause_consecutive_losses": 3,
    "auto_pause_win_rate_threshold": 45.0,
    "auto_pause_volatility_multiplier": 2.5,
    "trading_fee_rate": 0.1
  }'
```

### Modify Custom Profile

```bash
curl -X PUT http://localhost:5001/api/risk-profiles/6 \
  -H "Content-Type: application/json" \
  -d '{
    "max_daily_trades": 10,
    "max_position_size_pct": 7.0
  }'
```

---

## 📈 Workflow Examples

### Daily Trading Routine

```bash
# 1. Check recommendation
curl http://localhost:5001/api/models/1/recommend-profile

# 2. Review market conditions
curl http://localhost:5001/api/models/1/market-metrics

# 3. Apply recommended profile (if needed)
curl -X POST http://localhost:5001/api/models/1/apply-profile \
  -H "Content-Type: application/json" \
  -d '{"profile_id": 3}'

# 4. Start trading with optimal settings!
```

### Weekly Review

```bash
# 1. Check profile performance
curl http://localhost:5001/api/risk-profiles/3/performance

# 2. View profile history
curl http://localhost:5001/api/models/1/profile-history

# 3. Compare profiles
curl -X POST http://localhost:5001/api/risk-profiles/compare \
  -H "Content-Type: application/json" \
  -d '{"profile_ids": [2, 3, 4]}'

# 4. Optimize: Switch to best-performing profile
```

### Emergency Response

```bash
# If experiencing losses:

# 1. Get immediate recommendation
curl http://localhost:5001/api/models/1/recommend-profile

# 2. If recommends Ultra-Safe, apply immediately:
curl -X POST http://localhost:5001/api/models/1/apply-profile \
  -H "Content-Type: application/json" \
  -d '{"profile_id": 1}'

# Now protected with strictest risk controls!
```

---

## 🎯 Best Practices

### 1. Start Conservative
Begin with Conservative or Balanced profile while learning.

### 2. Check Recommendations Daily
Run `/recommend-profile` before each trading session.

### 3. Trust the Metrics
If confidence > 70%, seriously consider the recommendation.

### 4. Track Profile Performance
Review which profiles work best for your strategy.

### 5. Create Custom Profiles
Build profiles for specific market conditions or times.

### 6. Don't Fight the Data
If metrics show poor performance, downgrade risk level.

---

## 🚨 Warning Indicators

The system will recommend Ultra-Safe when:

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Drawdown | > 15% | Emergency mode |
| Consecutive Losses | ≥ 5 | Protect capital |
| Recent Win Rate | < 30% | Reduce exposure |
| Daily Loss | < -3% | Stop further losses |

**When you see Ultra-Safe recommended**: Take it seriously! Your capital is at risk.

---

## 📊 Performance Tracking

### View Profile Performance

```bash
# Get aggregated performance for a profile
curl http://localhost:5001/api/risk-profiles/3/performance

# Response:
{
  "total_sessions": 15,
  "total_trades": 234,
  "avg_win_rate": 58.5,
  "total_pnl": 1245.67,
  "avg_pnl_pct": 12.3,
  "avg_max_drawdown": 8.7
}
```

### View Your Usage History

```bash
# See which profiles you've used
curl http://localhost:5001/api/models/1/profile-history?limit=10

# Shows:
# - Profile used
# - Time period
# - Trades executed
# - Performance metrics
```

---

## 🔮 Next Steps (Optional JavaScript UI)

The backend is **100% complete**. To add the interactive UI:

1. **JavaScript Implementation** (~2-3 hours)
   - Profile loading and display
   - Click-to-switch functionality
   - Comparison modal
   - Custom profile creator

2. **Recommendation Banner** (~1 hour)
   - Show recommendation alert
   - One-click apply
   - Dismissible notices

See `docs/RISK_PROFILES_IMPLEMENTATION.md` for JavaScript code examples.

---

## 💾 Database

All data stored in: `AITradeGame.db`

Tables:
- `risk_profiles` - Profile definitions
- `profile_sessions` - Usage and performance tracking
- `model_settings` - Links models to active profiles

Backup your database regularly:
```bash
cp AITradeGame.db AITradeGame.db.backup
```

---

## 🐛 Troubleshooting

### "No models found"
Create a model first via the web UI or:
```python
from database_enhanced import EnhancedDatabase
db = EnhancedDatabase('AITradeGame.db')
db.create_model(name="Test Model", provider_id=1, initial_capital=10000)
```

### "Cannot connect to server"
Make sure Flask is running:
```bash
python3 app.py
```

### "Profile not found"
List available profiles:
```bash
curl http://localhost:5001/api/risk-profiles
```

### "Insufficient trade data"
System needs at least 5-10 trades for accurate recommendations. With fewer trades, it defaults to Balanced.

---

## 📚 Additional Resources

- **Full Implementation Guide**: `docs/RISK_PROFILES_IMPLEMENTATION.md`
- **Test Scripts**:
  - `test_risk_profiles.py` - Phase 1 & 2 tests
  - `test_recommendations.py` - Phase 3 tests
- **Source Code**:
  - `database_enhanced.py` - Profile management (lines 213-1277)
  - `market_analyzer.py` - Recommendation engine
  - `app.py` - API endpoints (lines 1045-1390)

---

## ✅ System Status

| Component | Status | Lines of Code |
|-----------|--------|---------------|
| Database Schema | ✅ Complete | ~100 |
| Profile Management | ✅ Complete | ~500 |
| API Endpoints | ✅ Complete | ~400 |
| Recommendation Engine | ✅ Complete | ~400 |
| Performance Tracking | ✅ Complete | ~200 |
| Test Scripts | ✅ Complete | ~800 |
| **Frontend UI** | ⏳ Pending | ~200 needed |

**Total Implementation**: ~2,400 lines of code

**Backend Status**: 100% Complete ✅

---

## 🎉 Success Metrics

After using the Risk Profile system, you should see:

✅ **Faster configuration** - 1 click vs 15 parameters
✅ **Better risk management** - Optimized settings per condition
✅ **Data-driven decisions** - Recommendations based on real performance
✅ **Protected capital** - Auto-downgrade during losses
✅ **Improved returns** - Right profile for right conditions

---

## 💬 Support

Questions? Check:
1. This guide
2. `docs/RISK_PROFILES_IMPLEMENTATION.md`
3. Test scripts for examples
4. API responses for detailed data

---

*Last Updated: 2025-11-12*
*System Version: Phase 1, 2, & 3 Complete*

# Enhanced UI Guide

## Access the Enhanced Dashboard

Start the Flask server and navigate to:
```
http://localhost:5000/enhanced
```

The classic view is still available at:
```
http://localhost:5000/
```

## Features

### 1. Dashboard Page

**Trading Mode Control:**
- Select between Simulation, Semi-Automated, and Fully Automated modes
- Changes take effect immediately
- Current mode displayed in header badge

**Risk Status Monitor:**
- Real-time display of 5 critical risk metrics:
  - Position Size Usage
  - Daily Loss Percentage
  - Open Positions Count
  - Cash Reserve Percentage
  - Daily Trades Count
- Color-coded status indicators (OK, Warning, Critical)

**Pending Decisions Queue:**
- View all pending AI trading decisions (Semi-Auto mode)
- Click any decision to see full details
- Approve, Reject, or Modify decisions
- Auto-refreshes every 10 seconds

**Quick Actions:**
- Execute Trading Cycle: Manually trigger AI analysis
- Emergency Pause: Switch model to Semi-Auto mode

### 2. Settings Page

**Risk Management Parameters:**
- Max Position Size (%) - Per-position portfolio limit
- Max Daily Loss (%) - Circuit breaker threshold
- Max Daily Trades - Trading frequency limit
- Max Open Positions - Simultaneous position limit
- Min Cash Reserve (%) - Minimum cash requirement
- Max Drawdown (%) - Auto-pause trigger for Full-Auto
- Trading Interval (minutes) - Check frequency

All settings have tooltips explaining their purpose.

**Actions:**
- Save Settings: Apply changes
- Reset to Defaults: Restore original values

### 3. Readiness Page

**Full Automation Readiness Score:**
- 0-100 point scoring system
- Visual score circle with color coding:
  - Green (≥70): Ready for Full Auto
  - Yellow (50-69): Approaching readiness
  - Red (<50): Not ready

**Performance Metrics:**
- Total Trades
- Win Rate (%)
- Approval Rate (%)
- Modification Rate (%)
- Risk Violations
- Total Return (%)
- Return Volatility (%)

### 4. Incidents Page

**Incident Log:**
- Chronological list of all system events
- Color-coded by severity:
  - Blue: Low (informational)
  - Yellow: Medium (warning)
  - Orange: High (important)
  - Red: Critical (urgent)

**Incident Types:**
- MODE_CHANGE: Trading mode changed
- TRADE_REJECTED: Risk manager blocked trade
- AUTO_PAUSE: Full-Auto paused automatically
- EMERGENCY_PAUSE: User-initiated pause
- EMERGENCY_STOP_ALL: All models stopped
- EXECUTION_ERROR: Trade execution failed
- API_ERROR: API connection issue

## Usage Workflow

### Starting with Simulation Mode

1. **Select Your Model** from dropdown
2. **Ensure mode is "Simulation"**
3. **Click "Execute Trading Cycle"** to see AI decisions
4. **Review the AI's reasoning** in simulation logs
5. **Adjust settings** as needed

### Progressing to Semi-Automated Mode

1. **Switch to "Semi-Automated"** mode
2. **Execute Trading Cycle**
3. **Review pending decisions** - click each to see full AI explanation
4. **Approve or Reject** each decision
   - Approve: Execute the trade
   - Reject: Skip the trade with optional reason
   - Modify: Adjust parameters before execution (coming soon)
5. **Monitor Risk Status** - ensure all metrics are "OK"
6. **Check Readiness Score** regularly

### Advancing to Fully Automated Mode

**Only when ready! Check readiness score first.**

1. **Verify Readiness Score ≥ 70** on Readiness page
2. **Review metrics:**
   - Win rate ≥ 50%
   - Approval rate ≥ 80%
   - Modification rate ≤ 10%
   - Zero risk violations
3. **Switch to "Fully Automated"** mode
4. **Monitor closely** in first hours
5. **Use Emergency Pause** if needed

## Emergency Controls

### Emergency Pause (Single Model)
- Located on Dashboard page
- Switches current model from Full-Auto to Semi-Auto
- Logged in incidents

### Emergency Stop All (All Models)
- Red STOP button in header
- Switches ALL models to Simulation mode
- Requires confirmation
- Use in critical situations

## Tips

**Learning Phase (Simulation):**
- Run multiple trading cycles
- Study AI reasoning
- Experiment with different settings
- No real money at risk

**Semi-Auto Phase:**
- Start with conservative settings
- Approve decisions you understand
- Reject uncertain decisions
- Learn AI patterns
- Modify settings based on results

**Full-Auto Phase:**
- Only when readiness score ≥ 70
- Monitor risk status daily
- Check incidents log regularly
- Keep max drawdown conservative (15% recommended)
- Use testnet first if available

## Auto-Refresh

The Dashboard page auto-refreshes:
- Pending Decisions: Every 10 seconds
- Risk Status: Every 10 seconds

Other pages: Manual refresh using button or browser refresh.

## Keyboard Shortcuts

Currently none implemented. Coming soon:
- `R` - Refresh current page
- `E` - Execute trading cycle
- `P` - Emergency pause
- `1-4` - Switch pages

## Mobile Support

The UI is responsive and works on mobile devices, though desktop is recommended for the full experience.

## Troubleshooting

**No pending decisions showing:**
- Ensure model is in Semi-Auto mode
- Execute a trading cycle
- Check if AI made any non-hold decisions

**Risk status shows "--":**
- Wait a moment for data to load
- Check if model is selected
- Refresh the page

**Readiness score is 0:**
- Need at least 10 trades for assessment
- Execute more trading cycles
- Check Incidents page for errors

**Settings won't save:**
- Check browser console for errors
- Ensure values are within valid ranges
- Verify model is selected

## Next Steps

After mastering the Enhanced UI:
1. Binance exchange integration for real trading
2. Testnet testing
3. Small live capital testing
4. Gradual scaling
5. Docker deployment

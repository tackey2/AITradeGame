# Testing Checklist for Enhanced Dashboard

## Session 4: Final Testing & Deployment

### Route Testing
- [ ] Visit `/` - Should load enhanced dashboard
- [ ] Visit `/enhanced` - Should load enhanced dashboard (alias)
- [ ] Visit `/classic` - Should load classic view (legacy)
- [ ] Verify "Classic View" link in enhanced dashboard works
- [ ] Verify navigation between pages works smoothly

### Dashboard Page (Session 1)
- [ ] Model selector loads all models
- [ ] Portfolio metrics display correctly (6 cards)
- [ ] Market ticker scrolls and updates
- [ ] Portfolio value chart loads with time range buttons (24H, 7D, 30D, 90D, ALL)
- [ ] Current positions table shows all open positions
- [ ] Trade history table loads with pagination
- [ ] Risk status cards display correctly
- [ ] Pending decisions section works
- [ ] AI conversations panel loads conversations
- [ ] Quick actions buttons work (Execute Trading, Emergency Pause)
- [ ] Trading environment radio buttons work (Simulation/Live)
- [ ] Automation level radio buttons work (Manual/Semi/Fully)
- [ ] Auto-refresh works for ticker, metrics, positions

### Analytics Section (Session 3)
- [ ] Asset allocation donut chart displays
- [ ] Asset allocation legend shows all positions with percentages
- [ ] Performance metrics cards display all 9 metrics:
  - Sharpe Ratio
  - Max Drawdown
  - Win Streak
  - Loss Streak
  - Best Trade
  - Worst Trade
  - Avg Win
  - Avg Loss
  - Profit Factor
- [ ] Refresh analytics button works
- [ ] AI conversations search works
- [ ] AI conversations filter works (All/Buy/Sell/Hold)
- [ ] AI conversations sort works (Newest/Oldest)
- [ ] Conversation expand/collapse works

### Models Page (Session 2)
- [ ] Multi-model toggle works
- [ ] Aggregated performance metrics display when toggle is on
- [ ] Models grid shows all models
- [ ] Model cards display correct stats
- [ ] Model status badges (Active/Paused) display correctly
- [ ] View Dashboard button switches to correct model
- [ ] Settings button opens model settings
- [ ] Pause/Resume buttons work
- [ ] Filter dropdown works (All/Active/Paused)
- [ ] Create New Model button works

### Settings Page
- [ ] AI Provider list loads
- [ ] Add AI Provider button opens modal
- [ ] Provider form validation works
- [ ] Load Models button fetches available models
- [ ] Model autocomplete datalist works
- [ ] Trading Models list loads
- [ ] Create New Model button opens modal
- [ ] Risk Profile presets display
- [ ] Create Custom Profile button works
- [ ] Compare Profiles button works
- [ ] Risk Management Settings form loads current values
- [ ] Save Settings button works
- [ ] Reset Settings button works
- [ ] Exchange Configuration loads
- [ ] Exchange environment selector works (Testnet/Mainnet)
- [ ] Credentials visibility toggle works
- [ ] Save/Validate/Delete credentials buttons work

### Readiness Page
- [ ] Readiness score displays (0-100)
- [ ] Performance metrics display
- [ ] Score message updates based on score

### Incidents Page
- [ ] Incident log loads
- [ ] Refresh button works
- [ ] Incidents display correctly

### Cross-Functional Testing
- [ ] Navigation between all pages works
- [ ] Emergency Stop button works from header
- [ ] Refresh button in header works
- [ ] All modals open and close correctly
- [ ] All notifications/toasts display correctly
- [ ] All tooltips work on hover
- [ ] No console errors
- [ ] No 404 errors for assets
- [ ] All API endpoints return valid data
- [ ] All charts render without errors
- [ ] Responsive design works (desktop only as specified)

### Backend API Endpoints
- [ ] GET `/api/providers` - Returns all providers
- [ ] GET `/api/models` - Returns all models
- [ ] GET `/api/models/<id>/portfolio-metrics` - Returns portfolio metrics
- [ ] GET `/api/models/<id>/portfolio-history?range=<range>` - Returns chart data
- [ ] GET `/api/models/<id>/asset-allocation` - Returns allocation data
- [ ] GET `/api/models/<id>/performance-analytics` - Returns analytics
- [ ] GET `/api/models/<id>/conversations?limit=<n>` - Returns conversations
- [ ] GET `/api/models/all-summary` - Returns all models summary
- [ ] GET `/api/models/<id>/risk-status` - Returns risk status
- [ ] POST `/api/risk-profiles` - Creates custom profile
- [ ] All endpoints handle errors gracefully

### Performance Testing
- [ ] Dashboard loads in < 3 seconds
- [ ] Charts render smoothly
- [ ] Auto-refresh doesn't cause lag
- [ ] Large datasets (100+ trades) load correctly
- [ ] Multiple models display efficiently

## How to Test

1. **Start the Flask application:**
   ```bash
   python app.py
   ```

2. **Open browser and test routes:**
   - http://localhost:5000/ (should show enhanced)
   - http://localhost:5000/enhanced (should show enhanced)
   - http://localhost:5000/classic (should show classic)

3. **Create test data:**
   - Add at least 1 AI provider
   - Create at least 2 models
   - Execute some trades in simulation mode

4. **Go through each page systematically:**
   - Use the checklist above
   - Check console for errors
   - Verify all features work as expected

5. **Test edge cases:**
   - No models created
   - No trades yet
   - Network errors (disconnect and reconnect)
   - Invalid model ID
   - Empty data states

## Known Limitations (By Design)
- Desktop-only (no mobile responsive for now)
- Auto-refresh intervals are gentle (30s-3min) to avoid server load
- Classic view is now legacy (minimal updates expected)
- Multi-model trading uses independent portfolios (not combined)

## Success Criteria
✅ All checklist items pass
✅ No console errors
✅ All features work as designed
✅ Enhanced view is accessible at `/`
✅ Classic view is accessible at `/classic`
✅ User experience is smooth and intuitive

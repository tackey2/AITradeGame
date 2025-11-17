# AITradeGame - Bug Fix Checklist

Quick reference for fixing identified issues. Check off as you complete each fix.

---

## 🔴 CRITICAL FIXES (Do First - ~1 hour)

### Fix #1: Function Name Mismatch (2 mins)
**File:** `static/enhanced.js`
- [ ] Line 2489: Change `showNotification` → `showToast`
- [ ] Line 2609: Change `showNotification` → `showToast`
- [ ] Test: Trigger analytics error, verify toast appears

### Fix #2: Remove Dead Code (2 mins)
**File:** `static/enhanced.js`
- [ ] Delete lines 1123-1131 (dead event listener code)
- [ ] Test: App loads without errors

### Fix #3: Database Consistency (30 mins)
**File:** `app.py`
- [ ] Replace `db.get_portfolio` → `enhanced_db.get_portfolio` (8 locations)
- [ ] Replace `db.get_trades` → `enhanced_db.get_trades` (5 locations)
- [ ] Replace `db.get_model` → `enhanced_db.get_model` (20+ locations)
- [ ] Replace `db.get_provider` → `enhanced_db.get_provider` (6 locations)
- [ ] Replace `db.get_all_models` → `enhanced_db.get_all_models` (5 locations)
- [ ] Test: Create trade, verify appears in all views

**Keep using `db` for:**
- [ ] `db.init_db()` - initialization
- [ ] `db.add_provider()`, `db.update_provider()`, `db.delete_provider()` - if enhanced_db doesn't have them

### Fix #4: Chart Safety Check (5 mins)
**File:** `static/enhanced.js`
- [ ] Line 2399: Add ECharts check to `initAssetAllocationChart()`
  ```javascript
  if (typeof echarts === 'undefined') {
      console.error('ECharts library not loaded');
      return;
  }
  ```
- [ ] Test: Load page with slow network, verify no chart errors

### Fix #5: Consolidate DOMContentLoaded (15 mins)
**File:** `static/enhanced.js`
- [ ] Lines 8-12: Keep this handler, modify it
- [ ] Lines 2790-2798: Delete this handler
- [ ] Merge all initialization into single handler (see CRITICAL_FIXES.md)
- [ ] Test: Page loads in correct order, no duplicate initializations

---

## 🟡 STABILITY FIXES (Do Next - ~4-6 hours)

### Fix #6: Model Validation (20 mins)
**File:** `app.py`
- [ ] Add `validate_model_exists()` helper function
- [ ] Update these endpoints to use it:
  - [ ] `/api/models/<model_id>/portfolio`
  - [ ] `/api/models/<model_id>/trades`
  - [ ] `/api/models/<model_id>/conversations`
  - [ ] `/api/models/<model_id>/risk-status`
  - [ ] `/api/models/<model_id>/settings`
  - [ ] `/api/models/<model_id>/portfolio-metrics`
  - [ ] `/api/models/<model_id>/portfolio-history`
  - [ ] `/api/models/<model_id>/asset-allocation`
  - [ ] `/api/models/<model_id>/performance-analytics`
  - [ ] All other `<model_id>` endpoints
- [ ] Test: Call endpoint with invalid model_id, verify 404 response

### Fix #7: Price Fetching Error Handling (15 mins)
**File:** `app.py`
- [ ] Create `get_current_market_prices()` helper function
- [ ] Replace all price fetching code to use helper
- [ ] Test: Stop market data service, verify error response

### Fix #8: Auto-Refresh Error Recovery (20 mins)
**File:** `static/enhanced.js`
- [ ] Add failure counter to `startAutoRefresh()`
- [ ] Add max retry limit (3 failures)
- [ ] Add exponential backoff
- [ ] Pause refresh after max failures
- [ ] Show user notification when paused
- [ ] Test: Stop backend, verify refresh pauses gracefully

### Fix #9: Null Checks in Risk Cards (10 mins)
**File:** `static/enhanced.js`
- [ ] Update `updateRiskCard()` to check for null/undefined
- [ ] Add default values when data missing
- [ ] Test: Send incomplete risk data, verify no crashes

### Fix #10: Error UI States (30 mins)
**File:** `static/enhanced.js`
- [ ] Add error state to `loadRiskStatus()`
- [ ] Add error state to `loadPortfolioMetrics()`
- [ ] Add error state to `loadAssetAllocation()`
- [ ] Add error state to `loadPerformanceAnalytics()`
- [ ] Add retry buttons to error states
- [ ] Test: Force each endpoint to fail, verify error UI shows

---

## 🟢 VALIDATION FIXES (Do Later - ~8-10 hours)

### Fix #11: Input Validation (2 hours)
**File:** `app.py`
- [ ] Add validation to `POST /api/models`
- [ ] Add validation to `POST /api/providers`
- [ ] Add validation to `POST /api/models/<id>/settings`
- [ ] Add validation to `POST /api/models/<id>/exchange/credentials`
- [ ] Validate all required fields
- [ ] Validate data types
- [ ] Return 400 with clear error messages
- [ ] Test: Send invalid requests, verify proper error responses

### Fix #12: Missing Null Checks (2 hours)
**File:** `static/enhanced.js`
- [ ] Add checks to `loadPortfolioMetrics()`
- [ ] Add checks to `loadPositionsTable()`
- [ ] Add checks to `loadTradeHistory()`
- [ ] Add checks to all chart data processing
- [ ] Test: Send incomplete API responses, verify graceful degradation

### Fix #13: CORS Configuration (5 mins)
**File:** `app.py`
- [ ] Change `CORS(app)` to `CORS(app, origins=[...])`
- [ ] Add localhost:5000 and 127.0.0.1:5000
- [ ] Test: Verify app still works

### Fix #14: Logging Infrastructure (1 hour)
**File:** `app.py`
- [ ] Import logging
- [ ] Configure logging with file handler
- [ ] Replace all `print()` with `logger.info()` / `logger.error()`
- [ ] Test: Verify logs written to file

---

## 🧹 TECHNICAL DEBT (Ongoing)

### Fix #15: Remove Unused Endpoints (1 hour)
**File:** `app.py`
- [ ] Comment out or remove `/api/aggregated/portfolio`
- [ ] Comment out or remove `/api/models/chart-data`
- [ ] Comment out or remove `/api/leaderboard`
- [ ] Comment out or remove `/api/check-update`
- [ ] Comment out or remove deprecated `/api/models/<id>/mode`
- [ ] Document which are removed
- [ ] Test: Verify no frontend calls these

### Fix #16: Hardcoded Constants (30 mins)
**File:** `app.py`
- [ ] Create `SUPPORTED_COINS` constant
- [ ] Replace all hardcoded coin lists
- [ ] Test: Verify app still works

### Fix #17: Error Response Standardization (1 hour)
**File:** `app.py`
- [ ] Define standard success format: `{success: true, data: {...}}`
- [ ] Define standard error format: `{success: false, error: '...'}`
- [ ] Update all endpoints to use standard format
- [ ] Update frontend to expect new format
- [ ] Test: Verify all API calls still work

### Fix #18: Function Shadowing (15 mins)
**File:** `static/enhanced.js`
- [ ] Merge `switchPage()` implementations (lines 89, 2366)
- [ ] Remove redundant fallback code
- [ ] Test: Page switching still works

---

## 📋 TESTING CHECKLIST

After each major fix:
- [ ] No console errors on page load
- [ ] No console errors during normal usage
- [ ] Error toasts appear when features fail
- [ ] Dashboard loads with model selected
- [ ] Model switching works
- [ ] Charts display correctly
- [ ] Auto-refresh works
- [ ] Risk status cards display
- [ ] All pages accessible (Dashboard, Models, Settings, Readiness, Incidents)

---

## 🎯 COMPLETION CRITERIA

**Phase 1 Complete (Critical):**
- [ ] All 🔴 fixes applied
- [ ] All smoke tests pass
- [ ] No runtime errors in console
- [ ] Commit: "fix: critical bugs - function names, database consistency, chart safety"

**Phase 2 Complete (Stability):**
- [ ] All 🟡 fixes applied
- [ ] Error handling robust
- [ ] User sees error messages (not just console logs)
- [ ] Auto-refresh gracefully handles failures
- [ ] Commit: "fix: stability improvements - error handling, validation, recovery"

**Phase 3 Complete (Validation):**
- [ ] All 🟢 fixes applied
- [ ] Input validation on all POST endpoints
- [ ] Comprehensive null checks
- [ ] Security hardened
- [ ] Commit: "fix: validation and security improvements"

**Phase 4 Complete (Tech Debt):**
- [ ] Dead code removed
- [ ] Code standardized
- [ ] Logging implemented
- [ ] Documentation updated
- [ ] Commit: "refactor: clean up technical debt"

---

## 📊 PROGRESS TRACKING

```
Critical Fixes:    [    ] 0/5  (0%)
Stability Fixes:   [    ] 0/5  (0%)
Validation Fixes:  [    ] 0/4  (0%)
Tech Debt:         [    ] 0/4  (0%)
-----------------------------------
TOTAL:             [    ] 0/18 (0%)
```

Update this as you complete fixes!

---

## 🚨 IF STUCK

1. Check `AUDIT_REPORT.md` for detailed explanation
2. Check `CRITICAL_FIXES.md` for code examples
3. Search for line numbers in files
4. Test incrementally (don't batch all changes)
5. Commit after each working fix

---

**Remember:** Fix incrementally, test frequently, commit often!

Good luck! 🚀

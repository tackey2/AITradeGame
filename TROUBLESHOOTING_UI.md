# Enhanced UI Troubleshooting Guide

Based on your testing results, here are the issues and fixes:

---

## Issue 1: "No model to select" ❌

**Problem:** Database is empty (you downloaded fresh, no models exist)

**Fix:**
```bash
# Run the debug script to create a test model:
python debug_ui.py
```

This will create "Test Trading Model" in your database.

**Or manually:**
```bash
python
>>> from database_enhanced import EnhancedDatabase
>>> db = EnhancedDatabase('AITradeGame.db')
>>> conn = db.get_connection()
>>> cursor = conn.cursor()
>>> cursor.execute("INSERT INTO models (name, coins, capital, trading_environment, automation_level) VALUES ('Test Model', 'BTC,ETH', 10000, 'simulation', 'manual')")
>>> conn.commit()
>>> exit()
```

---

## Issue 2: "No notifications when changing" ❌

**Problem:** `showToast()` function not showing toasts

**Possible Causes:**
1. JavaScript error preventing execution
2. Toast CSS not loading
3. Function being called but toast not visible

**Debug Steps:**

1. **Open Browser Console** (F12 → Console tab)
   - Look for red error messages
   - If you see errors, they'll tell us what's wrong

2. **Test Toast Manually:**
   ```javascript
   // In browser console, type:
   showToast('Test message')
   ```
   - If this works → toast function is OK
   - If error → JavaScript didn't load properly

3. **Check if enhanced.js loaded:**
   ```javascript
   // In console:
   typeof showToast
   ```
   - Should say: `"function"`
   - If says `"undefined"` → JavaScript didn't load

---

## Issue 3: "Live warning modal doesn't appear" ❌

**Problem:** Modal not showing when clicking Live radio button

**Possible Causes:**
1. Event listener not attached (JavaScript error earlier prevented it)
2. `showLiveWarning` function not defined
3. Modal CSS not making it visible

**Debug Steps:**

1. **Check if function exists:**
   ```javascript
   // In browser console:
   typeof showLiveWarning
   ```
   - Should be: `"function"`
   - If `"undefined"` → Event listener never attached

2. **Test modal manually:**
   ```javascript
   // In console:
   showLiveWarning(() => console.log('Confirmed'), () => console.log('Cancelled'))
   ```
   - Does modal appear?
   - If yes → Event listener is the problem
   - If no → Modal or CSS is the problem

3. **Check if event listener attached:**
   ```javascript
   // In console:
   document.querySelectorAll('input[name="environment"]').length
   ```
   - Should be: `2` (simulation and live)
   - If `0` → HTML didn't load properly

4. **Force show modal:**
   ```javascript
   // In console:
   document.getElementById('liveWarningModal').classList.add('active')
   ```
   - Does modal appear?
   - If yes → showLiveWarning function is the issue
   - If no → CSS or HTML is the issue

---

## Issue 4: "Badge doesn't update" ❌

**Problem:** Header badge shows `Simulation | Manual` but doesn't change

**Possible Causes:**
1. `updateModeBadge()` not being called
2. API call failing
3. `loadTradingMode()` not running after change

**Debug Steps:**

1. **Check if elements exist:**
   ```javascript
   // In console:
   document.getElementById('currentEnvironmentText')
   document.getElementById('currentAutomationText')
   ```
   - Both should show: `<span>...</span>`
   - If null → HTML structure problem

2. **Test update manually:**
   ```javascript
   // In console:
   updateModeBadge('live', 'semi_automated')
   ```
   - Does badge change to "Live | Semi-Auto"?
   - If yes → loadTradingMode not running
   - If no → updateModeBadge broken

3. **Test loadTradingMode:**
   ```javascript
   // In console (make sure you have model ID 1):
   currentModelId = 1
   loadTradingMode()
   ```
   - Does badge update?
   - Check Network tab for /api/models/1/config call

---

## Issue 5: "Selections don't persist after refresh" ❌

**Problem:** When you refresh, selections reset

**Possible Causes:**
1. Changes not being saved to database
2. Model ID not being set on page load
3. `loadTradingMode()` not being called on page load

**Debug Steps:**

1. **Check if model loads on startup:**
   ```javascript
   // After page loads, in console:
   currentModelId
   ```
   - Should be: `1` (or whatever model ID you have)
   - If `null` → Model not auto-selected

2. **Check Network tab:**
   - Refresh page
   - Go to Network tab in DevTools
   - Should see calls to:
     - `/api/models` (loads model list)
     - `/api/models/1/config` (loads current config)
   - Click on each call to see response

3. **Test database directly:**
   ```bash
   python
   >>> from database_enhanced import EnhancedDatabase
   >>> db = EnhancedDatabase('AITradeGame.db')
   >>> db.get_trading_environment(1)
   >>> db.get_automation_level(1)
   ```
   - Do these return the values you set?

---

## Complete Debug Process

### Step 1: Create Test Model

```bash
# Stop server (Ctrl+C if running)

# Run debug script
python debug_ui.py

# This creates a model if none exists
```

### Step 2: Clear Browser Cache

```
1. Close browser completely
2. Reopen browser
3. Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R on Mac)
```

### Step 3: Check JavaScript Console

```
1. Open Enhanced UI: http://localhost:5000/enhanced
2. Press F12 to open Developer Tools
3. Go to "Console" tab
4. Look for ANY red errors
5. Copy/paste them to share with me
```

### Step 4: Test Functions Manually

In browser console, test each function:

```javascript
// 1. Check current model
console.log('Model ID:', currentModelId)

// 2. Test API
fetch('/api/models/1/config').then(r => r.json()).then(console.log)

// 3. Test badge update
updateModeBadge('live', 'semi_automated')

// 4. Test modal
showLiveWarning(() => console.log('OK'), () => console.log('Cancel'))

// 5. Test toast
showToast('Test message')
```

### Step 5: Check Network Requests

```
1. Open DevTools → Network tab
2. Click "Live" radio button
3. Look for POST to /api/models/1/environment
4. Click on it
5. Check "Response" tab - what does it say?
```

---

## Most Likely Cause

Based on all 5 issues, the **most likely cause** is:

**JavaScript Error Early in File**

If there's a JavaScript error BEFORE the event listeners are attached, then:
- ❌ Event listeners never attach
- ❌ Functions never get called
- ❌ Modal never shows
- ❌ Badge never updates
- ❌ Toast never shows

**How to verify:**
1. Open Console (F12)
2. Look at the VERY FIRST error (if any)
3. That error is preventing everything else from running

---

## Quick Fixes to Try

### Fix 1: Create Model
```bash
python debug_ui.py
```

### Fix 2: Hard Refresh
```
Ctrl+Shift+R (Windows)
Cmd+Shift+R (Mac)
```

### Fix 3: Check Console
```
F12 → Console tab
Look for errors
```

### Fix 4: Test API Manually
```
http://localhost:5000/test_ui_debug.html
```

---

## If Still Not Working

Please share:

1. **Browser Console Errors** (F12 → Console → copy all red errors)
2. **Network Tab** (F12 → Network → screenshot of failed requests)
3. **Database Check:**
   ```bash
   python debug_ui.py
   ```
   Copy the output

4. **Browser & Version:**
   - Chrome/Edge/Firefox?
   - Version number?

With this information, I can pinpoint the exact issue!

---

## Test Page

I've created a simple test page: `test_ui_debug.html`

Access it at: http://localhost:5000/test_ui_debug.html

This page tests:
- API endpoints directly
- Radio button events
- Modal functionality

If this page works but Enhanced UI doesn't, it means there's a specific issue in enhanced.js

---

## Expected Behavior (When Working)

1. **Page Load:**
   - Model dropdown shows "Test Trading Model"
   - Model is auto-selected
   - Environment radio shows current (e.g., Simulation checked)
   - Automation radio shows current (e.g., Manual checked)
   - Badge shows: "Simulation | Manual"

2. **Change Environment to Live:**
   - Click "Live" radio
   - 🚨 Warning modal appears immediately
   - Click "Yes, Switch to Live"
   - Modal closes
   - Toast shows: "Environment changed to Live"
   - Badge updates to: "Live | Manual"

3. **Change Automation:**
   - Click "Semi-Auto" radio
   - Toast shows: "Automation changed to Semi-Auto"
   - Badge updates to: "Live | Semi-Auto"

4. **Refresh Page:**
   - Badge still shows: "Live | Semi-Auto"
   - Live radio still checked
   - Semi-Auto radio still checked

---

## Common Issues on Windows

### Issue: Port Already in Use
```
Error: Address already in use
```

**Fix:**
```bash
# Find process using port 5000
netstat -ano | findstr :5000

# Kill it (use the PID from above)
taskkill /PID <PID> /F

# Restart server
python app.py
```

### Issue: Python Not Found
```
'python' is not recognized
```

**Fix:**
```bash
# Try python3 instead
python3 app.py

# Or use full path
C:\Python311\python.exe app.py
```

### Issue: Module Not Found
```
ModuleNotFoundError: No module named 'flask'
```

**Fix:**
```bash
# Install requirements
pip install flask flask-cors openai

# Or from requirements file
pip install -r requirements.txt
```

---

## Next Steps

1. ✅ Run `python debug_ui.py` to create a test model
2. ✅ Start server: `python app.py`
3. ✅ Open http://localhost:5000/test_ui_debug.html
4. ✅ Test if basic functions work
5. ✅ Open http://localhost:5000/enhanced
6. ✅ Open Console (F12) and check for errors
7. ✅ Share any errors you see

I'm here to help debug further!

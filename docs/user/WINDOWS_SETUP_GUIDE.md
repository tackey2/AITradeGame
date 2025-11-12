# Windows Setup & Testing Guide

## Quick Start for Windows

Follow these steps to get the Enhanced UI running on your Windows laptop.

---

## Prerequisites

### 1. Check Python Installation

Open **Command Prompt** (or PowerShell):
- Press `Win + R`
- Type `cmd` and press Enter

Check if Python is installed:
```cmd
python --version
```

**Expected:** Python 3.8 or higher (e.g., "Python 3.11.0")

**If Python is not installed:**
1. Download from: https://www.python.org/downloads/
2. **IMPORTANT:** Check "Add Python to PATH" during installation
3. Restart Command Prompt after installation

---

## Step-by-Step Setup

### Step 1: Navigate to Project Folder

Open Command Prompt and navigate to your project:
```cmd
cd C:\path\to\AITradeGame
```

**Example:**
```cmd
cd C:\Users\YourName\Downloads\AITradeGame
```

**Tip:** You can also:
1. Open the folder in File Explorer
2. Type `cmd` in the address bar
3. Press Enter (Command Prompt opens in that folder)

---

### Step 2: Install Python Dependencies

Run this command to install all required packages:
```cmd
pip install flask flask-cors openai requests python-binance cryptography python-dotenv APScheduler
```

**Expected:** You'll see installation progress for each package.

**If you get "pip is not recognized":**
```cmd
python -m pip install flask flask-cors openai requests python-binance cryptography python-dotenv APScheduler
```

**This will take 1-2 minutes.**

---

### Step 3: Create Test Data

Run the setup script to create a test model:
```cmd
python test_setup.py
```

**Expected output:**
```
============================================================
ENHANCED UI TEST SETUP
============================================================
✅ Enhanced database schema initialized

1. Checking existing providers...
   Found 0 provider(s)

2. Creating test provider...
   ✓ Provider created: ID 1

3. Creating test model...
   ✓ Model created: ID 1

...

============================================================
SETUP COMPLETE!
============================================================
```

**This creates:**
- SQLite database: `AITradeGame.db`
- Test provider (OpenAI)
- Test model with $10,000 capital
- Default settings

---

### Step 4: Test the API (Optional but Recommended)

Verify all endpoints work:
```cmd
python quick_test.py
```

**Expected output:**
```
============================================================
QUICK ENHANCED API TEST
============================================================

1. Get models... ✓
2. Get trading mode... ✓
3. Get settings... ✓
4. Update settings... ✓
5. Get risk status... ✓
6. Get pending decisions... ✓
7. Get readiness... ✓
8. Get incidents... ✓
9. Set mode to semi_automated... ✓
10. Reset mode to simulation... ✓
11. Enhanced page loads... ✓

============================================================
ALL TESTS PASSED! ✓
============================================================
```

**If this fails:** The Flask server isn't running yet. That's fine, we'll start it in the next step.

---

### Step 5: Start the Flask Server

Start the web server:
```cmd
python app.py
```

**Expected output:**
```
============================================================
AITradeGame - Starting...
============================================================
[INFO] Initializing database...
✅ Enhanced database schema initialized
[INFO] Database initialized
[INFO] Initializing trading engines...
[INFO] Initialized 1 engine(s)

[INFO] Auto-trading enabled

============================================================
AITradeGame is running!
Server: http://localhost:5000
Press Ctrl+C to stop
============================================================
```

**The server is now running!**

**Notes:**
- Keep this Command Prompt window open
- The server will run continuously
- You'll see log messages as you use the UI
- To stop: Press `Ctrl + C`

**If you see errors:**
- Check that port 5000 is not in use by another program
- Make sure all dependencies installed correctly
- Check for error messages and note them

---

### Step 6: Open the Enhanced Dashboard

**Option 1: Automatic (if it didn't open)**
- The server should automatically open your browser
- If not, continue to Option 2

**Option 2: Manual**
1. Open your web browser (Chrome, Firefox, Edge)
2. Type in the address bar: `http://localhost:5000/enhanced`
3. Press Enter

**Expected:** You should see the Enhanced Dashboard with:
- Dark themed interface
- Header: "Personal Trading System"
- Green mode badge: "Simulation"
- Navigation buttons
- Model selector dropdown

---

## 🎯 Now Test the UI!

### Quick 5-Minute Test

**1. Select Your Model**
- Click the dropdown under "Select Model"
- Choose "Test Trading Model"
- Risk status cards should populate

**2. Switch Trading Modes**
- Click "Semi-Automated" radio button
- Watch the header badge change from green to yellow/orange
- Header text changes to "Semi-Auto"
- Switch back to "Simulation"

**3. Visit Settings Page**
- Click "Settings" in navigation
- See 7 risk parameters with values
- Hover over a "?" icon to see tooltip
- Change "Max Position Size" to 15
- Click "Save Settings"
- You should see toast: "Settings saved successfully"

**4. Check Readiness**
- Click "Readiness" in navigation
- See score circle: "0 /100"
- Message: "Need at least 10 trades for assessment"

**5. View Incidents**
- Click "Incidents" in navigation
- Should see at least 2 logged events
- Check timestamps and messages

**6. Back to Dashboard**
- Click "Dashboard" in navigation
- Everything should still work

---

## 📋 Detailed Testing Checklist

For comprehensive testing, open this file in your project folder:
```
BROWSER_TEST_CHECKLIST.md
```

This has 15 detailed test steps covering every feature.

---

## 🐛 Troubleshooting

### Problem: "python is not recognized"
**Solution:**
1. Reinstall Python from python.org
2. Check "Add Python to PATH" during installation
3. Restart Command Prompt

### Problem: "pip is not recognized"
**Solution:** Use `python -m pip` instead of `pip`:
```cmd
python -m pip install flask flask-cors ...
```

### Problem: "Port 5000 is already in use"
**Solution:**
1. Find what's using port 5000:
   ```cmd
   netstat -ano | findstr :5000
   ```
2. Kill that process in Task Manager
3. Or change port in `app.py` (last line: change 5000 to 5001)

### Problem: Browser shows "Can't connect" or "Page not found"
**Solution:**
1. Check server is running (Command Prompt should show log messages)
2. Try: `http://localhost:5000/enhanced` (not https)
3. Try: `http://127.0.0.1:5000/enhanced`
4. Check Windows Firewall isn't blocking Python

### Problem: Page loads but shows errors
**Solution:**
1. Press F12 to open Developer Tools
2. Click "Console" tab
3. Look for red error messages
4. Note the error and share it with me

### Problem: Risk status shows "--" instead of values
**Solution:**
1. Wait 2-3 seconds for data to load
2. Make sure you selected a model from dropdown
3. Click refresh button (↻) in header
4. Check Command Prompt for error messages

### Problem: Database errors
**Solution:**
Reset the database:
```cmd
del AITradeGame.db
python test_setup.py
python app.py
```

---

## 📁 Your Project Folder Should Have

After setup, you should see these files:
```
AITradeGame/
├── app.py                          (Flask server)
├── database_enhanced.py            (Database with enhanced features)
├── trading_modes.py                (Mode-aware execution)
├── risk_manager.py                 (Risk validation)
├── notifier.py                     (Notifications)
├── explainer.py                    (AI explanations)
├── test_setup.py                   (Setup test data)
├── quick_test.py                   (API tests)
├── AITradeGame.db                  (SQLite database - created after setup)
├── templates/
│   ├── index.html                  (Classic view)
│   └── enhanced.html               (Enhanced dashboard)
├── static/
│   ├── enhanced.css                (Enhanced dashboard styles)
│   └── enhanced.js                 (Enhanced dashboard logic)
└── BROWSER_TEST_CHECKLIST.md       (Testing guide)
```

---

## 🎮 What to Test

### Core Features to Try:

**✓ Model Selection**
- Dropdown works
- Risk cards populate after selection

**✓ Trading Mode Switching**
- Can switch between 3 modes
- Header badge changes color
- Toast notifications appear

**✓ Risk Status**
- 5 cards visible
- All show "OK" status
- Values displayed (not "--")

**✓ Settings Management**
- Can view all 7 parameters
- Tooltips show on hover
- Can modify and save
- Values persist after refresh

**✓ Navigation**
- All 4 pages load
- Active page highlighted
- Back/forward works

**✓ Readiness Monitor**
- Score displays (0/100 initially)
- 7 metrics shown
- Message explains status

**✓ Incidents Log**
- Events listed with timestamps
- Color-coded severity
- Refresh button works

---

## 📊 Expected Behavior

### Initial State:
- **Trading Mode:** Simulation (green)
- **Risk Status:** All "OK" (green)
- **Pending Decisions:** 0 (empty)
- **Readiness Score:** 0/100 (need trades)
- **Incidents:** 2+ events logged

### After Mode Switch:
- **Semi-Auto:** Badge turns yellow/orange
- **Full-Auto:** Badge turns red (don't use yet!)

### After Saving Settings:
- Toast notification appears
- Values persist after refresh
- New incident logged

---

## 🔍 Things to Look For

### Good Signs ✓
- Dark theme applied
- All pages load quickly
- No console errors
- Toast notifications appear
- Settings save successfully
- Navigation smooth

### Red Flags ✗
- White/blank pages
- Console errors (F12)
- Settings don't save
- Risk status stuck on "--"
- 404 errors
- Slow loading (>5 seconds)

---

## 💡 Pro Tips

**Tip 1: Use Chrome/Edge for Best Results**
- Better developer tools
- Easier debugging
- Best compatibility

**Tip 2: Keep Developer Tools Open**
- Press F12
- Click "Console" tab
- Watch for errors as you click

**Tip 3: Test in This Order**
1. Basic loading
2. Model selection
3. Mode switching
4. Settings
5. Navigation
6. Advanced features

**Tip 4: Take Screenshots**
- If you find a bug
- Screenshot helps me understand
- Press `Win + Shift + S` to screenshot

**Tip 5: Note What Confuses You**
- Unclear labels?
- Missing explanations?
- Unexpected behavior?
- Your feedback makes it better!

---

## 🎯 Success Checklist

You're ready to move forward if:
- [✓] Server starts without errors
- [✓] Dashboard loads at localhost:5000/enhanced
- [✓] Can select model from dropdown
- [✓] Can switch trading modes
- [✓] Risk status shows "OK" on all cards
- [✓] Settings page loads and saves
- [✓] All 4 pages accessible
- [✓] No critical errors in console

---

## 📞 Report Your Findings

After testing, tell me:

**What works:**
- "Model selection works perfectly"
- "Mode switching is smooth"
- etc.

**What doesn't work:**
- "Risk cards show '--'"
- "Can't save settings"
- "Page is blank"
- etc.

**What's confusing:**
- "What does Max Drawdown mean?"
- "When should I switch to Semi-Auto?"
- "Where are the pending decisions?"
- etc.

**Suggestions:**
- "Add a help button"
- "Explain tooltips better"
- "Change this color"
- etc.

---

## 🚀 Next Steps

After successful testing:

**Week 3:**
- Fix any bugs you find
- Improve UX based on feedback
- Binance exchange integration
- Real trading capability

**Week 4:**
- Docker setup for Windows
- Production deployment
- Documentation
- Real money testing (small amounts)

---

## 📝 Quick Reference Commands

**Navigate to project:**
```cmd
cd C:\path\to\AITradeGame
```

**Install dependencies:**
```cmd
pip install flask flask-cors openai requests python-binance cryptography python-dotenv APScheduler
```

**Setup test data:**
```cmd
python test_setup.py
```

**Run API tests:**
```cmd
python quick_test.py
```

**Start server:**
```cmd
python app.py
```

**Access dashboard:**
```
http://localhost:5000/enhanced
```

**Stop server:**
```
Press Ctrl + C in Command Prompt
```

**Reset database:**
```cmd
del AITradeGame.db
python test_setup.py
```

---

## ✅ You're Ready!

**Start here:**
1. Open Command Prompt in project folder
2. Run: `pip install flask flask-cors openai requests python-binance cryptography python-dotenv APScheduler`
3. Run: `python test_setup.py`
4. Run: `python app.py`
5. Open browser: `http://localhost:5000/enhanced`
6. Start testing!

**Good luck!** 🎉

Let me know what you find!

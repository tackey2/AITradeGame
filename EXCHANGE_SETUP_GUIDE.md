# Exchange Setup Guide - Complete Walkthrough

**For:** AITradeGame Week 3 - Exchange Integration
**Date:** November 12, 2025

This guide will walk you through setting up Binance exchange credentials and starting live trading (on testnet).

---

## 📋 Prerequisites

Before you begin, you'll need:

1. ✅ AITradeGame installed and running
2. ✅ Python dependencies installed (`pip install -r requirements.txt`)
3. ✅ A Binance Testnet account (we'll create this together)

**Important:** We'll start with **Testnet** (fake money) for safe testing!

---

## 🚀 Part 1: Get Binance Testnet Account (5 minutes)

### Step 1.1: Create Testnet Account

1. Open your browser and go to: **https://testnet.binance.vision/**

2. Click **"Register"** in the top right

3. Fill in:
   - Email: Your email address
   - Password: Create a strong password

4. Click **"Register"**

5. Check your email and verify your account

6. **Log in** to Binance Testnet

### Step 1.2: Get Free Test Funds

1. Once logged in, you'll see your testnet wallet
2. Click on **"Faucet"** or look for **"Get Test Funds"**
3. Binance Testnet automatically gives you test BTC, ETH, USDT, etc.
4. These are **fake coins** for testing - no real money involved!

### Step 1.3: Create API Keys

**This is the most important step!**

1. In Binance Testnet, click on your profile icon (top right)

2. Click **"API Management"** or go to:
   https://testnet.binance.vision/api-management.html

3. Click **"Create API"**

4. You'll be asked to name your API key:
   - Name: `AITradeGame-Test`
   - Click **"Create"**

5. **IMPORTANT:** You'll see two keys:
   ```
   API Key:    abc123def456... (long string)
   Secret Key: xyz789uvw012... (long string)
   ```

6. **COPY BOTH KEYS** and save them somewhere safe temporarily
   - We'll use these in Part 2
   - You can only see the Secret Key ONCE!

7. **Set Permissions:**
   - Make sure **"Enable Reading"** is checked ✅
   - Make sure **"Enable Spot & Margin Trading"** is checked ✅
   - **DO NOT** check "Enable Withdrawals" (for safety)

8. Click **"Save"**

**✅ You now have Testnet API keys!**

---

## 🖥️ Part 2: Configure AITradeGame (10 minutes)

### Step 2.1: Start the Application

1. Open terminal/command prompt

2. Navigate to AITradeGame folder:
   ```bash
   cd /path/to/AITradeGame
   ```

3. Start the Flask server:
   ```bash
   python app.py
   ```

4. You should see:
   ```
   * Running on http://127.0.0.1:5000
   ✅ Enhanced database schema initialized
   [OK] Model 1 line present
   ```

5. Open your web browser and go to:
   ```
   http://localhost:5000/enhanced
   ```

### Step 2.2: Select Your Model

1. At the top of the page, you'll see **"Select Model"**

2. Click the dropdown and select your model (e.g., "Test Trading Model")

3. The model should load - you'll see the Dashboard

### Step 2.3: Navigate to Settings

1. Look at the navigation bar on the left side

2. Click the **"Settings"** tab (it has a sliders icon 🎚️)

3. You'll see **"Risk Management Settings"**

4. **Scroll down** until you see **"Exchange Configuration"**

### Step 2.4: Enter Your Testnet Credentials

**Now we'll use the API keys from Part 1!**

1. Find the **"Exchange Environment"** section

2. Make sure **"Testnet"** is selected (it should be green with a shield icon 🛡️)
   - This is the default and recommended option
   - If "Mainnet" is selected, click "Testnet"

3. Scroll down to **"Testnet Credentials (Safe Testing)"**

4. Enter your credentials:

   **Testnet API Key:**
   - Click in the "Testnet API Key" field
   - Paste the API Key you copied from Binance Testnet
   - Example: `abc123def456ghi789...`

   **Testnet API Secret:**
   - Click in the "Testnet API Secret" field
   - Paste the Secret Key you copied
   - You'll see dots (••••••) - this is for security
   - Click the eye icon (👁️) if you want to verify what you typed
   - Example: `xyz789uvw012rst345...`

5. **Leave the "Mainnet Credentials" section empty** for now
   - We don't need real money credentials yet!

### Step 2.5: Save Your Credentials

1. Click the **"Save Credentials"** button (blue button with save icon 💾)

2. You should see a toast notification:
   ```
   ✅ Exchange credentials saved successfully
   ```

3. **Notice:** The input fields are now empty
   - This is a security feature
   - Your credentials are saved in the database
   - They won't be displayed again (for security)

4. Check the **"Exchange Status Card"** at the top:
   - **Exchange Connection:** Should now say "Configured" (green ✅)
   - **Testnet Credentials:** Should say "Configured" (green badge)
   - **Mainnet Credentials:** Will still say "Not Set" (that's okay!)

### Step 2.6: Validate Your Connection

**Let's test if the credentials work!**

1. Click the **"Validate Connection"** button (gray button with checkmark ✅)

2. The button will change to:
   ```
   ⏳ Validating...
   ```

3. Wait 2-3 seconds while it tests the connection to Binance Testnet

4. **If successful:**
   ```
   ✅ Toast: "Credentials validated successfully!"
   ```
   - **Last Validated:** Will show current date/time

5. **If it fails:**
   ```
   ❌ Toast: "Credential validation failed. Please check your API keys."
   ```
   - Go back to Step 2.4 and re-enter your credentials
   - Make sure you copied the ENTIRE key (no spaces at the end)

**✅ Your exchange is now configured and validated!**

---

## 🎯 Part 3: Configure Live Trading (5 minutes)

Now let's set up the trading system to use your exchange credentials.

### Step 3.1: Navigate to Dashboard

1. Click the **"Dashboard"** tab in the left navigation

2. You should see several sections:
   - Select Model (already selected)
   - Trading Environment
   - Automation Level

### Step 3.2: Set Trading Environment

1. Find the **"Trading Environment"** section

2. You'll see two options:
   - **Simulation (Paper Trading)** - Database only
   - **Live Trading** - Real exchange (testnet or mainnet)

3. Click **"Live Trading"** radio button

4. A modal will appear:
   ```
   ⚠️ Switch to Live Trading?

   Are you sure you want to enable live trading?
   This will execute trades on a real exchange...
   ```

5. **Read the checklist:**
   - [x] Exchange credentials are configured
   - [x] I have tested thoroughly in simulation
   - [x] I understand this uses real exchange APIs
   - [x] I am using Testnet for safe testing

6. Click **"Yes, Enable Live Trading"**

7. The badge at the top should now show:
   ```
   Live | Manual
   ```

### Step 3.3: Set Automation Level

**Choose how much control you want:**

**Option A: Manual (View Only)** - Recommended for first time
- AI makes decisions but doesn't execute
- You can see what the AI wants to do
- Good for learning and observation
- **Select this if:** You want to understand the system first

**Option B: Semi-Automated (Review & Approve)** - Recommended for testing
- AI creates pending decisions
- You review and approve each trade
- You stay in full control
- **Select this if:** You want to test with real execution but approve each trade

**Option C: Fully Automated (Autonomous)** - Only when ready!
- AI trades automatically after risk checks
- No approval needed
- Use only after extensive testing
- **Select this if:** You've tested extensively and trust the system

**For your first time, I recommend:**
1. Click **"Semi-Automated (Review & Approve)"**

2. The badge should now show:
   ```
   Live | Semi-Automated
   ```

**✅ You're now configured for live trading on Testnet!**

---

## 🧪 Part 4: Test a Trade (10 minutes)

Let's test the complete system!

### Step 4.1: Wait for AI Decision

**Important:** The AI runs on a schedule (default: every 60 minutes)

**To test immediately:**

You have two options:

**Option A: Wait for the next cycle**
- The system will automatically run within the next hour
- You'll see a notification when decisions are ready

**Option B: Manually trigger (requires code modification)**
- This requires running the trading cycle manually
- See "MANUAL_TESTING.md" for instructions

### Step 4.2: Review Pending Decisions

1. When the AI makes a decision, you'll see a notification (if using Semi-Automated)

2. The notification will say something like:
   ```
   🔔 Trade Approval Needed: BTC
   AI wants to BUY 0.001 BTC
   ```

3. You can review the decision in the Dashboard

### Step 4.3: Approve the Trade

1. Click on the pending decision

2. Review:
   - Coin: BTC
   - Action: BUY
   - Quantity: 0.001
   - Current Price: $43,250
   - Reasoning: (AI explanation)

3. Click **"Approve"**

4. The system will:
   - Call Binance Testnet API
   - Place a market order for 0.001 BTC
   - Update your database with the position
   - Show you the result

5. **Success looks like:**
   ```
   ✅ Trade Executed: BUY 0.001 BTC @ $43,250
   Order ID: 12345678
   ```

### Step 4.4: Verify on Binance Testnet

**Let's confirm the trade actually executed!**

1. Go back to https://testnet.binance.vision/

2. Log in to your account

3. Click **"Orders"** → **"Order History"**

4. You should see:
   ```
   Symbol: BTCUSDT
   Side: BUY
   Type: MARKET
   Quantity: 0.001
   Status: FILLED
   Time: (current time)
   ```

5. Click **"Wallet"** → **"Spot Wallet"**

6. You should now see:
   - BTC balance increased by 0.001
   - USDT balance decreased by ~$43.25

**🎉 Congratulations! You just executed a live trade on Binance Testnet!**

---

## 🛡️ Part 5: Safety & Best Practices

### Safety Checklist

✅ **Always start with Testnet**
- Never use Mainnet until you've done extensive testing
- Testnet uses fake money - it's completely safe

✅ **Use Semi-Automated mode first**
- Don't jump straight to Fully Automated
- Approve each trade manually until you're confident

✅ **Set conservative risk parameters**
- Settings → Risk Management Settings
- Max Position Size: 10% or less
- Max Daily Loss: 3% or less

✅ **Monitor regularly**
- Check the Dashboard daily
- Review the Incidents page for any issues
- Keep an eye on your Binance account

✅ **Never share your API keys**
- Don't post them anywhere
- Don't share your database file
- Treat them like passwords

### If Something Goes Wrong

**Emergency Stop:**
- Click the red **"STOP"** button in the header
- This will pause all trading immediately

**Delete Credentials:**
- Settings → Exchange Configuration
- Click "Delete Credentials"
- This will disconnect from the exchange

**Check Incidents:**
- Navigate to the "Incidents" tab
- Review any errors or warnings
- The system logs all important events

---

## 📊 Part 6: Understanding the Dashboard

### Exchange Status Card (Settings Page)

```
Exchange Connection: Configured ✅
Mainnet Credentials: Not Set
Testnet Credentials: Configured ✅
Last Validated: 11/12/2025, 3:45:23 PM
```

**What it means:**
- **Configured (green):** Exchange is connected and ready
- **Not Set (red):** Credentials not entered
- **Last Validated:** When you last tested the connection

### Trading Badge (Top of Page)

```
● Simulation | Manual
```

**Badge Colors:**
- **Green ●** - Simulation mode (safe)
- **Yellow ●** - Live + Manual (view only)
- **Orange ●** - Live + Semi-Auto (approval needed)
- **Red ●** - Live + Full-Auto (autonomous)

### Portfolio Section

Shows your current positions:
- **Cash:** Available USDT
- **Positions:** Open trades (BTC, ETH, etc.)
- **Total Value:** Portfolio worth
- **P&L:** Profit/Loss

---

## 🚀 Part 7: Next Steps

### Once You're Comfortable with Testnet:

**1. Test Different Scenarios**
- Try buying different coins
- Test selling positions
- Try the "Emergency Stop" button
- Switch between Manual and Semi-Auto

**2. Monitor Performance**
- Let it run for a few days
- Review the trade history
- Check win rate and P&L
- Adjust risk settings if needed

**3. Review Readiness Score**
- Navigate to "Readiness" tab
- This shows if you're ready for Full-Auto
- Need: High approval rate, good win rate, consistent performance

### When Ready for Mainnet (Real Money):

**⚠️ ONLY after extensive testnet testing!**

1. Create Binance **Mainnet** account: https://www.binance.com
2. Complete full KYC verification
3. Create Mainnet API keys
4. Return to Settings → Exchange Configuration
5. Enter Mainnet credentials in the "REAL MONEY" section
6. Validate connection
7. Set Exchange Environment to "Mainnet"
8. Start with **very small amounts**
9. Use Semi-Automated mode first
10. Monitor closely!

---

## ❓ Troubleshooting

### Problem: "Credentials validation failed"

**Solution:**
1. Go to Binance Testnet
2. Check API Management → Your API key
3. Make sure **"Enable Reading"** is checked
4. Make sure **"Enable Spot Trading"** is checked
5. Copy the keys again (make sure no extra spaces)
6. Delete old credentials in AITradeGame
7. Re-enter and save
8. Try validating again

### Problem: "Exchange not configured" error when trying to trade

**Solution:**
1. Go to Settings → Exchange Configuration
2. Check if status shows "Configured"
3. If not, re-enter credentials and save
4. Validate connection
5. Return to Dashboard and try again

### Problem: Trade not appearing on Binance

**Solution:**
1. Check Incidents tab for errors
2. Verify you're on the right Binance environment:
   - Settings shows "Testnet" → Check testnet.binance.vision
   - Settings shows "Mainnet" → Check binance.com
3. Check order history on Binance (may take a few seconds)
4. Verify your API keys have trading permissions

### Problem: Input fields are empty when I return to Settings

**This is normal!**
- For security, credentials are cleared after saving
- They're safely stored in the database
- The status card shows if they're configured
- You don't need to re-enter them unless you're changing them

---

## 📞 Need Help?

If you encounter issues:

1. Check the **Incidents** tab in the UI
2. Check the console where you ran `python app.py`
3. Review the documentation:
   - `EXCHANGE_CLIENT_GUIDE.md` - Exchange client details
   - `WEEK3_PHASE_B_COMPLETE.md` - Integration details
   - `WEEK3_PHASE_C_COMPLETE.md` - UI details

---

## ✅ Quick Reference

### Key URLs
- **AITradeGame:** http://localhost:5000/enhanced
- **Binance Testnet:** https://testnet.binance.vision/
- **Binance Mainnet:** https://www.binance.com

### Key Files
- **Start app:** `python app.py`
- **Database:** `AITradeGame.db`
- **Logs:** Check console output

### Key Settings
- **Exchange Configuration:** Settings → Scroll to bottom
- **Trading Environment:** Dashboard → Trading Environment section
- **Automation Level:** Dashboard → Automation Level section
- **Emergency Stop:** Red button in header

---

**Happy Trading! Remember: Start with Testnet, test thoroughly, and never risk more than you can afford to lose.** 🚀

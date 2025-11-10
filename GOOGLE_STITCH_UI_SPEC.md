# Google Stitch UI Specification
## AI Personal Trading System

---

## A. General Project & Branding Guidelines

| Section | Detail | Specification |
|:--------|:-------|:--------------|
| **Project Goal** | A personal AI-powered trading system for cryptocurrency and stock trading with comprehensive learning features, risk management, and automated/semi-automated execution modes. | |
| **Platform** | Responsive web application optimized for desktop (primary) and tablet. Mobile-responsive for monitoring. | |
| **Branding/Style** | **Modern Financial Dashboard Aesthetic**<br>- Primary Color: Deep Blue (#1E40AF) - trust, stability<br>- Accent Color: Emerald Green (#10B981) - profit, growth<br>- Warning Color: Amber (#F59E0B) - caution<br>- Danger Color: Red (#EF4444) - loss, alerts<br>- Background: Dark theme with #1F2937 (dark gray) and #111827 (darker gray)<br>- Cards: #374151 (medium gray) with subtle shadows<br>- Text: White (#FFFFFF) primary, Gray (#9CA3AF) secondary<br>- Design System: Modern, clean, data-dense (like Bloomberg Terminal meets modern SaaS)<br>- Typography: Monospace for numbers (Fira Code), Sans-serif for text (Inter)<br>- Icons: Simple, outlined style (Lucide or Heroicons) | |
| **Target User** | Individual traders/investors (ages 25-45) who want to learn trading while using AI assistance. Tech-savvy, detail-oriented, values transparency over gamification. | |

---

## B. Screen-by-Screen Breakdown

### Screen 1: Dashboard (Home Screen)

| Element | Detail | Specification |
|:--------|:-------|:--------------|
| **Screen Name** | Main Dashboard | |
| **Core Function** | At-a-glance view of all trading models' performance, recent trades, and system status. Primary navigation hub. | |
| **Layout Structure** | <br>**Header Bar (sticky):**<br>- App logo (left)<br>- Model selector dropdown (center-left)<br>- Mode indicator badge (Simulation/Semi-Auto/Full-Auto)<br>- Emergency "Kill Switch" button (right, red)<br>- Settings icon (right)<br><br>**Main Content (3-column grid):**<br>- Left column (30%): Model list + portfolio summary<br>- Center column (45%): Performance chart<br>- Right column (25%): Recent activity feed<br><br>**Navigation Sidebar (left, collapsible):**<br>- Dashboard (active)<br>- Trading<br>- Journal<br>- Analytics<br>- Settings | |
| **Required Components** | **1. Model List Card:**<br>- List of all trading models<br>- Each row shows: Model name, Current mode, P&L today, Total return %<br>- Status indicator (green=active, yellow=paused, red=error)<br>- Click to select model<br><br>**2. Portfolio Summary Card:**<br>- Total account value (large, prominent)<br>- Cash available<br>- Open positions count<br>- Today's P&L (with % and $)<br>- Total return since inception<br><br>**3. Performance Chart:**<br>- Line chart showing account value over time<br>- Multi-line if multiple models<br>- Date range selector (24h, 7d, 30d, All)<br>- Interactive tooltips on hover<br><br>**4. Recent Activity Feed:**<br>- Scrollable list of recent events<br>- Trade executions, approvals needed, alerts<br>- Timestamp for each event<br>- Color-coded by type<br><br>**5. Quick Stats Bar (above chart):**<br>- Win Rate, Total Trades, Avg Win, Avg Loss<br>- Small sparkline charts | |
| **Data Fields** | - Model name, status, mode<br>- Total value, cash, positions count<br>- P&L (daily, total)<br>- Return percentage<br>- Chart data (timestamps, values)<br>- Activity log (event type, message, timestamp) | |
| **Action Buttons** | - "Add New Model" (primary button)<br>- "Emergency Stop All" (danger button, top right)<br>- "Refresh Data" (icon button)<br>- Model-specific: "Pause", "Resume", "Settings" | |
| **Layout Notes** | - Chart should be largest visual element<br>- Use card-based layout with subtle shadows<br>- Ensure numbers are easily scannable (large, monospace font)<br>- Color-code P&L: green (positive), red (negative) | |

---

### Screen 2: Trading Control Panel

| Element | Detail | Specification |
|:--------|:-------|:--------------|
| **Screen Name** | Trading Control | |
| **Core Function** | Active trading interface showing current positions, pending decisions (semi-auto), and manual controls. | |
| **Layout Structure** | **Two-column layout:**<br>- Left column (60%): Current positions table + pending decisions<br>- Right column (40%): Market data + manual trade entry<br><br>**Tabs at top:**<br>- "Positions"<br>- "Pending Approvals" (with badge if any)<br>- "Manual Trade" | |
| **Required Components** | **1. Positions Table:**<br>- Columns: Asset, Side (Long/Short), Quantity, Entry Price, Current Price, P&L, P&L %, Actions<br>- Row actions: "View Details", "Close Position"<br>- Sort by: Asset, P&L, Entry time<br>- Filter by: Profit/Loss, Asset type<br><br>**2. Pending Approval Card (Semi-Auto Mode):**<br>- Large card for each pending decision<br>- Shows: Asset, AI decision (Buy/Sell/Hold), Quantity, Reasoning (collapsible)<br>- Price chart for the asset (small inline chart)<br>- Confidence score (progress bar)<br>- Risk metrics (position size %, max loss)<br>- Approve/Reject buttons (primary/secondary)<br>- "Modify" button (opens modal)<br>- Countdown timer (decision expires in X minutes)<br><br>**3. Market Data Panel:**<br>- Live price tickers for supported assets<br>- Price, 24h change %, Volume<br>- Mini chart for each asset<br>- "Add to Watchlist" icon<br><br>**4. Manual Trade Form (if needed):**<br>- Asset selector<br>- Order type (Market/Limit)<br>- Side (Buy/Sell)<br>- Quantity input<br>- Price input (if limit)<br>- Stop loss / Take profit (optional)<br>- "Preview Order" button | |
| **Data Fields** | - Position: asset, side, quantity, entry_price, current_price, pnl, pnl_pct<br>- Pending decision: asset, action, quantity, reasoning, confidence, risk_pct<br>- Market data: symbol, price, change_24h, volume<br>- Order: asset, type, side, quantity, price, stop_loss, take_profit | |
| **Action Buttons** | - "Approve Trade" (green, primary)<br>- "Reject Trade" (red, secondary)<br>- "Modify Before Executing" (blue, secondary)<br>- "Close Position" (amber)<br>- "Close All Positions" (danger, requires confirmation)<br>- "Submit Manual Trade" | |
| **Layout Notes** | - Pending approvals should be prominently displayed when in Semi-Auto mode<br>- Use a queue/card stack metaphor for pending decisions<br>- Real-time price updates (WebSocket or polling)<br>- Clear visual separation between automated and manual trading | |

---

### Screen 3: AI Explainability View

| Element | Detail | Specification |
|:--------|:-------|:--------------|
| **Screen Name** | AI Decision Explanation | |
| **Core Function** | Detailed breakdown of why AI made a specific trading decision. Educational and transparent. | |
| **Layout Structure** | **Single-column, card-based vertical scroll:**<br>- Decision summary card (top)<br>- Market analysis card<br>- Technical indicators card<br>- Risk assessment card<br>- Position sizing rationale card<br>- Historical pattern match card<br><br>**Explanation level toggle (top right):**<br>- Beginner / Intermediate / Advanced | |
| **Required Components** | **1. Decision Summary Card:**<br>- Large heading: "BUY 0.5 BTC @ $50,000"<br>- Confidence meter (0-100%)<br>- Timestamp<br>- Quick stats: Expected return, Risk, Time horizon<br><br>**2. Market Analysis Card:**<br>- Current price vs. moving averages<br>- Support/Resistance levels (visual diagram)<br>- Trend direction indicator<br>- Volume analysis<br><br>**3. Technical Indicators Card:**<br>- RSI gauge (visual, colored zones: oversold/neutral/overbought)<br>- MACD chart (small inline)<br>- Moving averages (SMA-7, SMA-14, SMA-50)<br>- Each indicator with interpretation text<br><br>**4. Risk Assessment Card:**<br>- Win probability (percentage)<br>- Risk:Reward ratio (visual scale)<br>- Worst/Best case scenarios (with $ amounts)<br>- Expected value calculation<br><br>**5. Position Sizing Card:**<br>- Portfolio value<br>- Risk per trade %<br>- Stop loss distance<br>- Calculation breakdown (step-by-step math)<br><br>**6. Pattern Recognition Card:**<br>- Similar past setups (count)<br>- Historical win rate for this pattern<br>- Avg win/loss for pattern<br>- "View Similar Trades" link | |
| **Data Fields** | - Decision: action, asset, quantity, price, confidence<br>- Market: current_price, sma_7, sma_14, rsi, macd, support, resistance<br>- Risk: win_probability, risk_reward_ratio, worst_case, best_case, expected_value<br>- Position: portfolio_value, risk_pct, stop_loss_distance, position_size<br>- Historical: pattern_name, similar_count, win_rate, avg_win, avg_loss | |
| **Action Buttons** | - "Approve This Decision" (if pending)<br>- "View on Chart" (opens chart with annotations)<br>- "Save to Notes"<br>- "Toggle Explanation Level" (dropdown)<br>- "View Similar Past Trades" | |
| **Layout Notes** | - Use progressive disclosure: show key info first, expand for details<br>- Visual aids are critical: gauges, charts, diagrams<br>- Beginner mode: Simple language, less jargon<br>- Advanced mode: Full calculations, statistical data<br>- Use color coding: Green (bullish factors), Red (bearish factors), Gray (neutral) | |

---

### Screen 4: Trade Journal

| Element | Detail | Specification |
|:--------|:-------|:--------------|
| **Screen Name** | Trade Journal | |
| **Core Function** | Historical log of all trades with auto-generated analysis, learning notes, and performance tracking. | |
| **Layout Structure** | **Main table view with expandable rows:**<br>- Filter bar (top)<br>- Summary stats cards (top)<br>- Trade table (main content)<br>- Detail panel (right side, slides in when row clicked)<br><br>**Filters:**<br>- Date range<br>- Asset<br>- Win/Loss<br>- Trading pattern | |
| **Required Components** | **1. Summary Stats Cards (horizontal row):**<br>- Total Trades<br>- Win Rate %<br>- Average Win %<br>- Average Loss %<br>- Profit Factor<br>- Best Trade<br>- Worst Trade<br><br>**2. Trade Table:**<br>- Columns: Date/Time, Asset, Side, Entry Price, Exit Price, Quantity, P&L, P&L %, Duration, Pattern, Status<br>- Sort by any column<br>- Color-coded rows (green=win, red=loss)<br>- Click row to expand details<br><br>**3. Trade Detail Panel (right slide-in):**<br>- Entry/Exit charts (side by side)<br>- AI reasoning at entry<br>- Outcome analysis<br>- "What went right" list<br>- "What went wrong" list<br>- Key learning point (highlighted)<br>- Pattern identification<br>- User notes section (auto-generated + manual)<br><br>**4. Pattern Filter Tags:**<br>- Clickable tags: "Support Bounce", "Breakout", "Mean Reversion"<br>- Shows count for each pattern<br>- Filter trades by pattern type | |
| **Data Fields** | - Trade: id, timestamp, asset, side, entry_price, exit_price, quantity, pnl, pnl_pct, duration<br>- Analysis: pattern, ai_reasoning, outcome_summary, what_went_right, what_went_wrong, key_learning<br>- Metadata: confidence, risk_amount, fees | |
| **Action Buttons** | - "Export to CSV"<br>- "Add Manual Note" (per trade)<br>- "Filter Trades"<br>- "View on Chart"<br>- "Similar Trades" | |
| **Layout Notes** | - Table should be scannable at a glance<br>- Use alternating row colors for readability<br>- P&L column should be most prominent (larger font, bold)<br>- Expandable rows for details (don't navigate away)<br>- Auto-generated insights should be clearly labeled vs. user notes | |

---

### Screen 5: Settings & Configuration

| Element | Detail | Specification |
|:--------|:-------|:--------------|
| **Screen Name** | Settings | |
| **Core Function** | Comprehensive configuration interface for all trading parameters, risk limits, and system settings. | |
| **Layout Structure** | **Left sidebar navigation (categories):**<br>- Trading Mode<br>- Capital Allocation<br>- Risk Management<br>- Trading Frequency<br>- Auto-Pause Triggers<br>- Notifications<br>- Exchange Settings<br>- AI Configuration<br><br>**Main content area:**<br>- Selected category settings<br>- Parameter inputs with explanations<br>- "Save Settings" button (sticky bottom) | |
| **Required Components** | **1. Trading Mode Section:**<br>- Radio buttons: Simulation / Semi-Automated / Fully Automated<br>- Description of each mode (expandable)<br>- Readiness indicator (if considering Full Auto)<br>- "View Readiness Report" link<br><br>**2. Capital Allocation:**<br>- Number input: "Total Capital Allocated"<br>- Display: Current usage (cash vs. positions, pie chart)<br>- Suggestion box: Recommended allocation based on experience<br><br>**3. Risk Management Parameters:**<br>- Slider: Max Position Size (1-25%, default 10%)<br>- Slider: Max Daily Loss (1-10%, default 3%)<br>- Number input: Max Daily Trades (5-100, default 20)<br>- Number input: Max Open Positions (1-20, default 5)<br>- Slider: Min Cash Reserve (10-50%, default 20%)<br>- Slider: Max Drawdown (5-30%, default 15%)<br>- Each parameter has ℹ️ tooltip with explanation and recommendations<br><br>**4. Auto-Pause Triggers (Full Auto only):**<br>- Checkboxes for enabling each trigger<br>- Number inputs for thresholds<br>- Triggers: Consecutive losses, Win rate drop, High volatility, API errors<br>- "Test Trigger" button (simulates trigger to show what happens)<br><br>**5. Notifications:**<br>- Email address input<br>- Checkboxes: Trades executed, Approvals needed, Daily summary, Risk triggers, Errors<br>- Email frequency: Immediate / Digest / Daily only<br><br>**6. Exchange Settings:**<br>- Dropdown: Exchange (Binance, Coinbase)<br>- API key input (masked)<br>- API secret input (masked)<br>- "Test Connection" button<br>- Checkbox: Use Testnet<br>- Trading fee rate input<br>- Multi-select: Supported assets<br><br>**7. AI Configuration:**<br>- Provider dropdown (OpenAI, OpenRouter, Custom)<br>- API URL input<br>- API Key input (masked)<br>- Model name input<br>- Slider: Temperature (0.0-1.0, default 0.7)<br>- Dropdown: Trading strategy (Day Trading - Mean Reversion, Trend Following, etc.)<br>- Dropdown: Explanation level (Beginner/Intermediate/Advanced) | |
| **Data Fields** | All configuration parameters as listed in components section | |
| **Action Buttons** | - "Save All Settings" (primary, bottom sticky)<br>- "Reset to Defaults" (secondary)<br>- "Test Connection" (per exchange)<br>- "View Readiness Report"<br>- "Export Configuration"<br>- "Import Configuration" | |
| **Layout Notes** | - CRITICAL: Every parameter must have an ℹ️ info icon with tooltip<br>- Tooltips should explain: What it is, Why it matters, Recommended values<br>- Use sliders for percentage values (visual, easy to adjust)<br>- Number inputs for counts/quantities<br>- Group related settings in cards<br>- Highlight changed settings before saving<br>- Show warnings for risky configurations (e.g., "Max daily loss >5% is aggressive") | |

---

### Screen 6: Readiness Assessment Dashboard

| Element | Detail | Specification |
|:--------|:-------|:--------------|
| **Screen Name** | Full Automation Readiness | |
| **Core Function** | Advisory dashboard showing objective data to help user decide if ready to switch from Semi-Auto to Full-Auto mode. | |
| **Layout Structure** | **Hero section:**<br>- Large readiness score (0-100%)<br>- Circular progress indicator<br>- Recommendation badge (Ready / Not Ready / Almost Ready)<br><br>**Criteria cards (2-column grid):**<br>- Each criterion in a card<br>- Pass/Fail indicator<br><br>**Bottom section:**<br>- Suggested next steps<br>- Action buttons | |
| **Required Components** | **1. Readiness Score Hero:**<br>- Large circular progress (0-100%)<br>- Score in center<br>- Color-coded: <70% red, 70-85% amber, >85% green<br>- Text: "Ready" or "Not Ready Yet" or "Almost Ready"<br><br>**2. Criteria Cards (Pass/Fail for each):**<br>- Trading History: "45 trades (need 30)" ✅<br>- Approval Rate: "92% (need 85%)" ✅<br>- Win Rate: "68% (need 60%)" ✅<br>- Total Return: "+12.4% (need +5%)" ✅<br>- Risk Violations: "0 (need 0)" ✅<br>- Modification Rate: "8% (need <15%)" ✅<br>- Return Volatility: "24% (need <20%)" ⚠️<br>- Each card shows: Metric name, Current value, Required value, Pass/Fail icon<br><br>**3. Approval Pattern Analysis:**<br>- What you approve: Win rate breakdown<br>- What you reject: Hypothetical P&L if taken<br>- Interpretation text<br><br>**4. Performance Consistency Chart:**<br>- Weekly returns bar chart<br>- Shows volatility visually<br><br>**5. Recommendation Box:**<br>- Based on criteria, show personalized advice<br>- "You're ready!" or "Work on X and Y first"<br>- Specific action items<br><br>**6. Decision Buttons:**<br>- "Keep Semi-Auto Mode" (secondary)<br>- "Switch to Full Auto" (primary, disabled if not ready)<br>- "Review in 1 Week" (secondary) | |
| **Data Fields** | - Readiness score (percentage)<br>- Each criterion: name, current_value, required_value, passed (boolean)<br>- Approval stats: approval_rate, modification_rate<br>- Performance: total_trades, win_rate, total_return, volatility<br>- Weekly returns: array of weekly P&L values | |
| **Action Buttons** | - "Switch to Full Auto" (conditional)<br>- "Keep Semi-Auto"<br>- "Export Report PDF"<br>- "Refresh Data" | |
| **Layout Notes** | - This is a decision-support tool, not a directive<br>- Emphasize "THIS IS ADVISORY - YOU DECIDE"<br>- Use visual progress indicators (checkmarks, progress bars)<br>- Make it clear what needs to improve if not ready<br>- Provide specific numbers, not vague statements<br>- Green = pass, Red = fail, Amber = borderline | |

---

### Screen 7: Performance Analytics

| Element | Detail | Specification |
|:--------|:-------|:--------------|
| **Screen Name** | Performance Analytics | |
| **Core Function** | Detailed performance attribution showing what trading patterns, assets, and time periods are profitable. | |
| **Layout Structure** | **Tab navigation:**<br>- By Pattern<br>- By Asset<br>- By Time<br>- By Market Condition<br><br>**Main content:**<br>- Summary cards (top)<br>- Data table or charts (middle)<br>- Insights panel (right sidebar) | |
| **Required Components** | **1. By Pattern Tab:**<br>- Table showing: Pattern name, # Trades, Win %, Avg Win, Avg Loss, Total P&L, Contribution %<br>- Sort by contribution<br>- Bar chart visualization<br>- Top patterns highlighted<br><br>**2. By Asset Tab:**<br>- Similar table for each asset (BTC, ETH, etc.)<br>- Shows which assets are most profitable<br>- Asset allocation pie chart<br><br>**3. By Time Tab:**<br>- Heatmap: Day of week vs. Hour of day (shows best trading times)<br>- Bar chart: P&L by time period (morning, afternoon, evening, night)<br>- Calendar view: Mark profitable days green, losing days red<br><br>**4. By Market Condition Tab:**<br>- Performance in: Strong uptrend, Weak uptrend, Sideways, Downtrend<br>- Shows which market regimes your strategy works in<br>- Scatter plot or grouped bar chart<br><br>**5. Insights Panel (right sidebar):**<br>- Auto-generated insights:<br>  - "✅ Your best performer: Support bounce trades (75% win rate)"<br>  - "✅ BTC trades outperform other assets"<br>  - "⚠️ Avoid SOL - consistent losses"<br>  - "💡 Focus on morning trades (9am-12pm)"<br>- Actionable recommendations<br>- Links to related trades | |
| **Data Fields** | - Pattern: name, trade_count, win_rate, avg_win, avg_loss, total_pnl<br>- Asset: symbol, trade_count, win_rate, total_pnl<br>- Time: period_name, trade_count, pnl<br>- Market condition: regime, trade_count, win_rate, pnl | |
| **Action Buttons** | - "Export Analysis CSV"<br>- "View Related Trades"<br>- "Apply Insights to Settings" (adjusts supported assets, trading times, etc.) | |
| **Layout Notes** | - Heavy use of data visualization (tables, charts, heatmaps)<br>- Make insights actionable, not just informational<br>- Use color coding: Green (profitable), Red (losing), Gray (neutral)<br>- Allow drill-down into specific categories<br>- Show both absolute ($) and relative (%) metrics | |

---

## C. Component Style Guidelines

### Typography
- **Headings:** Inter, Sans-serif, Bold
  - H1: 32px
  - H2: 24px
  - H3: 20px
  - H4: 18px
- **Body Text:** Inter, Sans-serif, Regular, 14px
- **Numbers/Data:** Fira Code, Monospace, Medium, 16px (larger for key metrics)
- **Labels:** Inter, Sans-serif, Medium, 12px uppercase

### Color Usage
| Element | Color | Use Case |
|:--------|:------|:---------|
| **Background** | #111827 | Main app background |
| **Cards** | #374151 | Elevated surfaces |
| **Primary Action** | #10B981 (Green) | Approve, Execute, Profit indicators |
| **Danger Action** | #EF4444 (Red) | Reject, Stop, Loss indicators |
| **Warning** | #F59E0B (Amber) | Alerts, Modifications needed |
| **Info** | #3B82F6 (Blue) | Informational elements |
| **Text Primary** | #FFFFFF | Main content |
| **Text Secondary** | #9CA3AF | Supporting text, labels |
| **Border** | #4B5563 | Dividers, card borders |

### Spacing
- **Card Padding:** 24px
- **Section Margin:** 32px
- **Component Spacing:** 16px
- **Grid Gap:** 24px

### Interactive Elements
- **Buttons:**
  - Primary: Green background, white text, 12px padding, rounded corners (8px)
  - Secondary: Gray border, white text, 12px padding, rounded corners (8px)
  - Danger: Red background, white text, 12px padding, rounded corners (8px)
  - Hover: Lighten by 10%
- **Inputs:**
  - Dark background (#1F2937), Light border (#4B5563), White text
  - Focus: Blue border (#3B82F6)
  - Error: Red border (#EF4444)
- **Tooltips:**
  - Dark background (#1F2937), white text, small (12px), arrow pointing to element
  - Appear on hover of ℹ️ icon

### Charts & Visualizations
- **Line Charts:** Use green for positive trends, red for negative
- **Bar Charts:** Alternate opacity for grouped data
- **Gauges:** Color zones (green=good, amber=warning, red=danger)
- **Tables:** Alternating row background (#374151 and transparent), hover highlight

---

## D. Interaction Patterns

### Navigation
- Sidebar navigation with icons and labels
- Active state: Blue accent border on left side
- Collapsible for more screen space
- Breadcrumbs for deep navigation

### Data Loading
- Skeleton screens while loading (don't show empty states)
- Smooth transitions (300ms ease-in-out)
- Real-time updates without full page refresh
- "Last updated X seconds ago" timestamp

### Modals & Overlays
- Dark overlay (50% opacity) behind modal
- Modal centered, max-width 600px
- Close button (X) top-right
- "Cancel" and "Confirm" buttons at bottom

### Notifications
- Toast notifications (top-right corner)
- Auto-dismiss after 5 seconds (unless error)
- Click to dismiss immediately
- Different icons for: Success, Error, Warning, Info

### Responsive Behavior
- Desktop (>1200px): Full 3-column layout
- Tablet (768-1199px): 2-column layout, collapsible sidebar
- Mobile (<768px): Single column, bottom tab navigation

---

## E. Key User Flows

### Flow 1: Approving a Trade (Semi-Auto Mode)
1. User receives notification: "Trade approval needed"
2. User clicks notification → Opens Trading Control panel
3. Pending decision card is prominent
4. User clicks "View Explanation" → AI Explainability slide-in panel
5. User reviews reasoning, risk, and chart
6. User clicks "Approve" → Trade executes immediately
7. Success toast notification appears
8. Trade appears in "Positions" table
9. Dashboard P&L updates in real-time

### Flow 2: Switching to Full Auto
1. User navigates to Settings
2. User sees "Trading Mode" section
3. User clicks "View Readiness Report" link
4. Readiness dashboard opens (new screen)
5. User reviews criteria (85% readiness score)
6. User clicks "Switch to Full Auto" button
7. Confirmation modal: "Are you sure? AI will trade autonomously."
8. User confirms
9. Mode switches, success notification
10. Dashboard header shows "Full Auto" badge

### Flow 3: Reviewing Trade History
1. User navigates to Trade Journal
2. User sees summary stats at top
3. User scrolls through trade table
4. User clicks on a losing trade row
5. Detail panel slides in from right
6. User reads "What went wrong" analysis
7. User sees similar trades that worked
8. User adds manual note: "Need tighter stop loss in volatile markets"
9. User closes panel
10. User exports journal to CSV for tax records

---

## F. Special Considerations

### Dark Mode
- This is the default and primary theme
- All UI elements designed for dark backgrounds
- Use sufficient contrast for accessibility (WCAG AA minimum)

### Data Density
- This is a professional trading tool, not a consumer app
- Users expect to see lots of data at once
- Prioritize information density over whitespace
- Use progressive disclosure (expand for details) to manage complexity

### Real-Time Updates
- Price data updates every 5 seconds
- Portfolio value recalculates on each update
- Visual feedback for live updates (subtle pulse animation)
- Avoid jarring reflows when data updates

### Mobile Considerations
- Primary use is desktop, but should be viewable on tablet/mobile for monitoring
- On mobile: Prioritize dashboard, positions, and alerts
- Hide complex charts on mobile, show summary stats instead

### Accessibility
- All interactive elements keyboard accessible
- ARIA labels for screen readers
- Color is not the only indicator (use icons + color)
- Sufficient contrast ratios
- Focus indicators visible

---

## G. Example Prompts for Google Stitch

### Example 1: Dashboard Screen
```
Create a dark-themed financial dashboard for a trading application.

Layout:
- Left sidebar with navigation (Dashboard, Trading, Journal, Analytics, Settings)
- Header bar with logo, model selector dropdown, mode badge, and red emergency stop button
- Main content in 3 columns: Model list (left 30%), Performance chart (center 45%), Activity feed (right 25%)

Color scheme:
- Background: #111827 dark gray
- Cards: #374151 medium gray with subtle shadows
- Primary color: #10B981 emerald green
- Danger color: #EF4444 red
- Text: White primary, #9CA3AF gray secondary

Components:
1. Model list card showing 3 trading models with names, status indicators (green dots), current P&L (green +$425, red -$120), and total return percentage
2. Large line chart showing account value over 7 days with green line trending upward
3. Portfolio summary card showing: Total Value $12,450 (large, white text), Cash $5,230, Open Positions: 3, Today's P&L: +$425 (green)
4. Activity feed with timestamped events, color-coded icons

Style: Modern, data-dense, professional (Bloomberg Terminal aesthetic with modern SaaS polish). Use Inter font for text, Fira Code monospace for numbers.
```

### Example 2: Pending Approval Card (Semi-Auto)
```
Design a prominent approval card for a semi-automated trading system.

Card content:
- Header: "🤖 Trade Approval Required" with countdown timer (expires in 58 min)
- Large decision: "BUY 0.5 BTC @ $50,000"
- Confidence meter: 75% (visual progress bar in green)
- Expandable AI reasoning section with bullet points explaining why (RSI oversold, support bounce, MACD crossover)
- Risk metrics: Position size 40% of portfolio ✅, Risk if stopped $250 (2%) ✅
- Small inline candlestick chart for BTC
- Three buttons at bottom: "✅ Approve" (green primary), "✏️ Modify" (blue secondary), "❌ Reject" (red secondary)

Style: Dark theme (#374151 background), white text, green accents for positive metrics. Make the approve button prominent. Add subtle border pulse animation to indicate urgency.
```

### Example 3: Settings Page - Risk Parameters
```
Design a settings section for configuring risk management parameters.

Layout: Single column with parameter cards.

Components (each with ℹ️ info tooltip):
1. Max Position Size slider: 1% to 25%, currently at 10%, with tooltip explaining "Maximum % of capital in a single position"
2. Max Daily Loss slider: 1% to 10%, currently at 3%, with red warning "CIRCUIT BREAKER - trading stops if exceeded"
3. Max Daily Trades: Number input, value 20, with text "Prevents over-trading and excessive fees"
4. Max Open Positions: Number input, value 5, with text "How many positions can be open at once"

Each parameter shows:
- Label (white text, medium weight)
- Input control (slider or number input, dark background, green accent)
- Current value displayed (monospace font)
- Info icon (ℹ️) that shows tooltip on hover
- Recommendation text in gray: "💡 Recommended: 8-12% for crypto day trading"

Bottom of page: "Save Settings" button (green, full-width, sticky)

Style: Dark theme, cards with #374151 background, white text, green sliders, clear visual hierarchy.
```

---

## H. Assets Needed

### Icons
- Navigation: Dashboard, Trading, Journal, Analytics, Settings
- Actions: Approve (checkmark), Reject (X), Modify (edit), Close (X in circle)
- Indicators: Arrow up (profit), Arrow down (loss), Pause, Play, Stop
- Alerts: Info (i), Warning (triangle), Error (!)
- Assets: BTC, ETH, SOL, BNB, XRP, DOGE logos

### Charts
- Line charts (time series)
- Bar charts (categorical comparisons)
- Pie charts (allocation)
- Candlestick charts (price action)
- Heatmaps (time-of-day analysis)
- Gauges (RSI, confidence meters)

### Illustrations (optional)
- Empty state: "No trades yet" (simple illustration)
- Error state: "Connection lost" (simple illustration)
- Success state: "Trade executed" (checkmark animation)

---

## I. Technical Notes for Stitch

- This is a web application (HTML/CSS/JavaScript)
- Desktop-first, responsive design
- Framework-agnostic (designs should work with React, Vue, or vanilla JS)
- Charts will be implemented with libraries like Chart.js or Recharts
- Real-time data via WebSocket or polling
- Forms use standard HTML inputs styled with CSS
- Modals/overlays use fixed positioning
- Tooltips use absolute positioning relative to parent
- Animations: CSS transitions (300ms ease-in-out)

---

**End of Specification**

Use this document to generate individual screen designs with Google Stitch. Each screen section can be used as a prompt, with the general guidelines (Section A, C, D, F) applied consistently across all screens.

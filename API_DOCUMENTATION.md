# Enhanced API Documentation

This document describes the new API endpoints added for the personal trading system with three trading modes (Simulation, Semi-Automated, Fully Automated).

## Base URL
`http://localhost:5000`

---

## Trading Mode Management

### Get Trading Mode
**GET** `/api/models/<model_id>/mode`

Get the current trading mode for a model.

**Response:**
```json
{
  "mode": "simulation|semi_automated|fully_automated"
}
```

### Set Trading Mode
**POST** `/api/models/<model_id>/mode`

Set the trading mode for a model.

**Request Body:**
```json
{
  "mode": "simulation|semi_automated|fully_automated"
}
```

**Response:**
```json
{
  "success": true,
  "mode": "semi_automated"
}
```

---

## Model Settings Management

### Get Model Settings
**GET** `/api/models/<model_id>/settings`

Get all settings for a model including risk parameters, trading configuration, and notification preferences.

**Response:**
```json
{
  "max_position_size_pct": 10.0,
  "max_daily_loss_pct": 3.0,
  "max_daily_trades": 20,
  "max_open_positions": 5,
  "min_cash_reserve_pct": 20.0,
  "max_drawdown_pct": 15.0,
  "trading_interval_minutes": 60,
  "trading_fee_rate": 0.1,
  "auto_pause_enabled": true,
  "auto_pause_consecutive_losses": 5,
  "auto_pause_win_rate_threshold": 40.0,
  "ai_temperature": 0.7,
  "ai_strategy": "day_trading_mean_reversion",
  "explanation_level": "intermediate",
  "email_enabled": false,
  "use_testnet": false,
  "supported_assets": ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE"]
}
```

### Update Model Settings
**POST** `/api/models/<model_id>/settings`

Update model settings. Only include fields you want to change.

**Request Body:**
```json
{
  "max_position_size_pct": 15.0,
  "max_daily_loss_pct": 5.0,
  "max_open_positions": 3
}
```

**Response:**
```json
{
  "success": true
}
```

---

## Pending Decisions (Semi-Automated Mode)

### Get All Pending Decisions
**GET** `/api/pending-decisions`

Get all pending decisions across all models or for a specific model.

**Query Parameters:**
- `model_id` (optional): Filter by model ID

**Response:**
```json
[
  {
    "id": 1,
    "model_id": 1,
    "coin": "BTC",
    "decision_data": {
      "signal": "buy_to_enter",
      "quantity": 0.5,
      "leverage": 10,
      "profit_target": 45000.0,
      "stop_loss": 42000.0,
      "confidence": 0.75,
      "justification": "Strong uptrend with RSI support"
    },
    "explanation_data": {
      "decision_summary": "...",
      "market_analysis": "...",
      "risk_assessment": "..."
    },
    "status": "pending",
    "expires_at": "2025-11-07T10:00:00",
    "created_at": "2025-11-07T09:00:00"
  }
]
```

### Approve Pending Decision
**POST** `/api/pending-decisions/<decision_id>/approve`

Approve a pending decision and execute it.

**Request Body (optional):**
```json
{
  "modified": false,
  "modifications": {
    "quantity": 0.3,
    "leverage": 5
  }
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "coin": "BTC",
    "signal": "buy_to_enter",
    "quantity": 0.3,
    "price": 43500.0,
    "status": "executed"
  }
}
```

### Reject Pending Decision
**POST** `/api/pending-decisions/<decision_id>/reject`

Reject a pending decision.

**Request Body:**
```json
{
  "reason": "Too risky given current market conditions"
}
```

**Response:**
```json
{
  "success": true
}
```

---

## Risk Status Monitoring

### Get Risk Status
**GET** `/api/models/<model_id>/risk-status`

Get current risk metrics and status for a model.

**Response:**
```json
{
  "position_size": {
    "current": 5000.0,
    "max": 10000.0,
    "usage_pct": 50.0,
    "status": "ok"
  },
  "daily_loss": {
    "current_pct": -1.5,
    "max_pct": 3.0,
    "status": "ok"
  },
  "open_positions": {
    "current": 2,
    "max": 5,
    "status": "ok"
  },
  "cash_reserve": {
    "current_pct": 30.0,
    "min_pct": 20.0,
    "status": "ok"
  },
  "daily_trades": {
    "current": 5,
    "max": 20,
    "status": "ok"
  }
}
```

**Status Values:**
- `ok`: Within safe limits
- `warning`: Approaching limits
- `critical`: At or exceeding limits

---

## Readiness Assessment

### Get Readiness Assessment
**GET** `/api/models/<model_id>/readiness`

Get readiness assessment for switching from semi-automated to fully automated mode.

**Response:**
```json
{
  "ready": false,
  "score": 65,
  "max_score": 100,
  "message": "⚠️ Approaching Readiness - Continue monitoring",
  "metrics": {
    "total_trades": 25,
    "win_rate": 52.0,
    "approval_rate": 85.0,
    "modification_rate": 12.0,
    "risk_violations": 2,
    "total_return": 3.5,
    "return_volatility": 3.2
  }
}
```

**Scoring Criteria:**
- Win rate (30 points): ≥55% = 30, ≥50% = 20, ≥45% = 10
- Approval rate (20 points): ≥90% = 20, ≥80% = 15, ≥70% = 10
- Modification rate (15 points): ≤5% = 15, ≤10% = 10, ≤20% = 5
- Risk violations (15 points): 0 = 15, ≤3 = 10, ≤5 = 5
- Total return (10 points): ≥5% = 10, ≥2% = 5, ≥0% = 2
- Return volatility (10 points): ≤2% = 10, ≤4% = 5, ≤6% = 2

**Ready:** Score ≥ 70

---

## Incidents Log

### Get Model Incidents
**GET** `/api/models/<model_id>/incidents`

Get incidents log for a specific model.

**Query Parameters:**
- `limit` (optional, default: 50): Number of incidents to retrieve

**Response:**
```json
[
  {
    "id": 1,
    "model_id": 1,
    "incident_type": "MODE_CHANGE",
    "severity": "low",
    "message": "Trading mode changed to semi_automated",
    "details": {
      "new_mode": "semi_automated"
    },
    "resolved": false,
    "timestamp": "2025-11-07T09:00:00"
  }
]
```

**Incident Types:**
- `MODE_CHANGE`: Trading mode changed
- `TRADE_REJECTED`: Trade rejected by risk manager
- `AUTO_PAUSE`: Full auto paused due to trigger
- `EMERGENCY_PAUSE`: User-initiated emergency pause
- `EMERGENCY_STOP_ALL`: All models stopped
- `EXECUTION_ERROR`: Trade execution failed
- `API_ERROR`: API connection error

**Severity Levels:**
- `low`: Informational
- `medium`: Warning
- `high`: Important
- `critical`: Requires immediate attention

### Get All Incidents
**GET** `/api/incidents`

Get incidents across all models.

**Query Parameters:**
- `limit` (optional, default: 100): Number of incidents to retrieve

---

## Emergency Controls

### Emergency Pause Model
**POST** `/api/models/<model_id>/pause`

Emergency pause - switch from fully automated to semi-automated mode.

**Request Body:**
```json
{
  "reason": "Market volatility too high"
}
```

**Response:**
```json
{
  "success": true,
  "previous_mode": "fully_automated",
  "new_mode": "semi_automated",
  "message": "Model paused successfully"
}
```

### Emergency Stop All Models
**POST** `/api/emergency-stop-all`

Emergency stop all models - switch all to simulation mode.

**Request Body:**
```json
{
  "reason": "Critical market event"
}
```

**Response:**
```json
{
  "success": true,
  "switched_count": 3,
  "switched_models": [
    {
      "model_id": 1,
      "model_name": "Model 1",
      "previous_mode": "fully_automated"
    },
    {
      "model_id": 2,
      "model_name": "Model 2",
      "previous_mode": "semi_automated"
    }
  ],
  "message": "All 3 models switched to simulation mode"
}
```

---

## Enhanced Trading Execution

### Execute Enhanced Trading Cycle
**POST** `/api/models/<model_id>/execute-enhanced`

Execute a trading cycle using the enhanced system (mode-aware execution).

**Response:**
```json
{
  "success": true,
  "result": {
    "mode": "semi_automated",
    "pending": [
      {
        "decision_id": 1,
        "coin": "BTC",
        "signal": "buy_to_enter",
        "quantity": 0.5
      }
    ],
    "skipped": []
  }
}
```

**Result by Mode:**

**Simulation Mode:**
```json
{
  "mode": "simulation",
  "executed": [
    {
      "coin": "BTC",
      "signal": "buy_to_enter",
      "quantity": 0.5,
      "price": 43500.0,
      "status": "simulated"
    }
  ],
  "skipped": []
}
```

**Semi-Automated Mode:**
```json
{
  "mode": "semi_automated",
  "pending": [
    {
      "decision_id": 1,
      "coin": "BTC",
      "signal": "buy_to_enter",
      "quantity": 0.5
    }
  ],
  "skipped": []
}
```

**Fully Automated Mode:**
```json
{
  "mode": "fully_automated",
  "executed": [
    {
      "coin": "BTC",
      "signal": "buy_to_enter",
      "quantity": 0.5,
      "price": 43500.0,
      "status": "executed"
    }
  ],
  "skipped": []
}
```

---

## Error Responses

All endpoints may return error responses in this format:

```json
{
  "error": "Error message description"
}
```

**Common HTTP Status Codes:**
- `200`: Success
- `400`: Bad request (invalid parameters)
- `404`: Resource not found
- `500`: Internal server error

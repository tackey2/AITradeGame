# Model ID Mismatch Issue - Diagnosis and Prevention Guide

## Problem Description

### What Happened
Your database has models with IDs **1 and 3** (not 1 and 2). All trading data for "Test Strategy 2" is stored under `model_id = 3`, but the frontend/dashboard might be querying `model_id = 2`, resulting in "0 trades" showing in graduation criteria.

### Root Cause: SQLite AUTOINCREMENT Behavior

SQLite's `AUTOINCREMENT` primary key counter increments **even when inserts fail**. Here's what likely happened during model creation:

```
Time 10:51:27: Model 1 created → ID = 1 ✅
Time 10:51:34: Model 2 creation attempted → ID = 2 assigned, but insert/initialization failed ❌
Time 10:51:34: Model 2 retry succeeds → ID = 3 assigned ✅
```

Possible failure scenarios:
1. Database constraint violation (foreign key, unique constraint)
2. Transaction rollback after ID assignment
3. Exception during TradingEngine initialization (after DB insert but before return)
4. Temporary database lock/timeout

## Verification Steps

### 1. Check Actual Model IDs in Database

```bash
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('AITradeGame.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get all models
cursor.execute('SELECT id, name, created_at FROM models ORDER BY id')
models = cursor.fetchall()

print("=== Actual Models in Database ===")
for m in models:
    print(f"ID: {m['id']}, Name: {m['name']}, Created: {m['created_at']}")

    # Count trades for this model
    cursor.execute('SELECT COUNT(*) as count FROM trades WHERE model_id = ?', (m['id'],))
    count = cursor.fetchone()['count']
    print(f"  → Trades: {count}")
    print()

conn.close()
EOF
```

### 2. Check What Frontend Is Requesting

Look at your browser's Network tab (F12 → Network) and check:
- When viewing "Test Strategy 2" graduation status
- Which URL is being called: `/api/models/2/graduation-status` or `/api/models/3/graduation-status`?

If it's calling ID 2 but actual data is under ID 3, that's the mismatch.

## Solutions

### Solution 1: Quick Fix - Use Actual Database IDs

**Frontend should always use `model.id` from the API response**, not array index or assumed sequential numbers.

**Bad Code Example:**
```javascript
// ❌ WRONG - Assumes sequential IDs
models.forEach((model, index) => {
    const displayId = index + 1;  // Assumes ID = 1, 2, 3...
    fetchGraduationStatus(displayId);  // Calls /api/models/2 when actual ID is 3
});
```

**Good Code Example:**
```javascript
// ✅ CORRECT - Uses actual database ID
models.forEach((model) => {
    const actualId = model.id;  // Use the real ID from database
    fetchGraduationStatus(actualId);  // Calls /api/models/3 correctly
});
```

### Solution 2: Add Validation in API Routes

Add a check to warn about missing models:

```python
@models_bp.route('/api/models/<int:model_id>/graduation-status', methods=['GET'])
def get_model_graduation_status(model_id):
    try:
        db = app_context['db']

        # Verify model exists first
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM models WHERE id = ?', (model_id,))
        model = cursor.fetchone()

        if not model:
            conn.close()
            # Log the error for debugging
            print(f"[WARN] Frontend requested model_id={model_id} but it doesn't exist")
            print(f"[INFO] Available model IDs: {[m['id'] for m in db.get_all_models()]}")
            return jsonify({'error': f'Model {model_id} not found'}), 404

        # ... rest of the code
```

### Solution 3: Database Cleanup (Optional)

If you want to reset IDs to be sequential (1, 2, 3...), you can:

**⚠️ WARNING: This will DELETE ALL DATA. Only do this if starting fresh!**

```python
# DANGER: This deletes everything!
# Only run if you want to start over with clean IDs

import sqlite3
conn = sqlite3.connect('AITradeGame.db')
cursor = conn.cursor()

# Delete all data
cursor.execute('DELETE FROM trades')
cursor.execute('DELETE FROM conversations')
cursor.execute('DELETE FROM portfolios')
cursor.execute('DELETE FROM account_values')
cursor.execute('DELETE FROM models')

# Reset autoincrement counter
cursor.execute('DELETE FROM sqlite_sequence WHERE name="models"')

conn.commit()
conn.close()

print("✅ Database cleaned. IDs will now start from 1")
```

### Solution 4: Add Error Handling to Model Creation

Wrap model creation in proper transaction handling:

```python
def add_model(self, name: str, provider_id: int, model_name: str, initial_capital: float = 10000) -> int:
    """Add new trading model with proper error handling"""
    conn = self.get_connection()
    cursor = conn.cursor()

    try:
        # Start transaction
        cursor.execute('BEGIN')

        # Insert model
        cursor.execute('''
            INSERT INTO models (name, provider_id, model_name, initial_capital)
            VALUES (?, ?, ?, ?)
        ''', (name, provider_id, model_name, initial_capital))

        model_id = cursor.lastrowid

        # Verify the insert worked
        cursor.execute('SELECT id FROM models WHERE id = ?', (model_id,))
        if not cursor.fetchone():
            raise Exception(f"Model insert failed - ID {model_id} not found after insert")

        # Commit only if everything succeeded
        conn.commit()
        print(f"[SUCCESS] Model {model_id} created successfully")
        return model_id

    except Exception as e:
        # Rollback on any error
        conn.rollback()
        print(f"[ERROR] Model creation failed: {e}")
        raise
    finally:
        conn.close()
```

## Prevention Best Practices

### 1. Always Use Actual IDs From Database
✅ **DO**: `const modelId = model.id;`
❌ **DON'T**: `const modelId = index + 1;`

### 2. Add Logging
Log the actual model IDs during operations:
```python
print(f"[INFO] Processing model ID {model_id} (Name: {model_name})")
```

### 3. Validate Model Existence
Before any operation, check if model exists:
```python
model = db.get_model(model_id)
if not model:
    return jsonify({'error': f'Model {model_id} not found'}), 404
```

### 4. Use Transactions Properly
Always wrap database operations in try-except with rollback:
```python
try:
    conn.execute('BEGIN')
    # ... database operations ...
    conn.commit()
except Exception as e:
    conn.rollback()
    raise
finally:
    conn.close()
```

### 5. Frontend Should Fetch IDs Dynamically
```javascript
// Get models from API
const models = await fetch('/api/models').then(r => r.json());

// Use the actual ID from each model object
models.forEach(model => {
    console.log(`Model: ${model.name}, ID: ${model.id}`);  // Don't assume ID!
    // Use model.id for all subsequent API calls
});
```

## Debugging Checklist

When "0 trades" appears but trades exist:

- [ ] Check actual model IDs: `SELECT id, name FROM models`
- [ ] Check which ID has trades: `SELECT DISTINCT model_id FROM trades`
- [ ] Check browser Network tab: Which model_id is frontend requesting?
- [ ] Check model creation logs: Any errors during initialization?
- [ ] Verify frontend uses `model.id`, not array index
- [ ] Add logging to API routes to see requested vs actual IDs

## Current State for Your Project

Based on your database:
- ✅ Model 1 exists (ID = 1)
- ❌ Model 2 does NOT exist (ID = 2 was skipped)
- ✅ Model 3 exists (ID = 3) - This is your "Test Strategy 2"
- ✅ All trades are under model_id = 3

**Immediate Fix:**
Make sure frontend queries `/api/models/3/graduation-status` for "Test Strategy 2", not `/api/models/2/graduation-status`.

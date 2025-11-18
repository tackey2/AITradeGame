#!/usr/bin/env python3
"""
Migration script to add slippage column to trades table
"""
import sqlite3
import os

db_path = 'AITradeGame.db'

if not os.path.exists(db_path):
    print(f"Database {db_path} not found. No migration needed.")
    exit(0)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if slippage column exists
cursor.execute("PRAGMA table_info(trades)")
columns = [row[1] for row in cursor.fetchall()]

if 'slippage' in columns:
    print("✓ Slippage column already exists. No migration needed.")
else:
    print("Adding slippage column to trades table...")
    try:
        cursor.execute("ALTER TABLE trades ADD COLUMN slippage REAL DEFAULT 0")
        conn.commit()
        print("✓ Successfully added slippage column!")
    except Exception as e:
        print(f"✗ Error adding slippage column: {e}")
        conn.rollback()

conn.close()

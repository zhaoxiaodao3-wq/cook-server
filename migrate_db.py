"""Manually upgrade the cookbook PostgreSQL database to match the current schema.
Uses psycopg2 (sync driver) to avoid Windows async event loop issues with alembic+psycopg.
Safe to run multiple times — uses IF NOT EXISTS / IF EXISTS.

Run: python migrate_db.py
"""
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="postgres",
    password="postgres",
    dbname="cookbook",
)
cur = conn.cursor()

print("Upgrading database schema...")

# 1. users: add bio column
cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT")
print("  [OK] users.bio")

# 2. categories: add key column
cur.execute("ALTER TABLE categories ADD COLUMN IF NOT EXISTS key VARCHAR(32)")
cur.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='uq_categories_key') THEN ALTER TABLE categories ADD CONSTRAINT uq_categories_key UNIQUE (key); END IF; END $$")
# Seed category keys
cur.execute("""
    INSERT INTO categories (name, key, icon, sort_order) VALUES
    ('早餐', 'breakfast', 'sunrise', 1),
    ('午餐', 'lunch', 'sun', 2),
    ('晚餐', 'dinner', 'moon', 3),
    ('甜品', 'dessert', 'cake', 4)
    ON CONFLICT (name) DO UPDATE SET key = EXCLUDED.key
""")
print("  [OK] categories.key (+ seeded default categories)")

# 3. dishes: add cuisine, tags columns
cur.execute("ALTER TABLE dishes ADD COLUMN IF NOT EXISTS cuisine VARCHAR(32)")
cur.execute("ALTER TABLE dishes ADD COLUMN IF NOT EXISTS tags JSONB")
print("  [OK] dishes.cuisine, dishes.tags")

# 4. ingredients: change amount type from NUMERIC to VARCHAR
cur.execute("""
    ALTER TABLE ingredients
    ALTER COLUMN amount TYPE VARCHAR(32) USING amount::varchar
""")
print("  [OK] ingredients.amount → VARCHAR")

# 5. favorites table
cur.execute("""
    CREATE TABLE IF NOT EXISTS favorites (
        id VARCHAR(36) PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL REFERENCES users(id),
        dish_id VARCHAR(36) NOT NULL REFERENCES dishes(id) ON DELETE CASCADE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        UNIQUE(user_id, dish_id)
    )
""")
print("  [OK] favorites table")

# 6. drafts table
cur.execute("""
    CREATE TABLE IF NOT EXISTS drafts (
        id VARCHAR(36) PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL REFERENCES users(id),
        title VARCHAR(128),
        step INTEGER NOT NULL DEFAULT 0,
        cover_image VARCHAR(512),
        duration INTEGER,
        difficulty VARCHAR(8),
        servings INTEGER,
        ingredients JSONB,
        steps JSONB,
        category VARCHAR(32),
        cuisine VARCHAR(32),
        tags JSONB,
        crowd VARCHAR(128),
        tips TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
""")
print("  [OK] drafts table")

conn.commit()
cur.close()
conn.close()
print("\nDone! All schema upgrades applied.")

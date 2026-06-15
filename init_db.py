"""One-time script to create all tables in PostgreSQL. Run: python init_db.py"""
import psycopg2
from app.core.config import settings

def _to_psycopg2_url(url: str) -> str:

    for prefix in ("postgresql+psycopg://", "postgresql+asyncpg://"):

        if url.startswith(prefix):

            return "postgresql://" + url[len(prefix):]

    return url

conn = psycopg2.connect(_to_psycopg2_url(settings.DATABASE_URL))
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    openid VARCHAR(128) UNIQUE NOT NULL,
    nickname VARCHAR(64) NOT NULL,
    avatar_url VARCHAR(512),
    bio TEXT,
    role VARCHAR(16) NOT NULL DEFAULT 'user',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
""")

cur.execute("CREATE INDEX IF NOT EXISTS idx_users_openid ON users(openid)")

cur.execute("""
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(32) UNIQUE NOT NULL,
    key VARCHAR(32) UNIQUE,
    icon VARCHAR(64),
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS dishes (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    cover VARCHAR(512),
    description TEXT,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    cuisine VARCHAR(32),
    tags JSONB,
    cooking_time INTEGER,
    difficulty SMALLINT CHECK (difficulty >= 1 AND difficulty <= 3),
    servings INTEGER,
    tips TEXT,
    nutrition TEXT,
    suitable_for VARCHAR(128),
    author_id VARCHAR(36) NOT NULL REFERENCES users(id),
    status VARCHAR(16) NOT NULL DEFAULT 'published',
    avg_rating NUMERIC(2,1) NOT NULL DEFAULT 0.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS ingredients (
    id VARCHAR(36) PRIMARY KEY,
    dish_id VARCHAR(36) NOT NULL REFERENCES dishes(id) ON DELETE CASCADE,
    name VARCHAR(64) NOT NULL,
    amount VARCHAR(32) NOT NULL DEFAULT '',
    unit VARCHAR(16) NOT NULL DEFAULT '',
    sort_order INTEGER NOT NULL DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS steps (
    id VARCHAR(36) PRIMARY KEY,
    dish_id VARCHAR(36) NOT NULL REFERENCES dishes(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    description TEXT NOT NULL,
    image VARCHAR(512),
    duration INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(dish_id, step_number)
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS ratings (
    id VARCHAR(36) PRIMARY KEY,
    dish_id VARCHAR(36) NOT NULL REFERENCES dishes(id) ON DELETE CASCADE,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    stars SMALLINT NOT NULL CHECK (stars >= 1 AND stars <= 5),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(dish_id, user_id)
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS suggestions (
    id VARCHAR(36) PRIMARY KEY,
    dish_id VARCHAR(36) NOT NULL REFERENCES dishes(id) ON DELETE CASCADE,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
""")

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
cur.execute('''

    INSERT INTO categories (name, key, icon, sort_order) VALUES

    ('早餐', 'breakfast', 'sunrise', 1),

    ('午餐', 'lunch', 'sun', 2),

    ('晚餐', 'dinner', 'moon', 3),

    ('甜品', 'dessert', 'cake', 4)

    ON CONFLICT (name) DO UPDATE SET

        key = EXCLUDED.key,

        icon = EXCLUDED.icon,

        sort_order = EXCLUDED.sort_order

''')
conn.commit()
cur.close()
conn.close()
print("建表完成！9 张表已成功创建。")

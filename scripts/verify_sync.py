import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="postgres",
    password="postgres",
    dbname="cookbook",
)
cur = conn.cursor()
cur.execute("SELECT count(*) FROM categories")
print("categories", cur.fetchone()[0])
cur.execute("SELECT count(*) FROM dishes WHERE status='published'")
print("dishes published", cur.fetchone()[0])
cur.execute("SELECT to_regclass('public.favorites')")
print("favorites table", cur.fetchone()[0])
cur.close()
conn.close()
print("sync DB OK")

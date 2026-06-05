import psycopg2
try:
    conn = psycopg2.connect(host='localhost', port=5432, user='postgres', password='postgres', dbname='cookbook')
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
    tables = [r[0] for r in cur.fetchall()]
    print(f"Tables ({len(tables)}):", tables)
    cur.close(); conn.close()
except Exception as e:
    print(f"Error: {e}")

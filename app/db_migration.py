import os, time, psycopg

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    # Retry loop in case postgres is not ready before app
    for attempt in range(1, 6):
        try:
            conn = psycopg.connect(DATABASE_URL, autocommit=True)
            print(f"INFO: DB connection successful.")
            return conn
        except Exception as e:
            print(f"WARNING: DB not ready, retrying...")
            time.sleep(1)

# Migration: create / update database schema
def migrate_schema():
    with open("./db/schema.sql") as f:
        schema_sql = f.read()
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(schema_sql)
        print("INFO: DB Schema migrated.")

def seed_sample_data():
    # If tables are still empty, seed sample data
    with get_conn() as conn, conn.cursor() as cur:
        if cur.execute("SELECT 1 FROM categories").fetchall():
            print("INFO: Tables not empty, skip data seed.")
        else:
            with open("./db/sample-data.sql") as f:
                data_sql = f.read()
                cur.execute(data_sql)
                print("INFO: Sample data inserted.")
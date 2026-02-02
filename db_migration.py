import os, psycopg

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg.connect(DATABASE_URL, autocommit=True)

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
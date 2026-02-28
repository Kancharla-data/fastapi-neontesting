from dotenv import load_dotenv 
load_dotenv() 
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
    from auth import hash_password  

    hashed = hash_password("test123")

    cur.execute("""
        INSERT INTO customers (name, email, password, role)
        VALUES (%s, %s, %s, %s)
    """, ("Test User", "test@example.com", hashed, "customer"))


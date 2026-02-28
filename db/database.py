import os
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    return conn

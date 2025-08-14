import psycopg
import os
from dotenv import load_dotenv; load_dotenv("MMServerManager/db.env")

with psycopg.connect(dbname="MMServerManager", user="postgres", password=os.getenv('PASSWORD'), host="localhost") as DBConnection:
    with DBConnection.cursor() as DBCursor:
        try:
            DBCursor.execute("""
                CREATE TABLE ServerUsers (
                    UserID BIGINT PRIMARY KEY,
                    Username TEXT,
                    LastActive TIMESTAMP)
            """)
        except psycopg.errors.DuplicateTable: pass
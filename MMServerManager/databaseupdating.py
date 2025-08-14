import sqlite3
import time as pythontime
from contextlib import closing
import psycopg
import os
from dotenv import load_dotenv; load_dotenv("MMServerManager/db.env")

"""
Helpful Links

"""

def DBConnectionManager(func, MaxAttempts: int = 30):
    """
    REQUIREMENTS:
        - Database connection / present

    PROVIDES:
        - DBConnection class-object to a function using a decorator.
            - connection: database connection to commit to
            - cursor: to do fetch requests or inserts

    EXAMPLES:
        DBConnection.cursor.execute(\<some SQL request\>)
        pulledInfo = DBConnection.cursor.fetchmany(1000)

    WHEN TO USE DECORATOR:
        The decorator should be used whenever there is a new function call chain
        that needs a database connection. If a function is being called further down the call chain
        and the funciton calling the current function already have the DBConnection object-class
        then there is not need to add the @DBConnectionManager decroate to the function.
    """
    """class CreateDBConnection:
        def __init__(self, SQLDBConnection):
            self.connection = SQLDBConnection
            self.cursor = SQLDBConnection.cursor()
    def wrapper(*args, **kwargs):
        with closing(sqlite3.connect('EVEIntelligence.db')) as ActiveDBConnection:
            Attempts = 0; result = None
            while Attempts < MaxAttempts:
                try:
                    DBConnectionObject = CreateDBConnection(ActiveDBConnection)
                    result = func(DBConnectionObject, *args, **kwargs)
                    return(result)
                except sqlite3.OperationalError: print(f"Database locked. Retry attempt {Attempts} of {MaxAttempts}"); Attempts += 1; pythontime.sleep(1)
    return wrapper"""
    return

#DBConnection = psycopg.connect(dbname="MMServerManager", user="postgres", password=os.getenv('PASSWORD'), host="locahost")

with psycopg.connect(dbname="MMServerManager", user="postgres", password=os.getenv('PASSWORD'), host="locahost") as DBConnection:
    with DBConnection.cursor as DBCursor:
        DBCursor.execute("""
            CREATE TABLE ServerUsers (
                UserID INTEGER PRIMARY KEY,
                Username TEXT)
        """)
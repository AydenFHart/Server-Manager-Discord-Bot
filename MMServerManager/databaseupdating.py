import time as pythontime
from datetime import *
from contextlib import closing
import psycopg
import os
from dotenv import load_dotenv; load_dotenv("MMServerManager/db.env")
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.DEBUG)

"""
Helpful Links
https://www.psycopg.org/psycopg3/docs/basic/usage.html
https://www.geeksforgeeks.org/postgresql/postgresql-data-types/
"""

def DBConnectionManager(func):
    """
    REQUIREMENTS:
        - Database connection / present

    PROVIDES:
        - DBConnection class-object to a function using a decorator.
            - connection: database connection to commit to
            - cursor: to do fetch requests or inserts

    EXAMPLES:

    WHEN TO USE DECORATOR:
        The decorator should be used whenever there is a new function call chain
        that needs a database connection. If a function is being called further down the call chain
        and the funciton calling the current function already have the DBConnection object-class
        then there is not need to add the @DBConnectionManager decroate to the function.
    """
    class CreateDBConnection:
        def __init__(self, SQLDBConnection:psycopg.Connection):
            self.connection = SQLDBConnection
            self.cursor = SQLDBConnection.cursor()
    def wrapper(*args, **kwargs):
        with closing(psycopg.connect(dbname="MMServerManager", user="postgres", password=os.getenv('PASSWORD'), host="localhost")) as ActiveDBConnection:
            result = None
            DBConnectionObject = CreateDBConnection(ActiveDBConnection)
            result = func(DBConnectionObject, *args, **kwargs)
            return(result)
    return wrapper

@DBConnectionManager
def UpdateActiveLastFromMessageSent(DBConnection, Message) -> None:
    """
    PURPOSE:
        Updates the database's LastActive datetime for a user whenever they send a message.
    """
    DBConnection.cursor.execute(f"""
        SELECT UserID
        FROM ServerUsers
        WHERE UserID = {Message.author.id}
    """)
    if DBConnection.cursor.fetchone() == None:
        logging.info(f"Creating new database entries for {str(Message.author)} in ServerUsers")
        DBQuery = ("""
            INSERT INTO ServerUsers (UserID, UserName, LastActive)
            VALUES (%s,%s,%s)
        """)
        Values = [int(Message.author.id), str(Message.author), Message.created_at]
        DBConnection.cursor.execute(DBQuery, Values)
    else:
        logging.info(f"Updating LastActive database entry for {Message.author} in ServerUsers")
        DBQuery = (f"""
            UPDATE ServerUsers
            SET LastActive = %s
            WHERE UserID = %s
        """)
        DBConnection.cursor.execute(DBQuery, [Message.created_at, Message.author.id])
    DBConnection.connection.commit()

    #MessageDatetime = Message.created_at
    #DBConnection.cursor.execute("""UPDATE ServerUsers""")
    #print(MessageDatetime)
    return


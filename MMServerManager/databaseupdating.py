import time as pythontime
from datetime import *
from contextlib import closing
import psycopg
import os
from dotenv import load_dotenv; load_dotenv("MMServerManager/db.env")
import logging

logger = logging.getLogger(__name__)
#logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.DEBUG)

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

@DBConnectionManager
def CreateServerUsersEntry(DBConnection, Member) -> None:
    """
    PURPOSE:
        Creates a new ServerUsers entry for the provided member.
        This allows for the server manager to operate its automated functionality.
    """
    DBQuery = ("""
        SELECT UserID
        FROM ServerUsers
        WHERE UserID = %s
    """)
    DBConnection.cursor.execute(DBQuery, [Member.id])
    if DBConnection.cursor.fetchone() == None:
        logging.info(f"Creating entries for {str(Member.name)} in ServerUsers")
        DBQuery = ("""
            INSERT INTO ServerUsers (UserID, UserName, LastActive)
            VALUES (%s,%s,%s)
        """)
        Values = [int(Member.id), str(Member.name), datetime.now()]
        try:
            DBConnection.cursor.execute(DBQuery, Values)
            DBConnection.connection.commit()
        except psycopg.errors as e:
            logging.error(e)
            DBConnection.connection.rollback()
    return

@DBConnectionManager
def CreateServerRolesEntry(DBConnection, Role) -> None:
    """
    PURPOSE:
        Create an entry in the serverroles database table if it doesn't exist
    """
    
    DBQuery = ("""
        SELECT RoleID
        FROM ServerRoles
        WHERE RoleID = %s
    """)
    DBConnection.cursor.execute(DBQuery, [Role.id])
    if DBConnection.cursor.fetchone() == None:
        logging.info(f"Creating entries for {Role.name} in ServerRoles")
        DBQuery = ("""
            INSERT INTO ServerRoles (RoleID, RoleName)
            Values (%s,%s)
        """)
        Values = [int(Role.id), str(Role.name)]
        try:
            DBConnection.cursor.execute(DBQuery, Values)
            DBConnection.connection.commit()
        except psycopg.errors as e:
            logging.error(e)
            DBConnection.connection.rollback()
    return

@DBConnectionManager
def StartupTableCleaning(DBConnection) -> None:
    """
    PURPOSE:
        Some tables should be dropped and rebuilt to check if the data is accurate

        EX: can prevent old roles form being accounted for in commands
    """
    logging.info("Deleting entries in ServerRoles table.")
    DBConnection.cursor.execute("DELETE FROM ServerRoles")

    DBConnection.connection.commit()
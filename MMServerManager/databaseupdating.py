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
    logging.info("Deleting entries in ServerRoles.")
    DBConnection.cursor.execute("DELETE FROM ServerRoles")

    DBConnection.connection.commit()

@DBConnectionManager
def FetchRoles(DBConnection) -> list[(str, int, str)]:
    """
    PURPOSE:
        Populate the options for the give-role commands.

    RETURNS:
        A list containing lists with string, integer, and string
        A list of roles, with the roles name, role id, and description (returned an an empty string)
    """

    logging.info("Populating role commands options list")
    DBQuery = ("""
        SELECT RoleName, RoleID
        FROM ServerRoles
    """)
    DBConnection.cursor.execute(DBQuery)
    return(DBConnection.cursor.fetchall())

@DBConnectionManager
def GrantRole(DBConnection, User, RoleID) -> None:
    """
    PURPOSE:
        Update UserRoles table with the new role they have been granted (if they dont already have it)
        Update the user's roles within the discord server based upon whats in the database.
    """
    
    DBQuery = ("""
        SELECT UserID
        FROM UserRoles
        WHERE UserID = %s
    """)
    DBConnection.cursor.execute(DBQuery, [User.id])
    if DBConnection.cursor.fetchone() == None:
        logging.info(f"Creating UserRoles entry for {User.name}.")
        DBQuery = ("""
            INSERT INTO UserRoles (UserID, Roles)
            VALUES (%s, %s)
        """)
        DBConnection.cursor.execute(DBQuery, [User.id, []])
        DBConnection.connection.commit()

    DBQuery = ("""
        SELECT Roles
        FROM UserRoles
        WHERE UserID = %s
    """)
    DBConnection.cursor.execute(DBQuery, [User.id])
    UserRoles = DBConnection.cursor.fetchone()[0]
    if RoleID in UserRoles: raise Exception("User already has role being added")

    DBQuery = ("""
        UPDATE UserRoles
        SET Roles = %s
        WHERE UserID = %s
    """)
    UserRoles.append(RoleID)
    logging.info(f"Adding {RoleID} role to {User.name}")
    DBConnection.cursor.execute(DBQuery, [UserRoles, User.id])
    DBConnection.connection.commit()
    return

@DBConnectionManager
def GetUserRoles(DBConnection, User) -> list[int]:
    """
    PURPOSE:
        Get the role id's that a user has from the database.
    """
    DBQuery = ("""
        SELECT Roles
        FROM UserRoles
        WHERE UserID = %s
    """)
    DBConnection.cursor.execute(DBQuery, [User.id])
    Roles = DBConnection.cursor.fetchone()
    if Roles == None: return
    return(Roles[0])

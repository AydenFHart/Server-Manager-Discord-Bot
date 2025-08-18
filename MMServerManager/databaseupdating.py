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
def GrantTemporaryRole(DBConnection, User, RoleID:int, ExpirationDatetime:datetime) -> None:
    """
    PURPOSE:
        Update TemporaryUserRoles table with the new role they have been granted (if they dont already have it)
        Update the user's roles within the discord server based upon whats in the database.
    """
    
    DBQuery = ("""
        SELECT UserID
        FROM TemporaryUserRoles
        WHERE UserID = %s
    """)
    DBConnection.cursor.execute(DBQuery, [User.id])
    if DBConnection.cursor.fetchone() == None:
        logging.info(f"Creating TemporaryUserRoles entry for {User.name}.")
        DBQuery = ("""
            INSERT INTO TemporaryUserRoles (UserID, Roles, Expiration)
            VALUES (%s, %s, %s)
        """)
        DBConnection.cursor.execute(DBQuery, [User.id, [], []])
        DBConnection.connection.commit()

    DBQuery = ("""
        SELECT Roles, Expiration
        FROM TemporaryUserRoles
        WHERE UserID = %s
    """)
    DBConnection.cursor.execute(DBQuery, [User.id])
    PulledInfo = DBConnection.cursor.fetchone()
    UserRoles, UserExpirations = PulledInfo[:2]
    if RoleID in UserRoles: raise Exception("User already has role being added")

    DBQuery = ("""
        UPDATE TemporaryUserRoles
        SET Roles = %s, Expiration = %s
        WHERE UserID = %s
    """)
    UserRoles.append(RoleID)
    UserExpirations.append(ExpirationDatetime)
    logging.info(f"Adding {RoleID} temporary role to {User.name}")
    DBConnection.cursor.execute(DBQuery, [UserRoles, UserExpirations, User.id])
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

@DBConnectionManager
def GetUserTemporaryRoles(DBConnection, User) -> list[int, datetime]:
    """
    PURPOSE:
        Get the role ids and expiration times that a user has from the database.
    """
    DBQuery = ("""
        SELECT Roles, Expiration
        FROM TemporaryUserRoles
        WHERE UserID = %s
    """)
    DBConnection.cursor.execute(DBQuery, [User.id])
    PulledInfo = DBConnection.cursor.fetchone()
    if PulledInfo == None: return
    return(PulledInfo)

@DBConnectionManager
def RemoveExpiredUserTemporaryRoles(DBConnection, User) -> None:
    """
    PURPOSE:
        Deleted expired user roles from temporaryuserroles
    """
    DBQuery = ("""
        SELECT Roles, Expiration
        FROM TemporaryUserRoles
        WHERE UserID = %s
    """)
    DBConnection.cursor.execute(DBQuery, [User.id])
    PulledInfo = DBConnection.cursor.fetchone()
    if PulledInfo == None: return
    RoleID, Expiration = PulledInfo[:2]

    NonExpired:list[list[int], list[datetime]] = [[], []]
    for Index, Datetime in enumerate(Expiration):
        if Datetime > datetime.now():
            NonExpired[0].append(RoleID[Index])
            NonExpired[1].append(Expiration[Index])
        else: logger.debug(f"Removed expired temporary role from {User.name}")

    if len(NonExpired[0]) == 0: #They have no more valid roles and should have entry deleted from db.
        DBQuery = ("""
            DELETE
            FROM TemporaryUserRoles
            WHERE UserID = %s
        """)
        DBConnection.cursor.execute(DBQuery, [User.id])
        DBConnection.connection.commit()
    if RoleID == NonExpired[0]: return #There is not change, so no reason to perform actions on db.
    else:
        DBQuery = ("""
            UPDATE TemporaryUserRoles
            SET Roles = %s, Expiration = %s
            WHERE UserID = %s
        """)
        DBConnection.cursor.execute(DBQuery, [NonExpired[0], NonExpired[1], User.id])
        DBConnection.connection.commit()
    return

@DBConnectionManager
def FetchTemporaryRoleUserIDs(DBConnection) -> list[int]:
    """
    PURPOSE:
        Find the user id's of any users who have temporary roles.
    """
    DBQuery = ("""
        SELECT UserID
        FROM TemporaryUserRoles
    """)
    DBConnection.cursor.execute(DBQuery)
    UserIDList = [i[0] for i in DBConnection.cursor.fetchall()]
    return(UserIDList)

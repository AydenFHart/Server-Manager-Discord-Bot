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
        except psycopg.errors.DuplicateTable: DBConnection.rollback()

        """
        USERROLES TABLE
            USERID: BIGINT PRIMARY KEY, ROLES: BIGINT[]

            USER ID: discord id of the user
            ROLES ARRAY: A list of server-roles that the character will be given.

            NEED TO ACCOUNT FOR: Being able temporary permissions for a category .
                SOLVED: addition of temporary roles table.
        """
        try:
            DBCursor.execute("""
                CREATE TABLE UserRoles (
                    UserID BIGINT PRIMARY KEY,
                    Roles BIGINT[])              
            """)
        except psycopg.errors.DuplicateTable: DBConnection.rollback()

        """
        TEMPORARYUSERROLES TABLE
            USERID: BIGINT PRIMARY KEY, ROLES: BIGINT[], EXPIRATIONDATETIME: TIMESTAMP[]

            USER ID: Discord id of the user.
            ROLES ARRAY: A list of the temporary roles that a user has.
            TIMESTAMP ARARY: A list of datetime's that the roles will expire after and be removed from the user.
        """
        try:
            DBCursor.execute("""
                CREATE TABLE TemporaryUserRoles (
                    UserID BIGINT PRIMARY KEY,
                    Roles BIGINT[],
                    Expiration TIMESTAMP[]
                )
            """)
        except psycopg.errors.DuplicateTable: DBConnection.rollback()
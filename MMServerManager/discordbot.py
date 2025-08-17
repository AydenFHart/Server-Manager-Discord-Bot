import discord
import logging
from discord import app_commands, ui
from discord.ext import commands

import os
from dotenv import load_dotenv; load_dotenv('MMServerManager/bot.env')

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.DEBUG)

"""
HELPFUL LINKS:
    UI / Buttons: https://gist.github.com/lykn/bac99b06d45ff8eed34c2220d86b6bf4

"""

#***FUNCTION IMPORTS***
from databaseUpdating import *

MyGuildID = 1322211561938354186
MyGuild = discord.Object(id=MyGuildID)
class MMSMClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MyGuild)
        await self.tree.sync(guild=MyGuild)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = False
client = MMSMClient(intents=intents)

@client.event
async def on_ready():
    logger.info(f'logged in as {client.user} (ID: {client.user.id})')
    StartupTableCleaning()

    guild = client.get_guild(MyGuildID)
    for member in guild.members:
        if member.bot == True: continue
        CreateServerUsersEntry(Member=member)
        await UpdateUserRoles(User=member) #Updating member roles.
    for role in guild.roles:
        if role.is_bot_managed() == True or role.is_default() == True: continue
        CreateServerRolesEntry(Role=role)

    for Role in FetchRoles():
        RoleOptions.append(discord.SelectOption(label=str(Role[0]), value=int(Role[1]), description=''))

@client.event
async def on_member_join(member):
    logger.info(f"{member.name} has joned the server.")
    CreateServerUsersEntry(Member=member)

@client.event
async def on_message(message):
    if message.author == client.user: return
    CategoryName = 'No Category'
    if message.channel.category != None: CategoryName = message.channel.category.name
    logger.debug(f"Message Recieved in {CategoryName} {message.channel.name}: {message.author} sent \'{message.content}\'")
    UpdateActiveLastFromMessageSent(Message=message)

RoleOptions = []

@client.tree.context_menu(name="Grant Role")
async def grant_role(interaction: discord.Interaction, TargetUser: discord.Member):
    logger.info(f"{interaction.user.name} has used Grant Role")

    class RoleSelectView(ui.View):
        def __init__(self, *, timeout = 15):
            super().__init__(timeout=timeout)

        @ui.select(placeholder='Select a role to give...', options=RoleOptions)
        async def selected_role(self, subinteraction: discord.Interaction, selection:discord.ui.Select):
            SelectionValue = int(selection.values[0])

            #***ADD A WAY TO ADD TRUSTED+ BEING ABLE TO ADD ANY ROLE TO ANYONE***

            if TargetUser.bot == True: await subinteraction.response.send_message("You cannot give roles to a bot.", ephemeral=True, delete_after=5); return
            #if discord.utils.get(interaction.user.roles, id=SelectionValue) == None:
            #    await subinteraction.response.send_message("You must have the selected role to grant it to someone else", ephemeral=True, delete_after=15)
            #    return
            if await HasRolePermissions(User=interaction.user, Roles=[SelectionValue]) == False:
                await subinteraction.response.send_message("You must have the selected role to grant it to someone else", ephemeral=True, delete_after=15)
                return
            
            try:
                GrantRole(User=TargetUser, RoleID=SelectionValue)
                await subinteraction.response.send_message(f"Role granted! {selection.values}", ephemeral=True)
            except Exception:
                await subinteraction.response.send_message("User already has the role.", ephemeral=True, delete_after=5)
            await UpdateUserRoles(User=TargetUser)


    if await HasRolePermissions(User=interaction.user, Roles=["Trusted"]) == True: #Must be trusted to give permanent roles.
        await interaction.response.send_message(f"Select what role to give {TargetUser.name}.", view=RoleSelectView(), ephemeral=True, delete_after=15); return
    else: await interaction.response.send_message("You do not have the permissions to use this command.", ephemeral=True, delete_after=15)

#***NEXT GOAL: ADD A COMMAND FOR MEMBERS TO USE THAT TEMPORARILY GIVES TRAGET USER ACESS TO GAME CATEGORY***

#***NEXT GOAL: ADD A COMMAND TO REMOVE ROLES FROM A MEMBER***

@client.tree.command(
        name="refresh_user_roles",
        description="Updates all users role.")
async def update_roles(interaction: discord.Interaction):
    logger.info(f"{interaction.user.name} has used refresh user roles")
    if HasRolePermissions(User=interaction.user, Roles=['Member']) == False:
        await interaction.response.send_message("You are missing the roles for to use this command", ephemeral=True, delete_after=15)
        return
    guild = client.get_guild(MyGuildID)
    for member in guild.members:
        if member.bot == True: continue
        CreateServerUsersEntry(Member=member)
        await UpdateUserRoles(User=member) #Updating member roles.
    await interaction.response.send_message("Roles for all users have been updated", ephemeral=True)

async def HasRolePermissions(User:discord.Member, Roles:list) -> bool:
    #i don't know if this needs to be async def'd?
    """
    PURPOSE:
        Check if a user has all roles provided in RoleIDs list.
        If they do not have all roles, return false.
        If they have all roles, return true.

    RETURNS:
        A boolean value if the user has all the roles or not
    """
    for Role in Roles:
        if isinstance(Role, int):
            if discord.utils.get(User.roles[1:], id=int(Role)) == None: return(False)
        elif isinstance(Role, str):
            if discord.utils.get(User.roles[1:], name=str(Role)) == None: return(False)
        else:
            logger.error("Provided role identifier is not a string or int")
            raise Exception("Provided role identifier is not a string or int")
    return(True) #User must have all roles provided for a true return

async def UpdateUserRoles(User: discord.Member) -> None:
    """
    PURPOSE:
        Update the provided user's roles in the discord server from information in database.
    """
    logger.debug(f"Updating roles for {User.name}")
    Guild = client.get_guild(MyGuildID)
    RoleIDs = GetUserRoles(User)

    for CurrentRole in User.roles[1:]: #Removing roles a use should not have.
        if RoleIDs != None:
            if int(CurrentRole.id) not in RoleIDs:
                logging.info(f"Removing {CurrentRole.name} from {User.name}")
                await User.remove_roles(CurrentRole)
        else:
            logging.info(f"Removing {CurrentRole.name} from {User.name}")
            await User.remove_roles(CurrentRole)

    if RoleIDs == None: return
    if RoleIDs[0] == None: return
    
    for RoleID in RoleIDs: #Adding roles a user is missing.
        Role = Guild.get_role(int(RoleID))
        if Role not in User.roles[1:]:
            logging.info(f"Adding {Role.name} to {User.name}")
            await User.add_roles(Role)

if __name__ == '__main__':
    client.run(os.getenv('TOKEN'))
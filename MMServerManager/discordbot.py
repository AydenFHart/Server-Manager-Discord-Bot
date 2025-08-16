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

"""
class TestViewButtons(ui.View):

    TargetUser:discord.member = None
    def __init__(self, *, timeout = 15):
        super().__init__(timeout=timeout)


    #@ui.button(label="Test", style=discord.ButtonStyle.grey)
    #async def test_button(self, button: ui.Button, interaction:discord.Interaction):
    #    await button.response.send_message("Hello world!", ephemeral=True)
    #print(self.Member)
"""


"""@client.tree.context_menu(name="Test context!")
async def test_context_menu_command(interaction: discord.Interaction, user: discord.Member):

    class TestButtonView(ui.View):
        def __init__(self, *, timeout = 15):
            super().__init__(timeout=timeout)
            
        @ui.button(label="Test", style=discord.ButtonStyle.grey)
        async def test_button(self, button: ui.Button, interaction: discord.Interaction):
            await button.response.send_message(f"Hello world! {user.name}", ephemeral = True, delete_after = 15)

    print(user.name)
    #await interaction.response.send_message("This is a test!", view=TestViewButtons(), ephemeral=True, delete_after=15)
    logging.debug("Context menu command used")
    await interaction.response.send_message("This is a test!", view = TestButtonView(), ephemeral=True, delete_after=15)"""

@client.tree.context_menu(name="Grant Role")
async def grant_role(interaction: discord.Interaction, TargetUser: discord.Member):

    class RoleSelectView(ui.View):
        def __init__(self, *, timeout = 15):
            super().__init__(timeout=timeout)

        @ui.select(placeholder='Select a role to give...', options=RoleOptions)
        async def selected_role(self, interaction: discord.Interaction, selection:discord.ui.Select):
            
            if TargetUser.bot == True: await interaction.response.send_message("You cannot give roles to a bot.", ephemeral=True, delete_after=5); return
            try:
                GrantRole(User=TargetUser, RoleID=int(selection.values[0]))
                await interaction.response.send_message(f"Role granted! {selection.values}", ephemeral=True)
            except Exception:
                await interaction.response.send_message("User already has the role.", ephemeral=True, delete_after=5)
            await UpdateUserRoles(User=TargetUser)

    await interaction.response.send_message(f"Select what role to give {TargetUser.name}.", view=RoleSelectView(), ephemeral=True, delete_after=15)

async def UpdateUserRoles(User: discord.Member):
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
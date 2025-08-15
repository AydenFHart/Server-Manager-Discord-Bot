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
from databaseUpdating import DBConnectionManager, UpdateActiveLastFromMessageSent

MyGuild = discord.Object(id=1322211561938354186)
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
    print(f'logged in as {client.user} (ID: {client.user.id})')

@client.event
async def on_message(message):
    if message.author == client.user: return
    CategoryName = 'No Category'
    if message.channel.category != None: CategoryName = message.channel.category.name
    logger.debug(f"Message Recieved in {CategoryName} {message.channel.name}: {message.author} sent \'{message.content}\'")
    UpdateActiveLastFromMessageSent(Message=message)

class TestViewButtons(ui.View):
    def __init__(self, *, timeout = 180):
        super().__init__(timeout=timeout)

    @ui.button(label="Test", style=discord.ButtonStyle.grey)
    async def test_button(self, button: ui.Button, interaction:discord.Interaction):
        await button.response.send_message("Hello world!", ephemeral=True)

@client.tree.context_menu(name="Test Content Menu Command")
async def test_context_menu_command(interaction: discord.Interaction, message: discord.Member):
    #await interaction.response.send_message("Test Content Menu Command!", ephemeral=True)
    TestView = TestViewButtons()
    await interaction.response.send_message("This is a test!", view=TestView, ephemeral=True)

if __name__ == '__main__':
    client.run(os.getenv('TOKEN'))
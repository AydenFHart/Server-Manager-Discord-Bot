import discord
import logging
from discord import app_commands

import os
from dotenv import load_dotenv; load_dotenv('MMServerManager/bot.env')

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.DEBUG)

#***FUNCTION IMPORTS***
from databaseUpdating import UpdateActiveLastFromMessageSent

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
client = MMSMClient(intents=intents)

@client.event
async def on_ready():
    print(f'logged in as {client.user} (ID: {client.user.id})')

@client.event
async def on_message(message):
    if message.author == client.user: return
    CategoryName = 'No Category'
    if message.channel.category != None: CategoryName = message.channel.category.name
    logger.debug(f"Message Recieved in {CategoryName} {message.channel.name}: {message.author} sent \'{message.content}\' at {message.created_at}")
    UpdateActiveLastFromMessageSent(Message=message)

client.run(os.getenv('TOKEN'))
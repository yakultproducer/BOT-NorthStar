import discord
from discord.ext import commands

import pymongo
from pymongo import MongoClient

# SECRET
import os
from dotenv import load_dotenv
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MONGODB_TOKEN = os.getenv("MONGODB_TOKEN")

# # azure secret
# from azure.identity import DefaultAzureCredential
# from azure.keyvault.secrets import SecretClient

# # Tokens access
# credential = DefaultAzureCredential()
# keyvault_url = 'https://northstar-key.vault.azure.net'

# # Create a SecretClient using the credential
# secret_client = SecretClient(vault_url=keyvault_url, credential=credential)
# # Retrieve the secret
# DISCORD_TOKEN = secret_client.get_secret("DISCORD-TOKEN").value
# MONGODB_TOKEN = secret_client.get_secret("MONGODB-TOKEN").value

cluster = pymongo.MongoClient(MONGODB_TOKEN)
db = cluster.NorthStarDB
setting = db.setting
user = db.users

'''
==========================
    The main juice
==========================
'''


intents = discord.Intents.all()
intents.reactions=True
bot = discord.Bot(intents=intents, command_prefix=".")


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


@bot.event
async def on_guild_join(guild):
    # Make Query for New Server
    id = str(guild.id)
    query_id = {"_id": id}
    query = setting.find_one(query_id)

    if not query:
        # Create default server settings
        default_settings = {
            "_id": str(guild.id),
            "switches": {
                "sw_logging": False,
                "sw_verify": False,
                # additional switches
            },
            "category": None, 
            "channels": {
                "logging": {
                    "channelId": None,
                    "category": None,
                },
                "verify": {
                    "channelId": None,
                    "category": None,
                    "roleId": None,
                },
                # additional channels
            },
            # other server settings
        }

        # Insert the default settings into the database
        setting.insert_one(default_settings)
        print(f"Finished initial setting for Guild - {guild.name}.")



extensions = [# load cogs
    'cogs.command1',
    'cogs.command2',
    'cogs.command3',
    'cogs.league',
]

if __name__ == '__main__': 
    # import cogs from cogs folder
    for extension in extensions:
        bot.load_extension(extension)


bot.run(DISCORD_TOKEN)  # bot token
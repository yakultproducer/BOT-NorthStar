import discord
from discord.commands import slash_command
from discord.commands import Option
from discord.ext import commands


import os
import string
import random
import asyncio
import datetime


class Utils(commands.Cog):
    """
    Various useful Commands for everyone
    """

    def __init__(self, bot):
        self.bot = bot

    # @discord.user_command()
    # async def greet(self, ctx, member: discord.Member):
    #     await ctx.respond(f'{ctx.author.mention} says hello to {member.mention}!')

    # @commands.Cog.listener() # we can add event listeners to our cog
    # async def on_member_join(self, member): # this is called when a member joins the server
    # # you must enable the proper intents
    # # to access this event.
    # # See the Popular-Topics/Intents page for more info
    #     await member.send('Welcome to the server!')

def setup(bot):
    bot.add_cog(Utils(bot))
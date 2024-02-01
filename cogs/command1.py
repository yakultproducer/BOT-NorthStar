import discord
from discord.commands import slash_command
from discord.commands import Option
from discord.ext import commands, tasks
from discord.ui import Button

from captcha.image import ImageCaptcha

import os
import string
import random
import asyncio
# import emoji
from datetime import datetime, timedelta

guild_id = 874869151892652103

# Poll View


class MyView(discord.ui.View):  # Create a class called MyView that subclasses discord.ui.View

    # Create a button with the label "😎 Click me!" with color Blurple
    @discord.ui.button(label="Click me!", style=discord.ButtonStyle.primary)
    async def button_callback(self, button, interaction):
        count_down = 20
        button.disabled = True
        # Send a message when the button is clicked
        await interaction.response.send_message("Counting Down!")
        for remaining_seconds in range(count_down, 0, -1):
            # Update the button label with the countdown
            button.label = remaining_seconds
            await interaction.message.edit(view=self)
            await asyncio.sleep(1)
        button.disabled = False
        await interaction.message.edit(view=self)


class Utils(commands.Cog):
    """
    Various useful Commands for everyone
    """

    def __init__(self, bot):
        self.bot = bot

    '''
    Commands
    ----------------
    -   Ping
    -   Poll-create
    -   
    '''
    @slash_command(name='ping', description='return bot latency', guilds_ids=[guild_id])
    async def ping(self, ctx):
        """
        Command:     
        Check ping to see is bot alive
        ---------------
        Who can use it:
        Everyone
        """
        await ctx.respond(f"PONG! {round(self.bot.latency * 1000)}ms")

    @slash_command(name="poll-create", description="Create a poll", guilds_ids=[guild_id])
    async def poll_create(
            self, ctx,
            question: Option(str, required=True, description="The question for the poll."),
            option1: str,
            option2: str,
            timer: Option(int, required=False, description="in minutes", default=0),
            option3: Option(str, required=False, default=''),
            option4: Option(str, required=False, default=''),
            option5: Option(str, required=False, default=''),
            option6: Option(str, required=False, default=''),
            option7: Option(str, required=False, default=''),
            option8: Option(str, required=False, default=''),
            option9: Option(str, required=False, default='')):
        '''
        Command:     
        create poll
        ---------------
        Who can use it:
        Everyone
        '''
        await ctx.respond('Poll create command invoked.', ephemeral=True)

        # Pre Setup
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣",
                  "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
        li_opt = [option1, option2, option3, option4,
                  option5, option6, option7, option8, option9]

        # Embed Setup
        embed = discord.Embed(
            title=f"Poll: {question}",
            color=discord.Colour.og_blurple()
        )
        embed.add_field(
            name="Author", value=f"<@{ctx.author.id}>\n", inline=False)
        for i in range(len(li_opt)):
            if (li_opt[i]):
                embed.add_field(
                    name=f"{emojis[i]}: {li_opt[i]}\n", value="", inline=False)
            else:
                break

        # formating button on view
        view = discord.ui.View()
        button1 = discord.ui.Button(
            style=discord.ButtonStyle.danger, label="Close Poll")
        button2 = discord.ui.Button(
            style=discord.ButtonStyle.secondary, label="Time: ", disabled=True)
        view.add_item(button1)
        if (timer != 0):
            view.add_item(button2)

        message = await ctx.send(embed=embed, view=view)

        async def pollCalculation(message):
            # Header
            embed = discord.Embed(
                title=f"Poll Result:",
                description=f"Question:\n {question}",
                color=discord.Colour.og_blurple()
            )
            # Fields
            embed.add_field(
                name="Author", value=f"<@{ctx.author.id}>\n", inline=False)
            embed.add_field(
                name="------Result------", value='', inline=False)
            for i in range(len(li_opt)):
                if (li_opt[i]):
                    reaction = message.reactions[i]
                    embed.add_field(
                        name=f"{reaction.emoji} :{li_opt[i]}\n", value=f"==={reaction.count-1} voted.===", inline=False)
                
            return embed

        
        async def closePoll(interaction: discord.Interaction):
            # Define the callback for the Close Poll button
            message = await ctx.channel.fetch_message(interaction.message.id)
            response = await pollCalculation(message)

            await message.channel.send(embed = response)
            await message.delete()

        # Add the callback to the button
        button1.callback = closePoll

        # adding reaction to message
        for j in range(i):
            await message.add_reaction(emojis[j])

        # Timer sequence
        if timer != 0:
            target_time = datetime.now() + timedelta(minutes=timer)
            while datetime.now() < target_time:
                diff = target_time - datetime.now()
                minutes_part, seconds_part = divmod(
                    int(diff.total_seconds()), 60)
                button2.label = f"Time: {minutes_part:02d}:{seconds_part:02d}"
                # update visual
                try:
                    await message.edit(embed=embed, view=view)
                    await asyncio.sleep(1)
                except discord.NotFound:
                    # prevent error when manually close poll
                    return

            # Close Poll
            message = await ctx.channel.fetch_message(message.id)
            response = await pollCalculation(message)
            await message.channel.send(embed = response)
            await message.delete()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        # ignore if its bot
        if user == self.bot.user:
            return
        # multi vote prevent
        message = reaction.message
        if message.author == self.bot.user and message.embeds:
            embed = message.embeds[0]
            # check is it a poll
            if embed.title and embed.title.lower().startswith("poll:"):
                for emoji in message.reactions:
                    users = await emoji.users().flatten()
                    # when detected user voted before
                    if emoji != reaction and user in users:
                        await message.remove_reaction(reaction, user)
                        return



    @slash_command(name="make-team", description="Create teams")
    async def make_team(
        self, ctx,
        event_title: str,
        event_description: str,
        team_size: Option(int,required=False, default=1),
        people: Option(int, required=False, description="The amount of peoples that can join.\n Default will be unlimited. ", default=None),
        timer: Option(int, required=False, description="Timer before closing the event application.\n Default will not close automatically.", default=0)):
        
        '''
        Command:     
        make team
        ---------------
        User:
        Mod team
        ---------------
        Functionality:
        Create team based pvp event application for people to join
        '''

        message = await ctx.respond("command invoked.", ephemeral=True)  
        await message.delete_original_response()

        # Embed
        embed = discord.Embed(
            title=f"Event: {event_title}",
            description=f"Author: <@{ctx.author.id}>\n",
            color=discord.Colour.og_blurple()
        )
        embed.add_field(
            name="Description", value=f"{event_description}", inline=False)

        # View
        view = discord.ui.View()
        button1 = discord.ui.Button(
            style=discord.ButtonStyle.primary, label="Join")
        button2 = discord.ui.Button(
            style=discord.ButtonStyle.secondary, label="Time: ", disabled=True)
        view.add_item(button1)
        if (timer != 0):
            view.add_item(button2)
        
        
        message = await ctx.send(embed=embed, view=view)

        # Timer sequence
        if timer != 0:
            target_time = datetime.now() + timedelta(minutes=timer)
            while datetime.now() < target_time:
                diff = target_time - datetime.now()
                minutes_part, seconds_part = divmod(
                    int(diff.total_seconds()), 60)
                button2.label = f"Time: {minutes_part:02d}:{seconds_part:02d}"
                # update visual
                try:
                    await message.edit(embed=embed, view=view)
                    await asyncio.sleep(1)
                except discord.NotFound:
                    # prevent error when manually close poll
                    return

         
        async def join(interaction: discord.Interaction):
            
            # Define the callback for the Close Poll button
            message = await ctx.channel.fetch_message(interaction.message.id)
            # 
            if team_size > 1:
                print("bigger than 1")
            else:
                print("solo team")
            
            await message.channel.send("hi")
            await interaction.response.defer()
        
        button1.callback = join


    @slash_command(name="test", description="test", guilds_ids=[guild_id])
    async def start_timer(self,ctx, li):
        return
            


def setup(bot):
    bot.add_cog(Utils(bot))

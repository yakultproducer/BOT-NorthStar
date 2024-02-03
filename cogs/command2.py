import discord
from discord import AllowedMentions
from discord.commands import slash_command
from discord.commands import Option
from discord.ext import commands

import pymongo
from pymongo import MongoClient

import datetime
from datetime import datetime
import textwrap

# SECRET
import os
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MONGODB_TOKEN = os.getenv("MONGODB_TOKEN")


# login into DataBases
cluster = pymongo.MongoClient(MONGODB_TOKEN)
db = cluster.NorthStarDB
setting = db.setting
user = db.users


class Settings(discord.ui.View):
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]

    def __init__(self, ctx, timeout=60):
        super().__init__(timeout=None)

        self.ctx = ctx
        self.author = self.ctx.author

        self.query_id = {"_id": str(ctx.guild.id)}
        self.query = setting.find_one(self.query_id)
        self.switches = self.query["switches"]
        # init decoration for the buttons
        for i, v in enumerate(self.switches):
            cur_button = self.children[i]
            cur_button.style = (
                discord.ButtonStyle.green
                if self.switches[v] == True
                else discord.ButtonStyle.gray
            )

    @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emojis[0], custom_id="b1")
    async def button1(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        self.button1.style = (
            discord.ButtonStyle.green
            if self.button1.style == discord.ButtonStyle.gray
            else discord.ButtonStyle.gray
        )

        # Logging Switch (DB update)
        setting.find_one_and_update(
            self.query_id,
            {"$set": {"switches.sw_logging": not self.switches["sw_logging"]}},
        )
        self.query = setting.find_one(self.query_id)
        self.switches["sw_logging"] = self.query["switches"]["sw_logging"]

        # Creating Category and Channel
        if self.switches["sw_logging"]:
            await Moderation.set_channel(self.ctx, "logging")

        # Visual Update
        await interaction.message.edit(view=self)
        await interaction.response.defer()

    @discord.ui.button(style=discord.ButtonStyle.gray, emoji=emojis[1], custom_id="b2")
    async def button2(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        self.button2.style = (
            discord.ButtonStyle.green
            if self.button2.style == discord.ButtonStyle.gray
            else discord.ButtonStyle.gray
        )

        # Verify Switch (DB update)
        setting.find_one_and_update(
            self.query_id,
            {"$set": {"switches.sw_verify": not self.switches["sw_verify"]}},
        )
        self.query = setting.find_one(self.query_id)
        self.switches["sw_verify"] = self.query["switches"]["sw_verify"]

        # Create Channel
        if self.switches["sw_verify"]:
            channel = await Moderation.set_channel(self.ctx, "verify")

            # Verify Channel Limitaion
            """
            - only default user can read 
            """
            guild = self.ctx.guild
            id = str(guild.id)
            query_id = {"_id": id}
            query = setting.find_one(query_id)

            # Creating Verified Role
            role = discord.utils.get(
                guild.roles, id=query["channels"]["verify"]["roleId"]
            )
            if not role:
                role = await guild.create_role(name="verified")
                setting.find_one_and_update(
                    query_id, {"$set": {"channels.verify.roleId": role.id}}
                )

            # Channel Permission Update
            permissions = discord.PermissionOverwrite()
            permissions.read_messages = False
            permissions.send_messages = False
            await channel.set_permissions(role, overwrite=permissions)
            permissions.read_messages = True
            permissions.send_messages = True
            await channel.set_permissions(guild.default_role, overwrite=permissions)

        # Visual Update
        await interaction.message.edit(view=self)
        await interaction.response.defer()


class Moderation(
    commands.Cog
):  # create a class for our cog that inherits from commands.Cogse
    # this class is used to create a cog, which is a module that can be added to the bot

    def __init__(
        self, bot
    ):  # this is a special method that is called when the cog is loaded
        self.bot = bot

    """
    Custom Check function
    """

    def is_guild_owner():
        """
        check is author the guild owner
        """

        async def predicate(ctx):
            guild = ctx.guild
            owner = guild.owner
            return ctx.author == owner

        return commands.check(predicate)

    """
    Commands
    """

    @slash_command(description="[Owner] Config the log category channel.")
    @commands.cooldown(1, 60, commands.BucketType.user)
    @is_guild_owner()
    async def conf_swch(self, ctx):
        await ctx.respond("Config switches have been sent to your DM.")
        response = "To activate/deactivate function click the corresponding emoji on this message\n\
            ```1️⃣: Logging System \n2️⃣: Verify System\n3️⃣: NSFW Censoring```"
        msg = await ctx.author.send(response, delete_after=60, view=Settings(ctx))

    @slash_command(name="verify-me", description="Verify new members")
    async def verifyme(self, ctx):
        """
        Command:
        Send a Captcha image to verify new member
        ---------------
        Who can use it:
        Only new member
        """

        # Info
        guild = ctx.guild
        id = str(guild.id)
        query_id = {"_id": id}

        # Switch Check
        if (
            not (query := setting.find_one(query_id))
            or not query["switches"]["sw_verify"]
        ):
            return
        
        # Text Format
        agreement_date = datetime.now().strftime("%d/%m/%y")
        response = (
            "# NorthStar Agreement\n"
            "\n"
            f"This Agreement is made and entered on {agreement_date} between:\n"
            "### Bot Developer:\n"
            f"<@{378780304002908161}>\n"
            "### Server Owner:\n"
            f"<@{ctx.guild.owner.id}>\n"
            "### User:\n"
            f"<@{ctx.author.id}>\n"
            "## 1. Chat Logging Consent:\n"
            "> The user acknowledges and agrees that the Discord bot provided by the Bot Developer will log chat messages within the Server ('Chat Logging'). This includes but is not limited to text messages, commands, and user interactions.\n"
            "\n"
            "## 2. Purpose of Chat Logging:\n"
            "> The purpose of Chat Logging is to enhance moderation, improve user experience, and assist in addressing issues related to the Discord server. The Bot Developer assures that any logged data will only stay within the server.\n"
            )

        view = discord.ui.View()
        btn_agree = discord.ui.Button(
            style=discord.ButtonStyle.success, label=f"I Agree")
        view.add_item(btn_agree)

        # Callback Function
        async def agree(interaction: discord.Interaction):
            role = discord.utils.get(
                guild.roles, id=query["channels"]["verify"]["roleId"]
            )
            await interaction.author.add_roles(role)
        btn_agree.callback = agree

        # Sending
        msg = await ctx.respond(response, view=view, ephemeral=True, allowed_mentions=discord.AllowedMentions.none())

    # @slash_command(name="addrank", description="Add role or ")
    # async def addrank(self, ctx):
    #     pass

    

    """
    Log Listener
    """

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """
        Function:
        - Copy the deleted message and send it to the logging channel.
        - Using embed to beautify the message.
        """
        # Exceptions
        if (
            not isinstance(
                message.channel,
                (discord.TextChannel, discord.DMChannel, discord.GroupChannel),
            )
            or message.author.bot
        ):
            return

        # Info
        guild = message.guild
        id = str(guild.id)
        query_id = {"_id": id}

        # Switch Check
        if (
            not (query := setting.find_one(query_id))
            or not query["switches"]["sw_logging"]
        ):
            return

        # Download if there is attachment
        my_files = []
        for attachment in message.attachments:
            await attachment.save(attachment.filename)
            my_file = discord.File(attachment.filename, filename=attachment.filename)
            my_files.append(my_file)

        # Determine Deleter
        audit_logs = await message.guild.audit_logs(
            limit=1, action=discord.AuditLogAction.message_delete
        ).flatten()
        deleter = f"<@{message.author.id}>"

        if audit_logs:
            entry = audit_logs[0]
            time_difference = (
                datetime.utcnow().replace(tzinfo=None)
                - entry.created_at.replace(tzinfo=None)
            ).total_seconds()
            if (
                abs(time_difference) <= round(self.bot.latency * 1000) + 150
            ):  # bot latancy delay
                deleter = f"<@{entry.user.id}>"

        # Embed Msg Design
        embed = discord.Embed(
            title="Message Deleted",
            color=discord.Color.brand_red(),
        )
        embed.add_field(name="Channel:", value=message.channel.mention, inline=True)
        embed.add_field(name="Author", value=f"<@{message.author.id}>", inline=True)
        embed.add_field(name="Deleter", value=deleter, inline=True)
        if my_files:
            embed.add_field(
                name="Message (Contained Attachments)",
                value=message.clean_content,
                inline=False,
            )
        else:
            embed.add_field(name="Message", value=message.clean_content, inline=False)

        # Sending
        mention = AllowedMentions(users=False)
        send_channel = discord.utils.get(
            guild.text_channels, id=query["channels"]["logging"]["channelId"]
        )
        if send_channel:
            msg = await send_channel.send(embed=embed, allowed_mentions=mention)
            if my_files:
                await msg.reply(
                    "Attachments: ", files=my_files, allowed_mentions=mention
                )
        else:
            setting.find_one_and_update(
                query_id, {"$set": {"switches.sw_logging": False}}
            )

        # Clean Up
        for attachment in message.attachments:
            os.remove(attachment.filename)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """
        Function:
        - Copy the "before vs after" message and send it to logging channel
        """
        message = before

        # Exceptions
        if (
            not isinstance(
                message.channel,
                (discord.TextChannel, discord.DMChannel, discord.GroupChannel),
            )
            or message.author.bot
        ):
            return

        # Info
        guild = message.guild
        id = str(guild.id)
        query_id = {"_id": id}

        # Switch Check
        if (
            not (query := setting.find_one(query_id))
            or not query["switches"]["sw_logging"]
        ):
            return

        # Confirmation
        if before.clean_content != after.clean_content:
            # Embed Msg Design
            embed = discord.Embed(
                title="Message Edited",
                color=discord.Color.dark_orange(),
            )
            embed.add_field(name="Channel:", value=message.channel.mention, inline=True)
            embed.add_field(name="Author", value=f"<@{message.author.id}>", inline=True)
            embed.add_field(
                name="Message(Before)", value=before.clean_content, inline=False
            )
            embed.add_field(
                name="Message(After)", value=after.clean_content, inline=False
            )

            mention = AllowedMentions(users=False)
            send_channel = discord.utils.get(
                guild.text_channels, id=query["channels"]["logging"]["channelId"]
            )
            # Sending
            if send_channel:
                msg = await send_channel.send(embed=embed, allowed_mentions=mention)
            else:
                setting.find_one_and_update(
                    query_id, {"$set": {"switches.sw_logging": False}}
                )

    """
    Error Handling
    """

    @conf_swch.error
    async def not_owner_error(ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            await ctx.respond("Only server owner can use this command.", ephemeral=True)
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.respond("It is already in your DM", ephemeral=True)

    """
    Utilities
    """

    async def set_area(ctx):
        """
        Function:
        - Setup a default category to contain all the channels create by this bot
        - Prevent default users to view category
        """

        # Info
        guild = ctx.guild
        id = str(guild.id)
        query_id = {"_id": id}
        query = setting.find_one(query_id)

        # Check is category exisits
        category_id = query["category"]
        category = discord.utils.get(ctx.guild.categories, id=category_id)
        if not category:
            cat = await ctx.guild.create_category("NorthStar-Playground")
            category_id = cat.id
            await cat.set_permissions(ctx.guild.default_role, read_messages=False)
            setting.find_one_and_update(query_id, {"$set": {"category": category_id}})
        return category_id

    async def set_channel(ctx, channel_name):
        """
        Function:
        - Setup a channel with the given name
        """

        # Info
        guild = ctx.guild
        id = str(guild.id)
        query_id = {"_id": id}
        query = setting.find_one(query_id)

        # Check category
        category_id = await Moderation.set_area(ctx)
        category = discord.utils.get(ctx.guild.categories, id=category_id)

        # Check channel
        channel_id = query["channels"][channel_name]["channelId"]
        channel = discord.utils.get(ctx.guild.text_channels, id=channel_id)
        if not channel:
            channel = await ctx.guild.create_text_channel(
                channel_name, category=category
            )
            setting.find_one_and_update(
                query_id, {"$set": {f"channels.{channel_name}.channelId": channel.id}}
            )
            setting.find_one_and_update(
                query_id, {"$set": {f"channels.{channel_name}.category": category.id}}
            )
        else:
            # Safety check
            await channel.edit(category=category)
            setting.find_one_and_update(
                query_id, {"$set": {f"channels.{channel_name}.category": category.id}}
            )
        return channel

    
def setup(bot):  # this is called by Pycord to setup the cog
    bot.add_cog(Moderation(bot))  # add the cog to the bot

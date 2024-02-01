import discord
from discord.commands import slash_command
from discord.commands import Option
from discord.ext import commands

import requests

# SECRET
import os
from dotenv import load_dotenv
load_dotenv()
RIOT_KEY = os.getenv("RIOT_KEY")



server_region = [
    "BR1",
    "EUN1",
    "EUW1",
    "JP1",
    "KR",
    "LA1",
    "LA2",
    "NA1",
    "OC1",
    "PH2",
    "RU",
    "SG2",
    "TH2",
    "TR1",
    "TW2",
    "VN2",
]


class Lol(commands.Cog):
    """
    Various useful Commands for everyone
    """

    def __init__(self, bot):
        self.bot = bot

    # Define a slash command group
    league = discord.SlashCommandGroup(name="league", description="League commands")

    @league.command(name="info", description="Check League of Legend player info.")
    async def check_rank(
        self,
        ctx,
        game_name,
        tag_line,
        region: Option(
            str,
            "The region of the account",
            required=True,
            choices=server_region,
        ),
    ):
        # Region Check
        if region not in server_region:
            await ctx.respond(f"Please use the region choices.", ephemeral=True)
            
        await ctx.defer()
        # Riot API URLs
        riot_ac_url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}?api_key={RIOT_KEY}"
        response = requests.get(riot_ac_url)

        # INFO
        old_name = None
        lvl = 0
        icon = 0
        solo_data = {
            "tier": None,
            "rank": None,
            "leaguePoints": 0,
            "wins": 0,
            "losses": 0,
        }
        flex_data = {
            "tier": None,
            "rank": None,
            "leaguePoints": 0,
            "wins": 0,
            "losses": 0,
        }

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            riot_ac_data = response.json()
            puuid = riot_ac_data["puuid"]

            # Summoner API URL
            summoner_url = f"https://{region.lower()}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}?api_key={RIOT_KEY}"
            response = requests.get(summoner_url)

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                summoner_data = response.json()
                summoner_id = summoner_data["id"]

                # Update Info
                lvl = summoner_data["summonerLevel"]
                icon = summoner_data["profileIconId"]

                # League API URL
                league_url = f"https://{region.lower()}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}?api_key={RIOT_KEY}"
                response = requests.get(league_url)

                # Check if the request was successful (status code 200)
                if response.status_code == 200:
                    league_data = response.json()
                    # Process league data as needed
                    for queue_type in league_data:
                        if queue_type["queueType"] == "RANKED_SOLO_5x5":
                            for key, value in queue_type.items():
                                if key in solo_data:
                                    solo_data[key] = value
                        elif queue_type["queueType"] == "RANKED_FLEX_SR":
                            for key, value in queue_type.items():
                                if key in solo_data:
                                    flex_data[key] = value
                    # Embed 
                    embed = discord.Embed(
                    title="League of Legend",
                    description=" ",
                    color=discord.Colour.dark_gold(),
                    )
                    embed.add_field(name="Player Info", value=f"Name: {game_name}#{tag_line}\n Level: {lvl}", inline=False)
                    embed.add_field(name=" ", value=f" ", inline=False)
                    if solo_data["tier"]:
                        str_data = ""
                        for key, value in solo_data.items():
                            str_data += f"{key}: {value}\n"
                        embed.add_field(name="RANKED SOLO:", value=f"{str_data}", inline=True)
                        embed.add_field(name=" ", value=f" ", inline=True)
                    if flex_data["tier"]:
                        str_data = ""
                        for key, value in flex_data.items():
                            str_data += f"{key}: {value}\n"
                        embed.add_field(name="RANKED FLEX:", value=f"{str_data}", inline=True)
                    embed.set_thumbnail(url=f"https://raw.communitydragon.org/latest/game/assets/ux/summonericons/profileicon{icon}.png")
                    await ctx.respond(embed=embed)

                # Error Handler
                else:
                    print(f"League API Error: {response.status_code} - {response.text}")
                    await ctx.respond(f"League API Error: {response.status_code} - {response.text}", ephemeral=True)
            else:
                print(f"Summoner API Error: {response.status_code} - {response.text}")
                await ctx.respond(f"Summoner API Error: {response.status_code} - {response.text}", ephemeral=True)
        else:
            print(f"Riot API Error: {response.status_code} - {response.text}")
            await ctx.respond(f"Riot API Error: {response.status_code} - {response.text}", ephemeral=True)


def setup(bot):
    bot.add_cog(Lol(bot))

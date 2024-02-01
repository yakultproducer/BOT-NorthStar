import discord
from discord.commands import slash_command
from discord.commands import Option
from discord.ext import commands
from discord.ui import Button, View


import os
import string
import random
import asyncio
import datetime
import math

import random
from random import shuffle



class TicTacToeGame:
    # TicTacToe Game Logic
    def __init__(self):
        self.board = ["-" for _ in range(9)]
        self.current_player = "X"
        self.ai = True

    def available_moves(self):
        return [i for i, val in enumerate(self.board) if val == "-"]

    def make_move(self, position):
        self.board[position] = self.current_player
        self.switch_player()

    def switch_player(self):
        self.current_player = "O" if self.current_player == "X" else "X"

    def check_winner(self):
        # Check rows, columns, and diagonals
        for i in range(3):
            # col
            if self.board[i] == self.board[i + 3] == self.board[i + 6] != "-":
                return self.board[i]
            # row
            if (
                self.board[i * 3]
                == self.board[i * 3 + 1]
                == self.board[i * 3 + 2]
                != "-"
            ):
                return self.board[i * 3]
        # diagonal
        if self.board[0] == self.board[4] == self.board[8] != "-":
            return self.board[4]
        if self.board[2] == self.board[4] == self.board[6] != "-":
            return self.board[4]
        return False

    def is_board_full(self):
        return "-" not in self.board


class Connect3Game:
    # Connect3 Game Logic
    def __init__(self):
        self.board = ["-" for _ in range(25)]
        self.current_player = "X"
        self.ai = True

    def available_moves(self):
        indexs = []
        for i in range(5):
            for j in range(5, 0, -1):
                if self.board[i+(j-1)*5] == "-":
                    indexs.append(i+(j-1)*5)
                    break
        return indexs           
        # return [i for i, val in enumerate(self.board) if val == "-"]

    def make_move(self, position):
        index = position
        while index + 5 <= 24:
            if self.board[index + 5] != "-":
                break
            index = index + 5
        self.board[index] = self.current_player
        self.switch_player()

    def switch_player(self):
        self.current_player = "O" if self.current_player == "X" else "X"

    def check_winner(self):
        # Check rows, columns, and diagonals
        for i in range(5):
            for j in range(3):
                # col
                if (
                    self.board[i + j*5]
                    == self.board[i + 5 + j*5]
                    == self.board[i + 10 + j*5]
                    != "-"
                ):
                    return self.board[i + j*5]
                # row
                if (
                    self.board[(5 * i + j)]
                    == self.board[(5 * i + j + 1)]
                    == self.board[(5 * i + j + 2)]
                    != "-"
                ):
                    return self.board[5 * i + j]
        # diagonal
        for i in range(10, 25):
            # top right direction
            if i % 5 in [0, 2]:
                if self.board[i] == self.board[i - 4] == self.board[i - 8] != "-":
                    return self.board[i]
            # top left direction
            if i % 5 in [2, 4]:
                if self.board[i] == self.board[i - 6] == self.board[i - 12] != "-":
                    return self.board[i]
        return False

    def is_board_full(self):
        return "-" not in self.board


class Games(commands.Cog):
    """
    Various useful Commands for everyone
    """

    def __init__(self, bot):
        self.bot = bot

    """
    Games Commands
    ----------------
    -   ttt (tictactoe)
    -   cnt (connect three)
    -   
    """

    @slash_command(name="ttt")
    async def tictactoe(
        self, ctx, opponent: Option(discord.Member, required=False, default=None)
    ):
        if opponent is None:
            opponent = self.bot.user
        players = [ctx.author.id, opponent.id]
        shuffle(players)

        game = TicTacToeGame()
        if not opponent.bot:
            game.ai = False

        def minimax(board, depth, is_maximizing, symbol):
            if board.is_board_full():
                winner = board.check_winner()
                if not winner:
                    return 0
                else:
                    return 1 if winner == symbol else -1

            scores = []
            for move in board.available_moves():
                board.make_move(move)
                scores.append(minimax(board, depth + 1, not is_maximizing, symbol))
                board.board[move] = "-"
                board.switch_player()

            # print(scores)
            return max(scores) if is_maximizing else min(scores)

        def find_best_move(board):
            best_val = -math.inf
            best_move = None
            symbol = board.current_player
            for move in board.available_moves():
                board.make_move(move)
                move_val = minimax(board, 0, False, symbol)
                board.board[move] = "-"  # Undo the move
                board.switch_player()

                if move_val > best_val:
                    best_move = move
                    best_val = move_val
            # print("---")

            return best_move

        async def ai_move(message):
            if game.ai:
                # message = interaction.message
                button_index = find_best_move(game)
                game.make_move(button_index)
                print(button_index)
                view = make_buttons()

                # Game Calculation
                if game.check_winner():
                    content = f"{game.current_player} have won!"
                    view.disable_all_items()
                else:
                    if game.is_board_full():
                        content = f"It's A Tie!\n"
                    else:
                        content = f"Current player: {game.current_player}\n"

                # update message
                await message.edit(content=content, view=view)

        def make_buttons():
            view = View()
            for row in range(3):
                for column in range(3):
                    btn = Button(
                        style=discord.ButtonStyle.secondary,
                        label=game.board[3 * row + column],
                        row=row,
                        custom_id=f"button_{3*row+column}",
                    )
                    if btn.label != "-":
                        btn.disabled = True
                    btn.callback = handle_button_click
                    view.add_item(btn)

            btn = Button(
                style=discord.ButtonStyle.danger,
                label="Stop",
                row=3,
                custom_id="stop_button",
            )
            btn.callback = handle_stop
            view.add_item(btn)
            return view

        async def handle_button_click(interaction):
            position = 1 if game.current_player == "O" else 0
            if interaction.user.id == players[position]:
                message = interaction.message
                button_index = int(interaction.custom_id.split("_")[1])
                game.make_move(button_index)
                view = make_buttons()

                # Game Calculation
                if game.check_winner():
                    content = f"{game.check_winner()} have won!"
                    view.disable_all_items()
                    await message.edit(content=content, view=view)
                    await interaction.response.defer()
                    return
                else:
                    if game.is_board_full():
                        content = f"It's A Tie!\n"
                        await message.edit(content=content, view=view)
                        await interaction.response.defer()
                        return
                    else:
                        content = f"Current player: {game.current_player}\n"

                # update message
                await message.edit(content=content, view=view)

            else:
                # Not ur turn or game
                await interaction.response("This is not your turn.", ephemeral=True)

            # AI turn
            if game.ai:
                message = interaction.message
                await ai_move(message)

            await interaction.response.defer()

        async def handle_stop(interaction):
            if interaction.user.id in players:
                content = f"Game Stopped by <@{interaction.user.id}>"
                await message.edit(content=content)
            else:
                await interaction.response("This is not your game.", ephemeral=True)
            await interaction.response.defer()

        # Game Board Setup
        view = make_buttons()

        await ctx.respond("Starting Tic Tac Toe...", ephemeral=True)
        response = f"Game Info:\n:x: :<@{players[0]}>\n:o: :<@{players[1]}>"
        await ctx.respond(response, allowed_mentions=discord.AllowedMentions.none())
        message = await ctx.send(view=view)

        # if bot move first
        player = ctx.guild.get_member(players[0])
        if player.bot:
            # message = ctx.message
            game.make_move(random.randint(0, 8))
            view = make_buttons()
            content = f"Current player: {game.current_player}\n"
            await message.edit(content=content, view=view)

    @slash_command(name="cnt")
    async def connectthree(
        self, ctx, opponent: Option(discord.Member, required=False, default=None)
    ):
        if opponent is None:
            opponent = self.bot.user
        players = [ctx.author.id, opponent.id]
        shuffle(players)

        game = Connect3Game()
        if not opponent.bot:
            game.ai = False

        def minimax(board, depth, is_maximizing, symbol):
            if depth > 5:
                return 0
            if board.is_board_full():
                winner = board.check_winner()
                if not winner:
                    return 0
                else:
                    return 1 if winner == symbol else -1

            scores = []
            for move in board.available_moves():
                board.make_move(move)
                scores.append(minimax(board, depth + 1, not is_maximizing, symbol))
                board.board[move] = "-"
                board.switch_player()

            # print(scores)
            return max(scores) if is_maximizing else min(scores)

        def find_best_move(board):
            best_val = -math.inf
            best_move = []
            symbol = board.current_player
            for move in board.available_moves():
                board.make_move(move)
                move_val = minimax(board, 0, False, symbol)
                board.board[move] = "-"  # Undo the move
                board.switch_player()

                if move_val == best_val:
                    best_move.append(move)

                if move_val > best_val:
                    best_move = [move]
                    best_val = move_val

            return best_move

        async def ai_move(message):
            if game.ai:
                # message = interaction.message
                button_indexs = find_best_move(game)
                shuffle(button_indexs)
                button_index = button_indexs[0]
                game.make_move(button_index)
                print(button_index)
                view = make_buttons()

                # Game Calculation
                if game.check_winner():
                    content = f"{game.check_winner()} have won!"
                    view.disable_all_items()
                else:
                    if game.is_board_full():
                        content = f"It's A Tie!\n"
                    else:
                        content = f"Current player: {game.current_player}\n"

                # update message
                await message.edit(content=content, view=view)

        def make_buttons():
            view = View()
            for row in range(5):
                for column in range(5):
                    btn = Button(
                        style=discord.ButtonStyle.secondary,
                        label=game.board[5 * row + column],
                        row=row,
                        custom_id=f"button_{5*row+column}",
                    )
                    if btn.label != "-" or row > 0:
                        btn.disabled = True
                    btn.callback = handle_button_click
                    view.add_item(btn)

            # btn = Button(
            #     style=discord.ButtonStyle.danger,
            #     label="Stop",
            #     # row=6,
            #     custom_id="stop_button",
            # )
            # btn.callback = handle_stop
            # view.add_item(btn)
            return view

        async def handle_button_click(interaction):
            position = 1 if game.current_player == "O" else 0
            if interaction.user.id == players[position]:
                message = interaction.message
                button_index = int(interaction.custom_id.split("_")[1])
                game.make_move(button_index)
                view = make_buttons()

                # Game Calculation
                if game.check_winner():
                    content = f"{game.check_winner()} have won!"
                    view.disable_all_items()
                    await message.edit(content=content, view=view)
                    await interaction.response.defer()
                    return
                else:
                    if game.is_board_full():
                        content = f"It's A Tie!\n"
                        await message.edit(content=content, view=view)
                        await interaction.response.defer()
                        return
                    else:
                        content = f"Current player: {game.current_player}\n"

                # update message
                await message.edit(content=content, view=view)

            else:
                # Not ur turn or game
                await interaction.response("This is not your turn.", ephemeral=True)

            # AI turn
            if game.ai:
                message = interaction.message
                await ai_move(message)

            await interaction.response.defer()

        async def handle_stop(interaction):
            if interaction.user.id in players:
                content = f"Game Stopped by <@{interaction.user.id}>"
                await message.edit(content=content)
            else:
                await interaction.response("This is not your game.", ephemeral=True)
            await interaction.response.defer()

        # Game Board Setup
        view = make_buttons()

        await ctx.respond("Starting Connect 3...", ephemeral=True)
        response = f"Game Info:\n:x: :<@{players[0]}>\n:o: :<@{players[1]}>"
        await ctx.respond(response, allowed_mentions=discord.AllowedMentions.none())
        message = await ctx.send(view=view)

        # if bot move first
        player = ctx.guild.get_member(players[0])
        if player.bot:
            # message = ctx.message
            game.make_move(random.randint(0, 8))
            view = make_buttons()
            content = f"Current player: {game.current_player}\n"
            await message.edit(content=content, view=view)


def setup(bot):
    bot.add_cog(Games(bot))

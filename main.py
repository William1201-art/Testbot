import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import random
import asyncio
from discord.ui import Button, View

from myserver import server_on

intents = discord.Intents.default()
intents.message_content = True  

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command()
async def hello(ctx):
    await ctx.send("อะไรมึง")


ARROWS = ["⬅️", "⬆️", "➡️", "⬇️"]

class ArrowGame(View):
    def __init__(self, sequence, timeout=15):
        super().__init__(timeout=timeout)
        self.sequence = sequence
        self.user_inputs = []
        self.result = None

        for arrow in ARROWS:
            self.add_item(ArrowButton(arrow, self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True  # อนุญาตให้ทุกคนกดได้

    async def on_timeout(self):
        if self.result is None:
            self.result = False

class ArrowButton(Button):
    def __init__(self, label, game_view):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.game_view = game_view

    async def callback(self, interaction: discord.Interaction):
        self.game_view.user_inputs.append(self.label)
        await interaction.response.defer()

        if len(self.game_view.user_inputs) == len(self.game_view.sequence):
            if self.game_view.user_inputs == self.game_view.sequence:
                self.game_view.result = True
            else:
                self.game_view.result = False
            self.game_view.stop()

@bot.command()
@commands.has_permissions(administrator=True)
async def startgame(ctx):
    sequence = random.choices(ARROWS, k=4)
    view = ArrowGame(sequence)

    embed = discord.Embed(
        description="จงกดปุ่มตามลำดับนี้ให้ถูกต้องภายในเวลา 15 วินาที:\n\n" + " ".join(sequence),
        color=discord.Color.blue()
    )

    embed.set_author(name="Testbot")

    await ctx.send(embed=embed, view=view)

    await view.wait()

    if view.result is None:
        await ctx.send("⏰ หมดเวลา!")
    elif view.result:
        await ctx.send("✅ ยินดีด้วย! คุณตอบถูก")
    else:
        await ctx.send("❌ คุณตอบผิด ลองใหม่อีกครั้ง")

server_on()

load_dotenv()

bot.run(os.environ['DISCORD_TOKEN'])
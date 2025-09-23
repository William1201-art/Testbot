import os
import random
import asyncio
from datetime import datetime
import discord
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host="0.0.0.0", port=8080)

def server_on():
    t = Thread(target=run)
    t.start()

ARROWS = ["⬅️", "⬆️", "➡️", "⬇️"]

load_dotenv()

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name(
    "discordworkattendance.json",
    scope
)
client = gspread.authorize(creds)
SHEET_NAME = "Work_attendance_HB"
sheet = client.open(SHEET_NAME).sheet1


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user.name}")


@bot.command()
async def hello(ctx):
    await ctx.send("อะไรมึง")


class ArrowGame(View):
    def __init__(self, sequence, timeout=15):
        super().__init__(timeout=timeout)
        self.sequence = sequence
        self.user_inputs = {} 
        self.result = {}  

        for arrow in ARROWS:
            self.add_item(ArrowButton(arrow, self))

    async def on_timeout(self):
        for user_id, inputs in self.user_inputs.items():
            if len(inputs) < len(self.sequence):
                self.result[user_id] = False


class ArrowButton(Button):
    def __init__(self, label, game_view):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.game_view = game_view

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        if user_id not in self.game_view.user_inputs:
            self.game_view.user_inputs[user_id] = []

        self.game_view.user_inputs[user_id].append(self.label)
        await interaction.response.defer()


        if len(self.game_view.user_inputs[user_id]) == len(self.game_view.sequence):
            if self.game_view.user_inputs[user_id] == self.game_view.sequence:
                self.game_view.result[user_id] = True
            else:
                self.game_view.result[user_id] = False


@bot.command(name="game")
@commands.has_permissions(administrator=True)
async def startgame(ctx):
    sequence = random.choices(ARROWS, k=4)
    view = ArrowGame(sequence)

    embed = discord.Embed(
        description="🎯 จงกดปุ่มตามลำดับนี้ให้ถูกต้องภายในเวลา 15 วินาที:\n\n" + " ".join(sequence),
        color=discord.Color.blue(),
    )
    embed.set_author(name="Mini Arrow Game")

    await ctx.send(embed=embed, view=view)

    await view.wait() 
    if not view.result:
        await ctx.send("⏰ ไม่มีใครกดครบ หมดเวลา!")
        return

    winners = [f"<@{uid}>" for uid, res in view.result.items() if res]
    losers = [f"<@{uid}>" for uid, res in view.result.items() if not res]

    if winners:
        await ctx.send("✅ คนที่ตอบถูกคือ: " + ", ".join(winners))
    if losers:
        await ctx.send("❌ คนที่ตอบผิดคือ: " + ", ".join(losers))



@bot.command()
async def ci(ctx):
    """ตอกบัตรเข้างาน + บันทึกเวลา + ส่งไป Google Sheet"""
    if not ctx.message.attachments:
        await ctx.send("⚠️ กรุณาแนบรูป .png ด้วย เช่น !ci พร้อมรูปถ่าย")
        return


    attachment = ctx.message.attachments[0]
    file_url = attachment.url

    checkin_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    
    data = [str(ctx.author), str(ctx.author.id), checkin_time, file_url]
    sheet.append_row(data)

  
    embed = discord.Embed(
        title="🕒 ตอกบัตรเข้างานเรียบร้อย",
        description=f"{ctx.author.mention} ลงชื่อเข้าทำงานเวลา {checkin_time}",
        color=discord.Color.green(),
    )
    embed.set_thumbnail(url=file_url)
    await ctx.send(embed=embed)


if __name__ == "__main__":
    server_on()  
    TOKEN = os.getenv("DISCORD_TOKEN")
    bot.run(TOKEN)

import os
import discord
import pyodbc
import time
import datetime
import subprocess
import sys
import logging

from dotenv import load_dotenv
from discord.ext import commands

#now = datetime.datetime.now().strftime("%d.%b %Y %H:%M:%S")
load_dotenv()

intents = discord.Intents.default()
intents.members = True
intents.guilds = True

client = discord.Client(intents=intents)

bot = commands.Bot(command_prefix='!', intents=intents)

async def message_recentlyplayed():
    channel = bot.get_channel(970336728466477086)
    await channel.send("""TEST 1""")

@bot.event
async def on_ready(): 
    print("send_recentlyplayed.py ONLINE")

bot.run(os.getenv('TOKEN'))


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

from recently_played import read_scores

#now = datetime.datetime.now().strftime("%d.%b %Y %H:%M:%S")
load_dotenv()

conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
( os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS') ) )

intents = discord.Intents.default()
intents.members = True
intents.guilds = True

client = discord.Client(intents=intents)

bot = commands.Bot(command_prefix='!', intents=intents)

async def message_recentlyplayed():
    channel = bot.get_channel(970336728466477086)
    await channel.send("""```ID:%s\tIGN:%s\n
    Title:%s\tArtist:%s\n
    Cool:%s Good:%s
    Bad:%s  Miss:%s```""" % (read_scores().line[2],read_scores().line[3],read_scores().chart_name, read_scores().chart_artist,read_scores().line[7], read_scores().line[8], read_scores().line[9], read_scores().line[10]))

@bot.event
async def on_ready(): 
    print("send_recentlyplayed.py ONLINE")

bot.run(os.getenv('TOKEN'))


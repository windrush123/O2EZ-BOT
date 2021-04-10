import os
import discord
import pyodbc
import time
import datetime

from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()

conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
( os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS') ) )

now = datetime.datetime.now().strftime("%d.%b %Y %H:%M:%S")

client = discord.Client()
bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print('[%s] ----- BOT ONLINE -----' % (now))


@bot.command(name='createinv')
async def createinv(ctx):
    #creating invite link
    invitelink = await ctx.channel.create_invite(max_uses=1,unique=True)
    sender = ctx.message.author
    #removing the url
    discordlink = invitelink.url
    invlink = discordlink.replace("https://discord.gg/","")
    #storing in db
    cursor = conncreate
    cursor.execute("INSERT INTO dbo.discordinv (invlink) VALUES (?)", invlink)
    cursor.commit()
    sender = ctx.message.author
    print('[%s][%s] has created an invite link: %s' % (now,sender,invitelink.url))
    await ctx.send(invitelink)

bot.run(os.getenv('TOKEN'))

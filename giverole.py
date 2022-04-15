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

now = datetime.datetime.now().strftime("%d.%b %Y %H:%M:%S")
load_dotenv()

conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
( os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS') ) )

#logger = logging.getLogger('discord')
#logger.setLevel(logging.DEBUG)
#handler = logging.FileHandler(filename='giverole.log', encoding='utf-8', mode='w')
#handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
#logger.addHandler(handler)



intents = discord.Intents.default()
intents.members = True
intents.guilds = True

client = discord.Client(intents=intents)

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    invitelink = sys.argv[1]
    channel = bot.get_channel(int(os.getenv('privatechannelmsg')))
    cursor = conncreate
    a = cursor.execute("SELECT discorduid FROM dbo.discordinv WHERE invlink=?", invitelink)
    for row in a:
        discorduid = (row.discorduid)
    cursor.execute("UPDATE dbo.member SET discorduid=? WHERE invlink=?", discorduid, invitelink)
    cursor.commit()
    guild = bot.get_guild(int(os.getenv('guildid')))
    member = guild.get_member(discorduid)
    role = discord.utils.get(member.guild.roles, name="Member")
    await member.add_roles(role)
    b = cursor.execute("SELECT usernick FROM dbo.member WHERE discorduid=?",discorduid)
    for row in b:
        print("setting nickname %s to %s" % (member,row.usernick))
        await member.edit(nick=row.usernick)
    a = cursor.execute("SELECT id,userid,discorduid,invlink FROM dbo.member WHERE invlink=?", invitelink)
    for row in a:
        memberid = (row.id)
        username = (row.userid)
    #logger.info("USER REGISTERED: [%s] %s : %s[%s] = %s" % (memberid, username, member, discorduid, invitelink))
    print("USER REGISTERED: [%s] %s : %s[%s] = %s" % (memberid, username, member, discorduid, invitelink))
    print("Deleting Record Invite Link: [%s]" % (invitelink))
    cursor.execute("DELETE FROM dbo.discordinv WHERE invlink=?", invitelink)
    cursor.commit()
    print("Record Delete!")
    #logger.info("RECORD DELETED: invite Link = %s" % (invitelink))
    time.sleep(3)
    exit()

bot.run(os.getenv('TOKEN'))
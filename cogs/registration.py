import discord
import pyodbc
import datetime

from discord.ext import commands
import os

conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
( os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS') ) )

class Register(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("Event cogs online!")
    
 
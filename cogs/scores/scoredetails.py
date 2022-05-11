import os
import pyodbc
from dotenv import load_dotenv
from discord.ext import commands

class scoredetails(commands.cog):
    def __init__(self, bot):
        self.bot = bot

    
def setup(bot):
    bot.add_cog(scoredetails(bot))
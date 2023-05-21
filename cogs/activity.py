import os
import pyodbc

# Discord Bot
import discord
from discord.ext import commands, tasks

import utils.logsconfig as logsconfig
logger = logsconfig.logging.getLogger("bot")

conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
( os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS') ) )

class Activity(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
        self.activity.start()

    def cog_unload(self):
        logger.info("Cog Unloaded - activity")
        self.activity.cancel()
    
    def cog_load(self):
        logger.info("Cog Loaded - activity")

    @tasks.loop(minutes=1)  
    async def activity(self):
        await Activity.set_activity(self)

    @activity.before_loop
    async def before_record(self):
        await self.bot.wait_until_ready()

    @activity.after_loop
    async def on_record_cancel(self):
        if self.activity.is_being_cancelled():
            self.activity.stop()      

    @commands.Cog.listener()
    async def set_activity(self):
        with conncreate.cursor() as cursor:
            query = "SELECT USER_ID FROM dbo.T_o2jam_login"
            player = cursor.execute(query).fetchall()
            
        await self.bot.change_presence(activity=discord.Game(name=f"with {len(player)} Player(s)"))
               

async def setup(bot: commands.Bot):
    await bot.add_cog(Activity(bot))  
    
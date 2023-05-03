import os
from discord.ext.commands.help import HelpCommand
import pyodbc

import utils.logsconfig as logsconfig
import discord
import subprocess
import traceback

from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

logger = logsconfig.logging.getLogger("bot")

conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
( os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS') ) )

intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

cogs = [
            "admin",
            #"recentlyplayed",
            "usercmds",
            "registration",
        ]

@bot.event
async def on_ready():
    logger.info(f"User: {bot.user} (ID:{bot.user.id})")
    

    #await utils.load_videocmds(bot)
    for extension in cogs:
        try:
            await bot.load_extension("cogs." + extension)
        except Exception:
            logger.error(f"Failed to load extension {extension}.")
            logger.error(traceback.print_exc())
    
    try:
        guildid = discord.Object(id=825723912729002004)
        bot.tree.copy_global_to(guild=guildid)
        synced = await bot.tree.sync(guild=guildid)
        print(f"synced {len(synced)} commands")
        
    except Exception as e:
        print(e)
    

bot.run(os.getenv('TOKEN'), root_logger=True)
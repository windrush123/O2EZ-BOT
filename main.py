import os
import pyodbc
import logsconfig
import discord

from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

logger = logsconfig.logging.getLogger("bot")

conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
( os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS') ) )

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logger.info(f"User: {bot.user} (ID:{bot.user.id})")

    await bot.load_extension("cogs.usercmds")
    await bot.load_extension("cogs.admin")
    print('bot online')

bot.run(os.getenv('TOKEN'), root_logger=True)

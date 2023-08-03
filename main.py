import os
import traceback
import discord

from discord.ext import commands
from dotenv import load_dotenv

from utils import logsconfig
load_dotenv()

logger = logsconfig.logging.getLogger("bot")

intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
guild_id = int(os.getenv('guildid'))

cogs = [
            "admin",
            "recentlyplayed",
            "usercmds",
            "registration",
            "invites",
            "activity"
        ]

@bot.event
async def on_ready():
    logger.info("User: %s ID: %d", bot.user, bot.user.id)

    #await utils.load_videocmds(bot)
    for extension in cogs:
        try:
            await bot.load_extension("cogs." + extension)
        except Exception:
            logger.error("Failed to load extension %s", extension)
            logger.error(traceback.print_exc())
    try:
        guildid = discord.Object(id=guild_id)
        bot.tree.copy_global_to(guild=guildid)
        synced = await bot.tree.sync(guild=guildid)
        logger.info("Synced a Total of %d Commands", len(synced))
    except Exception as e:
        logger.info(f"Error loading Slash Commands \n{e}")

bot.run(os.getenv('TOKEN'), root_logger=True)

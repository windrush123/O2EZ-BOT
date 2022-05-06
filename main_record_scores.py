import os
import pyodbc
import time
import glob
import re
import asyncio

from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta

from discord.ext import commands
import record_recently_played
#import send_recentlyplayed

bot = commands.Bot(command_prefix='!')
#bot.load_extension('userscore')


load_dotenv()

print("main ONLINE")
starttime = time.time()
def main():
    while True:
        refresh_timer = int(os.getenv('timer_scorereading'))
        record_recently_played.read_scores()
        time.sleep(refresh_timer - time.time() % refresh_timer)
        


main()



    
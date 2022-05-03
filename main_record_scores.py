import os
import pyodbc
import time
import glob
import re
import asyncio

from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta

import recently_played
#import send_recentlyplayed

#load_dotenv()

print("main ONLINE")
starttime = time.time()
def main():
    while True:
        recently_played.Record_Scores.read_scores()
        
        asyncio.run(recently_played.Record_Scores.discord_send_score())
        time.sleep(30 - time.time() % 30)

main()

    
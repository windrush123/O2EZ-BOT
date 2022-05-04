import os
import pyodbc
import time
import glob
import re
import asyncio

from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta

import record_recently_played
#import send_recentlyplayed

#load_dotenv()

print("main ONLINE")
starttime = time.time()
def main():
    while True:
        record_recently_played.read_scores()  
        time.sleep(60 - time.time() % 60)

main()

    
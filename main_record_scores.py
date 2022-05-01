import os
import pyodbc
import time
import glob
import re
import asyncio

from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta

from recently_played import read_scores
from send_recentlyplayed import message_recentlyplayed

#load_dotenv()

print("main ONLINE")
starttime = time.time()
def main():
    while True:
        read_scores()
        asyncio.run(message_recentlyplayed())
        time.sleep(30 - time.time() % 30)

main()

    
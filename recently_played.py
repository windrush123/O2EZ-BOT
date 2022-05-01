import os
import pyodbc
import time
import glob
import re
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
main_path = os.getenv('playerscoresfilepath')

conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
( os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS') ) )

print("recently_played Online")

def read_scores():
    print("Reading new scores....")
    scores_files_dir = glob.glob(os.path.join(main_path, '**'))
    latest_folder = scores_files_dir[-2:]
    x = len(latest_folder)
    print('Total Folder Count: '+ str(x))
    if x > 0: 
        channel_played = 0
        for x in range(0, x, 1): # check each folder
            today_score_files_dir = glob.glob(os.path.join(latest_folder[x],'*.txt')) #read exisiting txt files           
            i = len(today_score_files_dir)
            for i in range(0, i, 1): # check each files
                GetBaseName = os.path.basename(today_score_files_dir[i])
                verifying_filename = os.path.splitext(GetBaseName)[0]
                print("Found File: (%s)" % (today_score_files_dir[i]))
                read_scores=open(today_score_files_dir[i], 'r')
                score_lines = read_scores.readlines()
                line_count = 0
                for line in reversed(score_lines):
                    line_count += 1
                    # Convert txt into arrays
                    re.split(r't\+', line)
                    line = line.split("\t") 
                    print("%s" % (line))
                    time_played = datetime.strptime(line[1], '%Y-%m-%d %H:%M:%S')

                    # if scores within the timeframe
                    if abs(datetime.now() - time_played) < timedelta(seconds=30): 
                        print("Within 30 secs")
                        #Check what channel user played
                        if "15030" in verifying_filename: channel_played = 1                      
                        elif "15031" in verifying_filename: channel_played = 2
                        else: print("ERROR: CANNOT FIND CHANNEL PORT")                           
                        cursor = conncreate
                        songlist = cursor.execute("SELECT chart_id,chart_name,chart_artist FROM dbo.songlist WHERE ojn_id=? ", line[4])       
                        for row in songlist:
                            chart_id = (row.chart_id)
                            chart_name = (row.chart_name)
                            chart_artist = (row.chart_artist)
                        find_chart_level = cursor.execute("SELECT easy_level,normal_level,hard_level FROM dbo.songlist where ojn_id=?", line[4])
                        for row in find_chart_level:
                                if line[5] == 0: chart_level = (row.easy_level)
                                elif line[5] == 1: chart_level = (row.normal_level)
                                else: chart_level = (row.hard_level)
                        cursor.execute("""INSERT INTO dbo.userscores (usernick, id, chart_id,
                            channel, chart_name, chart_artist, chart_difficulty, chart_level,
                            cool, good, bad, miss, maxcombo, maxjam, total_score, date_played,
                            date_verified)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            line[3], #usernicK
                            line[2], #id
                            chart_id, 
                            channel_played,
                            chart_name,
                            chart_artist,
                            line[5], #chart diff
                            chart_level, # chart lvl
                            line[7], #cool
                            line[8], #good
                            line[9], #bad
                            line[10], #miss
                            line[11], #maxcombo
                            line[12], #maxjam
                            line[13], #totalscore
                            line[1], #dateplayed
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")) #date verified
                        cursor.commit()
                    else:
                       break
                i = i + 1
            x = x + 1           
    else: 
        return False
        print("No new scores...") 
    



#print(read_scores.read())

#def read_recently_played_text_file():

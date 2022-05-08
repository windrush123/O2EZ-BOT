import os
import pyodbc
import time
import glob
import re
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta


# Discord Bot
import discord
from discord.ext import commands
from discord.ext import tasks

load_dotenv()
main_path = os.getenv('playerscoresfilepath')

conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
( os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS') ) )

print("recently_played Online")

verified_score_format = []


class record_recently_played(commands.Cog):

    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.read_scores.start()

    @tasks.loop(seconds=5)    
    async def read_scores(self):
        scores_files_dir = glob.glob(os.path.join(main_path, '**'))
        latest_folder = scores_files_dir[-2:]
        x = len(latest_folder)
        #print('Total Folder Count: '+ str(x))
        if x > 0: 
            channel_played = 0
            for x in range(0, x, 1): # check each folder
                today_score_files_dir = glob.glob(os.path.join(latest_folder[x],'*.txt')) #read exisiting txt files           
                i = len(today_score_files_dir)
                for i in range(0, i, 1): # check each files
                    GetBaseName = os.path.basename(today_score_files_dir[i])
                    verifying_filename = os.path.splitext(GetBaseName)[0]
                    read_scores=open(today_score_files_dir[i], 'r')
                    score_lines = read_scores.readlines()
                    line_count = 0
                    for line in reversed(score_lines):
                        line_count += 1                        
                        # Convert txtlines into arrays
                        re.split(r't\+', line)
                        line = line.split("\t") 
                        time_played = datetime.strptime(line[1], '%Y-%m-%d %H:%M:%S')

                        # This is where Verification begins
                        # if scores within the timeframe
                        refresh_timer = int(os.getenv('timer_scorereading'))
                        if abs(datetime.now() - time_played) < timedelta(seconds=refresh_timer):
                            verified_score_format.clear() 
                            date_verified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            verified_score_format.append(line[3]) # usernick
                            verified_score_format.append(line[2]) # userid
                            #Check what channel user played
                            if "15030" in verifying_filename: channel_played = 1                      
                            elif "15031" in verifying_filename: channel_played = 2
                            else:
                                channel_played = 404 
                                print("ERROR: CANNOT FIND CHANNEL PORT") 
                            verified_score_format.append(channel_played) # channel                          
                            cursor = conncreate
                            songlist = cursor.execute("SELECT chart_id,chart_name,chart_artist FROM dbo.songlist WHERE ojn_id=? ", line[4])       
                            for row in songlist:
                                verified_score_format.append(row.chart_id) # chart_id
                                verified_score_format.append(row.chart_name) # chart_name
                                verified_score_format.append(row.chart_artist) # chart_artist
                            verified_score_format.append(line[5]) # chart_diff

                            # Find Chart Level
                            find_chart_level = cursor.execute("SELECT easy_level,normal_level,hard_level FROM dbo.songlist where ojn_id=?", line[4])
                            chart_level = 0
                            for row in find_chart_level:
                                # Chart_level
                                if line[5] == 0:  chart_level = (row.easy_level)
                                elif line[5] == 1: chart_level = (row.normal_level)   
                                else: chart_level = (row.hard_level)
                            verified_score_format.append(chart_level) # chart Level                                       
                            verified_score_format.append(line[7]) # cool
                            verified_score_format.append(line[8]) # good
                            verified_score_format.append(line[9]) # bad
                            verified_score_format.append(line[10]) # miss
                            verified_score_format.append(line[11]) # maxcombo
                            verified_score_format.append(line[12]) # maxjam
                            verified_score_format.append(line[13]) # total_score

                            verified_score_format.append(line[1]) # date_played
                            verified_score_format.append(date_verified) # date_verified

                            cursor.execute("""INSERT INTO dbo.userscores (usernick, id, channel,
                                chart_id, chart_name, chart_artist, chart_difficulty, chart_level,
                                cool, good, bad, miss, maxcombo, maxjam, total_score, date_played,
                                date_verified)
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                                """,
                                verified_score_format)
                            cursor.commit()
                            # Get Score_ID by fetching which score is added
                            # inefficienct, will update
                            f = cursor.execute("""SELECT @@IDENTITY""")
                            for row in f:
                                verified_score_format.insert(0, row[0])     


                            # Send to discord server


                            userscore = self.bot.get_cog('userscore')
                            if userscore is not None:
                                await userscore.send_score(verified_score_format[0])    



                            # High score Checking
                            if IsNewScore(verified_score_format[3], verified_score_format[2],  verified_score_format[7]) == False:
                                if IsHighScore(verified_score_format[3],  verified_score_format[2], verified_score_format[7],  verified_score_format[15]) == True:
                                    cursor.execute("""UPDATE dbo.user_highscores SET 
                                    score_id=?, cool=?, good=?,bad=?, miss=?, maxcombo=?,
                                    maxjam=?, total_score=?, date_played=?
                                    WHERE 
                                    id=? AND chart_id=? AND chart_difficulty=?""",
                                    verified_score_format[0],  # score_id=
                                    verified_score_format[9],  # cool
                                    verified_score_format[10], # good
                                    verified_score_format[11], # bad
                                    verified_score_format[12], # miss
                                    verified_score_format[13], # maxcombo
                                    verified_score_format[14], # maxjam
                                    verified_score_format[15], # total_score
                                    verified_score_format[16], # date_played
                                    
                                    verified_score_format[2],  # id
                                    verified_score_format[3],  # chart_id
                                    verified_score_format[7])  # chart_diff
                                    cursor.commit()
                                    print('[HIGH SCORE][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Total Score: %s]' 
                                    % (verified_score_format[1] , verified_score_format[7], verified_score_format[5],  verified_score_format[6], 
                                    verified_score_format[9], verified_score_format[10], verified_score_format[11], verified_score_format[12], 
                                    verified_score_format[13], verified_score_format[15]))
                                else: 
                                    print('[Verified][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Total Score: %s]' 
                                    % (verified_score_format[1] , verified_score_format[7], verified_score_format[5],  verified_score_format[6], 
                                    verified_score_format[9], verified_score_format[10], verified_score_format[11], verified_score_format[12], 
                                    verified_score_format[13], verified_score_format[15]))
                                    
                            else:
                                cursor.execute("""INSERT INTO dbo.user_highscores VALUES
                                (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                                verified_score_format[3], # chart_id
                                verified_score_format[7], # chart_diff
                                verified_score_format[0], # score_id
                                verified_score_format[2], # id
                                verified_score_format[1], # usernick
                                verified_score_format[9], # cool
                                verified_score_format[10], # good
                                verified_score_format[11], # bad
                                verified_score_format[12], # miss
                                verified_score_format[13], # max combo
                                verified_score_format[14], # max jam
                                verified_score_format[15], # total score
                                verified_score_format[16])  # date_played
                                cursor.commit()
                                print('[New Record][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Total Score: %s]' 
                                % (verified_score_format[1] , verified_score_format[7], verified_score_format[5],  verified_score_format[6], 
                                verified_score_format[9], verified_score_format[10], verified_score_format[11], verified_score_format[12], 
                                verified_score_format[13], verified_score_format[15]))
                        else:
                            break
                    i = i + 1
                    read_scores.close()
                x = x + 1   

    @read_scores.before_loop
    async def before_send_score(self):
        print('recently played waiting...')
        await self.bot.wait_until_ready()
        


def IsNewScore(chartid, userid, chart_diff,):
    cursor = conncreate
    count_score = 0
    find_score = cursor.execute("""SELECT * FROM dbo.user_highscores WHERE 
    chart_id=? AND id=? AND chart_difficulty=?""" , chartid, userid, chart_diff)
    for row in find_score:
        count_score += 1
    if count_score == 0: return True
    else: return False

def IsHighScore(chartid, userid, chart_diff, total_score):
    cursor = conncreate
    find_highscore = cursor.execute("""SELECT * FROM dbo.user_highscores WHERE 
    chart_id=? AND id=? AND chart_difficulty=?""" , chartid, userid, chart_diff)
    totalscore_highscore = 0
    for row in find_highscore:
        totalscore_highscore = (row.total_score)
    if int(total_score) > totalscore_highscore:
        return True
    else: return False


def setup(bot):
    bot.add_cog(record_recently_played(bot))
            




import os
from mysqlx import ProgrammingError
import pyodbc
import glob
import re
import asyncio
import time
import math
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

raw_score_line = []

class record_score(commands.Cog):
 
    def __init__(self, bot): 
        self.bot = bot
        self.record.start()

    def cog_unload(self):
        self.record.cancel()

    refresh_timer = int(os.getenv('timer_scorereading'))
    @tasks.loop(minutes=refresh_timer)  
    async def record(self):
        # print("reading new scores...")
        record_score.read_scores(self)

    @record.before_loop
    async def before_record(self):
        print('[Score Recording] Timer Started')
        await self.bot.wait_until_ready()

    @record.after_loop
    async def on_record_cancel(self):
        if self.record.is_being_cancelled():
            print('[Score Recording] Finishing loop before closing...')
            self.record.stop()      
            print('[Score Recording] Closed !')
   

    def read_scores(self):
        raw_score_line.clear()
        scores_files_dir = glob.glob(os.path.join(main_path, '**'))
        latest_folder = scores_files_dir[-2:]
        x = len(latest_folder)
        if x > 0: 
            for x in range(0, x, 1): # check each folder
                today_score_files_dir = glob.glob(os.path.join(latest_folder[x],'*.txt')) #read exisiting txt files           
                i = len(today_score_files_dir)
                for i in range(0, i, 1): # check each files
                    GetBaseName = os.path.basename(today_score_files_dir[i])
                    verifying_filename = os.path.splitext(GetBaseName)[0]    
                    try:
                        with open(today_score_files_dir[i], 'r') as file_read_scores:
                            score_lines = file_read_scores.readlines()
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
                                readed_score_line = line
                                if abs(datetime.now() - time_played) <= timedelta(minutes=refresh_timer):
                                    record_score.score_to_db(self, verifying_filename, readed_score_line)
                            i = i + 1
                    except IOError:
                        print("Error while Reading the file...")
                x = x + 1 
                    
    def score_to_db(self, filename, score_line):
        verified_score_format = [] 
        verified_score_format.clear()       
        date_verified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        verified_score_format.append(score_line[3]) # usernick
        verified_score_format.append(score_line[2]) # userid
        #Check what channel user played
        if "15030" in filename: channel_played = 1                      
        elif "15031" in filename: channel_played = 2
        else:
            channel_played = 404 
            print("ERROR: CANNOT FIND CHANNEL PORT") 
        verified_score_format.append(channel_played) # channel
        chartid = 0                           
        cursor = conncreate
        songlist = cursor.execute("SELECT chart_id,chart_name,chart_artist FROM dbo.songlist WHERE ojn_id=? ", score_line[4])       
        for row in songlist:
            chartid = (row.chart_id)
            verified_score_format.append(row.chart_id) # chart_id
            verified_score_format.append(row.chart_name) # chart_name
            verified_score_format.append(row.chart_artist) # chart_artist
        verified_score_format.append(score_line[5]) # chart_diff

        # Find Chart Level
        find_chart_level = cursor.execute("SELECT * FROM dbo.songlist where ojn_id=?", score_line[4])
        chart_level = 0
        chart_notecount = 0
        for row in find_chart_level:
            # Chart_level
            if score_line[5] == 0:  
                chart_level = (row.easy_level)
                chart_notecount = (row.easy_notecount)
            elif score_line[5] == 1: 
                chart_level = (row.normal_level)
                chart_notecount = (row.normal_notecount)   
            else: 
                chart_level = (row.hard_level)
                chart_notecount = (row.hard_notecount)
        
        verified_score_format.append(int(chart_level)) # chart Level                                       
        verified_score_format.append(int(score_line[7])) # cool
        verified_score_format.append(int(score_line[8])) # good
        verified_score_format.append(int(score_line[9])) # bad
        verified_score_format.append(int(score_line[10])) # miss
        verified_score_format.append(int(score_line[11])) # maxcombo
        verified_score_format.append(int(score_line[12])) # maxjam
        verified_score_format.append(int(score_line[13])) # total_score
            
        score_v2 = record_score.scorev2(self, int(score_line[7]),int(score_line[8]),int(score_line[9]),int(score_line[10]), chart_notecount)
        verified_score_format.append(int(score_v2)) # score v2

        accuracy = record_score.hitcount_to_accuracy(self, int(score_line[7]),int(score_line[8]),int(score_line[9]),int(score_line[10]))
        verified_score_format.append(float(accuracy)) # Accuracy

        hitcount = int(score_line[7]) + int(score_line[8]) + int(score_line[9]) + int(score_line[10])
        IsClear = record_score.IsPassed(self, chartid, score_line[5], hitcount)
        verified_score_format.append(IsClear) # Song clear

        verified_score_format.append(score_line[1]) # date_played
        verified_score_format.append(date_verified) # date_verified
        try:
            cursor.execute("""INSERT INTO dbo.userscores (usernick, id, channel,
                chart_id, chart_name, chart_artist, chart_difficulty, chart_level,
                cool, good, bad, miss, maxcombo, maxjam, total_score,score_v2,accuracy,
                song_clear,date_played,date_verified)
                
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                verified_score_format)
            cursor.commit()

            # Get Score_ID by fetching the latest inserted score
            # inefficienct, will update
            f = cursor.execute("""SELECT @@IDENTITY""")
            for row in f:
                verified_score_format.insert(0, row[0])
            record_score.highscore_to_db(self, verified_score_format)

            # Checking if there is a Async event already running. 
            # https://stackoverflow.com/a/70066649
            

            if ((hitcount / chart_notecount)*100) >= 10.0:
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:  # 'RuntimeError: There is no current event loop...'
                    loop = None

                if loop and loop.is_running():
                    
                    # print('Async event loop already running. Adding coroutine to the event loop.')
                    tsk = loop.create_task(record_score.send_score(self, verified_score_format[0]))
                    # ^-- https://docs.python.org/3/library/asyncio-task.html#task-object
                    # Optionally, a callback function can be executed when the coroutine completes
                    # tsk.add_done_callback(
                    #    lambda t: print(f'Task done with result = {t.result()}'))
                else:
                    print('Starting new event loop')
                    asyncio.run(record_score.send_score(self, verified_score_format[0])) 
        except ProgrammingError:
            print("[ERROR] There's a problem inserting the score to database. [invalid parameters]")
            print(verified_score_format)                                       
            
    def highscore_to_db(self, score):
        cursor = conncreate
        find_score = cursor.execute("""SELECT * FROM dbo.user_highscores WHERE 
        chart_id=? AND id=? AND chart_difficulty=?""" , score[4], score[2], score[7])
        count_score = 0
        for row in find_score:
            count_score += 1
            old_highscore = (row.score_v2)
        if count_score == 0:
            cursor.execute("""INSERT INTO dbo.user_highscores VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            score[4], # chart_id
            score[7], # chart_diff
            score[0], # score_id
            score[2], # id
            score[1], # usernick
            score[9], # cool
            score[10], # good
            score[11], # bad
            score[12], # miss
            score[13], # max combo
            score[14], # max jam
            score[15], # total score
            score[16], #  score v2
            score[17], #  accuracy
            score[18], # song clear
            score[19])  # date_played
            cursor.commit()
            print('[New Record][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Score: %s]' 
            % (score[1] ,score[7],score[5], score[6], 
            score[9],score[10],score[11],score[12], 
            score[13],score[16]))
        else:
            if int(score[17]) > old_highscore:
                cursor.execute("""UPDATE dbo.user_highscores SET 
                score_id=?, cool=?, good=?, bad=?, miss=?, maxcombo=?,
                maxjam=?, total_score=?, score_v2=?,
                accuracy=?, song_clear=?, date_played=?
                WHERE 
                id=? AND chart_id=? AND chart_difficulty=?""",    
                score[0],  # score_id
                score[9],  # cool
                score[10], # good
                score[11], # bad
                score[12], # miss
                score[13], # maxcombo
                score[14], # maxjam
                score[15], # total_score
                score[16], # score v2
                score[17], # accuracy
                score[18], # song clear
                score[19], # date_played

                score[2],  # id
                score[4],  # chart_id
                score[7])  # chart_diff

                cursor.commit()
                print('[HIGH SCORE][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Score: %s]' 
                % (score[1] ,score[7],score[5], score[6], 
                score[9],score[10],score[11],score[12], 
                score[13],score[16]))
            else:
                print('[Verified][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Total Score: %s]' 
                % (score[1] ,score[7],score[5], score[6], 
                score[9],score[10],score[11],score[12], 
                score[13],score[16]))  

    def scorev2(self, cool, good, bad, miss, notecount):
            # Formula by Schoolgirl
        # return 1000000*((cool+(0.30*good))-(bad/notecount)*(cool+good+bad+miss))/notecount
        # return (150*cool + 75*good + 10*bad)/(150*(cool + good + bad + miss))
        return 1000000*(cool+0.1*good-bad-3*miss)/notecount

    def notecount_to_accuracy(self, cool, good, bad, miss, notecount):
            # Formula by Schoolgirl
        # hitcount = int(cool) + int(good) + int(bad) + int(miss)
        return (cool + (0.50*good) + (0.15*bad))/notecount * 100

    def hitcount_to_accuracy(self, cool, good, bad, miss):
        hitcount = int(cool) + int(good) + int(bad) + int(miss)
        # return (cool + (0.50*good) + (0.15*bad))/hitcount * 100
        return (100*cool + 75*good - 75*bad - 100*miss)/(100*hitcount)*100


    def IsPassed(self, chart_id, difficulty, hitcount):
        notecount = 0
        cursor = conncreate
        x = cursor.execute("SELECT * FROM dbo.songlist WHERE chart_id=?", chart_id)       
        if difficulty == 0: # Easy Diff
            for row in x:
                notecount = (row.easy_notecount)
        elif difficulty == 1: # Normal Diff
            for row in x:
                notecount = (row.normal_notecount)
        else:
            for row in x:   # hard diff
                notecount = (row.hard_notecount)
            
        if notecount <= int(hitcount): 
            return True          
        else: 
            return False

    # Discord Embed
    async def send_score(self, scoreid):
        await asyncio.sleep(10)
        songbg_path = os.getenv('songbgfilepath')

        channel = self.bot.get_channel(int(os.getenv('recentlyplayedmsg')))

        scores = []
        diff_name = ''
        diff_color = 0
        cursor = conncreate
        
        #find_verfiedscores = cursor.execute("SELECT * FROM dbo.userscores WHERE date_verified BETWEEN DATEADD(day, -5, current_timestamp) AND current_timestamp")
        #for row in find_verfiedscores:
        #    print(row)
        
        #find_score = cursor.execute("SELECT * FROM dbo.userscores WHERE score_id=(SELECT max(score_id) FROM dbo.userscores)")
        find_score = cursor.execute("SELECT * FROM dbo.userscores WHERE score_id=?", scoreid)

        for row in find_score:
                scores = row
                usernick = row[1]
                chart_diff = row[7]
                chart_level = str(row[8])
                cool = str(row[9])
                good= str(row[10])
                bad=str(row[11])
                miss =str(row[12])
                maxcombo=str(row[13])
                totalscore = str(row[15])
                scorev2 = str(row[16])
                accuracy = str(round(row[17],2))
                passed = row[18]

        find_chartdetails = cursor.execute("SELECT * FROM dbo.songlist WHERE chart_id=?", scores[4])
        for row in find_chartdetails:    
            song = row
            chart_title = row[2]
            chart_artist = row[12]
            charter = row[11]
        if chart_diff == 0:
            diff_name = 'Easy Difficulty'
            diff_color = 0x00FF00 # Green
        elif chart_diff == 1:
            diff_name = 'Normal Difficulty'
            diff_color = 0xFFFF00 # Yellow
        else:
            diff_name = 'Hard Difficulty'
            diff_color = 0xFF0000 # Red

        bgfileformat = 'o2ma'+str(song[0])+'.jpg'
        current_bg_path = os.path.join(songbg_path, bgfileformat)
        if os.path.exists(current_bg_path) == False:
            current_bg_path = os.path.join(songbg_path, "_blank.jpg")

        #print(str(current_bg_path))
        
        if passed == False:
            embed=discord.Embed(title="[F][Lv. %s] %s" % (chart_level, chart_title) , 
            description="%s\nChart by: %s" % (chart_artist,charter), 
            color=diff_color) 
        else: 
            embed=discord.Embed(title="[Lv. %s] %s" % (chart_level, chart_title) , 
            description="%s\nChart by: %s" % (chart_artist,charter), 
            color=diff_color) 
        #embed.set_author(name="Recently Played by: %s" % (usernick))
        file = discord.File(current_bg_path, filename=bgfileformat)
        embed.set_thumbnail(url="attachment://" + bgfileformat)
        embed.add_field(name=diff_name, value="""
        **Cool:** %s
        **Bad:** %s"""% (cool, bad), inline=True)
        embed.add_field(name=u"\u200B", value="""
        **Good:** %s
        **Miss:** %s""" % (good, miss), inline=True)
        embed.add_field(name="Max Combo", value="%s" % (maxcombo), inline=False)
       # embed.add_field(name="Max Jam", value="500", inline=True)
        #embed.add_field(name="Total Score", value="%s" % (totalscore), inline=True)
        embed.add_field(name="Score", value="%s" % (scorev2), inline=True)
        embed.add_field(name="Accuracy", value=accuracy + "%", inline=True)
        embed.add_field(name=u"\u200B", value="Date Played: <t:%d:f>" % (time.time()), inline=False)
        #embed.set_footer(text=f"Date Played: <t:%d:f>" (time.time()))
        await channel.send("Recently Played by: %s" % (usernick),file=file, embed=embed)

def setup(bot):
    bot.add_cog(record_score(bot))

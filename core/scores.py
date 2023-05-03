import pyodbc
import os
import glob
import re

import asyncio
from mysqlx import ProgrammingError
from dotenv import load_dotenv
from datetime import datetime, timedelta
from pathlib import Path

import utils.logsconfig as logsconfig
import core.formula as formula
import core.sendscore as sendscores
import cogs.recentlyplayed as recentlyplayed

from discord.ext import tasks, commands

load_dotenv()
main_path = os.getenv('playerscoresfilepath')

conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
( os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS') ) )

raw_score_line = []

class Scores():
    def read_scores():    
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
                                    Scores.score_to_db(verifying_filename, readed_score_line)
                            i = i + 1
                    except IOError:
                        print("Error while Reading the file...")
                x = x + 1 
            else: print("[DEBUG] No Recent Scores")

    def score_to_db(filename, score_line):
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
        cursor = conncreate.cursor()
        songlist = cursor.execute("SELECT chart_id,chart_name,chart_artist FROM dbo.songlist WHERE ojn_id=? ", score_line[4])       
        for row in songlist:
            chartid = (row.chart_id)
            verified_score_format.append(row.chart_id) # chart_id
            verified_score_format.append(row.chart_name) # chart_name
            verified_score_format.append(row.chart_artist) # chart_artist
        verified_score_format.append(score_line[5]) # chart_diff

        # Find Chart Level
        try:
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
        except:
            print(f"cannot find ojn_id: {score_line[4]}")
        
        verified_score_format.append(int(chart_level)) # chart Level                                       
        verified_score_format.append(int(score_line[7])) # cool
        verified_score_format.append(int(score_line[8])) # good
        verified_score_format.append(int(score_line[9])) # bad
        verified_score_format.append(int(score_line[10])) # miss
        verified_score_format.append(int(score_line[11])) # maxcombo
        verified_score_format.append(int(score_line[12])) # maxjam
        verified_score_format.append(int(score_line[13])) # total_score
        try:    
            score_v2 = formula.Formula.scorev2(int(score_line[7]),int(score_line[8]),int(score_line[9]),int(score_line[10]), chart_notecount)
            verified_score_format.append(int(score_v2)) # score v2
        except ZeroDivisionError:
            print(f"[ERROR] Notecount not found! Invalid ojn_id: {chart_notecount}")
            return

        accuracy = formula.Formula.hitcount_to_accuracy(int(score_line[7]),int(score_line[8]),int(score_line[9]),int(score_line[10]))
        verified_score_format.append(float(accuracy)) # Accuracy

        hitcount = int(score_line[7]) + int(score_line[8]) + int(score_line[9]) + int(score_line[10])
        IsClear = Scores.IsPassed(chartid, score_line[5], hitcount)
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
            cursor.execute('SELECT @@IDENTITY AS id')
            row = cursor.fetchone()
            verified_score_format.insert(0, {row.id})
            
            print('[Verified][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Acc: %s] [Total Score: %s]' 
            % (verified_score_format[1] ,
                 verified_score_format[7],
                verified_score_format[5], 
                verified_score_format[6], 
                verified_score_format[9],
                verified_score_format[10],
                verified_score_format[11],
                verified_score_format[12], 
                verified_score_format[13], 
                round(verified_score_format[17],2) , 
                verified_score_format[16]))

            
        except ProgrammingError:
            print("[ERROR] There's a problem inserting the score to database. [invalid parameters]")
            print(verified_score_format)

        channelid = os.getenv('recentlyplayedmsg')
        #asyncio.run(sendscores.SendScore.send_score(self, channelid, verified_score_format[0]))

        # Recently Played
        
        # Get Score_ID by fetching the latest inserted score
        # inefficienct, will update
        

        Scores.highscore_to_db(verified_score_format)

        # Checking if there is a Async event already running. 
        # https://stackoverflow.com/a/70066649
        
        # Ignores short plays for recently played message
        # if ((hitcount / chart_notecount)*100) >= 0.1:
            #recentlyplayed.sendrecplayed(verified_score_format[0])

    def IsPassed(chart_id, difficulty, hitcount):
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
        else: return False

    def highscore_to_db(score):
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
            print('[New Record][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Acc: %s]  [Score: %s]' 
            % (score[1] ,score[7],score[5], score[6], 
            score[9],score[10],score[11],score[12], 
            score[13],round(score[17],2) ,score[16]))
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
                print('[HIGH SCORE][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Acc: %s] [Score: %s]' 
                % (score[1] ,score[7],score[5], score[6], 
                score[9],score[10],score[11],score[12], 
                score[13], round(score[17],2) , score[16]))
                return
            else:
                #print('[Verified][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Acc: %s] [Total Score: %s]' 
                #% (score[1] ,score[7],score[5], score[6], 
                #score[9],score[10],score[11],score[12], 
                #score[13], round(score[17],2) , score[16]))
                return 
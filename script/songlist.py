from encodings import utf_8
import os
import re
from mysqlx import IntegrityError
import pyodbc
import sys
import shutil


from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
( os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS') ) )

def songlist_main():
    main_path = os.path.dirname(os.path.abspath(__file__))
    txt_dir = os.path.join(main_path + '\songlist.txt')
    try:
        with open(txt_dir, 'r', encoding='UTF-8') as read_list:
            song_lines=read_list.readlines()
            cursor = conncreate
            #cursor.execute("DBCC CHECKIDENT ('dbo.songlist', reseed, 0)")
            #cursor.commit()
            line_count = 0 # To ignore the header of the text file (ID, OJN_ID, CHART_NAME, etc...) text.
            
            print("Deleting dbo.user_highscores data before proceeding...")
            cursor.execute("DELETE FROM dbo.user_highscores")
            print("Deleting dbo.songlist data before proceeding...")
            cursor.execute("DELETE FROM dbo.songlist")
            cursor.execute("DBCC CHECKIDENT ('dbo.songlist', reseed, 0)")
            cursor.commit()
            
            for line in song_lines:                               
                # Convert txt lines into array
                line = line.strip('\n')
                re.split(r't\+', line)
                line = line.split("\t")
                line = [x for x in line if x]
                try:
                    if len(line) == 12: 
                        chartid = insert_song(line)
                        # rename_songlist_bg(line[0], chartid)
                        line_count += 1
                    else: 
                        print("Counted %d Parameters, skipping..." % (len(line)))
                        print("Parameter Skipped: " + str(line))
                except:   
                    print("[ERROR] Please make sure the data is correct. [Line: %d]  " % (line_count))
                    cursor.execute("DELETE FROM dbo.songlist")
                    cursor.commit()
                    print("[SONGLIST] Deleting all data")
                    line_count = 0
                    raise TypeError("[ERROR] Please make sure the songlist data is correct. [Line: %d]" % (line_count))        
            else:
                print("Added %d Songs" % (line_count))          
    except IntegrityError:
        print("Error Deleting the songlist database. There's an existing data in dbo.userhighscore which conflicts in the songlistdb.")
    except:
        print("Error reading songlist.txt...")
    return 

def rename_songlist_bg(ojnid, chartid):       
    songbg_path = os.getenv('songbgfilepath')
    bgfileformat = 'o2ma'+str(ojnid)+'.jpg'
    old_name_path = os.path.join(songbg_path, bgfileformat)
    new_name_path = os.path.join(songbg_path, str(chartid) + '.jpg')
    if os.path.exists(old_name_path) == True:
        os.rename(old_name_path, new_name_path)

def update_songlist():
    main_path = os.path.dirname(os.path.abspath(__file__))
    txt_dir = os.path.join(main_path + r'\update_songlist.txt')
    try:
        with open(txt_dir, 'r', encoding='UTF-8') as read_list:
            song_lines=read_list.readlines()
            cursor = conncreate
            line_count = 0
            for line in song_lines:
                line_count += 1
                line = line.strip('\n')
                re.split(r't\+', line)
                line = line.split("\t")
                fetch = 0
                try:
                    a = cursor.execute("SELECT * FROM dbo.songlist WHERE ojn_id=? ", line[0])  
                    fetch = 0
                    songlines = []
                    for row in a:
                        fetch =+ 1
                        songlines = row
                except:
                    print("Something went wrong finding the ojn_id...")
                if fetch == 1: # Replacing OJN ID
                    cursor.execute("""UPDATE dbo.songlist SET 
                    ojn_id=NULL 
                    WHERE 
                    ojn_id=?""", line[0])
                    cursor.commit()
                    print("REMOVE FROM SONGLIST POOL: [CHART ID: %d][OJN ID: %s] %s - %s [%s]" % (songlines[0], str(line[0]),str(songlines[2]),str(songlines[11]),str(songlines[10])))
                    try: 
                        insert_song(line)
                        rename_songlist_bg(line[0],songlines[0])                
                    except: raise TypeError("[ERROR] Please make sure the songlist data is correct. [Line: %d]"% (line_count))                             
                elif fetch == 0: # Adding new Song to the pool with unused OJN ID
                    try: 
                        insert_song(line)
                        chart_id = 0
                        f = cursor.execute("SELECT * FROM dbo.songlist WHERE ojn_id=?", line[0])
                        for row in f:
                            chart_id = row[0]  
                        rename_songlist_bg(line[0], chart_id)                       
                    except: raise TypeError("[ERROR] Please make sure the songlist data is correct. [Line: %d]"% (line_count))  
    except Exception as e:
        print(e)

# Bring back the song from the current mappool
def restore_song(chartid, ojn):
    pass

def restore_highscore():      
    try:
        cursor = conncreate
        score_count = 0
        y = cursor.execute("SELECT COUNT(*) FROM dbo.userscores")
        for row in y:
            score_count = row[0]
        highscore_count = 0
        for i in range(1, score_count):
            x = cursor.execute("""SELECT * FROM (
            SELECT ROW_NUMBER() OVER (ORDER BY score_id) AS rownumber, * 
            FROM dbo.userscores
            )
            AS MyTable 
            WHERE rownumber=?""", i)
            score = []
            for rowb in x:
                score = [elem for elem in rowb]
                score.pop(0)
            try:
                find_score = cursor.execute("""SELECT * FROM dbo.user_highscores WHERE 
                chart_id=? AND id=? AND chart_difficulty=?""" , score[4], score[2], score[7])
                count_score = 0
                for row in find_score:
                    count_score += 1
                    old_highscore = row.score_v2
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
                    print('[Highscore Added][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Acc: %s]  [Score: %s]' 
                    % (score[1] ,score[7],score[5], score[6], 
                    score[9],score[10],score[11],score[12], 
                    score[13],round(score[17],2) ,score[16]))
                    highscore_count += 1
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
                        print('[Highscore Replaced][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Acc: %s] [Score: %s]' 
                        % (score[1] ,score[7],score[5], score[6], 
                        score[9],score[10],score[11],score[12], 
                        score[13], round(score[17],2) , score[16]))
                        highscore_count += 1
                i += 1
            except IndexError: print("Index Error")
        else: print("%d Total score count\n%d Total Highscores Processed" % (score_count, highscore_count))
    except Exception as E: print("Something is wrong when restoring users Highscores \n%s"% (E))



def update_song_metadata():
    main_path = os.path.dirname(os.path.abspath(__file__))
    txt_dir = os.path.join(main_path + r'\update_song_metadata.txt')
    try:
        with open(txt_dir, 'r', encoding='UTF-8') as read_list:
            song_lines=read_list.readlines()
            cursor = conncreate
            line_count = 0
            for line in song_lines:
                line_count += 1
                line = line.strip('\n')
                re.split(r't\+', line)
                line = line.split("\t")

                fetch = 0
                try:
                    a = cursor.execute("SELECT * FROM dbo.songlist WHERE chart_id=? ", line[0])  
                    fetch = 0
                    songlines = []
                    for row in a:
                        fetch =+ 1
                        songlines = row

                    if fetch == 1:
                        print("UPDATED FROM\n")
                        print("")
                        cursor.execute("""UPDATE dbo.songlist SET 
                            ojn_id=?,
                            chart_name=?,
                            easy_level=?,
                            easy_notecount=?,
                            normal_level=?,
                            normal_notecount=?,
                            hard_level=?,
                            hard_notecount=?,
                            bpm=?,
                            length=?,
                            charter=?,
                            chart_artist=?
                            WHERE 
                            chart_id=?""", line[1],line[2],line[3],
                            line[4],line[5],line[6],line[7],
                            line[8],line[9],line[10],line[11],
                            line[12], line[0])
                        cursor.commit()
                        print("Updating From")
                        print(songlines)
                        print("Into")
                        print(line)
                    if fetch == 0: print("Chart ID not Found")                      
                except: print("[ERROR] Please make sure the songlist data is correct. [Line: %d]")
    except: print("Error reading update_song_metadata.txt")
    
def insert_song(songlines):
    cursor = conncreate
    cursor.execute("""INSERT INTO dbo.songlist (
    ojn_id, 
    chart_name, 
    easy_level,
    easy_notecount, 
    normal_level, 
    normal_notecount,
    hard_level, 
    hard_notecount,
    bpm,
    length,
    charter,
    chart_artist) 
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""" , 
    songlines[0],songlines[1],songlines[2],
    songlines[3],songlines[4],songlines[5],songlines[6],
    songlines[7],songlines[8],songlines[9],songlines[10],
    songlines[11])            
    cursor.commit()
    f = cursor.execute("""SELECT @@IDENTITY""")
    chart_id = 0
    for row in f:
        chart_id = row[0]
    print('ADDED TO DATABASE: [CHART ID: %d][OJN ID: %s] %s - %s [%s]' % (chart_id, str(songlines[0]),str(songlines[1]),str(songlines[11]),str(songlines[10])))
    return chart_id


def delete_songlist():
    cursor = conncreate
    print("Deleting songlist Database")
    cursor.execute("DELETE FROM dbo.songlist")
    cursor.commit()

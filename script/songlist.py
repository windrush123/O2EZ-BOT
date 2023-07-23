from encodings import utf_8
import os
import re
from mysqlx import IntegrityError
import pyodbc

from pathlib import Path
from dotenv import load_dotenv

from core import HighScoreManager


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

def remove_song(chartid, ojn):
    pass

def restore_highscore():
    with conncreate.cursor() as cursor:
        count = 0
        query = "SELECT COUNT(*) FROM dbo.userscores"
        result = cursor.execute(query).fetchone()[0]

        for score_row in range(0, result):
            query = "SELECT * FROM dbo.userscores WHERE score_id=?"
            result = cursor.execute(query, (score_row,)).fetchone()
            if result is not None:
                scoreline = [row for row in result]
                highscore_to_db(scoreline)
                count += 1
        else:
            print(f"{count} Total highscore processed!")

def update_song_metadata():
    try:
        main_path = os.path.dirname(os.path.abspath(__file__))
        txt_dir = os.path.join(main_path + r'\update_song_metadata.txt')
        with open(txt_dir, 'r', encoding='UTF-8') as read_list:
            song_lines=read_list.readlines()
            line_count = 0
            try:
                for line in song_lines:
                    line_count += 1
                    line = line.strip('\n')
                    re.split(r't\+', line)
                    line = line.split("\t")
                    print(line)
                    #try:
                    with conncreate.cursor() as cursor:
                        query = "SELECT * FROM dbo.songlist WHERE ojn_id=? "
                        musicdata = list(cursor.execute(query, line[0]).fetchone())
                        musicdata.pop(0)
                        print(musicdata)

                        # Convert text Data types to match the data on the SQL 
                        line[0] = int(line[0])
                        for i in range(2, 7):
                            line[i] = int(line[i])
                        line[8] = float(line[8])

                        query = """UPDATE dbo.songlist SET
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
                        WHERE ojn_id=?
                        """
                        cursor.execute(query, (line[1],line[2],line[3],line[4],
                                            line[5],line[6],line[7],line[8],
                                            line[9],line[10],line[11],line[0]))
                        cursor.commit()
                        changes = []
                        for element in musicdata:
                            if element not in line:
                                changes.append(element)
                        print(f'CHANGED METADATA: [{line[0]}][{line[1]}][{line[10]}] Changes: {changes}')
                                     
            except Exception as e: 
                   print(f"[ERROR] Please make sure the songlist data is correct. [Line: {line_count}]\n{e}")
    except: print(f"Error reading update_song_metadata.txt")
    
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

def highscore_to_db(scorelist):
    new_score = 1
    # Fetch Old score
    with conncreate.cursor() as cursor:
        query = """SELECT score_v2, song_clear FROM dbo.user_highscores WHERE 
        chart_id=? AND id=? AND chart_difficulty=?"""
        cursor.execute(query ,(scorelist[4], scorelist[2], scorelist[7]))
        for row in cursor:
            old_score = int(row.score_v2)
            old_clear = (row.song_clear)
            new_score = 0

    # If New Score
    if new_score:
        with conncreate.cursor() as cursor:
            query = """INSERT INTO dbo.user_highscores VALUES
                (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
            cursor.execute(query,(
                scorelist[4], # chart_id
                scorelist[7], # chart_diff
                scorelist[0], # score_id
                scorelist[2], # id
                scorelist[1], # usernick
                scorelist[9], # cool
                scorelist[10], # good
                scorelist[11], # bad
                scorelist[12], # miss
                scorelist[13], # max combo
                scorelist[14], # max jam
                scorelist[15], # total score
                scorelist[16], #  score v2
                scorelist[17], #  accuracy
                scorelist[18], # song clear
                scorelist[19]))  # date_played
            cursor.commit()
            print('[New Record][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Acc: %s]  [Score: %s]' 
            % (scorelist[1] , scorelist[7],scorelist[5], scorelist[6], 
            scorelist[9], scorelist[10],scorelist[11],scorelist[12], 
            scorelist[13], round(scorelist[17],2) ,scorelist[16]))
            return True
        
    # If not a new score
    else:
        # If new score is not cleared
        if scorelist[18] == False: 
            # if old score is cleared
            if old_clear == True:
                print('[Verified][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Acc: %s]  [Score: %s]' 
                % (scorelist[1], scorelist[7],scorelist[5], scorelist[6], 
                scorelist[9], scorelist[10],scorelist[11],scorelist[12], 
                scorelist[13], round(scorelist[17],2) ,scorelist[16]))
                return False
            else:
                # if old score is higher than new score
                if scorelist[16] < int(old_score):
                    print('[Verified][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Acc: %s]  [Score: %s]' 
                    % (scorelist[1], scorelist[7],scorelist[5], scorelist[6], 
                    scorelist[9], scorelist[10],scorelist[11],scorelist[12], 
                    scorelist[13], round(scorelist[17],2) ,scorelist[16]))
                    return False
                else:
                    with conncreate.cursor() as cursor:
                        query = """UPDATE dbo.user_highscores SET 
                        score_id=?, cool=?, good=?, bad=?, miss=?, maxcombo=?,
                        maxjam=?, total_score=?, score_v2=?,
                        accuracy=?, song_clear=?, date_played=?
                        WHERE 
                        id=? AND chart_id=? AND chart_difficulty=?"""
                        cursor.execute(query, (  
                            scorelist[0],  # score_id
                            scorelist[9],  # cool
                            scorelist[10], # good
                            scorelist[11], # bad
                            scorelist[12], # miss
                            scorelist[13], # maxcombo
                            scorelist[14], # maxjam
                            scorelist[15], # total_score
                            scorelist[16], # score v2
                            scorelist[17], # accuracy
                            scorelist[18], # song clear
                            scorelist[19], # date_played

                            scorelist[2],  # id
                            scorelist[4],  # chart_id
                            scorelist[7])
                            )  # chart_diff
                        cursor.commit()
                        print('[NEW HIGHSCORE][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Acc: %s]  [Score: %s]' 
                        % (scorelist[1] , scorelist[7],scorelist[5], scorelist[6], 
                        scorelist[9], scorelist[10],scorelist[11],scorelist[12], 
                        scorelist[13], round(scorelist[17],2) ,scorelist[16]))
                        return True

        # If new score is cleared
        else:
            # if old score is cleared
            if old_clear == True:
                # Compare each scores
                if scorelist[16] < int(old_score):
                    print('[Verified][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Acc: %s]  [Score: %s]' 
                    % (scorelist[1], scorelist[7],scorelist[5], scorelist[6], 
                    scorelist[9], scorelist[10],scorelist[11],scorelist[12], 
                    scorelist[13], round(scorelist[17],2) ,scorelist[16]))
                    return False
                
            with conncreate.cursor() as cursor:
                query = """UPDATE dbo.user_highscores SET 
                score_id=?, cool=?, good=?, bad=?, miss=?, maxcombo=?,
                maxjam=?, total_score=?, score_v2=?,
                accuracy=?, song_clear=?, date_played=?
                WHERE 
                id=? AND chart_id=? AND chart_difficulty=?"""
                cursor.execute(query, (  
                    scorelist[0],  # score_id
                    scorelist[9],  # cool
                    scorelist[10], # good
                    scorelist[11], # bad
                    scorelist[12], # miss
                    scorelist[13], # maxcombo
                    scorelist[14], # maxjam
                    scorelist[15], # total_score
                    scorelist[16], # score v2
                    scorelist[17], # accuracy
                    scorelist[18], # song clear
                    scorelist[19], # date_played

                    scorelist[2],  # id
                    scorelist[4],  # chart_id
                    scorelist[7])
                    )  # chart_diff
                cursor.commit()
                print('[NEW HIGHSCORE][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Acc: %s]  [Score: %s]' 
                % (scorelist[1] , scorelist[7],scorelist[5], scorelist[6], 
                scorelist[9], scorelist[10],scorelist[11],scorelist[12], 
                scorelist[13], round(scorelist[17],2) ,scorelist[16]))
                return True
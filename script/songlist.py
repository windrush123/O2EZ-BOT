from encodings import utf_8
import os
import re
from mysqlx import IntegrityError
import pyodbc

from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
( os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS') ) )

def songlist_main():
    main_path = os.path.dirname(os.path.abspath(__file__))
    txt_dir = os.path.join(main_path + '\songlist.txt')
    try:
        with open(txt_dir, 'r', encoding='ANSI') as read_list:
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
                line_count += 1
                
                # Convert txt lines into array
                line = line.strip('\n')
                re.split(r't\+', line)
                line = line.split("\t")
                #print(line)
                try:
                   insert_song(line)
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

def update_songlist():
    main_path = os.path.dirname(os.path.abspath(__file__))
    txt_dir = os.path.join(main_path + r'\update_songlist.txt')
    try:
        with open(txt_dir, 'r', encoding='ANSI') as read_list:
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
                if fetch == 1: # Removing song from the current pool.
                    cursor.execute("""UPDATE dbo.songlist SET 
                    ojn_id=NULL 
                    WHERE 
                    ojn_id=?""", line[0])
                    cursor.commit()
                    print("REMOVE FROM SONGLIST POOL: [CHART ID: %d][OJN ID: %s] %s - %s [%s]" % (songlines[0], str(songlines[0]),str(songlines[2]),str(songlines[11]),str(songlines[10])))
                    try: insert_song(line)                       
                    except: raise TypeError("[ERROR] Please make sure the songlist data is correct. [Line: %d]"% (line_count))                             
                elif fetch == 0: # Adding new Song to the pool.
                    try: insert_song(line)                      
                    except: raise TypeError("[ERROR] Please make sure the songlist data is correct. [Line: %d]"% (line_count))  
    except:
        print("Error reading update_songlist.txt")

def update_song_metadata():
    main_path = os.path.dirname(os.path.abspath(__file__))
    txt_dir = os.path.join(main_path + r'\update_song_metadata.txt')
    try:
        with open(txt_dir, 'r', encoding='ANSI') as read_list:
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


def delete_songlist():
    cursor = conncreate
    print("Deleting songlist Database")
    cursor.execute("DELETE FROM dbo.songlist")
    cursor.commit()

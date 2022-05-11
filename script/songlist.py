import os
import re
from mysqlx import IntegrityError
import pyodbc

from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
( os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS') ) )

def main():
    main_path = os.path.dirname(os.path.abspath(__file__))
    txt_dir = os.path.join(main_path + '\songlist.txt')
    read_list=open(txt_dir, 'r', encoding='utf-8')
    song_lines=read_list.readlines()
    cursor = conncreate
    #cursor.execute("DBCC CHECKIDENT ('dbo.songlist', reseed, 0)")
    #cursor.commit()
    line_count = 0 # To ignore the header of the text file (ID, OJN_ID, CHART_NAME, etc...) text.
    
    for line in song_lines:
        line_count += 1
        
        # Convert txt lines into array
        line = line.strip('\n')
        re.split(r't\+', line)
        line = line.split("\t")
        #print(line)
        try:
            cursor.execute("""INSERT INTO dbo.songlist (
            chart_id,
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
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""" , 
            line[0],line[0],line[1],line[2],
            line[3],line[4],line[5],line[6],
            line[7],line[8],line[9],line[10],
            line[11])            
            cursor.commit()
        except:   
            print("[ERROR] Please make sure the data is correct. [Line: %d]  " % (line_count))
            cursor.execute("DELETE FROM dbo.songlist")
            cursor.commit()
            print("...Deleting all data")
            line_count = 0 
            break
        else:
            print('ADDED TO DATABASE: [%s] %s - %s [%s]' % (str(line[0]),str(line[1]),str(line[11]),str(line[10])))
    else:
        print("Added %d Songs" % (line_count))        

main()
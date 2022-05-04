import os
import re
import pyodbc

from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
( os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS') ) )

def main():
    main_path = os.path.dirname(os.path.abspath(__file__))
    txt_dir = os.path.join(main_path + '\songlist.txt')
    read_list=open(txt_dir, 'r')
    song_lines=read_list.readlines()[2:]
    line_count = 0 # To ignore the top bar of the text file (ID, OJN_ID, CHART_NAME, etc...) text.
    for line in song_lines:
        line_count += 1
        
        # Convert txt lines into array
        line = line.strip('\n')
        re.split(r't\+', line)
        line = line.split("\t")

        cursor = conncreate
        cursor.execute("""INSERT INTO dbo.songlist (ojn_id, chart_name, chart_artist,
        bpm, charter, easy_level, easy_notecount, normal_level, normal_notecount,
        hard_level, hard_notecount) 
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""" , 
        line[1],line[2],line[3],
        line[4],line[5],line[6],line[7],
        line[8],line[9],line[10],line[11])
        cursor.commit()
        print('ADDED TO DATABASE: [%s] %s - %s [%s]' % (str(line[1]),str(line[3]),str(line[2]),str(line[5])))        

main()
from fileinput import close
from tkinter import Y
from dotenv import load_dotenv
from script import songlist
import pyodbc
import os

load_dotenv()

conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
( os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS') ) )

success_count = 0

def main():
    global success_count
    print("Setting up the Database...")
    alter_member_tbl()
    create_discordinv_db()
    create_userscores_db()
    create_songlist_db()
    create_highscores_db()
    if success_count == 6: 
        print("[SUCCESS] Database Complete...")
        ans = input("Do you want to import the songlist to Database? [Y/N]\nInput: ")
        if any(ans.lower() == f for f in ["yes", 'y', '1']):
            songlist_to_db()
        elif any(ans.lower() == f for f in ["no", 'n', '0']):
            print("[WARNING] Remember to import the songlist before running the record_score module.")
            quit()  
    else: 
        print("[WARNING] Some Database/Table was not successfully created!!!")       
    
def songlist_to_db():
    try:
        songlist.songlist_main()
        print("[SUCCESS] FINISHED SETTING UP. YOU CAN NOW RUN THE DISCORD BOT.")
        quit()           
    except TypeError:
        retry = input("Do you want to retry adding songs? [Y/N]\nInput: ")
        if any(retry.lower() == f for f in ["yes", 'y', '1']):
            songlist_to_db()
        elif any(retry.lower() == f for f in ["no", 'n', '0']):
            print("[WARNING] Remember to import the songlist before running the record_score module.")
            quit() 

def alter_member_tbl():
    cursor = conncreate 
    global success_count
    try:
        cursor.execute("""
        ALTER TABLE dbo.member ADD 
        discorduid varchar(50);""")
        cursor.commit()
        print("[DATABASE] Altered dbo.member. Added discorduid column.")
        success_count = success_count + 1
    except pyodbc.ProgrammingError:
        print("[DATABASE] discorduid column already exists inside dbo.member. skipping...")
        success_count = success_count + 1
    except Exception as e:
        print("[FAILED] Error creating discorduid column inside dbo.member")
        print(e)
    
    try:
        cursor.execute("""
        ALTER TABLE dbo.member ADD 
        invlink varchar(50);""")
        cursor.commit()
        print("[DATABASE] Altered dbo.member. Added invlink column.")
        success_count = success_count + 1
    except pyodbc.ProgrammingError:
        print("[DATABASE] invlink column already exists inside dbo.member. skipping...")
        success_count = success_count + 1
    except Exception as e:
        print("[FAILED] Error creating invlink column inside dbo.member")
        print(e)

def create_discordinv_db():
    cursor = conncreate  
    global success_count
    try:
        cursor.execute("""
            CREATE TABLE dbo.discordinv (
            invlink varchar(50),
            discorduid bigint,
            used bit);""")
        cursor.commit()
        print("[DATABASE] Successfully created dbo.discordinv.")
        success_count = success_count + 1
    except pyodbc.ProgrammingError:
        print("[DATABASE] dbo.discordinv already exists. skipping...")
        success_count = success_count + 1
    except Exception as e:
        print("[FAILED] Error creating dbo.discordinv")
        print(e)

def create_userscores_db():
    cursor = conncreate
    global success_count     
    try:
        cursor.execute("""
            CREATE TABLE dbo.userscores (
            score_id bigint	NOT NULL IDENTITY(1,1) PRIMARY KEY,
            usernick varchar(32),
            id bigint,
            channel smallint,
            chart_id int,
            chart_name varchar(50),
            chart_artist varchar(50),
            chart_difficulty tinyint,
            chart_level smallint,
            cool int,
            good int,
            bad int,
            miss int ,
            maxcombo int,
            maxjam int,
            total_score	bigint,
            score_v2 int,
            accuracy float,
            song_clear bit,
            date_played datetime,
            date_verified datetime);
            """)
        cursor.commit()
        print("[DATABASE] Successfully created dbo.userscores.")
        success_count = success_count + 1
    except pyodbc.ProgrammingError:
        print("[DATABASE] dbo.userscores already exists. skipping...")
        success_count = success_count + 1
    except Exception as e:
        print("[FAILED] Error creating dbo.userscores")
        print(e)

def create_songlist_db():
    cursor = conncreate
    global success_count
    try:
        cursor.execute("""CREATE TABLE dbo.songlist (
            chart_id bigint	NOT NULL IDENTITY(1,1) PRIMARY KEY,
            ojn_id int,	
            chart_name varchar(100),	
            easy_level smallint,	
            easy_notecount int,	
            normal_level smallint,
            normal_notecount int,	
            hard_level smallint,
            hard_notecount int,
            bpm float,	
            length varchar(16),	
            charter varchar(100),	
            chart_artist varchar(100)	
        """)
        cursor.commit()
        print("[DATABASE] Successfully created dbo.songlist.")
        success_count = success_count + 1
    except pyodbc.ProgrammingError: 
        print("[DATABASE] dbo.songlist already exists. skipping...") 
        success_count = success_count + 1  
    except Exception as e:
        print("[FAILED] Error creating dbo.songlist")
        print(e)


def create_highscores_db():
    global success_count
    try:
        cursor = conncreate
        cursor.execute("""CREATE TABLE dbo.user_highscores (
            chart_id bigint	NOT NULL FOREIGN KEY REFERENCES dbo.songlist(chart_id), 
            chart_difficulty tinyint,	
            score_id bigint	NOT NULL FOREIGN KEY REFERENCES dbo.userscores(score_id),
            id bigint, 
            usernick varchar(50),	
            cool int,	
            good int,	
            bad int,	
            miss int,	
            maxcombo int,	
            maxjam int,	
            total_score bigint,	
            score_v2 int,	
            accuracy float,	
            song_clear bit,	
            date_played datetime
            )
        
        """)
        cursor.commit()
        print("[DATABASE] Successfully created dbo.user_highscores.")
        success_count = success_count + 1
    except pyodbc.ProgrammingError:
        print("[DATABASE] dbo.user_highscores already exists. skipping...")
        success_count = success_count + 1
    except Exception as e:
        print("[FAILED] Error creating dbo.user_highscores")
        print(e)
main()
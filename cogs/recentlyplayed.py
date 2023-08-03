import os
from mysqlx import ProgrammingError
import pyodbc
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Discord Bot
import discord
from discord.ext import commands, tasks

import utils.logsconfig as logsconfig
import core.HighScoreManager as HighScoreManager

logger = logsconfig.logging.getLogger("bot")

load_dotenv()
main_path = os.getenv('playerscoresfilepath')

conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
( os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS') ) )


class RecentlyPlayed(commands.Cog):
    def __init__(self, bot): 
        self.bot = bot
        self.record.start()

        # Timer for Record scores and Recently Played
        self.refresh_timer = int(os.getenv('timer_scorereading'))
        
        # Enable/Disable Discord embed for recently Played
        self.enable_SP_embed = True
        self.enable_MP_embed = True

        # Minimum Total hitcount in Percentage for qualified in discord Embed Recently Played.
        # This will avoid player who retries the song.
        self.minimum_score_progress = 10 
        
        # Enable/Disable difficulty for discord Embed
        self.enable_easy_embed = False
        self.enable_normal_embed = False
        self.enable_hard_embed = True

    def cog_unload(self):
        logger.info("Cog Unloaded - recentlyplayed")
        self.record.cancel()
    def cog_load(self):
        logger.info("Cog Loaded - recentlyplayed")

    refresh_timer = int(os.getenv('timer_scorereading'))
    @tasks.loop(minutes=refresh_timer)  
    async def record(self):
        # logger.info("reading new scores...")
        await RecentlyPlayed.read_scores(self)

    @record.before_loop
    async def before_record(self):
        logger.info('[Score Recording] Timer Started')
        await self.bot.wait_until_ready()

    @record.after_loop
    async def on_record_cancel(self):
        if self.record.is_being_cancelled():
            logger.info('[Score Recording] Finishing loop before closing...')
            self.record.stop() 
            logger.info('[Score Recording] Closed !')

    async def read_scores(self):
        scorelist = []
        scores_files_dir = [Path(main_path, folder) for folder in os.listdir(main_path)]
        latest_folder = scores_files_dir[-2:]
        if latest_folder:
            for folder in latest_folder:
                today_score_files_dir = folder.glob('*.txt')
                for file_path in today_score_files_dir:
                    verifying_filename = file_path.stem
                    with file_path.open('r') as file_read_scores:
                        score_lines = file_read_scores.readlines()
                        for line in reversed(score_lines):
                            line = line.split("\t")
                            time_played = datetime.strptime(line[1], '%Y-%m-%d %H:%M:%S')
                            refresh_timer = int(os.getenv('timer_scorereading'))
                            if abs(datetime.now() - time_played) <= timedelta(minutes=refresh_timer):
                                await RecentlyPlayed.score_to_db(self, verifying_filename, line)
                                scorelist.append(line)

        unique_items = []
        duplicate_items = {}

        for item in scorelist:
            if item[0] not in duplicate_items:
                duplicate_items[item[0]] = [item]
            else:
                duplicate_items[item[0]].append(item)

        for key, value in duplicate_items.items():
            if len(value) == 1:
                unique_items.append(value[0])
            else:
                if value[0][5] == 2:
                    await RecentlyPlayed.MP_Score(self, value)
        for item in unique_items:
            chart_data = RecentlyPlayed.get_chart_details(self, int(item[4]))
            if int(item[5]) == 2:
                hitcount = (int(item[7]) + int(item[8]) + int(item[9]) + int(item[10]))
                if ((hitcount / chart_data['hard_notecount'])*100 ) >= 15.0:
                    await RecentlyPlayed.SP_Score(self, item)           
                   
    async def score_to_db(self, channel, score_line):
        verified_score_format = [] 
        verified_score_format.clear()       
        date_verified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        verified_score_format.append(score_line[3]) # usernick
        verified_score_format.append(score_line[2]) # userid
        #Check what channel user played
        if "15030" in channel: channel_played = 1                      
        elif "15031" in channel: channel_played = 2
        else:
            channel_played = 404 
            logger.info("ERROR: CANNOT FIND CHANNEL PORT") 
        verified_score_format.append(channel_played) # channel
        chartid = 0                           
        with conncreate.cursor() as cursor:
            song_list_query = "SELECT chart_id, chart_name,chart_artist FROM dbo.songlist WHERE ojn_id=?"
            songlist = cursor.execute(song_list_query, (score_line[4],)).fetchone()       
            if songlist:
                chartid = songlist[0]  
                verified_score_format.append(songlist[0])  # chart_id
                verified_score_format.append(songlist[1])  # chart_name
                verified_score_format.append(songlist[2])
        verified_score_format.append(score_line[5]) # chart_diff

        # Find Chart Level
        with conncreate.cursor() as cursor:
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
        try:    
            score_v2 = RecentlyPlayed.scorev2(self, int(score_line[7]),int(score_line[8]),int(score_line[9]),int(score_line[10]), chart_notecount)
            verified_score_format.append(int(score_v2)) # score v2
        except ZeroDivisionError:
            logger.info(f"[ERROR] Notecount not found! Invalid ojn_id: {chart_notecount}")
            return   

        accuracy = RecentlyPlayed.hitcount_to_accuracy(self, int(score_line[7]),int(score_line[8]),int(score_line[9]),int(score_line[10]))
        verified_score_format.append(float(accuracy)) # Accuracy

        hitcount = int(score_line[7]) + int(score_line[8]) + int(score_line[9]) + int(score_line[10])
        IsClear = RecentlyPlayed.IsPassed(self, chartid, int(score_line[5]), hitcount)
        verified_score_format.append(IsClear) # Song clear

        verified_score_format.append(score_line[1]) # date_played
        verified_score_format.append(date_verified) # date_verified
        # logger.info(verified_score_format)
        try:
            with conncreate.cursor() as cursor:
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
                cursor.execute('SELECT @@IDENTITY AS id')
                row = cursor.fetchone()
                getid = int(row[0])          
                verified_score_format.insert(0, getid)
                RecentlyPlayed.highscore_to_db(self, verified_score_format)
                #await RecentlyPlayed.score(self, verified_score_format[0])
        except ProgrammingError:
            logger.info("[ERROR] There's a problem inserting the score to database. [invalid parameters]")
            logger.info(verified_score_format)                                        
            
    def highscore_to_db(self, scorelist):
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
                logger.info('[New Record][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Acc: %s]  [Score: %s]' 
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
                    logger.info('[Verified][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Acc: %s]  [Score: %s]' 
                    % (scorelist[1], scorelist[7],scorelist[5], scorelist[6], 
                    scorelist[9], scorelist[10],scorelist[11],scorelist[12], 
                    scorelist[13], round(scorelist[17],2) ,scorelist[16]))
                    return False
                else:
                    # if old score is higher than new score
                    if scorelist[16] < int(old_score):
                        logger.info('[Verified][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Acc: %s]  [Score: %s]' 
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
                            logger.info('[NEW HIGHSCORE][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Acc: %s]  [Score: %s]' 
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
                        logger.info('[Verified][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Acc: %s]  [Score: %s]' 
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
                    logger.info('[NEW HIGHSCORE][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Acc: %s]  [Score: %s]' 
                    % (scorelist[1] , scorelist[7],scorelist[5], scorelist[6], 
                    scorelist[9], scorelist[10],scorelist[11],scorelist[12], 
                    scorelist[13], round(scorelist[17],2) ,scorelist[16]))
                    return True
                
    def scorev2(self, cool, good, bad, miss, notecount):
            # Formula by Schoolgirl
        score = 1000000*(cool+0.1*good-bad-3*miss)/notecount
        if score > 0: return score
        else: return 0

    def notecount_to_accuracy(self, cool, good, bad, miss, notecount):
            # Formula by Schoolgirl
        # hitcount = int(cool) + int(good) + int(bad) + int(miss)
        return ((200*cool)+(150*good)+(50*bad))/(200*notecount)*100

    def hitcount_to_accuracy(self, cool, good, bad, miss):
        hitcount = int(cool) + int(good) + int(bad) + int(miss)
        return ((200*cool)+(150*good)+(50*bad))/(200*hitcount)*100

    def get_chart_details(self, chartid):
        """
            Returns a dictionary
        """
        chart_details = {}
        with conncreate.cursor() as cursor:
            sql = "SELECT * FROM dbo.songlist WHERE ojn_id=?"
            results = cursor.execute(sql, (chartid,)).fetchone()
            if results:
                chart_details['chart_id'] = results[0]
                chart_details['ojn_id'] = results[1]
                chart_details['chart_name'] = results[2]
                chart_details['easy_level'] = results[3]
                chart_details['easy_notecount'] = results[4]
                chart_details['normal_level'] = results[5]
                chart_details['normal_notecount'] = results[6]
                chart_details['hard_level'] = results[7]
                chart_details['hard_notecount'] = results[8]
                chart_details['bpm'] = results[9]
                chart_details['length'] = results[10]
                chart_details['charter'] = results[11]
                chart_details['chart_artist'] = results[12]
                return chart_details
            else:
                return {}

    def IsPassed(self, chart_id, difficulty, hitcount):
        notecount = 0
        with conncreate.cursor() as cursor:
            query = "SELECT easy_notecount, normal_notecount, hard_notecount FROM dbo.songlist WHERE chart_id=?"
            result = cursor.execute(query, (chart_id)).fetchone()
            difficulty_mapping = {
                0: result[0],
                1: result[1],
                2: result[2]
            }
            
        notecount = difficulty_mapping.get(difficulty) 
        if notecount <= int(hitcount): 
            return True          
        else: 
            return False

    # Discord Embed

    # Singleplayer Score Discord Embed
    async def SP_Score(self, scoreline):       
        songbg_path = os.getenv('songbgfilepath')
        channel = self.bot.get_channel(int(os.getenv('recentlyplayedmsg')))
        usernick = scoreline[3]
        cool = int(scoreline[7])
        good = int(scoreline[8])
        bad = int(scoreline[9])
        miss = int(scoreline[10])
        maxcombo = int(scoreline[11])
        chart_data = RecentlyPlayed.get_chart_details(self, scoreline[4])
        if not chart_data:
            logger.info(f"OJNID NOT FOUND [ID: {scoreline[4]}]")
            return
        if scoreline[5] == 0:
            diff_name = "Easy Difficulty"
            difficulty = 0
            chart_notecount = chart_data['easy_notecount']
            chart_level = chart_data["easy_level"]
            # diff_color = 0x00FF00 # Green
        elif scoreline[5] == 1:
            diff_name = "Normal Difficulty"
            difficulty = 1
            chart_notecount = chart_data['normal_notecount']
            chart_level = chart_data["normal_level"]
            # diff_color = 0xFFFF00 # Yellow
        else:
            diff_name = "Hard Difficulty"
            difficulty = 2
            chart_notecount = chart_data['hard_notecount']
            chart_level = chart_data["hard_level"]
            # diff_color = 0xFF0000 # Red
        
        scorev2 = round(RecentlyPlayed.scorev2(self, cool, good, bad, miss, chart_notecount))
        accuracy = round(RecentlyPlayed.hitcount_to_accuracy(self, cool, good, bad, miss),2)

        songbg_path = os.getenv('songbgfilepath')
        bgfileformat = str(chart_data['chart_id'])+'.jpg'
        current_bg_path = os.path.join(songbg_path, bgfileformat)
        if os.path.exists(current_bg_path) == False:
            current_bg_path = os.path.join(songbg_path, "_blank.jpg")
        file = discord.File(current_bg_path, filename=bgfileformat)

        hitcount = int(scoreline[7]) + int(scoreline[8]) + int(scoreline[9]) + int(scoreline[10])
        passed = RecentlyPlayed.IsPassed(self, chart_data['chart_id'], difficulty, hitcount) 

        with conncreate.cursor() as cursor:
            query = "SELECT discorduid FROM dbo.member WHERE usernick=?"
            result = cursor.execute(query, (usernick,)).fetchone()
            discorduid = int(result[0])

        member = self.bot.get_user(int(discorduid))

        # Discord Embed
        if passed == False:
            embed=discord.Embed(title="[Lv. %s] %s" % (chart_level, chart_data['chart_name']) , 
            description="%s\nChart by: %s" % (chart_data['chart_artist'],chart_data['charter']), 
            color=0xFF0000) # Red
            embed.set_author(name=f"{usernick} - Failed", icon_url=member.display_avatar)
        else:
            embed=discord.Embed(title="[Lv. %s] %s" % (chart_level, chart_data['chart_name']) , 
            description="%s\nChart by: %s" % (chart_data['chart_artist'],chart_data['charter']), 
            color=0x00FF00) # Green 
            embed.set_author(name=f"{usernick} - Cleared", icon_url=member.display_avatar)
            
        embed.set_thumbnail(url="attachment://" + bgfileformat)
        embed.add_field(name=diff_name, value="""
        **Cool:** %s
        **Bad:** %s"""% (cool, bad), inline=True)
        embed.add_field(name=u"\u200B", value="""
        **Good:** %s
        **Miss:** %s""" % (good, miss), inline=True)
        embed.add_field(name="Max Combo", value="%s" % (maxcombo), inline=False)
        #embed.add_field(name="Max Jam", value="500", inline=True)
        #embed.add_field(name="Total Score", value="%s" % (totalscore), inline=True)
        embed.add_field(name="Score", value=f"{scorev2}", inline=True)
        embed.add_field(name="Accuracy", value=f"{accuracy}%", inline=True)

        date_played = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
        embed.set_footer(text=f"Date Verified: {date_played}")  

        await channel.send(file=file, embed=embed)



    # Multiplayer Score Discord Embed

    async def MP_Score(self, lobby_scores):
        channel = self.bot.get_channel(int(os.getenv('recentlyplayedmsg')))
        ojnid = lobby_scores[0][4]
        chart_data = RecentlyPlayed.get_chart_details(self, ojnid)
        difficulty = 0
        if not chart_data:
            logger.info(f"OJNID NOT FOUND [ID: {lobby_scores[0][4]}]")
            return
        if lobby_scores[0][5] == 0:
            difficulty = 0
            chart_notecount = chart_data['easy_notecount']
            chart_level = chart_data["easy_level"]
            diff_color = 0x00FF00 # Green
        elif lobby_scores[0][5] == 1:
            difficulty = 1
            chart_notecount = chart_data['normal_notecount']
            chart_level = chart_data["normal_level"]
            diff_color = 0xFFFF00 # Yellow
        else:
            difficulty = 2
            chart_notecount = chart_data['hard_notecount']
            chart_level = chart_data["hard_level"]
            diff_color = 0xFF0000 # Red

        # Chart Image for Discord Embed
        songbg_path = os.getenv('songbgfilepath')
        bgfileformat = str(chart_data['chart_id'])+'.jpg'
        current_bg_path = os.path.join(songbg_path, bgfileformat)
        if os.path.exists(current_bg_path) == False:
            current_bg_path = os.path.join(songbg_path, "_blank.jpg")

        clear_player_scores = []
        failed_player_scores = []
        for line in lobby_scores:
            score_format = []
            player_cool = int(line[7])
            player_good = int(line[8])
            player_bad = int(line[9])
            player_miss = int(line[10])
            player_maxcombo = int(line[11])
            player_hitcount = player_cool + player_good + player_bad + player_miss
            player_scorev2 = RecentlyPlayed.scorev2(self, player_cool, player_good, player_bad, player_miss, chart_notecount)
            player_accuracy = RecentlyPlayed.hitcount_to_accuracy(self, player_cool, player_good, player_bad, player_miss)
            chart_clear = RecentlyPlayed.IsPassed(self, chart_data['chart_id'], difficulty, player_hitcount)

            score_format.append(line[3]) # usernick
            score_format.append(player_cool)
            score_format.append(player_good)
            score_format.append(player_bad)
            score_format.append(player_miss)
            score_format.append(player_maxcombo)
            score_format.append(player_accuracy)
            score_format.append(player_scorev2)  

            if chart_clear == True:
                clear_player_scores.append(score_format)
            else:
                failed_player_scores.append(score_format)

        else:
            # Sort by score v2
            clear_player_scores.sort(key=lambda x: x[7], reverse=True)
            failed_player_scores.sort(key=lambda x: x[7], reverse=True)
        
        # Discord Embed

        embed=discord.Embed(title=f"[Lv. {chart_level}] {chart_data['chart_name']}", 
            description=f"{chart_data['chart_artist']}\nChart by: {chart_data['charter']}", 
            color=diff_color)
        embed.set_author(name=f"Multiplayer Lobby")
        file = discord.File(current_bg_path, filename=bgfileformat)
        embed.set_thumbnail(url="attachment://" + bgfileformat)
        count = 0
        if len(clear_player_scores) > 0:
            embed.add_field(name="Cleared", value="------------------------------", inline=False)
            for score_line in clear_player_scores:
                count += 1
                embed.add_field(name=f"{count}. {score_line[0]} - [`{round(score_line[6],2)}%`] [`{round(score_line[7])}`]",
                                value=f"Combo: `x{score_line[5]}` - [`{score_line[1]}` - `{score_line[2]}` - `{score_line[3]}` - `{score_line[4]}`]",
                                inline=False)
        if len(failed_player_scores) > 0:
            embed.add_field(name="Failed", value="------------------------------", inline=False) 
            for score_line in failed_player_scores:
                count += 1
                embed.add_field(name=f"{count}. {score_line[0]} - [`{round(score_line[6],2)}%`] [`{round(score_line[7])}`]",
                                value=f"Combo: `x{score_line[5]}` - [`{score_line[1]}` - `{score_line[2]}` - `{score_line[3]}` - `{score_line[4]}`]",
                                inline=False)
        date_played = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
        embed.set_footer(text=f"ID: {lobby_scores[0][0]} Date Verified: {date_played}")  
        await channel.send(file=file, embed=embed)
   
async def setup(bot):
    await bot.add_cog(RecentlyPlayed(bot))
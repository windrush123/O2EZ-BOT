from turtle import color
from dotenv import load_dotenv
from pathlib import Path
import pyodbc
import os
import discord
import time
from discord.ext import commands
from discord.ext import tasks

load_dotenv()
conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
( os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS') ) )

class userscore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_score(self, scoreid):
        songbg_path = "C:\\Users\\carlo\\source\\repos\\Record Management\\O2EZ-BOT\\assets\\songbg\\"
        channel = self.bot.get_channel(970336728466477086)

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
             totalscore =str(row[15])
             scorev2 = str(row[16])
             accuracy = str(row[17])
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
       
        
        embed=discord.Embed(title="[Lv. %s] %s" % (chart_level, chart_title) , 
        description="%s\nChart by: %s" % (chart_artist,charter), 
        color=diff_color) 
        #embed.set_author(name="Recently Played by: %s" % (usernick))
        file = discord.File(current_bg_path, filename=bgfileformat)
        embed.set_thumbnail(url="attachment://" + bgfileformat)
        embed.add_field(name=diff_name, value="""
        **Cool:** %s
        **Good:** %s"""% (cool, good), inline=True)
        embed.add_field(name=u"\u200B", value="""
        **Bad:** %s
        **Miss:** %s""" % (bad, miss), inline=True)
        embed.add_field(name="Max Combo", value="%s" % (maxcombo), inline=False)
        #embed.add_field(name="Max Jam", value="500", inline=True)
        embed.add_field(name="Total Score", value="%s" % (totalscore), inline=True)
        embed.add_field(name="ScoreV2", value="%s" % (scorev2), inline=True)
        embed.add_field(name="Accuracy", value="00.00", inline=True)
        embed.add_field(name=u"\u200B", value="Date Played: <t:%d:f>" % (time.time()), inline=False)
        #embed.set_footer(text=f"Date Played: <t:%d:f>" (time.time()))
        await channel.send("Recently Played by: %s" % (usernick),file=file, embed=embed)
    
    async def before_send_score(self):
        print('userscore waiting...')
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(userscore(bot))

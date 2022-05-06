from turtle import color
from dotenv import load_dotenv
import pyodbc
import os
import discord
from discord.ext import commands
from discord.ext import tasks

load_dotenv()
conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
( os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS') ) )

class userscore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def setup_hook(self) -> None:
        self.send_userscore.start()

    @commands.command()
    async def rs(self, ctx):
        songbg_path = "C:\\Users\\carlo\\source\\repos\\Record Management\\O2EZ-BOT\\assets\\songbg\\"
        
        scores = []
        
        cursor = conncreate

        find_score = cursor.execute("SELECT * FROM dbo.userscores WHERE score_id=(SELECT max(score_id) FROM dbo.userscores)")
        for row in find_score:
             scores = row
             usernick = row[1]
             chart_level = str(row[8])
             cool = str(row[9])
             good= str(row[10])
             bad=str(row[11])
             miss =str(row[12])
             maxcombo=str(row[13])
             totalscore =str(row[15])


        find_chartdetails = cursor.execute("SELECT * FROM dbo.songlist WHERE chart_id=?", scores[4])
        for row in find_chartdetails:    
            song = row
            chart_title = row[2]
            chart_artist = row[3]
            charter = row[5]
        bgfileformat = 'o2ma'+str(song[0])+'.jpg'
        current_bg_path = os.path.join(songbg_path, bgfileformat)
        #print(str(current_bg_path))
        channel = self.bot.get_channel(970336728466477086)
        
        embed=discord.Embed(title="[Lv. %s] %s" % (chart_level, chart_title) , description="%s\nChart by: %s" % (chart_artist,charter), color=0xff0000)
        #embed.set_author(name="Recently Played by: %s" % (usernick))
        file = discord.File(current_bg_path, filename=bgfileformat)
        embed.set_thumbnail(url="attachment://" + bgfileformat)
        embed.add_field(name="Hard Difficulty", value="""
        **Cool:** %s
        **Good:** %s"""% (cool, good), inline=True)
        embed.add_field(name=u"\u200B", value="""
        **Bad:** %s
        **Miss:** %s""" % (bad, miss), inline=True)
        embed.add_field(name="Max Combo", value="%s" % (maxcombo), inline=False)
        #embed.add_field(name="Max Jam", value="500", inline=True)
        embed.add_field(name="Total Score", value="%s" % (totalscore), inline=False)
        embed.add_field(name=u"\u200B", value="Date Played: <t:1651857116:f>", inline=False)
        #embed.set_footer(text=f"Played At: <t:1651857116:f>")
        await ctx.send("Recently Played by: %s" % (usernick),file=file, embed=embed)

        #await channel.send("<t:1651857116:f>")
    

def setup(bot):
    bot.add_cog(userscore(bot))

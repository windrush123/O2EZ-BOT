import os
import pyodbc
from dotenv import load_dotenv

from discord.ext import commands

load_dotenv()

conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
( os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS') ) )

class highscore(commands.Cog):
    def __init__(self, bot) -> None:
        super().__init__()
        self.bot = bot
    
    def import_highscore(self, score):
        cursor = conncreate
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
        print('[HIGH SCORE][%s][%s] %s - %s : cool: %s good: %s bad: %s miss: %s [Max Combo:%s] [Total Score: %s]' 
        % (score[1] ,score[7],score[5], score[6], 
        score[9],score[10],score[11],score[12], 
        score[13],score[15]))


def setup(bot):
    bot.add_cog(highscore(bot))
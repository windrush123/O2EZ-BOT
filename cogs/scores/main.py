import os
from dotenv import load_dotenv

from discord.ext import commands
from discord.ext import tasks

load_dotenv()

class main(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.record.start()
        

    
    refresh_timer = int(os.getenv('timer_scorereading'))
    @tasks.loop(seconds=refresh_timer)  
    async def record(self):
        record_score = self.bot.get_cog('record_score')
        await record_score.read_scores()

    @record.before_loop
    async def before_record(self):
        print('Score Recording Online...!')
        await self.bot.wait_until_ready()

    @record.after_loop
    async def on_record_cancel(self):
        print('[Score Recording] Finishing loop before closing...')
        self.record.stop()      
        print('[Score Recording] Closed !')

        
def setup(bot):
    bot.add_cog(main(bot))

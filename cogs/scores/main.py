from dotenv import load_dotenv

from discord.ext import commands
from discord.ext import tasks

load_dotenv()

class main(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.record.start()

    @tasks.loop(seconds=5)  
    async def record(self):
        record_score = self.bot.get_cog('record_score')
        await record_score.read_scores()

    async def before_record(self):
        print('Score Recording Online...!')
        await self.bot.wait_until_ready()
        
def setup(bot):
    bot.add_cog(main(bot))

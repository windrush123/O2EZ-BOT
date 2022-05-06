from discord.ext import commands
import os



class userscore:
    def __init__(self, bot):
        self.bot = bot

    async def send_userscore():
        global bot 
        channel = bot.get_channel(970336728466477086)
        await channel.send("""TEST 1""")

def setup(bot):
    bot.add_cog(userscore(bot))

bot.run(os.getenv('TOKEN'))   
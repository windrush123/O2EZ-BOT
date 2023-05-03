import discord
import os
import pyodbc
import utils.logsconfig as logsconfig
import datetime

from discord import app_commands
import core.sendscore as sendscore

from discord.ext import commands
 

logger = logsconfig.logging.getLogger("bot")

conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
( os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS') ) )

class usercmds(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def online(self, ctx):
        logger.info('[%s#%s] has printed Online users' % (ctx.message.author.name,ctx.message.author.discriminator))
        cursor = conncreate
        pageCount = usercount = maxusercount = 0
        pages, users, ign = [], [], []
        a = cursor.execute("SELECT * FROM dbo.T_o2jam_login")
        x = ''
        for t in a: maxusercount += 1
        if maxusercount > 0:  
            a = cursor.execute("SELECT * FROM dbo.T_o2jam_login")
            for row in a:
                ign.append(row.USER_ID)
            for name in ign:
                b = cursor.execute("SELECT USER_NICKNAME FROM dbo.T_o2jam_charinfo WHERE USER_ID=?", name)
                for row in b:        
                    x += str("- " + row.USER_NICKNAME + "\n")   
                usercount += 1
                if (usercount % 10 == 0):
                    pageCount += 1
                    users.append("%s" % (x))
                    x = ''
                elif (usercount >= maxusercount):
                    users.append("%s" % (x))
                    x = ''
                currentPageCount = 0
            while (currentPageCount <= int(pageCount)):
                page = discord.Embed (title = "Online Users", description = users[currentPageCount], color=0x00ffff)
                page.set_footer(text='Page ' + str(currentPageCount + 1) + '/' + str(pageCount + 1))
                pages.append(page)
                currentPageCount += 1 
            message = await ctx.send(embed = pages[0])
            if(pageCount >= 1):
                await message.add_reaction('◀')
                await message.add_reaction('▶')
                def check(reaction, user):
                    return user == ctx.author
                i = 0
                reaction = None
                while True:
                    if str(reaction) == '◀':
                        if i > 0:
                            i -= 1
                            await message.edit(embed = pages[i])
                    elif str(reaction) == '▶':
                        if  i < len(pages)-1:
                            i += 1
                            await message.edit(embed = pages[i])
                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', timeout = 30.0, check = check)
                        await message.remove_reaction(reaction, user)
                    except:
                        break
                await message.clear_reactions()
        else: 
            page = discord.Embed (title = " ", description = "No one is online!", color=0x00ffff)
            await ctx.send(embed=page)  

    @commands.command()
    async def unstuck(self, ctx):
        cursor = conncreate
        discorduid = ctx.message.author.id
        registered = stucked = 0
        #check if user is registered
        a = cursor.execute("SELECT userid FROM dbo.member WHERE discorduid=?",discorduid)    
        for row in a:
            userids = (row.userid)
            registered += 1
        if registered >= 1:
            #check if stucked    
            b = cursor.execute("SELECT USER_ID FROM dbo.T_o2jam_login WHERE USER_ID=?",userids)
            for row in b:
                stucked += 1
            if stucked >= 1:
                cursor.execute("DELETE FROM dbo.T_o2jam_login WHERE USER_ID=?", userids)
                cursor.commit()
                sender = ctx.message.author
                userids.strip()
                logger.info('[%s] Unstuck ID: [%s]' % (sender,userids.strip()))
                await ctx.send('[%s] Successfully unstucked!' % (userids.strip()))
            else:
                await ctx.send('Your account is not stuck.')
        else:
            await ctx.send('Username not found!')
        
    @commands.command()
    @commands.has_role(os.getenv('memberrole'))
    async def profile(self, ctx, *, member: discord.Member=None):
            # if user is not mentioned
            if not member:
                member = ctx.message.author 
            cursor = conncreate
            registered = 0
            userdata = 0
            onlinestatus = 0
            discorduid = member.id     
            #check if user/sender is registered 
            c = cursor.execute("SELECT usernick from dbo.member where discorduid=?", discorduid)
            for row in c:
                usernick = (row.usernick)
                registered =+ 1
            if registered >= 1:
                a = cursor.execute("SELECT USER_INDEX_ID,USER_NICKNAME,Level,Battle,Experience FROM dbo.T_o2jam_charinfo where USER_NICKNAME=?", usernick)
                for row in a:
                    index_id = (row.USER_INDEX_ID)
                    ign = (row.USER_NICKNAME)
                    level = (row.Level)
                    PlayCount = (row.Battle)
                    Exp = (row.Experience)
                    userdata =+ 1
                #check if user/sender profile data exists
                if userdata >= 1:
                    b = cursor.execute ("SELECT registdate FROM dbo.member where usernick=?", ign)
                    for row in b:
                        registdate = (row.registdate)                
                    dateformat ='%Y-%m-%d %H:%M:%S.%f'
                    datejoined = datetime.datetime.strptime(str(registdate),dateformat)
                    author = ctx.message.author
                    pfp = author.avatar
                    embed=discord.Embed(title=u"\u200B", color=0x00ffff)
                    embed.set_author(name="%s#%s Profile" % (member.name, member.discriminator), icon_url=member.avatar)
                    embed.set_thumbnail(url=member.avatar)
                    #embed.add_field(name="ID", value="%s" % (index_id), inline=True)
                    embed.add_field(name="In-Game Name", value="%s" % (ign), inline=True)
                    embed.add_field(name="Level", value="%s" % (level), inline=True)
                    embed.add_field(name=u"\u200B", value=u"\u200B", inline=False)
                    embed.add_field(name="Playcount", value="%s" % (PlayCount), inline=True)
                    #embed.add_field(name="Experienced", value="%s" % (Exp), inline=True)
                    embed.add_field(name="Date Joined", value="%s" % (datejoined.strftime("%B %d %Y")), inline=True)
                    embed.add_field(name=u"\u200B", value=u"\u200B", inline=False)
                    x = cursor.execute("SELECT USER_ID FROM dbo.T_o2jam_login WHERE USER_ID=?",  ign)
                    for row in x:
                        onlinestatus += 1
                    if onlinestatus >= 1: embed.set_footer(text="🟢 Online")               
                    else: embed.set_footer(text="🔴 Offline")          
                    await ctx.send(embed=embed)
                    logger.info("[%s#%s] printed their profile." % (ctx.message.author.name,ctx.message.author.discriminator))
                else: await ctx.send("Profile not found, users have to play once before getting a profile.")
            else: await ctx.send("User not yet Registered!")

    @commands.command()
    @commands.has_role(os.getenv('memberrole'))
    async def score(self, ctx, scoreid: int):
        async with ctx.typing():
            channel = ctx.channel.id
            await sendscore.SendScore.send_score(self, channel, scoreid)

    @commands.command()
    @commands.has_role(os.getenv('memberrole'))
    async def accountdetails(self, ctx):
        cursor = conncreate
        registered = 0
        discorduid = ctx.message.author.id 
        user = cursor.execute("SELECT usernick from dbo.member where discorduid=?", discorduid)
        logger.info("[%s#%s] asked for their account details." % (ctx.message.author.name,ctx.message.author.discriminator))
        await ctx.message.delete()
        for row in user:
            registered =+ 1
        if registered >= 1:
            username_search = cursor.execute("SELECT userid,passwd from dbo.member where discorduid=?", discorduid)
            for row in username_search:
                username_field = (row.userid)
                password_field = (row.passwd)
            try:
                await ctx.message.author.send("\nThis message will be deleted in 15 seconds.\n```username: %s \npassword: %s```" % (username_field.strip(), password_field.strip()), delete_after=15)

            # if a bot cannot message a user
            except discord.Forbidden:
                logger.warning("Error DMing the user (Forbidden)")
                return await ctx.send("<@%s> Failed to send details, please check this server's privacy settings and allow direct messages." % ctx.message.author.id)
            except discord.HTTPException:
                logger.warning("Error DMing the user (HTTTPException)")
                return await ctx.send("Forbidden 400, contact a server admin for help.")
        else: 
            logger.info("Error: User not Found.")
            await ctx.send("%s Error: User not Found." % (ctx.message.author.mention))


    @profile.error
    async def profile_error(ctx, error):
        if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
            logger.info("[%s#%s] is trying to print a profile but has no role" % (ctx.message.author.name,ctx.message.author.discriminator))       

    @online.error
    async def online_error(ctx, error):
        if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
            logger.info("[%s][%s#%s] is trying to print profile but has no role." % (ctx.message.author.name,ctx.message.author.discriminator))

    @unstuck.error
    async def unstuck_error(ctx, error):
        if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
            logger.info("[%s#%s] is trying to use unstuck but has no role." % (ctx.message.author.name,ctx.message.author.discriminator))
    
    @accountdetails.error
    async def accountdetails_error(ctx, error):
        if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
            logger.info("[%s#%s] is trying to use accountdetails but has no role." % (ctx.message.author.name,ctx.message.author.discriminator))
    
    @score.error
    async def score_error(ctx, error):
        if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
            logger.info("[%s#%s] is trying to use score but has no role." % (ctx.message.author.name,ctx.message.author.discriminator))
            
async def setup(bot):
    await bot.add_cog(usercmds(bot))
import discord
import os
import subprocess
import pyodbc
import logsconfig
import datetime
from discord.ext import commands 

logger = logsconfig.logging.getLogger("bot")

conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
( os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS') ) )

class admin(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_role(os.getenv('adminrole'))
    async def helpadmin(self, ctx):
        await ctx.send(
            '''```
    General Category:
    !helpadmin
        Shows this message
    !createinv
        Create an invite link
    !deleteinv [invite link or code]
        Deletes an invite link
    !deleteallinv
        Deletes all unused invite link
    !syncnames
        Sync players name to their discord
    !relinkdiscord [IGN] [Discorduid]
        Link user to his current discorduid
    !relinkinvite [Invite Link/Code] [Discorduid]
        Link discorduid to invite code
    !startserver
        Start the O2Jam Server
    !stopserver
        Stop the O2Jam Server```''')

    #@commands.command()
    #@commands.has_role(os.getenv('adminrole'))
    #async def createinv(self, ctx):
    #    #creating invite link
    #    RegistrationChannel = self.bot.get_channel(int(os.getenv('registrationchannel')))
    #    invitelink = await RegistrationChannel.create_invite(max_uses=1,unique=True)
    #    discordlink = invitelink.url
    #    invlink = discordlink.replace("https://discord.gg/","") 
    #    #storing in db
    #    cursor = conncreate
    #    cursor.execute("INSERT INTO dbo.discordinv (invlink,used) VALUES (?,'False')", invlink)
    #    cursor.commit()
    #    sender = ctx.message.author
    #    print('[%s][%s] has created an invite link: %s' % (now,sender,invitelink.url))
    #    await ctx.send(invitelink)
    #    invites[ctx.guild.id] = await ctx.guild.invites()
        
    #@commands.command()
    #@commands.has_role(os.getenv('adminrole'))
    #async def deleteinv(self, ctx, invlink):
    #    invite_count = 0
    #    cursor = conncreate
    #    invlink = invlink.replace("https://discord.gg/","")
    #    a = cursor.execute("SELECT invlink,discorduid FROM dbo.discordinv WHERE invlink=?", invlink)
    #    for row in a:
    #        invitelink = (row.invlink)
    #        discorduid = (row.discorduid)
    #        invite_count += 1
    #    if invite_count >= 1:       
    #        embed=discord.Embed(title="Invite Code found: `%s`" % invitelink, description="Deleted Successfully!", color=0xff0000)
    #        cursor.execute("DELETE FROM dbo.discordinv WHERE invlink=?", invlink)
    #        cursor.commit()
    #        sender = ctx.message.author   
    #        print("[%s][%s] DELETED Invite Code: %s" %(now, sender, invlink))      
    #        await ctx.send(embed=embed)
    #        await self.bot.delete_invite(invlink)
    #    else:
    #        await ctx.send("Invite code not Found")

    #@commands.command()
    #@commands.has_role(os.getenv('adminrole'))
    #async def deleteallinv(ctx):
    #    cursor = conncreate
    #    unused_invlink_count = 0
    #    invlink = []
    #    a = cursor.execute("SELECT * FROM dbo.discordinv")
    #    for row in a:
    #        unused_invlink_count += 1
    #        invlink.append(row.invlink)
    #    if unused_invlink_count == 0: await ctx.send("No unused Invite link found!")    
    #    else:
    #        x = 0
    #        while x < unused_invlink_count:
    #            cursor.execute("DELETE FROM dbo.discordinv WHERE invlink=?", invlink[x])
    #            cursor.commit()
    #            print(invlink)
    #            await bot.delete_invite(invlink[x])
    #            print("Deleted Invite Link: %s" % invlink[x])        
    #            x += 1
    #        await ctx.send("%s Records Deleted" % unused_invlink_count)    

    # Sync player names
    @commands.command()
    @commands.has_role(os.getenv('adminrole'))
    async def syncnames(self, ctx):
        ign = users = []
        guild = ctx.guild
        adminrole = guild.get_role(int(os.getenv('adminroleid')))
        logger.info("[%s] syncnames command" % (ctx.message.author))
        cursor = conncreate
        a = cursor.execute("SELECT * FROM dbo.member")
        for row in a:
            users.append(row.discorduid)
        for discorduid in users:
            try:
                if guild.get_member(int(discorduid)):
                    member = guild.get_member(int(discorduid))
                    if adminrole in member.roles:
                        logger.info("%s is an admin, skipping." % (member))
                    else:
                        b = cursor.execute("SELECT usernick FROM dbo.member WHERE discorduid=?",discorduid)
                        for row in b:
                            logger.info("setting nickname %s to %s" % (member,row.usernick))
                            await member.edit(nick=row.usernick)
            except TypeError:  
                logger.info("Sync Names finished!")
                await ctx.send("Sync Names finished!")
                break
            
    @commands.command()
    @commands.has_role(os.getenv('adminrole'))
    async def relinkdiscord(self, ctx, ign, discorduid):
        cursor = conncreate
        registered = 0
        a = cursor.execute("SELECT usernick FROM dbo.member WHERE usernick=?", ign)
        for row in a:
            user = (row.usernick)
            registered =+ 1
        if registered >= 1:
            cursor.execute("UPDATE dbo.member SET discorduid=? WHERE usernick=?", discorduid, user.strip())
            cursor.commit()
            logger.info("Updating %s discorduid to %s" % (user.strip(), discorduid))
            await ctx.send("`%s` discorduid set to `%s`" % (user.strip(), discorduid))
        else: await ctx.send("IGN not found!")

    @commands.command()
    @commands.has_role(os.getenv('adminrole'))
    async def relinkinvite(self, ctx, invlink, discorduid):
        cursor = conncreate
        invitelink_found = 0
        invitelink = invlink.replace("https://discord.gg/","")
        a = cursor.execute("SELECT invlink FROM dbo.discordinv WHERE invlink=?", invitelink)
        for row in a:
            invitelink = (row.invlink)
            invitelink_found =+ 1
        if invitelink_found >= 1:
            cursor.execute("UPDATE dbo.discordinv SET discorduid=?,used='True' WHERE invlink=?", discorduid, invitelink)
            cursor.commit()
            logger.info("Updating Invite code %s discorduid -> %s" % (invitelink, ctx.message.author))
            await ctx.send("Successfully relinked discord invite `%s` to user <@%s>" % (invitelink, discorduid))
        else: await ctx.send("Invite Code not found!")

    @commands.command()
    @commands.has_role(os.getenv('adminrole'))
    async def startserver(self, ctx):  
        sleep_timer = os.getenv('timer_scorereading')
        sleep_timer_to_seconds = int(sleep_timer) * 60
        path = r"%s" % os.getenv('SERVER_PATH')
        open_path = os.path.join(path, "Start Server.bat")
        p = subprocess.Popen(str(open_path), cwd=path)
        stdout, stderr = p.communicate()
        #os.system("start " + '"" ' + '"' + os.getenv('SERVER_PATH') + "\Start Server.bat" + '"')
        logger.info('[%s] has started the Server' % (ctx.message.author))
        await ctx.send('`O2JAM Server` Online!')
        logger.info('O2JAM Server Online!')
        logger.info("[ONLINE] Record Scores Module")

    @commands.command()
    @commands.has_role(os.getenv('adminrole'))
    async def stopserver(self, ctx):
        #try: 
           # bot.unload_extension('cogs.scores.record_score')
        #    await ctx.send("`Record Scores Module` Offline! ")
            #await asyncio.sleep(5)
        #    logger.info("Successfully unloaded record scores")
        #except:
        #    logger.info("record_scores not online")
        path = r"%s" % os.getenv('SERVER_PATH')
        close_path = os.path.join(path, "Stop Server.bat")
        p = subprocess.Popen(str(close_path), cwd=path)
        stdout, stderr = p.communicate()       
        logger.warning('[%s] has stopped the server' % (ctx.message.author))
        await ctx.send('`O2JAM Server` Closed!')

    @commands.command()
    @commands.has_role(os.getenv('adminrole'))
    async def logs(self, ctx):
        await ctx.send(file=discord.File("logs/infos.log"))
async def setup(bot):
    await bot.add_cog(admin(bot))
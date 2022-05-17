from asyncio.windows_events import NULL
from email import message
import os
import sys
import discord
import pyodbc
import time
import datetime
import subprocess

from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()

conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
( os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS') ) )

now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

invites = {}

def find_invite_by_code(invite_list, code):       
   for inv in invite_list:    
        if inv.code == code:          
            return inv

@bot.event
async def on_ready():
    for guild in bot.guilds:
        invites[guild.id] = await guild.invites()        
    print('[%s] ----- BOT ONLINE -----' % (now))

@bot.event
async def on_member_join(member):
    cursor = conncreate
    botinvite = ban = 0
    username = ''
    PubChannel = bot.get_channel(int(os.getenv('publicchannelmsg')))
    PrivChannel = bot.get_channel(int(os.getenv('privatechannelmsg')))

    invites_after_join = await member.guild.invites()
    invites_before_join = invites[member.guild.id]
    usedinvites = list(set(set(invites_before_join).symmetric_difference(set(invites_after_join))))

    b = cursor.execute('SELECT userid FROM dbo.member WHERE discorduid=?', member.id)
    for row in b:
        username = (row.userid)

    if username:
        g = cursor.execute('SELECT USER_ID from dbo.T_o2jam_banishment where USER_ID=?', username)
        for row in g:
            ban += 1
    

    def removeban(uname):
        cursor.execute('DELETE FROM dbo.T_o2jam_banishment where USER_ID=?', uname.strip())
        cursor.commit()
        print("[%s] %s#%s successfully unbanned" % (now, member.name, member.discriminator))
    
    def find_invite_by_code(invite_list, code):      
        for inv in invite_list:            
            if inv.code == code:                      
                return inv

    #if bot generated invite
    if len(usedinvites):
        invitelink = str(usedinvites[0])
        invite = invitelink.replace("https://discord.gg/","")
        a = cursor.execute('SELECT invlink FROM dbo.discordinv where invlink=?', invite)
        for row in a:
            botinvite += 1

    #if direct invite with many uses
    # PS: somtimes, "usedivites" variable returns no index so this is for error handling      
    elif not len(usedinvites):
        for invite in invites_before_join:
            if invite.uses < find_invite_by_code(invites_after_join, invite.code).uses: 
                PublicembedVar = discord.Embed(title="%s#%s has joined" % (member.name, member.discriminator), description="", color=0x00ff00)
                await PubChannel.send(embed=PublicembedVar)              
                if ban >= 1:
                    removeban(username)
                    await PrivChannel.send("`%s#%s` re-joined the server using direct invite and successfully unbanned `User_ID: %s` `Invite Code: %s`" % (member.name, member.discriminator, username.strip(), invite.code))
                    return None
                await PrivChannel.send("`%s#%s` has joined the server using direct invite `Invite Code: %s`" % (member.name, member.discriminator, invite.code))
                print("[%s] %s#%s has joined the server using direct invite Invite Code: %s" % (now, member.name, member.discriminator, invite.code))

    #if user new to server and uses bot generated invite code
    if ban == 0 and botinvite == 1:
        print('[%s] joined DISCORD UID: %s' % (now, member.id))
        print('[%s] joined USERNAME: %s#%s' % (now, member.name, member.discriminator))
        print('[%s] Invite Code: %s' % (now, invite))
        #Private Channel Send          
        embedVar = discord.Embed(title="%s#%s has joined the server" % (member.name, member.discriminator), description="", color=0x00ff00)
        embedVar.add_field(name="Username:", value=member.name, inline=True)
        embedVar.add_field(name="UserID:", value="%s#%s" % (member.id, member.discriminator), inline=True)
        embedVar.add_field(name="Invite Code: ", value=invite, inline=True)
        await PrivChannel.send(embed=embedVar)
        #public Channel Send
        PublicembedVar = discord.Embed(title="%s#%s has joined the server" % (member.name, member.discriminator), description="", color=0x00ff00)
        await PubChannel.send(embed=PublicembedVar)
        cursor.execute("UPDATE dbo.discordinv SET discorduid=? WHERE invlink=?", member.id,invite)
        cursor.commit()

    elif ban >= 1 and botinvite == 1:
        print("[%s] %s#%s re-joined the server and using Bot Generated Invite Code [User_ID: %s][Invite Code: %s]" % (now, member.name, member.discriminator,username.strip(), invite))
        removeban(username)
        await PrivChannel.send("`%s#%s` re-joined the server using Bot Generated Invite link and successfully unbanned `User_ID: %s` `Invite Link: %s`" % (member.name, member.discriminator, username.strip(), invite))
       
        print("[%s] Proceeding to delete Invite Code from the database... [Invite Link: %s]" % (now, invite))
        cursor.execute("DELETE FROM dbo.discordinv WHERE invlink=?" ,invite)
        cursor.commit()
        await PrivChannel.send("`Invite Code: %s` has been deleted from the database." % (invite))
        print("[%s][Invite Code: %s] has been deleted from the database" % (now, invite))

    invites[member.guild.id] = invites_after_join 

@bot.event
async def on_member_remove(member):
    cursor = conncreate
    registered = 0
    ban = 0
    unusedinvite = 0
    PubChannel = bot.get_channel(int(os.getenv('publicchannelmsg')))
    PrivChannel = bot.get_channel(int(os.getenv('privatechannelmsg')))
    #Check if user registered before leaving the server
    a = cursor.execute("SELECT userid,invlink,usernick FROM dbo.member where discorduid=?", member.id)
    for row in a:
        userids = (row.userid)
        invlink = (row.invlink)
        usernick = (row.usernick)
        registered =+ 1
    if registered == 1:
        b = cursor.execute("SELECT USER_INDEX_ID FROM dbo.T_o2jam_charinfo where USER_ID=?", userids)
        for row in b:
            userindexid = (row.USER_INDEX_ID)
            ban =+ 1
        #Ban a player when he leave discord server
        if ban == 1:
            cursor.execute("INSERT INTO dbo.T_o2jam_banishment (USER_INDEX_ID,USER_ID,Ban_date) VALUES (?,?,?)", userindexid, userids, now)
            cursor.commit()
            #private channel send
            embedVar = discord.Embed(title="%s#%s has left the server" % (member.name, member.discriminator), description="", color=0xff0000)
            embedVar.add_field(name="Username:", value=userids, inline=True)
            embedVar.add_field(name="UserID:", value=member.id, inline=True)
            embedVar.add_field(name="Invite Code: ", value=invlink, inline=True)
            await PrivChannel.send(embed=embedVar)
            #public channel send
            PublicembedVar = discord.Embed(title="%s#%s has left the server" % (member.name, member.discriminator), description="In-Game Name: %s" % (usernick), color=0xff0000)
            await PubChannel.send(embed=PublicembedVar)
            print("[%s][IGN:%s] %s#%s has left the server" % (now, usernick.strip(), member.name, member.discriminator))
            print("[%s][IGN:%s] has been added into banishment table" % (now, usernick.strip()))
        else:
            #PublicembedVar = discord.Embed(title="%s#%s has left the server" % (member.name, member.discriminator), description="In-Game Name: Not Registered", color=0xff0000)
            #await PubChannel.send(embed=PublicembedVar)
            print("[%s] %s#%s HAS LEFT THE SERVER BUT DATA NOT FOUND IN T_O2jam_Charinfo!!!" % (now, member.name, member.discriminator))
            await PrivChannel.send("%s#%s Has left the server but data is not found in T_o2jam_charinfo!" % (member.name, member.discriminator)) 
    #if player did not registered before leaving
    else: 
        #check invite link
        b = cursor.execute("SELECT invlink FROM dbo.discordinv where discorduid=?", member.id)        
        for row in b:
            print("[%s] Found unused invite link proceeding to delete..." % (now))      
            unusedinvite =+ 1
        if unusedinvite >= 1: # delete invite link
            cursor.execute("DELETE FROM dbo.discordinv where discorduid=?", member.id)
            cursor.commit()
            print("[%s] Invite link successfully deleted!" % (now))
        else: # if no invite code found
            await PrivChannel.send("%s#%s has left the server but invite link was not found in the database! probably someone made a direct invite?" % (member.name, member.discriminator))
            print("[%s] %s#%s has left the server but invite link was not found in the database!" % (now, member.name, member.discriminator))
            return None

        await PrivChannel.send("%s#%s has left the server but never registered!" % (member.name, member.discriminator))
        PublicembedVar = discord.Embed(title="%s#%s has left the server" % (member.name, member.discriminator), description="In-Game Name: Not Registered", color=0xff0000)
        await PubChannel.send(embed=PublicembedVar)
        print("[%s] %s#%s HAS LEFT THE SERVER BUT NEVER REGISTERED!!!" % (now, member.name, member.discriminator))

    #updates the invite code list when someone leaves    
    invites[member.guild.id] = await member.guild.invites()

#----------------------------------
# User Commands
#----------------------------------

@bot.remove_command('help')
@bot.command(name='help')
@commands.has_role(os.getenv('memberrole'))
async def help(ctx):
    await ctx.send(
        '''```
General Category:
 !help
    Shows this message
 !online
    Shows who is currently online in the server

User Related:
 !profile
    Shows your detailed profile
 !unstuck
    Try this command if you successfully login to the server but you can't get passed into Channel Selection
 !accountdetails
    If you forget your username and password. (Make sure your DMs are open). ```
            ''')

@bot.command(name='unstuck')
@commands.has_role(os.getenv('memberrole'))
async def unstuck(ctx):
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
            print('[%s][%s] Unstuck ID: [%s]' % (now,sender,userids.strip()))
            await ctx.send('[%s] Successfully unstucked!' % (userids.strip()))
        else:
            await ctx.send('Your account is not stuck.')
    else:
        await ctx.send('Username not found!')

@bot.command(name='online')
@commands.has_role(os.getenv('memberrole'))
async def online(ctx):
    print('[%s][%s#%s] has printed Online users' % (now,ctx.message.author.name,ctx.message.author.discriminator))
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
                    reaction, user = await bot.wait_for('reaction_add', timeout = 30.0, check = check)
                    await message.remove_reaction(reaction, user)
                except:
                    break
            await message.clear_reactions()
    else: 
        page = discord.Embed (title = " ", description = "No one is online!", color=0x00ffff)
        await ctx.send(embed=page)         


@bot.command(name='profile')
@commands.has_role(os.getenv('memberrole'))
async def profile(ctx, *, member: discord.Member=None):
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
                pfp = author.avatar_url
                embed=discord.Embed(title=u"\u200B", color=0x00ffff)
                embed.set_author(name="%s#%s Profile" % (member.name, member.discriminator), icon_url=member.avatar_url)
                embed.set_thumbnail(url=member.avatar_url)
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
                print("[%s][%s#%s] printed their profile." % (now,ctx.message.author.name,ctx.message.author.discriminator))
            else: await ctx.send("Profile not found, users have to play once before getting a profile.")
        else: await ctx.send("User not yet Registered!")

@bot.command(name='accountdetails')
@commands.has_role(os.getenv('memberrole'))
async def accountdetails(ctx):
    cursor = conncreate
    registered = 0
    discorduid = ctx.message.author.id 
    user = cursor.execute("SELECT usernick from dbo.member where discorduid=?", discorduid)
    print("[%s][%s#%s] asked for their account details." % (now,ctx.message.author.name,ctx.message.author.discriminator))
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
            print ("Error DMing the user (Forbidden)")
            return await ctx.send("<@%s> Failed to send details, please check this server's privacy settings and allow direct messages." % ctx.message.author.id)
        except discord.HTTPException:
            print ("Error DMing the user (HTTTPException)")
            return await ctx.send("Forbidden 400, contact a server admin for help.")
    else: 
        print("Error: User not Found.")
        await ctx.send("%s Error: User not Found." % (ctx.message.author.mention))
    
#-----------------------------------------------
#               Admin Commands
#-----------------------------------------------
@bot.command(name='helpadmin')
@commands.has_role(os.getenv('adminrole'))
async def helpadmin(ctx):
    await ctx.send(
        '''```
General Category:
 !helpadmin
    Shows this message
 !createinv
    Create an invite link
 !deleteinv [invite link or code]
    Deletes an invite link
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

@bot.command(name='createinv')
@commands.has_role(os.getenv('adminrole'))
async def createinv(ctx):
    #creating invite link
    RegistrationChannel = bot.get_channel(int(os.getenv('registrationchannel')))
    invitelink = await RegistrationChannel.create_invite(max_uses=1,unique=True)
    discordlink = invitelink.url
    invlink = discordlink.replace("https://discord.gg/","") 
    #storing in db
    cursor = conncreate
    cursor.execute("INSERT INTO dbo.discordinv (invlink,used) VALUES (?,'False')", invlink)
    cursor.commit()
    sender = ctx.message.author
    print('[%s][%s] has created an invite link: %s' % (now,sender,invitelink.url))
    await ctx.send(invitelink)
    invites[ctx.guild.id] = await ctx.guild.invites()
    
@bot.command(name='deleteinv')
@commands.has_role(os.getenv('adminrole'))
async def deleteinv(ctx, invlink):
    invite_count = 0
    cursor = conncreate
    invlink = invlink.replace("https://discord.gg/","")
    a = cursor.execute("SELECT invlink,discorduid FROM dbo.discordinv WHERE invlink=?", invlink)
    for row in a:
        invitelink = (row.invlink)
        discorduid = (row.discorduid)
        invite_count += 1
    if invite_count >= 1:       
        embed=discord.Embed(title="Invite Code found: `%s`" % invitelink, description="Deleted Successfully!", color=0xff0000)
        cursor.execute("DELETE FROM dbo.discordinv WHERE invlink=?", invlink)
        cursor.commit()
        sender = ctx.message.author   
        print("[%s][%s] DELETED Invite Code: %s" %(now, sender, invlink))      
        await ctx.send(embed=embed)
        await bot.delete_invite(invlink)
    else:
        await ctx.send("Invite code not Found")

# Sync player names
@bot.command(name='syncnames')
@commands.has_role(os.getenv('adminrole'))
async def syncnames(ctx):
    ign = users = []
    guild = ctx.guild
    adminrole = guild.get_role(int(os.getenv('adminroleid')))
    print("[%s][%s] syncnames command" % (now, ctx.message.author))
    cursor = conncreate
    a = cursor.execute("SELECT * FROM dbo.member")
    for row in a:
        users.append(row.discorduid)
    for discorduid in users:
        try:
            if guild.get_member(int(discorduid)):
                member = guild.get_member(int(discorduid))
                if adminrole in member.roles:
                    print("%s is an admin, skipping." % (member))
                else:
                    b = cursor.execute("SELECT usernick FROM dbo.member WHERE discorduid=?",discorduid)
                    for row in b:
                        print("setting nickname %s to %s" % (member,row.usernick))
                        await member.edit(nick=row.usernick)
        except TypeError:  
            print("[%s] Sync Names finished!" % (now))
            break
           

@bot.command(name='relinkdiscord')
@commands.has_role(os.getenv('adminrole'))
async def relinkdiscord(ctx, ign, discorduid):
    cursor = conncreate
    registered = 0
    a = cursor.execute("SELECT usernick FROM dbo.member WHERE usernick=?", ign)
    for row in a:
        user = (row.usernick)
        registered =+ 1
    if registered >= 1:
        cursor.execute("UPDATE dbo.member SET discorduid=? WHERE usernick=?", discorduid, user.strip())
        cursor.commit()
        print("[%s] Updating %s discorduid to %s" % (now, user.strip(), discorduid))
        await ctx.send("`%s` discorduid set to `%s`" % (user.strip(), discorduid))
    else: await ctx.send("IGN not found!")

@bot.command(name='relinkinvite')
@commands.has_role(os.getenv('adminrole'))
async def relinkinvite(ctx, invlink, discorduid):
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
        print("[%s] Updating Invite code %s discorduid -> %s" % (now, invitelink, ctx.message.author))
        await ctx.send("Successfully relinked discord invite `%s` to user <@%s>" % (invitelink, discorduid))
    else: await ctx.send("Invite Code not found!")

@bot.command(name='startserver')
@commands.has_role(os.getenv('adminrole'))
async def startserver(ctx):   
    os.system("start " + '"" ' + '"' + os.getenv('SERVER_PATH') + "\Start Server.bat" + '"')
    print('[%s][%s] has started the Server' % (now,ctx.message.author))
    await ctx.send('[%s] has started the Server' % (ctx.message.author))

@bot.command(name='stopserver')
@commands.has_role(os.getenv('adminrole'))
async def stopserver(ctx):
    os.system("start " + '"" ' + '"' + os.getenv('SERVER_PATH') + "\Stop Server.bat" + '"')
    print('[%s][%s] has stopped the server' % (now,ctx.message.author))
    await ctx.send('[%s] has stopped the server' % (ctx.message.author))


#-----------------------------------------------
#           Error Handling
#-----------------------------------------------

#@help.error
#async def help_error(ctx, error):
#    if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
#        print("[%s][%s#%s] !help command error, No Role!" % (now,ctx.message.author.name,ctx.message.author.discriminator)) 

@helpadmin.error
async def helpadmin_error(ctx, error):
    if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)): 
        print("[%s][%s#%s] !helpadmin command error, No Role!" % (now,ctx.message.author.name,ctx.message.author.discriminator)) 

@profile.error
async def profile_error(ctx, error):
    if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
        print("[%s][%s#%s] is trying to print a profile but has no role" % (now,ctx.message.author.name,ctx.message.author.discriminator)) 
@startserver.error
async def startserver_error(ctx, error):
    if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)): 
        print("[%s][%s#%s] is trying to start the server." % (now,ctx.message.author.name,ctx.message.author.discriminator))
        #await ctx.send("You don't have enough permision.")

@stopserver.error
async def stopserver_error(ctx, error):
    if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):        
        print("[%s][%s#%s] is trying to stop the server." % (now,ctx.message.author.name,ctx.message.author.discriminator))
        #await ctx.send("You don't have enough permision.")

@createinv.error
async def createinv_error(ctx, error):
    if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
        print("[%s][%s#%s] is trying to create an invite link." % (now,ctx.message.author.name,ctx.message.author.discriminator))
        #await ctx.send("You don't have enough permision.")
     

@deleteinv.error
async def deleteinv_error(ctx, error):
    if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
        print("[%s][%s#%s] is trying to delete an invite link." % (now, ctx.message.author.name,ctx.message.author.discriminator))
        #await ctx.send("You don't have enough permision.")
    elif isinstance(error, (commands.MissingRequiredArgument)):
        await ctx.send("Invalid Syntax: `!deleteinv [Invite Link/Code]`")

@online.error
async def online_error(ctx, error):
    if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
        print("[%s][%s#%s] is trying to print profile but has no role." % (now,ctx.message.author.name,ctx.message.author.discriminator))

@unstuck.error
async def unstuck_error(ctx, error):
    if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
        print("[%s][%s#%s] is trying to unstuck but has no role." % (now,ctx.message.author.name,ctx.message.author.discriminator))

@syncnames.error
async def syncnames_error(ctx, error):
    if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
        print("[%s][%s#%s] is trying to sync names." % (now,ctx.message.author.name,ctx.message.author.discriminator))

@relinkdiscord.error
async def relinkdiscord_error(ctx, error):
    if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
        print("[%s][%s#%s] is trying to use the command `!relinkdiscord`." % (now,ctx.message.author.name,ctx.message.author.discriminator))
    if isinstance(error, (commands.MissingRequiredArgument)):
        await ctx.send("Invalid Syntax: `!relinkdiscord [IGN] [DiscordUID]`")

@relinkinvite.error
async def relinkinvite_error(ctx, error):
    if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
        print("[%s][%s#%s] is trying to use the command `!relinkinvite`." % (now,ctx.message.author.name,ctx.message.author.discriminator))
    if isinstance(error, (commands.MissingRequiredArgument)):
        await ctx.send("Invalid Syntax: `!relinkinvite [Invite Link/Code] [DiscordUID]`")
   
@accountdetails.error
async def accountdetails_error(ctx, error):
    if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
        print("[%s][%s#%s] is trying to sync names." % (now,ctx.message.author.name,ctx.message.author.discriminator))


bot.load_extension('cogs.scores.record_score')

bot.run(os.getenv('TOKEN'))
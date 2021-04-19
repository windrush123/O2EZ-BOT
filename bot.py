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

now = datetime.datetime.now().strftime("%d.%b %Y %H:%M:%S")

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
    print('[%s]----- BOT ONLINE -----' % (now))


@bot.event
async def on_member_join(member):
    invites_after_join = await member.guild.invites()
    invites_before_join = invites[member.guild.id]
    usedinvites = list(set(set(invites_before_join).symmetric_difference(set(invites_after_join))))
    invitelink = str(usedinvites[0])
    invite = invitelink.replace("https://discord.gg/","")
    channel = bot.get_channel(int(os.getenv('joinchannelmsg')))
    print(invites_after_join)
    print('[%s]last joined userid: %s' % (now, member.id))
    print('[%s]last joined username: %s' % (now, member.name))
    print('[%s]invite code: %s' % (now, invite))          
    embedVar = discord.Embed(title="%s#%s has joined" % (member.name, member.discriminator), description="", color=0x00ff00)
    embedVar.add_field(name="Username:", value=member.name, inline=True)
    embedVar.add_field(name="UserID:", value=member.id, inline=True)
    embedVar.add_field(name="Invite Code: ", value=invite, inline=True)
    cursor = conncreate
    cursor.execute("UPDATE dbo.discordinv SET discorduid=? WHERE invlink=?", member.id,invite)
    cursor.commit()   
    await channel.send(embed=embedVar)
    invites[member.guild.id] = invites_after_join 

@bot.command(name='unstuck')
@commands.has_role(os.getenv('memberrole'))
async def unstuck(ctx, userid):
    cursor = conncreate
    count = 0
    a = cursor.execute("SELECT USER_ID FROM dbo.T_o2jam_login WHERE USER_ID=?", userid)    
    for row in a:
        userids = (row.USER_ID)
        count += 1
    if count >= 1:                       
        cursor.execute("DELETE FROM dbo.T_o2jam_login WHERE USER_ID=?", userid)
        cursor.commit()
        sender = ctx.message.author
        print('[%s][%s] Unstuck ID: [%s]' % (now,sender,userid))
        await ctx.send('[%s] Successfully unstucked!' % (userid))
    else:
        await ctx.send('Username not found!')

#-----------------------------------------------
#               Admin Commands
#-----------------------------------------------

@bot.command(name='createinv')
@commands.has_role(os.getenv('adminrole'))
async def createinv(ctx):
    #creating invite link
    invitelink = await ctx.channel.create_invite(max_uses=1,unique=True)
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
    count = 0
    cursor = conncreate
    invlink = invlink.replace("https://discord.gg/","")
    a = cursor.execute("SELECT invlink,discorduid FROM dbo.discordinv WHERE invlink=?", invlink)
    for row in a:
        invitelink = (row.invlink)
        discorduid = (row.discorduid)
        count += 1
    if count >= 1:
        await bot.delete_invite(invlink)
        embed=discord.Embed(title="Invite Code found: `%s`" % invitelink, description="Deleted Successfully!", color=0xff0000)
        cursor.execute("DELETE FROM dbo.discordinv WHERE invlink=?", invlink)
        cursor.commit()   
        print("[%s][%s] Invite Code: DELETED" %(now,invlink))
        await ctx.send(embed=embed)
    else:
        await ctx.send("Invite Code not Found")


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


@bot.command(name='myid')
@commands.has_role(os.getenv('adminrole'))
async def myid(ctx):
    discorduid = ctx.message.author.id
    discordname = ctx.message.author.name
    print("[%s] is your name" % (discordname))
    print("[%s] is your id" % (discorduid))
    print("[%s] is your name" % (ctx.message.author.discriminator))
    print("[%s] is your id" % (ctx.message.author.nick))

#-----------------------------------------------
#           Error Handling
#-----------------------------------------------

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
        await ctx.send("`!deleteinv [Invite Link/Code]`")

@unstuck.error
async def unstuck_error(ctx, error):
    if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
        print("[%s][%s#%s] is trying to unstuck but has no role." % (now,ctx.message.author.name,ctx.message.author.discriminator))
    elif isinstance(error, (commands.MissingRequiredArgument)):
        await ctx.send("`!unstuck [username]`")



#@myid.error
#async def myid_error(ctx, error):
#    if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
#        await ctx.send("You don't have enough permision.") 
#    elif isinstance(error, (commands.MissingRequiredArgument)):
#        await ctx.send("Command is missing an argument")


#@bot.command(name='getdata')
#async def getdata(ctx):
#   cursor = conncreate
#   row = cursor.fetchone() if row: print row
#   for row in cursor.execute("SELECT discorduid, invlink, used FROM dbo.discordinv WHERE discorduid=?", ctx.message.author.id):
#       print(row.discorduid, row.invlink)
#       await ctx.send("%s %s" % (row.discorduid, row.invlink))
#   cursor.commit()

bot.run(os.getenv('TOKEN'))

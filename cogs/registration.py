import discord
import pyodbc
import utils.logsconfig as logsconfig

import datetime
from discord import app_commands

from discord.ext import commands
import os
from dotenv import load_dotenv
from discord.app_commands import AppCommandError
load_dotenv()

logger = logsconfig.logging.getLogger("bot")

conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
( os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS') ) )

intents = discord.Intents.default()
intents.message_content = True

guildid = discord.Object(id=(os.getenv('guildid')))


class registration_form(discord.ui.Modal, title="O2EZ Registration Form"):
    username = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="username",
        min_length=6,
        max_length=16,
        required=True,
        placeholder="Enter your Username"
    )
    password = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Password",
        min_length=6,
        max_length=16,
        required=True,
        placeholder="Enter your Password"
    )

    conf_password = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Confirm Password",
        required=True,
        min_length=6,
        max_length=16,
        placeholder="Confirm your password"
    )

    ign = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="In-Game Name",
        required=True,
        min_length=6,
        max_length=12,
        placeholder="Enter your In-Game Name"
    )

    invite_link = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Invite Link or Code",
        required=True,
        placeholder="https://discord.gg/abcdefghi or abcdefghi"
    )

    async def on_submit(self, interaction: discord.Interaction):
        invite_code = self.invite_link.value.replace("https://discord.gg/","")
        exist_username = False
        exist_ign = False
        with conncreate.cursor() as cursor:
            sql = """SELECT * FROM dbo.member WHERE userid=?"""
            cursor.execute(sql, (self.username.value))
            for row in cursor:
                exist_username = True
        if exist_username: raise ValueError("exist_username")

        with conncreate.cursor() as cursor:
            sql = """SELECT * FROM dbo.member WHERE usernick=?"""
            cursor.execute(sql, (self.ign.value))
            for row in cursor:
                exist_ign = True
            if exist_ign: raise ValueError("exist_ign")
               
        if " " in self.password.value:
            raise ValueError("password_error")
        
        if self.password.value != self.conf_password.value:
            raise ValueError("conf_password")
        
        with conncreate.cursor() as cursor:
            sql = """SELECT * FROM dbo.discordinv WHERE invlink=?"""
            cursor.execute(sql , invite_code)
            for row in cursor:
                valid_code = True
        if valid_code == False:
            raise ValueError("invlid_code")
        


        channel = interaction.guild.get_channel(845353678907113511)        
        with conncreate.cursor() as cursor:
            sql = """INSERT INTO dbo.member 
                (userid, usernick, sex, passwd, registdate, id9you, discorduid, invlink) 
                VALUES (?, ?, 'True', ?, CURRENT_TIMESTAMP, '-1', ?, ?)"""
            cursor.execute(sql , (self.username.value, self.ign.value, self.password.value, interaction.user.id, invite_code))
            cursor.commit()
            cursor.execute("SELECT @@IDENTITY AS id")
            row = cursor.fetchone()
            getid = int(row[0])
            sql = "DELETE FROM dbo.discordinv WHERE invlink=?"
            cursor.execute(sql, (invite_code))
            cursor.commit()

        embed = discord.Embed(title="Member Regsitration",
                              description="DEBUG",
                              color=discord.Color.yellow())
        embed.add_field(name="ID", value=getid, inline=False)
        embed.add_field(name="Username", value=self.username.value, inline=False)
        embed.add_field(name="IGN", value=self.ign.value, inline=False)
        embed.add_field(name="Password", value=self.password.value, inline=False)
        embed.add_field(name="Invite", value=invite_code, inline=False)
        embed.add_field(name="DiscordID", value=interaction.user.id, inline=False)
        embed.set_author(name=self.ign.value)

        await channel.send(embed=embed)
        await interaction.response.send_message(f"Thank you, {self.user.nick} {self.user.id}", ephemeral=True)
        
    async def on_error(self, interaction: discord.Interaction, error : Exception):
        await interaction.response.send_message(f'Oops! Something went wrong. {interaction.user.id}', ephemeral=True)
        print(type(error), error, error.__traceback__)

class Registration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invites = {}
    def cog_load(self):
        pass
    def cog_unload(self):
        pass
        logger.error("This error was handled with option 1 from ?tag treeerrorcog")

    @app_commands.command(name="register", description='Open the Registration Form.')
    async def register(self, interaction: discord.Interaction) -> None: 
        register_modal = registration_form()
        register_modal.user = interaction.user
        await interaction.response.send_modal(register_modal)

    @commands.Cog.listener()
    async def on_ready(self): 
        for guild in self.bot.guilds:
            # Adding each guild's invites to our dict
            self.invites[guild.id] = await guild.invites()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        cursor = conncreate
        botinvite = ban = 0
        username = ''
        PubChannel = self.bot.get_channel(int(os.getenv('publicchannelmsg')))
        PrivChannel = self.bot.get_channel(int(os.getenv('privatechannelmsg')))

        invites_after_join = await member.guild.invites()
        invites_before_join = self.invites[member.guild.id]
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
            logger.info("%s#%s successfully unbanned" % (member.name, member.discriminator))
        
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
                    logger.info("%s#%s has joined the server using direct invite Invite Code: %s" % (member.name, member.discriminator, invite.code))
       
        if ban == 0 and botinvite == 1: # If user is new to the server and uses the bot generated invite code.
            logger.info(f"Recently Joined the server: {member.name}#{member.discrminator} UID:{member.id} Invite Code: {invite}")
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
            logger.info("%s#%s re-joined the server using the Bot Generated Invite Code [User_ID: %s][Invite Code: %s]" % 
                        (member.name, member.discriminator,username.strip(), invite))
            removeban(username)
            await PrivChannel.send("`%s#%s` re-joined the server using Bot Generated Invite link and successfully unbanned `User_ID: %s` `Invite Link: %s`" % 
                                   (member.name, member.discriminator, username.strip(), invite))        
            logger.info("[Invite Link: %s] Proceeding to delete Invite Code from the database." % (invite))
            try:
                cursor.execute("DELETE FROM dbo.discordinv WHERE invlink=?" ,invite)
                cursor.commit()
            except Exception as e:
                logger.warning(f"There's some problem deleting the invite link from the Database [{invite}]\n{e}")
            await PrivChannel.send("`Invite Code: %s` has been deleted from the database." % (invite))
            logger.info("[Invite Code: %s] has been deleted from the database" % (invite))
        self.invites[member.guild.id] = invites_after_join 

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        cursor = conncreate
        registered = 0
        ban = 0
        unusedinvite = 0
        PubChannel = self.bot.get_channel(int(os.getenv('publicchannelmsg')))
        PrivChannel = self.bot.get_channel(int(os.getenv('privatechannelmsg')))
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
                cursor.execute("INSERT INTO dbo.T_o2jam_banishment (USER_INDEX_ID,USER_ID,Ban_date) VALUES (?,?,CURRENT_TIMESTAMP)", userindexid, userids)
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
                logger.info("[IGN:%s] %s#%s has left the server" % (usernick.strip(), member.name, member.discriminator))
                logger.info("[IGN:%s] has been added into banishment table" % (usernick.strip()))
            else:
                #PublicembedVar = discord.Embed(title="%s#%s has left the server" % (member.name, member.discriminator), description="In-Game Name: Not Registered", color=0xff0000)
                #await PubChannel.send(embed=PublicembedVar)
                logger.info("%s#%s has left the server [Registered but never played]" % (member.name, member.discriminator))
                await PrivChannel.send("%s#%s Has left the server [Registered but never played]" % (member.name, member.discriminator)) 
        
        else: #if player did not registered before leaving 
            #check invite link
            b = cursor.execute("SELECT invlink FROM dbo.discordinv where discorduid=?", member.id)        
            for row in b:    
                unusedinvite =+ 1
            if unusedinvite >= 1: # delete invite link
                cursor.execute("DELETE FROM dbo.discordinv where discorduid=?", member.id)
                cursor.commit()
                logger.info("Invite link successfully deleted!")
            else: # if no invite code found
                await PrivChannel.send("%s#%s has left the server but invite link was not found in the database! probably someone made a direct invite?" % (member.name, member.discriminator))
                logger.info("%s#%s has left the server but invite link was not found in the database." % (member.name, member.discriminator))
                return None

            await PrivChannel.send("%s#%s has left the server but never registered!" % (member.name, member.discriminator))
            PublicembedVar = discord.Embed(title="%s#%s has left the server" % (member.name, member.discriminator), description="In-Game Name: Not Registered", color=0xff0000)
            await PubChannel.send(embed=PublicembedVar)
            logger.info("%s#%s Has left the server but never registered" % (member.name, member.discriminator))   
        self.invites[member.guild.id] = await member.guild.invites()


    # Creating and Deleting invites commands


    @commands.command()
    @commands.has_role(os.getenv('adminrole'))
    async def createinv(self, ctx):
        #creating invite link
        RegistrationChannel = self.bot.get_channel(int(os.getenv('registrationchannel')))
        invitelink = await RegistrationChannel.create_invite(max_uses=1,unique=True)
        discordlink = invitelink.url
        invlink = discordlink.replace("https://discord.gg/","") 
        #storing in db
        cursor = conncreate
        cursor.execute("INSERT INTO dbo.discordinv (invlink,used) VALUES (?,'False')", invlink)
        cursor.commit()
        sender = ctx.message.author
        logger.info('[%s] has created an invite link: %s' % (sender,invitelink.url))
        await ctx.send(invitelink)
        self.invites[ctx.guild.id] = await ctx.guild.invites()
        
    @commands.command()
    @commands.has_role(os.getenv('adminrole'))
    async def deleteinv(self, ctx, invlink):
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
            logger.info("[%s] DELETED Invite Code: %s" %(sender, invlink))      
            await ctx.send(embed=embed)
            await self.bot.delete_invite(invlink)
            self.invites[ctx.guild.id] = await ctx.guild.invites()
        else:
            await ctx.send("Invite code not Found")

    @commands.command()
    @commands.has_role(os.getenv('adminrole'))
    async def deleteallinv(self, ctx):
        cursor = conncreate
        unused_invlink_count = 0
        invlink = []
        a = cursor.execute("SELECT * FROM dbo.discordinv")
        for row in a:
            unused_invlink_count += 1
            invlink.append(row.invlink)
        if unused_invlink_count == 0: await ctx.send("No unused Invite link found!")    
        else:
            x = 0
            while x < unused_invlink_count:
                cursor.execute("DELETE FROM dbo.discordinv WHERE invlink=?", invlink[x])
                cursor.commit()
                print(invlink)
                await self.bot.delete_invite(invlink[x])
                #logger.info("Deleted Invite Link: %s" % invlink[x])        
                x += 1
            await ctx.send("%s Records Deleted" % unused_invlink_count)
            logger.info(f"{unused_invlink_count} Records Deleted")
        self.invites[ctx.guild.id] = await ctx.guild.invites() 

    # Error handling

    @createinv.error
    async def createinv_error(self, ctx, error):
        if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
            logger.info("[%s#%s] is trying to create an invite link." % (ctx.message.author.name,ctx.message.author.discriminator))
        

    @deleteinv.error
    async def deleteinv_error(self, ctx, error):
        if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
            logger.info("[%s#%s] is trying to delete an invite link." % (ctx.message.author.name,ctx.message.author.discriminator))
        elif isinstance(error, (commands.MissingRequiredArgument)):
            await ctx.send("Invalid Syntax: `!deleteinv [Invite Link/Code]`")
    
    @deleteallinv.error
    async def deleteallinv_error(self, ctx, error):
        if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
            logger.info("[%s#%s] is trying to delete an invite link." % (ctx.message.author.name,ctx.message.author.discriminator))
        elif isinstance(error, (commands.MissingRequiredArgument)):
            await ctx.send("Invalid Syntax: `!deleteinv [Invite Link/Code]`")


async def setup(bot: commands.Bot):
    await bot.add_cog(Registration(bot))
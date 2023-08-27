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
admin_role_id = int(os.getenv('adminroleid'))

class Invites(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invites = {}

    async def cog_load(self):
        logger.info("Cog Loaded - invites")
        for guild in self.bot.guilds:
            # Adding each guild's invites to our dict
            self.invites[guild.id] = await guild.invites()

    def cog_unload(self):
        logger.info("Cog Unloaded - invites")
    
    def find_invite_by_code(self, invite_list, code):      
            for inv in invite_list:            
                if inv.code == code:                      
                    return inv

    @commands.Cog.listener()
    async def on_member_join(self, member):
        botinvite = 0
        ban = 0
        username = ''
        general_channel = self.bot.get_channel(int(os.getenv('publicchannelmsg')))
        mod_channel = self.bot.get_channel(int(os.getenv('privatechannelmsg')))
        invites_after_join = await member.guild.invites()
        invites_before_join = self.invites[member.guild.id]

        usedinvites = list(set(set(invites_before_join).symmetric_difference(set(invites_after_join))))

        with conncreate.cursor() as cursor:
            query = "SELECT userid FROM dbo.member WHERE discorduid=?"
            cursor.execute(query, (member.id))
            for row in cursor:
                username = (row.userid)
            
        if username:
            with conncreate.cursor() as cursor:
                query = "SELECT COUNT (*) FROM dbo.T_o2jam_banishment WHERE USER_ID=?"
                ban_query = cursor.execute(query, (username))
                ban = ban_query.fetchone()[0]
       
        # if bot generated invite
        if len(usedinvites):
            invitelink = str(usedinvites[0])
            invite = invitelink.replace("https://discord.gg/","")
            with conncreate.cursor() as cursor:
                query = "SELECT COUNT (*) FROM dbo.discordinv where invlink=?"
                botinvite = cursor.execute(query, (invite)).fetchone()[0]

            # If new user
            if ban == 0:
                with conncreate.cursor() as cursor:
                    query = "UPDATE dbo.discordinv SET discorduid=? WHERE invlink=?"
                    values = (member.id, invite)
                    cursor.execute(query, values)
                    cursor.commit()
                
                ModEmbed = discord.Embed(title="{} has joined the server".format(member.name),
                            description="",
                            color=0x00ff00)
                # Mod Channel Send
                ModEmbed.add_field(name="Discord Username", value=member.name, inline=True)
                ModEmbed.add_field(name="UserID", value=member.id, inline=True)
                ModEmbed.add_field(name="Invite Code", value=invite, inline=True)                
                logger.info(f"{member.name} has joined the server. UID:{member.id} Invite Code: {invite}")
            
            # If existing user who leave the server and got banned.
            else:
                try:
                    with conncreate.cursor() as cursor:
                        removeban_query =  "DELETE FROM dbo.T_o2jam_banishment where USER_ID=?"
                        cursor.execute(removeban_query, (username.strip()))
                        cursor.commit()
                        logger.info(f"{username} has been removed from banishment table")

                        delete_invlink_query = "DELETE FROM dbo.discordinv WHERE invlink=?"
                        cursor.execute(delete_invlink_query ,(invite))
                        cursor.commit()
                        logger.info("[Invite Link: %s] Deleted from the Database." % (invite))
                except Exception as e:
                    logger.info(f"There's some problem deleting the invite link from the Database [{invite}]\n{e}")

                logger.info("%s re-joined the server using the Bot Generated Invite Code [User_ID: %s][Invite Code: %s]" % 
                            (member.name, username.strip(), invite))
                
                ModEmbed = discord.Embed(title="{} has joined the server".format(member.name),
                            description="Re-joined using Bot Generated Invite Link",
                            color=0x00ff00)
                ModEmbed.add_field(name="O2EZ Username", value=username.strip(), inline=True)
                ModEmbed.add_field(name="UserID", value=member.id, inline=True)
                ModEmbed.add_field(name="Invite Code", value=invite, inline=True)
                ModEmbed.set_footer(text="Account Status: UNBANNED")

        # if direct invite with many uses
        # PS: "usedinvites" randomly returns no index so this is for error handling      
        elif not len(usedinvites):
            for invite in invites_before_join:
                if invite.uses < Invites.find_invite_by_code(self, invites_after_join, invite.code).uses: 
                    #PublicembedVar = discord.Embed(title=f"{member.name} has joined the server", description="", color=0x00ff00)
                    #await general_channel.send(embed=PublicembedVar)              
                    if ban >= 1:
                        with conncreate.cursor() as cursor:
                            query = "DELETE FROM dbo.T_o2jam_banishment where USER_ID=?"
                            cursor.execute(query, (username.strip()))
                            cursor.commit()
                        
                        logger.info(f"[Username: {username.strip()} Invite Code: {invite.code}] {member.name} re-joined the server using direct invite and successfully unbanned.")
                        ModEmbed = discord.Embed(title="{} has joined the server.".format(member.name),
                            description="Re-joined using Direct Invite.",
                            color=0x00ff00)
                        ModEmbed.add_field(name="O2EZ Username", value=username.strip(), inline=True)
                        ModEmbed.add_field(name="UserID", value=member.id, inline=True)
                        ModEmbed.add_field(name="Invite Code", value=invite, inline=True)
                        ModEmbed.set_footer(text="Account Status: UNBANNED")
                        
                    else:
                        ModEmbed = discord.Embed(title="{} joined the server using DIRECT INVITE.".format(member.name),
                            description="WARNING: This user cannot register using Direct Invite Code.",
                            color=0x00ff00)
                        ModEmbed.add_field(name="Discord Username", value=member.name, inline=True)
                        ModEmbed.add_field(name="UserID", value=member.id, inline=True)
                        ModEmbed.add_field(name="DIRECT INVITE", value=invite, inline=True)
                        logger.info("{} joined the server using Direct Invite.".format(member.name))

        await mod_channel.send(embed=ModEmbed)
        self.invites[member.guild.id] = invites_after_join

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        registered = 0
        ban = 0
        unusedinvite = 0
        general_channel = self.bot.get_channel(int(os.getenv('publicchannelmsg')))
        mod_channel = self.bot.get_channel(int(os.getenv('privatechannelmsg')))

        # Check if user registered before leaving the server
        with conncreate.cursor() as cursor:
            member_query = "SELECT userid,invlink,usernick FROM dbo.member where discorduid=?"
            cursor.execute(member_query, (member.id))
            results = cursor.fetchall()
            for row in results:
                userids = (row.userid)
                invlink = (row.invlink)
                usernick = (row.usernick)
                registered =+ 1

        if registered:
            userindexid = 0
            with conncreate.cursor() as cursor:
                character_query = "SELECT USER_INDEX_ID FROM dbo.T_o2jam_charinfo where USER_ID=?"
                result = cursor.execute(character_query, (userids))
                for row in result:
                    userindexid = (row.USER_INDEX_ID)
                    
            # Ban a player when they leave the discord server
            if userindexid:
                with conncreate.cursor() as cursor:
                    ban_query = "INSERT INTO dbo.T_o2jam_banishment (USER_INDEX_ID,USER_ID,Ban_date) VALUES (?,?,CURRENT_TIMESTAMP)"
                    values = (userindexid, userids)
                    cursor.execute(ban_query, values)
                    cursor.commit()
                    logger.info(f"[username:{usernick.strip()}] has been added into banishment table")

                logger.info(f"{usernick.strip()} {member.name} has left the server")
                # Private channel message
                ModEmbed = discord.Embed(title="{} has left the server.".format(member.name),
                                    description="",
                                    color=0xff0000)
                ModEmbed.add_field(name="Username", value=userids, inline=True)
                ModEmbed.add_field(name="UserID", value=member.id, inline=True)
                ModEmbed.add_field(name="Invite Code ", value=invlink, inline=True)
                ModEmbed.set_footer(text="Account Status: BANNED")
    
            else:

                with conncreate.cursor() as cursor:
                    query = "DELETE FROM dbo.member WHERE discorduid=?;"
                    cursor.execute(query, (member.id))
                    cursor.commit()
                    logger.info(f"{member.name} userdata deleted from dbo.member since the user have not played once.")
                
                ModEmbed = discord.Embed(title="{} has left the server [Registered but never played].".format(member.name),
                                    description="Login data has been deleted from the database.",
                                    color=0xff0000)
                ModEmbed.add_field(name="Username:", value=userids, inline=True)
                ModEmbed.add_field(name="UserID:", value=member.id, inline=True)
                ModEmbed.add_field(name="Invite Code: ", value=invlink, inline=True)
                ModEmbed.set_footer(text="Account Status: DELETED")
                logger.info(f"{member.name} has left the server [Registered but never played]")
                
        # If a Player did not registered before leaving.
        else: 
            # check Invite link
            with conncreate.cursor() as cursor:
                invite_query = "SELECT invlink FROM dbo.discordinv where discorduid=?"
                cursor.execute(invite_query, (member.id))
                for row in cursor:
                    unusedinvite = (row.invlink)

            if unusedinvite:
                # Delete Invite link
                with conncreate.cursor() as cursor:
                    invite_delete_query = "DELETE FROM dbo.discordinv where discorduid=?"
                    cursor.execute(invite_delete_query, (member.id))
                    cursor.commit()
                ModEmbed = discord.Embed(title="{} has left the server and did not registered.".format(member.name),
                                    description="Unused Invite link has been deleted from databse.",
                                    color=0xff0000)
                logger.info(f"{member.name} has left the server but never registered.")  
                logger.info("Unused invite link successfully deleted!")
            else: 
                # If no Invite found
                ModEmbed = discord.Embed(title="{} has left the server.".format(member.name),
                                    description="Invite Code was not found in the database. Probably a direct invite.",
                                    color=0xff0000)
                logger.info(f"{member.name} has left the server but invite link was not found in the database! probably someone made a direct invite?")
        
        await mod_channel.send(embed=ModEmbed)
        self.invites[member.guild.id] = await member.guild.invites()

    
    # Commands

    # Creating invite link
    @app_commands.command(name="createinv", 
                          description="Create an invite link")
    @app_commands.checks.has_role(admin_role_id)
    async def createinv(self, interaction: discord.Interaction):
        await interaction.response.defer()
        RegistrationChannel = self.bot.get_channel(int(os.getenv('registrationchannel')))
        invitelink = await RegistrationChannel.create_invite(max_uses=1,unique=True)
        discordlink = invitelink.url
        invlink = discordlink.replace("https://discord.gg/","") 

        with conncreate.cursor() as cursor:
            invite_link_query = "INSERT INTO dbo.discordinv (invlink,used) VALUES (?,'False')"
            cursor.execute(invite_link_query, (invlink))
            cursor.commit()
        
        sender = interaction.user.name
        logger.info('[%s] has created an invite link: %s' % (sender,invitelink.url))
        await interaction.followup.send(invitelink)
        self.invites[interaction.guild.id] = await interaction.guild.invites()
        
    @app_commands.command(name="deleteinv", 
                          description="Delete an invite link")
    @app_commands.checks.has_role(admin_role_id)
    async def deleteinv(self, interaction: discord.Interaction):
        await interaction.response.defer()
        invlink = invlink.replace("https://discord.gg/","")
        with conncreate.cursor() as cursor:
            query = "SELECT invlink FROM dbo.discordinv WHERE invlink=?"
            result = cursor.execute(query, (invlink))
            invitelink = result.fetchone()

        if invitelink:     
            embed=discord.Embed(title="Invite Code found: `%s`" % invlink, description="Deleted Successfully!", color=0xff0000)
            with conncreate.cursor() as cursor:
                delete_query = "DELETE FROM dbo.discordinv WHERE invlink=?"
                cursor.execute(delete_query, (invlink))
                cursor.commit()
            sender = interaction.user.name
            logger.info("[%s] DELETED Invite Code: %s" %(sender, invlink))      
            await interaction.followup.send(embed=embed)
            await self.bot.delete_invite(invlink)
            self.invites[interaction.guild.id] = await interaction.guild.invites()
        else:
            await interaction.followup.send("Invite code not Found")

    @app_commands.command(name="deleteallinv", 
                          description="Deletes all unused invite link.")
    @app_commands.checks.has_role(admin_role_id)
    async def deleteallinv(self, interaction: discord.Interaction):
        await interaction.response.defer()
        invlink = ()  
        with conncreate.cursor() as cursor:
            query = "SELECT * FROM dbo.discordinv"
            cursor.execute(query)
            invlink = cursor.fetchall()

        if invlink: 
            x = 0
            while x < len(invlink):
                with conncreate.cursor() as cursor:
                    delete_query = "DELETE FROM dbo.discordinv WHERE invlink=?"
                    cursor.execute(delete_query, (invlink[x][1]))
                    cursor.commit()
                    logger.info(f"[{invlink[x][1]}] : Invite Code Delete from Database.")   
                try:
                    await self.bot.delete_invite(invlink[x][1])
                except discord.NotFound:
                    logger.info(f"[{invlink[x][1]}] : Not Found in Guild Invites.")
                x += 1
            await interaction.followup.send("%s Records Deleted" % x)
            logger.info(f"{x} Records Deleted")
        else:
            await interaction.followup.send("No unused Invite link found!")        
        self.invites[interaction.guild.id] = await interaction.guild.invites() 

async def setup(bot: commands.Bot):
    await bot.add_cog(Invites(bot))
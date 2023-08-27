import discord
import os
import subprocess
import pyodbc
import utils.logsconfig as logsconfig
import datetime
import asyncio
import pathlib

from discord.ext import commands 
from discord import app_commands
from discord.app_commands import AppCommandError

logger = logsconfig.logging.getLogger("bot")

conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
( os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS') ) )

admin_role_id = int(os.getenv('adminroleid'))

class admin(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        
    def cog_load(self):
        tree = self.bot.tree
        tree.on_error = self.on_app_command_error
        logger.info("Cog Loaded - admin")

    def cog_unload(self):
        tree = self.bot.tree
        tree.on_error = tree.__class__.on_error
        logger.info("Cog Unloaded - admin")
    
    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: AppCommandError
    ):
        logger.info(error)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: AppCommandError):
        if isinstance(error, (app_commands.errors.MissingRole, app_commands.MissingAnyRole)):
            logger.info(f"{interaction.user.name} don't have the required role for this command.")
            await interaction.response.send_message("You don't have the required role for this command.", ephemeral=True)
        else:
            logger.info(error)


    @app_commands.command(name="helpadmin", description="Send list of available admin commands")
    @app_commands.checks.has_role(admin_role_id)
    async def helpadmin(self, interaction: discord.Interaction) -> None:
        command_list = """
        `/helpadmin` - Shows this message.
        `/startserver` - Start the O2Jam Server.
        `/stopserver`  - Stop the O2Jam Server. 
        `/createinv` - Create an invite link.
        `/deleteinv [Invite Link/Code]`  - Deletes an invite link.
        `/deleteallinv` - Deletes all unused invite link.
        `/syncnames`  - Sync players name to their discord.
        `/syncban` - Run a ban checker if the users is not in the server anymore.
        `/relinkdiscord [Member] [IGN]`  - Link user to his current discorduid.
        `/relinkinvite [Invite Link/Code] [Discorduid]` - Link discorduid and invite code.
        `/reloadcog [cog]` - Reload Discord Bot Cogs.
        `/forcergistration` - Force Registration of member if something goes wrong.
        `/unstuckall` - Unstuck everyone.
        """
        embed = discord.Embed(title="List of Available Admin Commands",
                              description=command_list,
                              color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)


    @app_commands.command(name="changeign", description="Sends a detailed user profile")
    @app_commands.checks.has_role(admin_role_id)
    async def changeign(self, interaction: discord.Interaction, member: discord.Member, new_ign: str):
        await interaction.response.defer()
        discorduid = member.id
        with conncreate.cursor() as cursor:
            query = "SELECT usernick FROM dbo.member WHERE discorduid=?"
            old_ign = cursor.execute(query, (discorduid)).fetchone()[0]

        if old_ign:
            with conncreate.cursor() as cursor:
                query = "UPDATE dbo.member SET usernick=? WHERE discorduid=?"
                cursor.execute(query, (new_ign ,discorduid))
                cursor.commit()
                query = "UPDATE dbo.T_o2jam_charinfo SET USER_NICKNAME=? WHERE USER_NICKNAME=?"
                cursor.execute(query, (new_ign , old_ign))
                cursor.commit()
            await member.edit(nick=new_ign)
            await asyncio.sleep(3)
            await interaction.followup.send(f"IGN Successfully Changed. [`{old_ign}`] -> `[{new_ign}]`")
        else:    
            await interaction.followup.send(f"Cannot find user.")


    @app_commands.command(name="reloadcog", 
                          description="Reload Discord Bot Cogs.")
    @app_commands.checks.has_role(admin_role_id)
    @app_commands.choices(cogs=[
        app_commands.Choice(name="admin", value="cogs.admin"),
        app_commands.Choice(name="recentlyplayed", value="cogs.recentlyplayed"),
        app_commands.Choice(name="usercmds", value="cogs.usercmds"),
        app_commands.Choice(name="registration", value="cogs.registration"),
        app_commands.Choice(name="invites", value="cogs.invites"),
        app_commands.Choice(name="activity", value="cogs.activity")
        ])
    async def reloadcog(self, 
                        interaction: discord.Interaction, 
                        cogs: app_commands.Choice[str]):
        try:
            await self.bot.reload_extension(name=cogs.value)
            await interaction.response.send_message(f"`{cogs.name}` Reloaded")
        except Exception as e:
            logger.info(e)
            await interaction.response.send_message(e)        

    # Sync player names
    @app_commands.command(name="syncnames", 
                          description="Sync Disord Names to their In-Game Name")
    @app_commands.checks.has_role(admin_role_id)
    async def syncnames(self, interaction: discord.Interaction):
        await interaction.response.defer()
        syncnames_count = 0
        all_members = interaction.guild.members 
        admin_id = discord.utils.get(interaction.guild.roles, id=admin_role_id)
        for member in all_members:
            with conncreate.cursor() as cursor:
                name = None
                query = "SELECT usernick FROM dbo.member WHERE discorduid=?"
                cursor.execute(query,(member.id))
                for row in cursor:
                    name = str.strip(row.usernick)
            if member.bot:
                logger.info((f"{member.name} is a bot. Skipping..."))
                continue
            if name:          
                if admin_id in member.roles:
                    logger.info(f'{member.name} is Admin, Skipping...')
                    continue
                else:
                    if member.global_name != name:
                        await member.edit(nick=name)
                        logger.info(f"{member.global_name} Changed into {name}")
                        syncnames_count =+ 1
                    
            else:
                await member.edit(nick="UNREGISTERED")
                logger.info(f"{member.name} {member.id} Not yet registered")
        else:
            await interaction.followup.send(f"{syncnames_count} Total Names Synced. Total Members: {len(all_members)}")

    @app_commands.command(name="syncban", 
                          description="Run a ban checker if the user is not in the server anymore.")
    @app_commands.checks.has_role(admin_role_id)
    async def syncban(self, interaction: discord.Interaction):
        await interaction.response.defer()
        bancount = 0
        
        with conncreate.cursor() as cursor:
            query = "SELECT discorduid FROM dbo.member"
            result = cursor.execute(query).fetchall()
            discorduid = [row[0] for row in result]
        for discord_id in discorduid:
            if discord_id is None: continue
            username = None
            user_index = None
            if interaction.guild.get_member(int(discord_id)) is None:
                currently_banned = False               
                with conncreate.cursor() as cursor:
                    query = "SELECT userid FROM dbo.member WHERE discorduid=?"
                    cursor.execute(query, int(discord_id))
                    for row in cursor:
                        username = row[0].strip()
                    if username is None:
                        logger.info(f"{discord_id} not found in the database.")
                        continue

                    query = "SELECT USER_INDEX_ID FROM dbo.T_o2jam_charinfo WHERE USER_ID=?"
                    cursor.execute(query, (username))
                    for row in cursor:
                        user_index = row[0]

                    if user_index is None:
                        with conncreate.cursor() as cursor:
                            query = "DELETE FROM dbo.member WHERE discorduid=?;"
                            cursor.execute(query, (discord_id))
                            cursor.commit()
                            logger.info(f"{username} Deleted from dbo.member since the user have not played once.")
                            continue

                    # Check if Currently Banned
                    query = "SELECT * FROM dbo.T_o2jam_banishment WHERE USER_INDEX_ID=?"
                    result = cursor.execute(query, user_index)
                    for row in result:
                        currently_banned = True

                if currently_banned == False:
                    with conncreate.cursor() as cursor:
                        ban_query = "INSERT INTO dbo.T_o2jam_banishment (USER_INDEX_ID,USER_ID,Ban_date) VALUES (?,?,CURRENT_TIMESTAMP)"
                        cursor.execute(ban_query, (user_index, username))
                        cursor.commit()
                    logger.info(f"[{username.strip()}] has been added into banishment table.")
                    bancount += 1
                else:
                    continue
        else:
            with conncreate.cursor() as cursor:
                query = "SELECT USER_INDEX_ID, USER_ID, Ban_date FROM dbo.T_o2jam_banishment"
                result = cursor.execute(query).fetchall()
                ban_list = [row for row in result]
                logger.info(f"Ban List: {ban_list}")

            await interaction.followup.send(f"`{bancount}` Total New Banned Players. \n`{len(ban_list)}` Total Banned Players.\n check `/logs` for details.")
            

    @app_commands.command(name="relinkdiscord", description="Relink O2JAM Account discordUID")
    @app_commands.checks.has_role(admin_role_id)
    async def relinkdiscord(self, interaction: discord.Interaction, member: discord.Member, ign: str):
        user = None
        await interaction.response.defer()
        with conncreate.cursor() as cursor:
            query = "SELECT usernick FROM dbo.member WHERE usernick=?"
            cursor.execute(query, (ign))
            for row in cursor:
                user = (row.usernick)
        if user:
            with conncreate.cursor() as cursor:
                cursor.execute("UPDATE dbo.member SET discorduid=? WHERE usernick=?", member.id, user.strip())
                cursor.commit()
            logger.info("Updated [%s] account [IGN: %s]" % (member.name, user.strip()))
            await interaction.followup.send("Updated [%s] account [IGN: %s]" % (member.name, user.strip()))
        else: 
            await interaction.followup.send("IGN not found!")

    @app_commands.command(name="relinkinvite", description="Relink DiscordUID and Invites.")
    @app_commands.checks.has_role(admin_role_id)
    async def relinkinvite(self, interaction: discord.Interaction, member: discord.Member, invlink: str):
        await interaction.response.defer()
        invitelink = invlink.replace("https://discord.gg/","")
        valid_invitelink = False
        with conncreate.cursor() as cursor:
            query = "SELECT invlink FROM dbo.discordinv WHERE invlink=?"
            cursor.execute(query, (invitelink))
            for row in cursor:
                invitelink = (row.invlink)
                valid_invitelink = True
            if valid_invitelink:
                cursor.execute("UPDATE dbo.discordinv SET discorduid=?,used='True' WHERE invlink=?", member.id, invitelink)
                cursor.commit()
                logger.info("Relink Invite:[%s] = DiscordUID [%s]" % (invitelink, member.name))
                await interaction.followup.send("Successfully relinked discord invite `%s` to user <@%s>" % (invitelink, member.id))
            else: 
                await interaction.followup.send("Invite Code not found!")


    @app_commands.command(name='forceregistration', 
                          description='Force Registration of member if something goes wrong.')
    @app_commands.checks.has_role(admin_role_id)
    async def forceregistration(self, interaction: discord.Interaction, 
                                member: discord.Member, 
                                username: str, 
                                password: str,
                                ign: str, 
                                invlink: str):
        await interaction.response.defer()
        
        mod_channel = interaction.guild.get_channel(int(os.getenv("privatechannelmsg")))
        general_channel = interaction.guild.get_channel(int(os.getenv("publicchannelmsg")))
        member_role = discord.utils.get(interaction.guild.roles, name="Member")   
        invite_code = invlink.replace("https://discord.gg/","")

        # Check Invite Link if valid
        with conncreate.cursor() as cursor:
            sql = """SELECT * FROM dbo.discordinv WHERE invlink=?"""
            cursor.execute(sql , (invite_code))
            row = cursor.fetchone()
            if row is None:
                interaction.followup.send(f"Invalid Invite Link. `{invite_code}`")
                return

        # Check if discordid is already linked
        with conncreate.cursor() as cursor:
            sql = """SELECT * FROM dbo.member WHERE discorduid=?"""
            row = cursor.execute(sql , (member.id)).fetchone()
            if row is not None:
                interaction.followup.send(f"Discord Account already linked to an existing O2JAM Account. `{row}`")
                return

        try:
            with conncreate.cursor() as cursor:
                query = """INSERT INTO dbo.member 
                (userid, usernick, sex, passwd, registdate, id9you, discorduid, invlink)
                VALUES
                (?,?,'True',?,CURRENT_TIMESTAMP, '-1', ?, ?)"""
                query_values = (username, ign, password, member.id,invlink)
                cursor.execute(query, query_values)
                cursor.commit()
                cursor.execute("SELECT @@IDENTITY AS id")
                row = cursor.fetchone()
                getid = int(row[0])
                sql = "DELETE FROM dbo.discordinv WHERE invlink=?"
                cursor.execute(sql, (invite_code))
                cursor.commit()
                logger.info(f"Registered - ID:[{getid}]{username} / {ign} [{member.id}: {invite_code}] ")
            await interaction.followup.send(f"**{member.mention} Successfully Registered!**\nIn 30 seconds, you will be given a member role and access to the server.\nPlease take a moment to read the rules and follow them. We want to keep this place friendly and fun for everyone.\n\nWe hope you enjoy your stay here.")
            await asyncio.sleep(30)
           
            await member.add_roles(member_role)
            await member.edit(nick=ign)
            await general_channel.send(f"""Welcome to O2EZ! {member.mention}

Please take a moment to read the rules and follow them. We want to keep this place friendly and fun for everyone. 
We hope you enjoy your stay here.""" )

            embed = discord.Embed(title=f"New User: {member.name}",
                              description="DEBUG",
                              color=discord.Color.green())
            embed.add_field(name="ID", value=getid, inline=True)
            embed.add_field(name="Username", value=username, inline=True)
            embed.add_field(name="IGN", value=ign, inline=True)
            embed.add_field(name="Invite", value=invite_code, inline=True)
            embed.add_field(name="DiscordID", value=member.id, inline=True)
            embed.set_author(name="Member Registration")
            await mod_channel.send(embed=embed)
        except Exception as e: 
            logger.info(f"Force Registration Failed!\n{e}")
            await interaction.followup.send(f"Force Registration Failed!\n{e}")



    @app_commands.command(name='startserver', description='Start O2Jam Server.')
    @app_commands.checks.has_role(admin_role_id)
    async def startserver(self, interaction: discord.Interaction):
        await interaction.response.defer()
        server_path = pathlib.Path(os.getenv('SERVER_PATH'))
        start_path = server_path / "Start Server.bat"
        process = await asyncio.create_subprocess_exec(str(start_path), cwd=str(server_path))
        await process.communicate()
        logger.info(f"[{interaction.user.name}] has started the server.")
        await interaction.followup.send("`O2JAM Server` Started!")

    @app_commands.command(name='stopserver', description='Stop O2Jam Server.')
    @app_commands.checks.has_role(admin_role_id)
    async def stopserver(self, interaction: discord.Interaction):
        await interaction.response.defer()
        server_path = pathlib.Path(os.getenv('SERVER_PATH'))
        close_path = server_path / "Stop Server.bat"
        process = await asyncio.create_subprocess_exec(str(close_path), cwd=str(server_path))
        await process.communicate()
        logger.info(f"[{interaction.user.name}] has stopped the server")
        await interaction.followup.send("`O2JAM Server` Closed!")

    @app_commands.command(name='logs', description='Send Bot log file.')
    @app_commands.checks.has_role(admin_role_id)
    async def logs(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.followup.send(file=discord.File("logs/infos.log"))

    @app_commands.command(name='unstuckall', description='Unstuck Everyone.')
    @app_commands.checks.has_role(admin_role_id)
    async def unstuckall(self, interaction: discord.Interaction):
        await interaction.response.defer()
        with conncreate.cursor() as cursor:
            query = "SELECT COUNT (*) FROM dbo.T_o2jam_login"
            count = cursor.execute(query).fetchone()[0]
            if count > 0: 
                query = "DELETE FROM dbo.T_o2jam_login"
                cursor.execute(query)
                cursor.commit()
                logger.info(f"{count} Total Unstucked.")
                await interaction.followup.send(f"{count} Total Unstucked.")
            else:
                await interaction.followup.send("No one is currently stucked.")

async def setup(bot):
    await bot.add_cog(admin(bot))
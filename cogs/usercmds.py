from typing import Optional
import discord
import os
import asyncio
import pyodbc
import datetime

import utils.logsconfig as logsconfig
import utils.paginator as paginator

from discord.ext import commands
from discord import app_commands
from discord.app_commands import AppCommandError

import core.sendscore as sendscore

intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

member_role_id = int(os.getenv('memberroleid'))
logger = logsconfig.logging.getLogger("bot")

conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
( os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS') ) )

class Profile(discord.ui.View):
    def __init__(self, *, timeout: float | None = 180):
        super().__init__(timeout=timeout)
        self.default_embed = None
        self.usernick = None
        self.user_id = None
        self.mentioned_user = None
        
    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)

    @discord.ui.button(label='Profile', style=discord.ButtonStyle.gray)
    async def profile_default(self, interaction: discord.Interaction, button: discord.ui.Button): 
        await interaction.response.defer()
        await asyncio.sleep(1)
        await interaction.edit_original_response(embed=self.default_embed)
        self.message = await interaction.original_response()

    # Top Played

    @discord.ui.button(label='Top Played', style=discord.ButtonStyle.green)
    async def top_played(self, interaction: discord.Interaction, button: discord.ui.Button):   
        with conncreate.cursor() as cursor:
            query = """
                SELECT TOP 10
                user_highscores.*,
                songlist.chart_name,
                songlist.charter,
                songlist.chart_artist,
                    CASE 
                        WHEN user_highscores.chart_difficulty = 0 THEN songlist.easy_level
                        WHEN user_highscores.chart_difficulty = 1 THEN songlist.normal_level
                        WHEN user_highscores.chart_difficulty = 2 THEN songlist.hard_level
                    END AS song_level
                FROM user_highscores
                JOIN songlist ON user_highscores.chart_id = songlist.chart_id
                WHERE user_highscores.id = ?
                AND user_highscores.song_clear = 'True'
                AND user_highscores.chart_difficulty  = 2
                ORDER BY song_level DESC;
                """
            cursor.execute(query, (self.user_id))
            rows = [list(row) for row in cursor.fetchall()]
            
        embed = discord.Embed(title=f"{self.usernick} - Top 10 Plays",
                                description=" ",
                                color=discord.Color.green())
        embed.set_author(name=f"{self.mentioned_user.display_name} Profile", icon_url=self.mentioned_user.avatar)
        count = 1
        if not rows:
            embed.add_field(name=f"No Top Played found in the database",
                            value="Try clearing some songs.",
                            inline=True)
        else:
            for score_row in rows:
                embed.add_field(name=f"{count}. [Lv. {score_row[19]}] {score_row[16]} - {score_row[18]} \nChart By: {score_row[17]}", 
                                value=f"Score: `{score_row[12]}` Acc: `{round(score_row[13],2)}` (`{score_row[5]}`/`{score_row[6]}`/`{score_row[7]}`/`{score_row[8]}`) (Combo: `x{score_row[9]}`)", 
                                inline=False)
                count += 1
        embed.set_thumbnail(url=self.mentioned_user.avatar)
        await interaction.response.defer()
        await asyncio.sleep(1)
        await interaction.edit_original_response(embed=embed)
        self.message = await interaction.original_response()
    # Recently Played

    @discord.ui.button(label='Recently Played', style=discord.ButtonStyle.blurple)
    async def recently_played(self, interaction: discord.Interaction, button: discord.ui.Button):
        with conncreate.cursor() as cursor:
            query = "SELECT TOP 10 * from userscores WHERE id=? ORDER BY date_verified DESC"
            cursor.execute(query, (self.user_id))
            rows = [list(row) for row in cursor.fetchall()]

        embed = discord.Embed(title=f"{self.usernick} - Recently Played",
                              description=" ",
                              color=discord.Color.green())
        embed.set_author(name=f"{self.mentioned_user.display_name} Profile", icon_url=self.mentioned_user.avatar)
        count = 1
        if not rows:
            embed.add_field(name=f"No Recently Played found in the database",
                            value="Play one song.",
                            inline=True)
        else:
            for score_row in rows:
                if score_row[18]:
                    embed.add_field(name=f"[Cleared][Lv. {score_row[8]}] {score_row[5]} - {score_row[6]}", 
                                    value=f"Score: `{score_row[16]}` Acc: `{round(score_row[17],2)}` (`{score_row[9]}`/`{score_row[10]}`/`{score_row[11]}`/`{score_row[12]}`) (Combo: `x{score_row[13]}`)", 
                                    inline=False)
                else:
                    embed.add_field(name=f"[Failed][Lv. {score_row[8]}] {score_row[5]} - {score_row[6]}", 
                                    value=f"Score: `{score_row[16]}` Acc: `{round(score_row[17],2)}` (`{score_row[9]}`/`{score_row[10]}`/`{score_row[11]}`/`{score_row[12]}`) (Combo: `x{score_row[13]}`)", 
                                    inline=False)
                count += 1
        embed.set_thumbnail(url=self.mentioned_user.avatar)
        await interaction.response.defer()
        await asyncio.sleep(1)
        await interaction.edit_original_response(embed=embed)
        self.message = await interaction.original_response()


class Change_Password(discord.ui.Modal, title="Account Change Password"):
    old_password = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Current Password",
        min_length=6,
        max_length=16,
        required=True,
        placeholder="Enter your Current Password"
    )
    new_password = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="New Password",
        min_length=6,
        max_length=16,
        required=True,
        placeholder="Enter your New Password"
    )
    confirm_password = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Confirm Password",
        min_length=6,
        max_length=16,
        required=True,
        placeholder="Confirm your Password"
    )
    async def on_submit(self, interaction: discord.Interaction):
        with conncreate.cursor() as cursor:
            query = "SELECT passwd FROM dbo.member WHERE discorduid=?"
            cursor.execute(query, (interaction.user.id))
            for row in cursor:
                old_password = str.strip(row.passwd)
        if old_password != self.old_password.value:
            raise ValueError("wrong_pass")
        if self.new_password.value != self.confirm_password.value:
            raise ValueError("pass_not_matched")
        if " " in self.new_password.value:
            raise ValueError("invalid_text_format")
        
        with conncreate.cursor() as cursor:
            query = """UPDATE dbo.member 
                    SET passwd=? 
                    WHERE discorduid=?"""
            cursor.execute(query, (self.new_password.value, interaction.user.id))
            cursor.commit()
        await interaction.response.send_message("Your password has been successfully updated.", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error : Exception):
        mod_channel = int(os.getenv('privatechannelmsg'))
        if isinstance(error, ValueError):
            error_messages = {
                'wrong_pass': "Your current password is incorrect. Please try again.",
                'pass_not_matched': "The passwords you entered do not match. Please double-check your passwords and try again.",
                'invalid_text_format' : 'Please remove any spaces from any of the textbox and try again.\nSpaces are not allowed because they can cause errors and security issues.'
            }
            error_msg = error_messages.get(str(error), "We encountered an error while processing your request. Please try again later.")
            await interaction.response.send_message(error_msg, ephemeral=True)
          
            with conncreate.cursor() as cursor:
                query = """SELECT * FROM dbo.member WHERE discorduid=?"""
                cursor.execute(query, (interaction.user.id))
                for row in cursor:
                    username = row.userid
                    usernick = row.usernick
                    old_password = row.passwd 
            logger.info(error)
            embed = discord.Embed(title=f"{str(type(error))}",
                              description="Error",
                              color=discord.Color.red())
            embed.set_author(name="Change Password Error Report")
            embed.add_field(name="Username", value=username, inline=True)
            embed.add_field(name="IGN", value=usernick, inline=True)
            embed.add_field(name="Current Password", value=old_password, inline=True)
            embed.add_field(name="UserInput: Old_Password", value=self.old_password.value, inline=True)
            embed.add_field(name="UserInput: New_password", value=self.new_password.value, inline=True)
            embed.add_field(name="UserInput: Conf_password", value=self.confirm_password.value, inline=True)
            await mod_channel.send(embed=embed)
            
            logger.error(error)
            logger.info(type(error), error, error.__traceback__)

class usercmds(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        
    def cog_load(self):
        tree = self.bot.tree
        tree.on_error = self.on_app_command_error
        logger.info("Cog Loaded - usercmds")

    def cog_unload(self):
        tree = self.bot.tree
        tree.on_error = tree.__class__.on_error
        logger.info("Cog Unloaded - usercmds")

    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: AppCommandError
    ):
        pass

    def cooldown_for_everyone_but_me(interaction: discord.Interaction) -> Optional[app_commands.Cooldown]:
        admin_role_id = int(os.getenv('adminroleid'))
        for role in interaction.user.roles:
            if role.id == admin_role_id:
                return None
        return app_commands.Cooldown(1, 60.0)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: AppCommandError):
        if isinstance(error, (app_commands.errors.MissingRole, app_commands.MissingAnyRole)):
            logger.info(f"{interaction.user.name} don't have the required role for this command.")
            await interaction.response.send_message("You don't have the required role for this command.", ephemeral=True)
        else:
            logger.info(error)

    @app_commands.checks.has_role(member_role_id)
    @app_commands.checks.dynamic_cooldown(cooldown_for_everyone_but_me)
    @app_commands.command(name="help", description='Get help about the bot.')
    async def help(self, interaction: discord.Interaction) -> None:
        command_list = """
        `/online` - Check who is playing on the server.
        `/profile` - Display user data, recently plays, and top plays.
        `/unstuck` -  Try this command if can't get enter Channel Selection.
        `/changepassword` - Change your account password.
        `/leaderboard` -  Check server leaderboards.
        `/accountdetails` - Take a look on your account information.
        """
        embed = discord.Embed(title="List of Available User Commands",
                                description=command_list,
                                color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)


    @app_commands.checks.has_role(member_role_id)
    @app_commands.checks.dynamic_cooldown(cooldown_for_everyone_but_me)
    @app_commands.command(name="changepassword", description='Change your account password.')
    async def changepassword(self, interaction: discord.Interaction) -> None:
        changepass_modal = Change_Password()
        changepass_modal.user = interaction.user
        await interaction.response.send_modal(changepass_modal)


    @app_commands.checks.has_role(member_role_id)
    @app_commands.checks.dynamic_cooldown(cooldown_for_everyone_but_me)
    @app_commands.command(name="online", description='Check who is playing on the server.')
    async def online(self, interaction: discord.Interaction):
        await interaction.response.defer()
        results = []
        with conncreate.cursor() as cursor:
            query = "SELECT SUB_CH, USER_INDEX_ID, USER_ID FROM dbo.T_o2jam_login"
            cursor.execute(query)
            results = cursor.fetchall()

        online_user = []
        with conncreate.cursor() as cursor:
            for row in results:
                query = "SELECT USER_NICKNAME FROM dbo.T_o2jam_charinfo WHERE USER_INDEX_ID=?"
                cursor.execute(query, (row[1],))
                ign = cursor.fetchone()[0]
                if row[0] == 0:
                    online_user.append(f"CH1 - {ign}")
                else:
                    online_user.append(f"CH2 - {ign}")

        online_user.sort()

        if len(online_user) > 0:
            view = paginator.StaticPaginator(
                online_user,
                line_limit=15,
                base_embed=discord.Embed(title="Online Users", color=0xB00B69,)
            )
            embs = view.get_page(1)
            await interaction.followup.send(embeds=embs, view=view, ephemeral=True)
        else:         
            page = discord.Embed (title = " ", description = "No one is online.", color=0x00ffff)
            await interaction.followup.send(embed=page, ephemeral=True)

    @app_commands.checks.has_role(member_role_id)
    @app_commands.checks.dynamic_cooldown(cooldown_for_everyone_but_me)
    @app_commands.command(name="unstuck", description="Try this command if can't get enter Channel Selection")
    async def unstuck(self, interaction: discord.Interaction):
        await interaction.response.defer()
        discorduid = interaction.user.id
        stucked = False
        userids = None
        #check if user is registered
        with conncreate.cursor() as cursor:
            query = "SELECT userid FROM dbo.member WHERE discorduid=?"
            cursor.execute(query, (discorduid))
            for row in cursor:
                userids = str.strip(row.userid)
        if userids:
            with conncreate.cursor() as cursor:
                query = "SELECT USER_ID FROM dbo.T_o2jam_login WHERE USER_ID=?"
                stucked = cursor.execute(query, (userids,)).fetchone()    
            if stucked:
                with conncreate.cursor() as cursor:
                    query = "DELETE FROM dbo.T_o2jam_login WHERE USER_ID=?"
                    cursor.execute(query, (userids))
                    cursor.commit()
                sender = interaction.user
                logger.info('[%s] Unstuck ID: [%s]' % (sender ,userids))
                await interaction.followup.send('[%s] Successfully unstucked!' % (userids), ephemeral=True)
            else:
                await interaction.followup.send('Your account is not stuck.', ephemeral=True)
        else:
            await interaction.followup.send('Username not found!')
        
    @app_commands.command(name="profile", description="Sends a detailed user profile")
    @app_commands.checks.dynamic_cooldown(cooldown_for_everyone_but_me)
    @app_commands.checks.has_role(member_role_id)
    async def profile(self, interaction: discord.Interaction, member: discord.Member=None):
        await interaction.response.defer(thinking=True)
        view = Profile(timeout=60.0)
        onlinestatus = 0

        # if user is not mentioned
        if not member:
            member = interaction.user
            view.mentioned_user = interaction.user
        else:
            view.mentioned_user = member

        discorduid = member.id
        #check if user/sender is registered 
        with conncreate.cursor() as cursor:
            query = "SELECT usernick FROM dbo.member where discorduid=?"
            cursor.execute(query, (discorduid))
            for row in cursor:
                view.usernick = str.strip(row[0])
            if row is None:
                await interaction.followup.send("Userdata not found in database. Missing: Discord ID.")
                return           
          
        if view.usernick:
            with conncreate.cursor() as cursor:
                query = "SELECT USER_INDEX_ID, Level, Battle, Experience FROM dbo.T_o2jam_charinfo where USER_NICKNAME=?"
                result = cursor.execute(query, (view.usernick))
                for row in result:
                    view.user_id = row[0]
                    level = row[1]
                    PlayCount = row[2]
                    Exp = row[3]

            #check if user/sender profile data exists
            if view.user_id:
                with conncreate.cursor() as cursor:
                    query = "SELECT registdate FROM dbo.member where discorduid=?"
                    register_date = cursor.execute (query, (discorduid)).fetchone()[0]
                dateformat ='%Y-%m-%d %H:%M:%S.%f'
                datejoined = datetime.datetime.strptime(str(register_date),dateformat)
                profile = discord.Embed (title = " ", description = " ", color=0x00ffff)
                
                profile.set_author(name=f"{member.global_name} Profile", icon_url=member.avatar)
                profile.set_thumbnail(url=member.avatar)
                profile.add_field(name="ID", value="%s" % (view.user_id), inline=True)
                profile.add_field(name="In-Game Name", value="%s" % (view.usernick), inline=True)
                profile.add_field(name="Level", value="%s" % (level), inline=True)
                profile.add_field(name="Playcount", value="%s" % (PlayCount), inline=True)
                profile.add_field(name="Experience", value="%s" % (Exp), inline=True)
                profile.add_field(name="Date Joined", value="%s" % (datejoined.strftime("%B %d %Y")), inline=True)
                
                with conncreate.cursor() as cursor:
                    query = "SELECT USER_INDEX_ID FROM dbo.T_o2jam_login WHERE USER_INDEX_ID=?"
                    onlinestatus = cursor.execute(query,  (view.user_id)).fetchone()
                if onlinestatus:
                    profile.set_footer(text="🟢 Online")
                else: 
                    profile.set_footer(text="🔴 Offline")
                
                await asyncio.sleep(3)
                view.default_embed = profile         
                await interaction.followup.send(embed=profile, view=view)
                view.message = await interaction.original_response()
                logger.info(f"{interaction.user.global_name} used a profile command.")
            else: 
                await interaction.followup.send("You cannot generate a profile yet. You need to play at least one game before you can create your profile.")
        else: 
            await interaction.followup.send("User not yet Registered!")

    @app_commands.command(name="leaderboard", description="Check server leaderboards.")
    @app_commands.checks.dynamic_cooldown(cooldown_for_everyone_but_me)
    @app_commands.checks.has_role(member_role_id)
    async def leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer()
        logger.info(f"{interaction.user.name} used a command leaderboard.")
        discorduid = interaction.user.id
        with conncreate.cursor() as cursor:
            query = """SELECT usernick FROM dbo.member WHERE discorduid=?"""
            cursor.execute(query, (discorduid))
            for row in cursor:
                ign = (row.usernick)
        with conncreate.cursor() as cursor:
            query = """SELECT rank
                    FROM (
                        SELECT USER_INDEX_ID, USER_NICKNAME, Battle, RANK() OVER (ORDER BY battle DESC) as rank
                        FROM dbo.T_o2jam_charinfo
                    ) t
                    WHERE USER_NICKNAME = ?"""
            cursor.execute(query, (ign))
            for row in cursor:
                player_rank = (row.rank)
            query = """ SELECT TOP 10 * FROM dbo.T_o2jam_charinfo ORDER BY Battle DESC;"""
            cursor.execute(query)
            char_rows = [list(row) for row in cursor.fetchall()]
        embed = discord.Embed(title="O2EZ Leaderboard", description=f"Your Rank: {player_rank}" ,color=0x00ffff)
        count = 1
        for row in char_rows:
            embed.add_field(name=f"{count}. {row[2]}", value=f"Playcount: {row[5]}", inline=False)
            count += 1
        await interaction.followup.send(embed=embed)

    @commands.command()
    @commands.has_role(member_role_id)
    async def score(self, ctx, scoreid: int):
        async with ctx.typing():
            channel = ctx.channel.id
            await sendscore.SendScore.send_score(self, channel, scoreid)

    @app_commands.command(name="accountdetails", description="Take a look at your account information.")
    @app_commands.checks.has_role(member_role_id)
    @app_commands.checks.dynamic_cooldown(cooldown_for_everyone_but_me)
    async def accountdetails(self, interaction: discord.Interaction):
        #await interaction.response.defer()
        discorduid = interaction.user.id
        with conncreate.cursor() as cursor:
            query = "SELECT usernick,userid,passwd from dbo.member where discorduid=?"
            cursor.execute(query, (discorduid))
            for row in cursor:
                username = str(row.userid)
                password = str(row.passwd)
        if username:
            logger.info(f"{interaction.user.global_name} asked for their account details.")
            await interaction.response.send_message(f"\nThis message will be deleted in 30 seconds.\n```username: {username} \npassword: {password}```", ephemeral=True, delete_after=30)
        else:
            logger.info(f"{interaction.user.global_name} Error: User not Found.")
            await interaction.response.send_message(f"{interaction.user.name} Error: User not Found.", ephemeral=True)


# Error handling

    @commands.Cog.listener()
    async def  on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            msg = await ctx.send("We have migrated all commands into Slash`(/)` Commands.\nType `/help` to send the list of available commands.")
            await msg.delete(delay=30)

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.errors.CommandOnCooldown):
            await interaction.response.send_message(f"Slow down! Try again in {round(error.retry_after)} seconds.", ephemeral=True, delete_after=8.0)


async def setup(bot):
    await bot.add_cog(usercmds(bot))
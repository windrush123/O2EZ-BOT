import discord
import pyodbc
import utils.logsconfig as logsconfig

import datetime
from discord import app_commands
from discord.app_commands import AppCommandError
from discord.ext import commands

import os
from dotenv import load_dotenv

load_dotenv()

logger = logsconfig.logging.getLogger("bot")

conncreate = pyodbc.connect('driver={%s};server=%s;database=%s;uid=%s;pwd=%s' % 
( os.getenv('DRIVER'), os.getenv('SERVER'), os.getenv('DATABASE'), os.getenv('UID'), os.getenv('PASS') ) )

intents = discord.Intents.default()
intents.message_content = True

guildid = discord.Object(id=(os.getenv('guildid')))


class registration_button(discord.ui.View):
    @discord.ui.button(label="Register", style=discord.ButtonStyle.green)
    async def button_callback(self, interaction: discord.Interaction, button):
        register_modal = registration_form()
        register_modal.user = interaction.user
        await interaction.response.send_modal(register_modal)

class registration_form(discord.ui.Modal, title="O2EZ Registration Form"):
    username = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="username",
        min_length=6,
        max_length=12,
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
        channel = interaction.guild.get_channel(int(os.getenv("privatechannelmsg")))
        member_role = discord.utils.get(interaction.guild.roles, name="Member")   

        with conncreate.cursor() as cursor:
            sql = """SELECT * FROM dbo.member WHERE userid=?"""
            cursor.execute(sql, (self.username.value))
            for row in cursor:
                exist_username = True
        if exist_username: raise ValueError("username_exist")

        with conncreate.cursor() as cursor:
            sql = """SELECT * FROM dbo.member WHERE usernick=?"""
            cursor.execute(sql, (self.ign.value))
            for row in cursor:
                exist_ign = True
            if exist_ign: raise ValueError("ign_exist")
               
        if " " in self.password.value:
            raise ValueError("pass_format_error")
        
        if self.password.value != self.conf_password.value:
            raise ValueError("conf_pass")
        
        with conncreate.cursor() as cursor:
            sql = """SELECT * FROM dbo.discordinv WHERE invlink=?"""
            cursor.execute(sql , invite_code)
            for row in cursor:
                valid_code = True
        if valid_code == False:
            raise ValueError("invalid_invite")
        
             
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
            logger.info(f"Registered - ID:[{getid}]{self.username.value} / {self.ign.value} [{interaction.user.id}: {invite_code}] ")
      
        await interaction.user.add_roles(member_role)

        embed = discord.Embed(title=f"New User: {self.username.value}",
                              description="DEBUG",
                              color=discord.Color.green())
        embed.add_field(name="ID", value=getid, inline=True)
        embed.add_field(name="Username", value=self.username.value, inline=True)
        embed.add_field(name="IGN", value=self.ign.value, inline=True)
        embed.add_field(name="Invite", value=invite_code, inline=True)
        embed.add_field(name="DiscordID", value=interaction.user.id, inline=True)
        embed.set_author(name="Member Registration")
        await channel.send(embed=embed)
        await interaction.response.send_message(f"Thank you, {self.user.nick} {self.user.id}", ephemeral=True)
        
        
    async def on_error(self, interaction: discord.Interaction, error : Exception):
        if isinstance(error, ValueError):
            error_messages = {
                'username_exist': "The username you entered already exists. Please choose a different username and try again.",
                'ign_exist': "The In-Game name you entered already exists. Please choose a different in-game name and try again.",
                'pass_format_error': "The password you entered does not meet the required format. Please choose a password that meets the requirements and try again.",
                'conf_pass': "The passwords you entered do not match. Please double-check your passwords and try again.",
                'invalid_invite': "The Discord invite link you entered is invalid. Please enter a valid invite link and try again."
            }
            error_msg = error_messages.get(str(error), "We encountered an error while processing your request. Please try again later.")
            await interaction.response.send_message(error_msg, ephemeral=True)
        else:
            channel = interaction.guild.get_channel(int(os.getenv("privatechannelmsg")))
            await interaction.response.send_message(f"""We encountered an issue while attempting to submit your form. 
                                                    Our Moderation team has been notified and will provide assistance as soon as possible.""", ephemeral=True)
            logger.error(error)
            print(type(error), error, error.__traceback__)
            embed = discord.Embed(title=f"{str(type(error))}",
                                description=error,
                                color=discord.Color.red())
            embed.add_field(name="Username", value=self.username.value, inline=True)
            embed.add_field(name="IGN", value=self.ign.value, inline=True)
            embed.add_field(name="password", value=self.password.value, inline=True)
            embed.add_field(name="password2", value=self.conf_password.value, inline=True)
            embed.add_field(name="Invite", value=self.invite_link, inline=True)
            embed.add_field(name="DiscordID", value=interaction.user.id, inline=True)
            embed.set_author(name="Registration Error Report")
            await channel.send(embed=embed)
        

class Registration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invites = {}
    def cog_load(self):
        logger.info("Cog Loaded - registration")
    def cog_unload(self):
        logger.info("Cog Unloaded - registration")

    @app_commands.command(name="register", description='Open the Registration Form.')
    async def register(self, interaction: discord.Interaction) -> None:

        message = """Welcome to O2EZ!

To access other channels, kindly proceed with the registration process by clicking the button below. Ensure that you input the Discord invite you received in the designated Invitation Link box.

Please be advised that refraining from leaving the Discord server is crucial, as failure to do so may result in your account being restricted."""
        await interaction.response.send_message(message, view=registration_button())

async def setup(bot: commands.Bot):
    await bot.add_cog(Registration(bot))
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
        channel = interaction.guild.get_channel(int(os.getenv("privatechannelmsg")))
        member_role = discord.utils.get(interaction.guild.roles, name="Member")   


        with conncreate.cursor() as cursor:
            sql = """SELECT * FROM dbo.member WHERE userid=?"""
            cursor.execute(sql, (self.username.value))
            for row in cursor:
                exist_username = True
        if exist_username: raise ValueError("Username already exists. Please try again.")

        with conncreate.cursor() as cursor:
            sql = """SELECT * FROM dbo.member WHERE usernick=?"""
            cursor.execute(sql, (self.ign.value))
            for row in cursor:
                exist_ign = True
            if exist_ign: raise ValueError("In-Game Name already exists. Please try again")
               
        if " " in self.password.value:
            raise ValueError("Password does not match. Please try again.")
        
        if self.password.value != self.conf_password.value:
            raise ValueError("Invalid password format. Please try again.")
        
        with conncreate.cursor() as cursor:
            sql = """SELECT * FROM dbo.discordinv WHERE invlink=?"""
            cursor.execute(sql , invite_code)
            for row in cursor:
                valid_code = True
        if valid_code == False:
            raise ValueError("Invalid discord invite link. Please try again.")
        
             
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
        if error == type(ValueError):
            await interaction.response.send_message(error, ephemeral=True)
        channel = interaction.guild.get_channel(int(os.getenv("privatechannelmsg")))
        await interaction.response.send_message(f"""We encountered an issue while attempting to submit your form. 
                                                Our Moderation team has been notified and will provide assistance as soon as possible.""", ephemeral=True)
        embed = discord.Embed(title=f"{str(type(error))}",
                              description=error,
                              color=discord.Color.red())
        embed.add_field(name="Username", value=self.username.value, inline=True)
        embed.add_field(name="IGN", value=self.ign.value, inline=True)
        embed.add_field(name="password", value=self.password.value, inline=True)
        embed.add_field(name="password2", value=self.conf_password.value, inline=True)
        embed.add_field(name="Invite", value=self.invite_link, inline=True)
        embed.add_field(name="DiscordID", value=interaction.user.id, inline=True)
        embed.set_author(name="Error Report")
        await channel.send(embed=embed)
        logger.error(error)
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

async def setup(bot: commands.Bot):
    await bot.add_cog(Registration(bot))
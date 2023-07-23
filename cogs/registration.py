from typing import Optional
import discord
import pyodbc
import asyncio
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
admin_role_id = int(os.getenv('adminroleid'))

class registration_button(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Register", style=discord.ButtonStyle.green, custom_id="registration_button")
    async def button_callback(self, interaction: discord.Interaction, button):
        with conncreate.cursor() as cursor:
            query = "SELECT * FROM dbo.member WHERE discorduid=?"
            IsRegistered = cursor.execute(query, (interaction.user.id)).fetchone()
        if not IsRegistered:
            register_modal = registration_form()
            register_modal.user = interaction.user
            await interaction.response.send_modal(register_modal)
        else:
            await interaction.response.send_message(f"You are already registered with this Discord account.\nIf you forgot your account details, please contact our Discord Moderators.",
                                                    ephemeral=True)


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
        mod_channel = interaction.guild.get_channel(int(os.getenv("privatechannelmsg")))
        general_channel = interaction.guild.get_channel(int(os.getenv("publicchannelmsg")))
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
        
        if self.password.value != self.conf_password.value:
            raise ValueError("conf_pass")
        
        with conncreate.cursor() as cursor:
            sql = """SELECT * FROM dbo.discordinv WHERE invlink=?"""
            cursor.execute(sql , (invite_code))
            row = cursor.fetchone()
            if row is None:
                raise ValueError("invalid_invite")

        if any(" " in value for value in [self.password.value, self.ign.value, self.username.value]):
            raise ValueError("invalid_text_format")
        
             
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
      
        await interaction.user.edit(nick=self.ign.value)

        embed = discord.Embed(title=f"New User: {interaction.user.name}",
                              description="DEBUG",
                              color=discord.Color.green())
        embed.add_field(name="ID", value=getid, inline=True)
        embed.add_field(name="Username", value=self.username.value, inline=True)
        embed.add_field(name="IGN", value=self.ign.value, inline=True)
        embed.add_field(name="Invite", value=invite_code, inline=True)
        embed.add_field(name="DiscordID", value=interaction.user.id, inline=True)
        embed.set_author(name="Member Registration")
        await mod_channel.send(embed=embed)
        await interaction.response.send_message("### Successfully Registered!\nIn 30 seconds, you will be given a member role and access to the server.\nPlease take a moment to read the rules and follow them. We want to keep this place friendly and fun for everyone.\n\nWe hope you enjoy your stay here. ", 
                                                ephemeral=True, delete_after=30.0)
        await asyncio.sleep(30)
        await interaction.user.add_roles(member_role)
        await general_channel.send(f"Welcome to O2EZ! {interaction.user.mention}" )
        
        
    async def on_error(self, interaction: discord.Interaction, error : Exception):
        if isinstance(error, ValueError):
            error_messages = {
                'username_exist': "The username you entered is already in use. Please choose a different username and try again.",
                'ign_exist': "The In-Game name you entered is already in use. Please choose a different in-game name and try again.",
                'conf_pass': "The passwords you entered do not match. Please double-check your passwords and try again.",
                'invalid_text_format' : 'Please remove any spaces from any of the textbox and try again.\nSpaces are not allowed because they can cause errors and security issues.',
                'invalid_invite': "The Discord invite link you entered is invalid. Please enter a valid invite link and try again."
            }
            error_msg = error_messages.get(str(error), "We encountered an error while processing your request. Please try again later.")
            await interaction.response.send_message(error_msg, ephemeral=True)
        else:
            mod_channel = interaction.guild.get_channel(int(os.getenv("privatechannelmsg")))
            await interaction.response.send_message(f"""We encountered an issue while attempting to submit your form. 
                                                    Our Moderation team has been notified and will provide assistance as soon as possible.""", ephemeral=True)
            logger.info(error)
            logger.info(type(error), error, error.__traceback__)
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
            await mod_channel.send(embed=embed)
        

class Registration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invites = {}
    def cog_load(self):
        logger.info("Cog Loaded - registration")
        
    def cog_unload(self):
        logger.info("Cog Unloaded - registration")

    async def setup_hook(self) -> None:
        # Register the persistent view for listening here.
        # Note that this does not send the view to any message.
        # In order to do this you need to first send a message with the View, which is shown below.
        # If you have the message_id you can also pass it as a keyword argument, but for this example
        # we don't have one.
        self.add_view(registration_button())


    @app_commands.checks.has_role(admin_role_id)
    @app_commands.command(name="register", description='Open the Registration Form.')
    async def register(self, interaction: discord.Interaction) -> None:
        channel = interaction.channel

        message = """## Welcome to O2EZ!

If you want to check out the other channels, make sure to register first. Just click the button below to get started. Remember to enter the Discord invite you received in the Invitation Link box.

__Also, it's important to stay in the Discord server once you join, as leaving may lead to your account being restricted.__

Enjoy your time on **O2EZ**!"""
        await channel.send(message, view=registration_button())
        await interaction.response.send_message("Registration Message Sent!\n**Remember to invoke this command again if the bot needed a restart.**\nYou may dismiss this message.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Registration(bot))
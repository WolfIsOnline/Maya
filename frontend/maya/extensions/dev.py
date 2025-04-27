import requests

import discord

# pylint: disable=E0611
from discord import guild_only, option
from discord.ext import commands
from discord.commands import SlashCommandGroup

from maya import BACKEND_URL


class Dev(commands.Cog):
    """Commands for the devs"""

    def __init__(self, bot: discord.Bot):
        self.bot = bot

    smg_dev = SlashCommandGroup("dev", "Dev only commands")

    @commands.is_owner()
    @smg_dev.command(description="")
    @guild_only()
    async def addguild(self, ctx: discord.ApplicationContext) -> None:
        """Add guild to database

        Args:
            ctx (discord.ApplicationContext): application context
        """
        request = requests.post(
            url=f"{BACKEND_URL}/guilds",
            json={"guild_id": ctx.guild_id},
            timeout=10,
        )
        response = f"API Response: ```Content: {request.content}\nStatus Code: {request.content}```"
        await ctx.respond(embed=await self._dev_response(response))

    @commands.is_owner()
    @smg_dev.command(description="")
    @option("extension", description="Extension name")
    async def unload(self, ctx: discord.ApplicationContext, ext: str):
        """Unload an extension

        Args:
            ctx (discord.ApplicationContext): context application
            ext (str): the exception that the user passes
        """
        response = ""
        try:
            self.bot.unload_extension(f"maya.extensions.{ext}")
            response = f"{ext} unloaded"
        except discord.ExtensionError as e:
            response = e
        await ctx.respond(embed=self._dev_response(response))

    @commands.is_owner()
    @smg_dev.command(description="")
    @option("extension", description="Extension name")
    async def load(self, ctx: discord.ApplicationContext, ext: str) -> None:
        """Load an extension

        Args:
            ctx (discord.ApplicationContext): context application
            ext (str): the exception that the user passes
        """
        response = ""
        try:
            self.bot.load_extension(f"maya.extensions.{ext}")
            response = f"{ext} loaded"
        except discord.ExtensionError as e:
            response = e
        await ctx.respond(embed=self._dev_response(response))

    @commands.is_owner()
    @smg_dev.command(description="")
    @option("extension", description="Extension name")
    async def reload(self, ctx: discord.ApplicationContext, ext: str) -> None:
        """Reload an extension

        Args:
            ctx (discord.ApplicationContext): context application
            ext (str): the exception that the user passes
        """
        response = ""
        try:
            self.bot.reload_extension(f"maya.extensions.{ext}")
            response = f"{ext} reloaded"
        except discord.ExtensionError as e:
            response = e
        await ctx.respond(embed=self._dev_response(response))

    def _dev_response(self, message: str) -> discord.Embed:
        embed = discord.Embed(color=0x000000, title="Dev Commands", description=message)
        return embed

    @commands.is_owner()
    @smg_dev.command(description="")
    async def ls(self, ctx: discord.ApplicationContext):
        """List out extensions that are loaded

        Args:
            ctx (discord.ApplicationContext): context application
        """
        exts = self.bot.cogs
        if exts:
            ext_names = ", ".join(exts.keys())
            await ctx.respond(
                embed=self._dev_response(f"Loaded extensions: {ext_names}")
            )
        else:
            await ctx.respond(embed=self._dev_response("No extensions are loaded"))

    @commands.Cog.listener()
    async def on_application_command_error(
        self, ctx: discord.ApplicationContext, error: discord.DiscordException
    ):
        """Notify user when unauthorized access is detected

        Args:
            ctx (discord.ApplicationContext): context application
            error (discord.DiscordException): exception that is thrown
        """
        if isinstance(error, commands.NotOwner):
            await ctx.respond("This command is only available to devs.")


def setup(bot):
    bot.add_cog(Dev(bot))

import discord

# pylint: disable=E0611
from discord import option
from discord.ext import commands


class User(commands.Cog):
    """User commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Display user's avatar")
    @option("user", description="Enter username", default=None)
    async def avatar(self, ctx: discord.ApplicationContext, user: discord.User):
        """Display user's avatar

        Args:
            ctx (discord.ApplicationContext): context application
            user (discord.User): discord user object
        """
        if user is None:
            await ctx.respond(ctx.author.display_avatar)
        else:
            await ctx.respond(user.display_avatar)


def setup(bot):
    bot.add_cog(User(bot))

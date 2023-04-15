import hikari
import lightbulb
import logging
import wolfiebot
import random

from lightbulb import commands
from wolfiebot.core.bank import Bank
from wolfiebot.database.database import Database

log = logging.getLogger(__name__)
plugin = lightbulb.Plugin("commands.user")
bot = lightbulb.BotApp
db = Database()


@plugin.command
@lightbulb.option("user", "Select a member", type=hikari.User, required=False)
@lightbulb.command("avatar", "Get users avatar", aliases="pfp")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def avatar(ctx: lightbulb.Context):
    try:
        user = ctx.options.user
        avatar_url = ctx.options.user.display_avatar_url
        
    except AttributeError:
        user = ctx.author
        avatar_url = ctx.author.display_avatar_url
        
    embed = hikari.Embed(color=wolfiebot.DEFAULT_COLOR, title=user, description=f"{avatar_url}")
    embed.set_image(avatar_url)
    
    await ctx.respond(embed)
    
@plugin.command
@lightbulb.option("user", "Select a member", type=hikari.User, required=False)
@lightbulb.command("quote", "Get a random quote")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def quote(ctx: lightbulb.Context):
    quotes = db.read_guild_data(ctx.get_guild().id, "quotes")
    sorted_quote_data = []
    if ctx.options.user is not None:
        for raw_quote_data in quotes:
            if raw_quote_data["quote_user_id"] == str(ctx.options.user.id):
                sorted_quote_data.append(raw_quote_data)
    else:
        sorted_quote_data = quotes
        
    random_quote = random.choice(sorted_quote_data)
    quote = random_quote["quote"]
    if random_quote["quote_user"] != "Unknown":
        quote_user = "<@" + random_quote["quote_user_id"] + ">"
    else:
        quote_user = "Unknown"
        
    await ctx.respond(f"\"{quote}\" - {quote_user}")
    
def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)

def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(plugin)

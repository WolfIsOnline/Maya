import hikari
import lightbulb
import logging
import wolfiebot

from lightbulb import commands
from wolfiebot.database.database import Database

log = logging.getLogger(__name__)
plugin = lightbulb.Plugin("commands.admin")
db = Database()

@plugin.command
@lightbulb.option("channel", "Select the channel", type=hikari.TextableChannel, required=True)
@lightbulb.command("setquotes", "Set quotes channel")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def set_quotes(ctx: lightbulb.Context):
    channel = ctx.options.channel
    db.edit_guild_data(ctx.get_guild().id, "quotes_channel", channel.id)
    await ctx.respond(f"Quotes channel set to {channel.mention}")
    
@plugin.command
@lightbulb.option("channel", "Select the voice channel", type=hikari.GuildVoiceChannel, required=True)
@lightbulb.command("setroom", "Sets parent room channel")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def set_room(ctx: lightbulb.Context):
    channel = ctx.options.channel
    db.edit_guild_data(ctx.get_guild().id, "autoroom_parent", channel.id)
    await ctx.respond(f"Room parent channel set to {channel.mention}")
    
@plugin.command
@lightbulb.option("channel", "Select the logs channel", type=hikari.TextableChannel, required=True)
@lightbulb.command("setlogs", "Sets the logs channel")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def set_logs(ctx: lightbulb.Context):
    channel = ctx.options.channel
    db.edit_guild_data(ctx.get_guild().id, "logs_channel", channel.id)
    await ctx.respond(f"Logs channel set to {channel.mention}")

@plugin.command
@lightbulb.option("message_id", "Input the message ID", type=str, required=True)
@lightbulb.command("savequote", "Saves quote from message ID")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def save_quote(ctx: lightbulb.Context):
    message = await plugin.bot.rest.fetch_message(ctx.channel_id, ctx.options.message_id)
    await wolfiebot.core.quotes.commit(message.content, message.author.id, ctx.get_guild().id, ctx)
    
@plugin.command
@lightbulb.option("channel", "Select the welcome channel", type=hikari.TextableChannel, required=True)
@lightbulb.command("setwelcome", "Sets the welcome channel")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def set_welcome(ctx: lightbulb.Context):
    channel = ctx.options.channel
    db.edit_guild_data(ctx.get_guild().id, "welcome_channel", channel.id)
    await ctx.respond(f"Welcome channel set to {channel.mention}")
    
@plugin.command
@lightbulb.option("role", "Select the role", type=hikari.Role)
@lightbulb.command("addrole", "Adds autorole to list")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def add_role(ctx: lightbulb.Context):
    role = ctx.options.role
    roles = db.read_guild_data(ctx.get_guild().id, "autoroles")
    if roles is not None:
        for _role in roles:
            if _role == role.id:
                await ctx.respond(f"{role.mention} has already been added!")
                return
    db.append_guild_data(ctx.get_guild().id, "autoroles", role.id)
    await ctx.respond(f"{role.mention} added!")
    
@plugin.command
@lightbulb.option("role", "Select the role", type=hikari.Role)
@lightbulb.command("removerole", "Removes autorole from list")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def remove_role(ctx: lightbulb.Context):
    role = ctx.options.role
    db.remove_guild_data_array(ctx.get_guild().id, "autoroles", role.id)
    await ctx.respond(f"{role.mention} removed!")

def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)

def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(plugin)
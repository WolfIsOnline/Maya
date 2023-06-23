import os
import openai
import hikari
import lightbulb
import logging
import wolfiebot
import re

from wolfiebot.database.database import Database

plugin = lightbulb.Plugin("core.chat")
log = logging.getLogger(__name__)
db = Database()
openai.api_key = wolfiebot.OPENAI_API_KEY

@plugin.listener(hikari.GuildMessageCreateEvent)
async def check(event):
    if plugin.bot.get_me().id in event.message.user_mentions:
        system_prompt = db.read_user_data(plugin.bot.get_me().id, "prompt")
        user_id = event.author.id
        channel = event.message.channel_id
        content = event.message.content
        parsed = re.sub(r"<.*?>", "", content)
        prompt_data = {"role": "user", "content": parsed}
        system_data = {"role": "system", "content": system_prompt}
        db.append_user_data(user_id, "conversation", prompt_data)
        messages = []
        messages.append(system_data)
        previous_messages = db.read_user_data(user_id, "conversation")
        for c, line in enumerate(previous_messages):
            messages.append(line)
        messages.append(prompt_data)
        
        await plugin.bot.rest.trigger_typing(channel)
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo-0613", messages=messages)
        
        reply = response["choices"][0]["message"]["content"]
        await plugin.bot.rest.create_message(channel, reply)
        db.append_user_data(user_id, "conversation", {"role": "assistant", "content": reply})
        
        if len(previous_messages) > 29:
            db.remove_user_data_array_by_index(user_id, "conversation", 0)
            
@plugin.listener(hikari.DMMessageCreateEvent)
async def dm_check(event):
    if event.author_id == plugin.bot.get_me().id:
        return
    
    system_prompt = db.read_user_data(plugin.bot.get_me().id, "prompt")
    user_id = event.author.id
    channel = event.message.channel_id
    content = event.message.content
    parsed = re.sub(r"<.*?>", "", content)
    prompt_data = {"role": "user", "content": parsed}
    system_data = {"role": "system", "content": system_prompt}
    db.append_user_data(user_id, "conversation", prompt_data)
    messages = []
    messages.append(system_data)
    previous_messages = db.read_user_data(user_id, "conversation")
    for c, line in enumerate(previous_messages):
        messages.append(line)
    messages.append(prompt_data)
        
    await plugin.bot.rest.trigger_typing(channel)
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo-0613", messages=messages, temperature=1.2)
        
    reply = response["choices"][0]["message"]["content"]
    await plugin.bot.rest.create_message(channel, reply)
    db.append_user_data(user_id, "conversation", {"role": "assistant", "content": reply})
        
    if len(previous_messages) > 29:
        db.remove_user_data_array_by_index(user_id, "conversation", 0)
        
    
    
def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)

def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(plugin)

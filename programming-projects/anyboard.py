#json is arranged like so
#{
#    "excluded_users": [user_id1, user_id2, ...]
#    "channels": {
#        emoji_id1: channel_id1,
#        emoji_id2: channel_id2,
#        ...
#    }
#    "messages": {
#        "message_id1" {
#            "emoji_id1" {                                                   *will be unicode if it isnt a custom emoji*
#                "count": number_of_reactions_of_this_emoji,
#                "board_message_id": message_id_of_message_in_emoji_board    *A value of None will correspond to not sent*
#            },
#            "emoji_id2" {
#                "count": number_of_reactions_of_this_emoji,
#                "board_message_id": message_id_of_message_in_emoji_board
#            },
#            ...
#            "removed": Boolean
#        },
#        message_id2 {
#            ...
#        },
#        ...
#    }
#}

#!SINCE ITS PARSED FROM JSON, KEYS WILL ALWAYS BE STRINGS!

import discord as d
from discord.ext import commands, tasks 
import os
import json
import copy
from typing import Union, Optional
from collections import defaultdict
import datetime

intents = d.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

bot_token = ''
file_name = "anyboard_db.json"

guild_id = 1234567890

board_category_name = "whatever" #category where the channels will be added
board_category_position = 0 #positioning is discord is really weird so id just see where it goes and adjust accordingly
reaction_threshold = 3 #how many reactions until a message gets boarded
admin_override_id = 1234567890 #id which is able to do !rm on any message

anyboard_db = None #dict that can be encoded into json

if not os.path.isfile(file_name):
    with open(file_name, "w") as db:
        json.dump(
        {
            "excluded_users": [],
            "channels": {},
            "messages": {}
        },
        db, indent=4)
  
with open(file_name, "r") as db:
    anyboard_db = json.load(db)
    print('Loaded database')

print(anyboard_db)

@bot.event
async def on_ready():
    update.start()

@bot.event
async def on_raw_reaction_add(re: d.RawReactionActionEvent): #see: https://discordpy.readthedocs.io/en/stable/api.html#discord.RawReactionActionEvent
    if re.guild_id != guild_id:
        return
    
    guild = bot.get_guild(guild_id)
    channel = guild.get_channel_or_thread(re.channel_id)
    message = await channel.fetch_message(re.message_id)

    for id in anyboard_db['excluded_users']:
        if message.author.id == id:
            print("User is on exempt list")
            return

    if re.emoji.name == "⭐":
        print("Reaction was normal star")
        return
    if re.user_id == re.message_author_id:
        print("User tried to react their own message")
        return
    if message.author.id == bot.application_id:
        print("Reaction was on anyboard message")
        return

    if anyboard_db['messages'].get(str(message.id)) == None:
        anyboard_db['messages'][str(message.id)] = {}

    if anyboard_db['messages'][str(message.id)].get("removed") == True:
        print("Message had !rm used on it")
        return

    emoji = re.emoji.id if re.emoji.is_custom_emoji() else re.emoji.name
    emoji_name = re.emoji.name

    if anyboard_db['messages'][str(message.id)].get(str(emoji)) == None:
        anyboard_db['messages'][str(message.id)][str(emoji)] = {"count": 0}
    
    message_dict = anyboard_db['messages'][str(message.id)][str(emoji)]
    
    message_dict['count'] += 1 #update count
    count = message_dict['count']
    
    if count >= reaction_threshold: #check if count is above threshold and there is no board message that already exists
        board_category = await get_or_create_board_category(guild)
        board_channel = await get_or_create_board_channel(emoji, emoji_name, guild, board_category)

        if message_dict.get("board_message_id") != None:
            board_message = await board_channel.fetch_message(message_dict['board_message_id'])
            await edit_message_content(board_message, message.jump_url, guild, re.emoji, count)
            print(f"{message.id} already in {emoji_name}-board. Edited count to {count}")
            return

        board_content = await create_message_content(guild, re.emoji, count, message.jump_url)

        embeds, view = await create_embeds_and_buttons(message)

        board_message = await board_channel.send(board_content, embeds=embeds, view=view)
        message_dict['board_message_id'] = board_message.id
        print(f"Sent message {board_message.id}")

@bot.event
async def on_raw_reaction_remove(re: d.RawReactionActionEvent):
    if re.guild_id != guild_id:
        return
    
    guild = bot.get_guild(guild_id)
    channel = guild.get_channel_or_thread(re.channel_id)
    message = await channel.fetch_message(re.message_id)

    await decrement_or_delete(re, message, guild)

@bot.event
async def on_raw_reaction_clear_emoji(re: d.RawReactionClearEmojiEvent):
    if re.guild_id != guild_id:
        return

    guild = bot.get_guild(guild_id)
    channel = guild.get_channel_or_thread(re.channel_id)
    message = await channel.fetch_message(re.message_id)

    await decrement_or_delete(re, message, guild)

async def decrement_or_delete(re: Union[d.RawReactionActionEvent, d.RawReactionClearEmojiEvent], message: d.Message, guild: d.Guild):
    if anyboard_db['messages'].get(str(message.id)) == None:
        return
    if anyboard_db['messages'][str(message.id)].get("removed") == True:
        return
    
    if re.emoji.name == "⭐":
        print("Reaction was normal star")
        return
    if re.user_id == re.message_author_id:
        print("User tried to remove react their own message")
        return
    if message.author.id == bot.application_id:
        print("Remove reaction was on anyboard message")
        return

    emoji = re.emoji.id if re.emoji.is_custom_emoji() else re.emoji.name

    message_dict = anyboard_db['messages'][str(message.id)][str(emoji)]
    
    if message_dict.get("board_message_id") == None:
        return
    
    board_category = await get_or_create_board_category(guild)
    board_channel = await get_or_create_board_channel(emoji, None, guild, board_category)
    board_message = await board_channel.fetch_message(message_dict['board_message_id'])
    
    message_dict['count'] -= 1 #update count
    if isinstance(re, d.RawReactionClearEmojiEvent):
        message_dict['count'] = 0 #update count
    count = message_dict['count']
    
    if count < reaction_threshold:    
        await board_message.delete()
        print(f"Deleted message {message_dict['board_message_id']}")
        message_dict['board_message_id'] = None
    else:
        await edit_message_content(board_message, message.jump_url, guild, re.emoji, count)

async def get_or_create_board_category(guild: d.Guild):
    for category in guild.categories:
        if category.name == board_category_name:
            return category
    overwrites = {
        guild.default_role: d.PermissionOverwrite(send_messages=False, send_messages_in_threads=False, create_public_threads=False, create_private_threads=False),
        guild.me: d.PermissionOverwrite()
    }
    category = await guild.create_category(board_category_name, overwrites=overwrites, position=board_category_position)
    await category.set_permissions(bot.user, overwrite=None)    
    print(f"Created category: {category}")
    return category

async def get_or_create_board_channel(reaction_emoji_id: str, reaction_emoji_name: Optional[str], guild: d.Guild, category: d.CategoryChannel):
    name = reaction_emoji_id if reaction_emoji_name == None else reaction_emoji_name

    if anyboard_db['channels'].get(str(reaction_emoji_id)) == None:
        channel = await guild.create_text_channel(f"{name}-board", category=category)
        print(f"Created channel {channel.name} with id {channel.id}")
        anyboard_db['channels'][str(reaction_emoji_id)] = channel.id
        return channel

    return guild.get_channel(anyboard_db['channels'].get(str(reaction_emoji_id)))

async def create_message_content(guild: d.Guild, emoji: Union[d.PartialEmoji, d.Emoji], count: int, jump_url: str):
    emoji_in_message = emoji.name

    if emoji.is_custom_emoji():
        emoji_in_message = f'[{emoji.name}]({emoji.url})'
        if guild.get_emoji(emoji.id) != None:
            emoji_in_message = f'<:{emoji.name}:{emoji.id}>'

    return f"{emoji_in_message} {count} | {jump_url}"

async def edit_message_content(board_message: d.Message, message_jump_url: str, guild: d.Guild, emoji: Union[d.PartialEmoji, d.Emoji], count: int):
    message_content = await create_message_content(guild, emoji, count, message_jump_url)
    await board_message.edit(content=message_content)

async def create_embeds_and_buttons(message: d.Message):
    channel = message.channel    
    embeds = []
    buttons = []
    image_types = {
        "image/jpg": True,
        "image/png": True,
        "image/gif": True
    }
    image_types = defaultdict(lambda:False, image_types)
    
    if message.reference != None: 
        reply = message.reference.cached_message if message.reference.cached_message != None else await channel.fetch_message(message.reference.message_id)
        attachment = None
        video_url = None
        
        if len(reply.attachments) > 0:
            if image_types[reply.attachments[0].content_type]:
                attachment = reply.attachments[0].url
            elif reply.attachments[0].content_type == 'video/webm' or reply.attachments[0].content_type == 'video/mp4':
                video_url = f"\n\n[{reply.attachments[0].filename}]({reply.attachments[0].url})"

        reply_embed = d.Embed(color=d.Color.light_gray(), description=reply.content + f"{video_url}")

        (reply_embed
            .set_author(name=f"Replying to {reply.author.display_name}", icon_url=reply.author.display_avatar.url)
            .set_image(url=attachment)
        )
        reply_embed.timestamp = datetime.datetime.now()
        embeds.append(reply_embed)

    valid_attachments = []
    button_links = []

    for attachment in message.attachments:
        if image_types[attachment.content_type]:
            valid_attachments.append(attachment)
        else:
            button_links.append(attachment)

    main_message_embed = d.Embed(color=d.Color.yellow(), description=message.content)
    
    (main_message_embed
            .set_author(name=f"{message.author.display_name}", icon_url=message.author.display_avatar.url)
            .set_image(url=valid_attachments.pop(0) if len(valid_attachments) > 0 else None)
    )
    main_message_embed.timestamp = datetime.datetime.now()
    embeds.append(main_message_embed)

    for attachment in valid_attachments:
        attachment_embed = d.Embed(color=d.Color.yellow())
        attachment_embed.set_image(url=attachment.url)
        embeds.append(attachment_embed)

    for link in button_links:
        button = d.ui.Button(style=d.ButtonStyle.link, label=link.filename, url=link.url)
        buttons.append(button)

    while len(embeds) > 10:
        embeds.pop()

    view = d.ui.View()

    for button in buttons:
        view.add_item(button)

    return embeds, view

async def clear_empty_channels():
    guild = bot.get_guild(guild_id)
    #hacky im trying to get done
    found = False
    for category in guild.categories:
        if category.name == board_category_name:
            found = True
    if not found:
        return
    category = await get_or_create_board_category(guild)
    inverted_channels = await invert_dict(anyboard_db['channels'])

    for channel in category.channels:
        message = [i async for i in channel.history(limit=1)]
        if len(message) <= 0:
            key = inverted_channels.get(channel.id)
            if key == None:
                continue
            anyboard_db['channels'].pop(key)
            print(f"deleted empty channel {channel.name}")
            await channel.delete()

async def invert_dict(normal_dict: dict):
    return {value: key for key, value in normal_dict.items()}

old_db = None #used to check if there are any changes between last write and current write
@tasks.loop(seconds=15)
async def update():
    global old_db
    await clear_empty_channels()
    if old_db != anyboard_db:
        await write_db(anyboard_db, file_name)
        print("JSON updated")
        old_db = copy.deepcopy(anyboard_db)
        return

async def write_db(database, file_name):
    with open(file_name, "w") as db:
        json.dump(database, db, indent=4)

@bot.command("exempt")
async def exempt(ctx):
    if anyboard_db['excluded_users'].count(ctx.author.id) == 0:
        anyboard_db['excluded_users'].append(ctx.author.id)
        print(f"added {ctx.author.global_name} ({ctx.author.id}) to exempt list")
        await ctx.send("Your messages will now no longer appear in non-starboard boards.")
    else:
        print("User tried to exempt more than once")
        await ctx.send("Already on exempt list")

@bot.command("unexempt")
async def unexempt(ctx):
    try:
        anyboard_db['excluded_users'].remove(ctx.author.id)
        print(f"removed {ctx.author.global_name} ({ctx.author.id}) from exempt list")
        await ctx.send("Removed from exempt list")
    except ValueError:
        print("User was not on exempt list")
        await ctx.send("Not on exempt list")
    except:
        print("Something has gone very wrong")

@bot.command("rm")
async def rm(ctx: commands.Context):
    if ctx.message.reference == None:
        return
    
    reference_message_id = ctx.message.reference.message_id
    message = await ctx.channel.fetch_message(reference_message_id)

    if anyboard_db['messages'].get(str(message.id)) == None:
        return
    
    if message.author.id != ctx.author.id and ctx.author.id != admin_override_id:
        return
    
    message_dict = anyboard_db['messages'][str(message.id)]

    for i in message_dict.keys():
        if message_dict[i].get('board_message_id') == None:
            continue
        channel_id = anyboard_db['channels'].get(i)
        channel = ctx.guild.get_channel(channel_id)
        board_message = await channel.fetch_message(message_dict[i].get('board_message_id'))
        await board_message.delete()

    message_dict['removed'] = True

bot.run(bot_token)
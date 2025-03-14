import discord
from discord.ext import commands, tasks
import asyncio
from random import randrange, shuffle

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

guild_id = 123456789
color_loop_minutes = 5
channel_random_minutes = 60
nick_shuffle_minutes = 1
owner_name = '' #so the bot doesn't try and change the owner's nick and get an error
role_names = ['Red', 'Orange', 'Yellow', 'Green', 'Blue', 'Purple']
wordlist_file_name = 'big.txt'
bot_token = 'ABCDEFGHIJ1234567890'

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    edit.start()
    channels.start()
    shuffle_nick.start()
@tasks.loop(minutes=color_loop_minutes)
async def edit():
    print('start channel edit')
    guild = bot.get_guild(guild_id)
    server_roles = guild.roles
    role = None
    for role_name in role_names:
        for server_role in server_roles:
            if server_role.name == role_name:
                role = server_role
                break
        if role == None:
            print(f'Could not find {role_name}')
            break
        color = randrange(0,16777216)
        hex_color = hex(color)
        await role.edit(color=color)
        print(f'{role.name} edited! color: {hex_color}')
        await asyncio.sleep(1)
@tasks.loop(minutes=channel_random_minutes)
async def channels():
    guild = bot.get_guild(guild_id)
    wordslistfile = open(wordlist_file_name,'r')
    words = wordslistfile.readlines()
    for channel in guild.channels:
        word = words[randrange(0, len(words))]
        await channel.edit(name=word)
        print(f'changed channel {channel} to {word}')
        await asyncio.sleep(1)
@tasks.loop(minutes=nick_shuffle_minutes)
async def shuffle_nick():
    await asyncio.sleep(3) #offset from the channel changing
    guild = bot.get_guild(guild_id)
    members = list(guild.members)
    shuffle(members)
    for i in range(len(members)):
        if members[i].name == owner_name:
            members.pop(i)
            break
    for i in range(int(len(members)/2)): #does mean one person is not swapped if member count is odd
        member1 = members[i * 2]
        member2 = members[i * 2 + 1]
        if member1.nick == None:
            name1 = member1.global_name
        else:
            name1 = member1.nick
        if member2.nick == None:
            name2 = member2.global_name
        else:
            name2 = member2.nick
        await member1.edit(nick=name2)
        await member2.edit(nick=name1)
        print(f'{name1} <-> {name2}')
        await asyncio.sleep(1)
    print('done swapping!')
bot.run(bot_token)
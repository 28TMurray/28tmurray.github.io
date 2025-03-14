import discord
from discord.ext import commands
import asyncio
from random import randint
from pathlib import Path
import numpy as np
#flamingos imports
import csv
import matplotlib.pyplot as plt
from datetime import datetime

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
bot_token = 'asd'
guild_id = 123

min = 100 #min for message queue
max = 200 #max for message queue
message_queue = 0 #make randint(min, max) if you want it to start random
file_name = 'messageandratings.csv'
exempt_file_name = 'exempt_list.txt'

emojis_list = ['tierF', 'tierE', 'tierD', 'tierC', 'tierB', 'tierA', 'tierS']
emojis = None #{emoji.name:str(emoji) for emoji in bot.emojis}
emoji_to_index_dict = {}
for i in range(len(emojis_list)):
    emoji_to_index_dict[emojis_list[i]] = i + 1
score_to_letter_dict = {
    7: 'S',
    6: 'A',
    5: 'B',
    4: 'C',
    3: 'D',
    2: 'E',
    1: 'F',
    0: 'N/A'
}
#just creates file if it doesnt exist
file = Path(file_name)
if file.is_file() == False:
    file = open(file_name, '+w')
    file.write('Message ID,F,E,D,C,B,A,S,Rating,RatingFloat,Author,Content')
    file.close()
exempt_file = Path(exempt_file_name)
if exempt_file.is_file() == False:
    exempt_file = open(exempt_file_name, '+w')
    exempt_file.write('')
    exempt_file.close()

data_table = None
async def update_table():
    global data_table
    file = open(file_name, "+r")
    lines = file.readlines()
    for i in range(len(lines)):
        lines[i] = lines[i].replace('\n', '')
    data_table = [lines[i].split(sep=',') for i in range(len(lines))] #ie data_table[y][x]
    file.close()

async def append_to_file(message):
    file = open(file_name, '+a')
    message_id = message.id
    author = message.author.name
    content = bytes(message.content.replace(',', '/.').replace('’', '\'').replace('\n', 'NEWLINE'), 'utf-8').decode('utf-8', 'backslashreplace') + ' '.join(i.url for i in message.attachments)
    message = f'\n{message_id},0,0,0,0,0,0,0,N/A,0,{author},{content}'
    file.write(message)
    file.close()
    await update_table()

async def update_rating():
    for y in range(1, len(data_table)):
        numbers = []
        divisor = 0
        for x in range(1, len(emojis_list)+1):
            if int(data_table[y][x]) > 0:
                quant = int(data_table[y][x])
                numbers.append(x*quant)
                divisor += quant
        if divisor == 0:
            divisor = 1
        rating_float = np.sum(numbers)/divisor
        rating = score_to_letter_dict[np.round(rating_float)]
        data_table[y][len(emojis_list)+1] = rating
        data_table[y][len(emojis_list)+2] = str(rating_float)
async def write_file():
    lines = []
    for i in range(len(data_table)):
        lines.append(",".join(data_table[i])+'\n')
    lines[-1] = lines[-1].replace('\n', '')
    file = open(file_name, '+w')
    file.writelines(lines)
    file.close()
async def update_file(reaction):
    message = reaction.message
    for i in range(1, len(data_table)):
        if int(data_table[i][0]) == message.id:
            data_table[i][emoji_to_index_dict[reaction.emoji.name]] = str(int(data_table[i][emoji_to_index_dict[reaction.emoji.name]])+1)
    await update_rating()
    await write_file()
    
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    await update_table()

async def check_exempt(id):
    exempt_file = open(exempt_file_name, '+r')
    exempt_array = exempt_file.read().split(',')
    exempt_file.close()
    for i in exempt_array:
        if i == '':
            continue
        if int(i) == id:
            return True
    return False

@bot.event
async def on_message(message):
    global guild_id
    if message.guild.id != guild_id:
        return
    global message_queue
    global emojis
    await bot.process_commands(message)
    if await check_exempt(message.author.id) == True:
        return
    if emojis == None:
        emojis = {emoji.name:str(emoji) for emoji in bot.emojis}
    if message_queue <= 0:
        message_queue = randint(min, max)
        for i in range(len(emojis_list)):
            await message.add_reaction(emojis[emojis_list[-i-1]])
            await asyncio.sleep(0.15)
        await append_to_file(message)
        await update_table()
    else:
        message_queue -= 1

user_reactions = [] #stored as [user_id, msg_id]
@bot.event
async def on_reaction_add(reaction, user):
    global guild_id
    if reaction.message.guild.id != guild_id:
        return
    if user.id == bot.application_id:
        return
    if hasattr(reaction.emoji, 'name') == False:
        return
    in_list = False #i've already nested this shit too much im very sorry if someone who knows anything about programming this sees this
    for i in emojis_list:
        if i == reaction.emoji.name:
            in_list = True
            break
    if in_list == False:
        return
    message = reaction.message
    for i in range(1, len(data_table)):
        if int(data_table[i][0]) == message.id:
            for i2 in range(len(user_reactions)):
                if user_reactions[i2][0] == user.id and user_reactions[i2][1] == message.id:                   
                    await message.channel.send(f'<@{user.id}> Only your first reaction will be counted!')
                    return
            user_reactions.append([user.id, message.id])
            await update_file(reaction)
            break
    return
    
@bot.command()
async def exempt(ctx):
    global guild_id
    if ctx.message.guild.id != guild_id:
        return
    if await check_exempt(ctx.author.id) == True:
        return
    exempt_file = open(exempt_file_name, '+a')
    exempt_file.write(f'{ctx.author.id},')
    await ctx.send('added')
    exempt_file.close()
@bot.command()
async def unexempt(ctx):
    global guild_id
    if ctx.guild.id != guild_id:
        return
    exempt_file = open(exempt_file_name, '+r')
    exempt_array = exempt_file.read().split(',')
    exempt_file.close()
    for i in range(len(exempt_array)):
        if exempt_array[i] == '':
            continue
        if int(exempt_array[i]) == ctx.author.id:
            exempt_array.pop(i)
            exempt_write = ','.join(exempt_array)
            exempt_file = open(exempt_file_name, '+w')
            exempt_file.write(exempt_write)
            exempt_file.close()
            await ctx.send('removed')
            break
@bot.command()
async def rm(ctx):
    global guild_id
    if ctx.message.guild.id != guild_id:
        return
    if ctx.message.reference == None:
        return
    else:
        message = await ctx.fetch_message(ctx.message.reference.message_id)
        if message.author.id == ctx.author.id:
            for i in range(1, len(data_table)):
                if int(data_table[i][0]) == ctx.message.reference.message_id:
                    data_table.pop(i)
                    await write_file()
                    await message.clear_reactions()
                    await ctx.message.delete()
                    return
#flamingo wrote this command so IDK how it works
@bot.command()
async def histogram(ctx):
    rows = []
    with open(file_name, newline='') as f:    
        for row in csv.reader(f):
            rows.append(row)
            
    # transpose, i.e. convert FROM list of rows TO row of columns
    # then form a dictionary, in the format of { 'column_name': [column_list] }
    csv_dict = { column[0]:list(column[1:]) for column in list(zip(*rows)) }

    msgid = msg_content = msg_author = data = None
    colors = ['#ff7c82', '#ffbf7f', '#feff7f', '#7eff7e', '#76b1ec', '#807fff', '#fe7ffe']
    ranks = ['S', 'A', 'B', 'C', 'D', 'E', 'F']
    if ctx.message.type == discord.MessageType.reply:
        msgid = str(ctx.message.reference.message_id)
        try:
            msg_index = csv_dict['Message ID'].index(msgid) + 1
        except ValueError:
            await ctx.reply('this message has no reactions or is not in the spreadsheet')
            return
        counts = [int(i) for i in rows[msg_index][7:0:-1] ]
        ticks = range(7)
        msg_author = rows[msg_index][10]
        msg_content = rows[msg_index][11]
        title = f'\"{msg_content}\"\n - {msg_author}'
    else:
        colors += ['#aaaaaa']
        ranks += ['N/A']
        labels, counts = np.unique(csv_dict['Rating'], return_counts=True)
        ticks = range(8)
        title = f'rankings of {len(rows)} messages\n' + datetime.now().strftime('%I:%M %p, %b %d, %Y')

    print(f'{counts=}, {msg_author=}, {msg_content=}')
    plt.bar(ticks, counts, align='center', color=colors)
    plt.xticks(ticks, ranks)
    plt.title(title)
    plt.savefig('plt.png')
    plt.close()
    await ctx.send(file=discord.File('plt.png'))
    counts = None
bot.run(bot_token)
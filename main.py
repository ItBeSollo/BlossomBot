import disnake
import random
import asyncio
import json
from disnake.ext import commands

# Define the intents for your bot
intents = disnake.Intents.default()
intents.members = True
intents.message_content = True  # Enable the message content intent

# Create a Disnake bot instance with the defined intents
bot = commands.Bot(command_prefix=';', intents=intents)

cogs = ['trivia', 'users', 'safari', 'battle', 'raids', 'pokemon', 'inventory', 'admin']

for cog in cogs:
    try:
        bot.load_extension(cog)
        print(f'Cog "{cog}" loaded successfully.')
    except Exception as e:
        print(f'Failed to load cog "{cog}": {e}')
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    print('Bot is ready to start processing events!')
    game = disnake.Game("In Development")
    await bot.change_presence(activity=game)
  
# Run the bot
bot.run("token goes here")

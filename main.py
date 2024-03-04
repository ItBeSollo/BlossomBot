import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix=';', intents=intents)

cogs = ['trivia', 'users', 'safari', 'battle', 'raids', 'pokemon', 'inventory', 'admin']
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print(f'I am currently in {len(bot.guilds)} servers.')
    game = discord.Game("In Development")
    await bot.change_presence(activity=game)
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f'Cog "{cog}" loaded successfully.')
        except Exception as e:
            print(f'Failed to load cog "{cog}": {e}')

bot.run("token")

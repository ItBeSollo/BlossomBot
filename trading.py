import json
import discord
import asyncio
from discord.ext import commands

def has_started():
    async def predicate(ctx):
        user_id = str(ctx.author.id)
        try:
            with open('user_data.json', 'r') as file:
                user_data = json.load(file)
        except FileNotFoundError:
            await ctx.send("Error: User data not found.")
            return False
        
        # Check if the user has started by looking for their ID in the user_data
        if user_id in user_data:
            return True
        else:
            await ctx.send("You haven't started yet!")
            return False
    return commands.check(predicate)

class Trading(commands.Cog):
    """
    A cog for managing trading-related commands.
    """
    def __init__(self, bot):
        """
        Initialize the trading cog.

        Parameters:
        - bot (discord.ext.commands.Bot): The bot instance.
        """
        self.bot = bot
    @has_started()
    @commands.command(name='give')
    async def give(self, ctx, user: discord.Member, *pokemon_ids: int):
        """
        Give Pokémon to another user.

        Parameters:
            ctx (commands.Context): The context in which the command was invoked.
            user (discord.Member): The user to whom the Pokémon will be given.
            *pokemon_ids (int): The IDs of the Pokémon to be given.
        """
        try:
            with open('collections.json', 'r') as file:
                collections = json.load(file)
        except FileNotFoundError:
            await ctx.send("Pokémon data not found.")
            return

        user_id = str(ctx.author.id)
        recipient_id = str(user.id)

        if user_id not in collections:
            await ctx.send("You don't have any Pokémon to give.")
            return

        user_pokemon = collections[user_id]
        recipient_pokemon = collections.get(recipient_id, [])

        # Check if all provided Pokémon IDs are valid
        invalid_ids = [pid for pid in pokemon_ids if pid not in [pokemon['id'] for pokemon in user_pokemon]]
        if invalid_ids:
            await ctx.send(f"You don't own the following Pokémon IDs: {', '.join(map(str, invalid_ids))}.")
            return

        # Find the Pokémon to be given and remove them from the sender's collection
        pokemon_to_give = [pokemon for pokemon in user_pokemon if pokemon['id'] in pokemon_ids]
        user_pokemon = [pokemon for pokemon in user_pokemon if pokemon not in pokemon_to_give]

        # Assign new IDs to the given Pokémon based on the recipient's collection size
        max_number = len(recipient_pokemon) + 1
        for pokemon in pokemon_to_give:
            pokemon['ownerid'] = recipient_id
            pokemon['id'] = max_number
            max_number += 1

        # Add the given Pokémon to the recipient's collection
        recipient_pokemon.extend(pokemon_to_give)
        collections[recipient_id] = recipient_pokemon

        # Update the IDs of the sender's remaining Pokémon
        for i, pokemon in enumerate(user_pokemon, start=1):
            pokemon['id'] = i

        # Save the updated sender's collection
        collections[user_id] = user_pokemon

        # Save the updated collections
        with open('collections.json', 'w') as file:
            json.dump(collections, file, indent=4)

        # Ask for confirmation
        confirmation_message = await ctx.send(f"Do you want to give {user.mention} the specified Pokémon? (yes/no)")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['yes', 'no']

        try:
            # Wait for a response from the author
            response = await self.bot.wait_for('message', timeout=30.0, check=check)

            if response.content.lower() == 'yes':
                await ctx.send(f"You have given {user.mention} the specified Pokémon.")
            else:
                await ctx.send("Trade canceled.")
        except asyncio.TimeoutError:
            await ctx.send("Trade timed out.")
    @has_started()
    @commands.command()
    async def giftredeems(self, ctx, user: discord.Member, amount: int):
        # Check if the user is trying to gift to themselves
        if ctx.author == user:
            await ctx.send("You cannot gift redeems to yourself.")
            return
        
        # Check if the amount is negative
        if amount <= 0:
            await ctx.send("Please provide a positive amount of redeems to gift.")
            return
        
        # Load user data from file
        try:
            with open('user_data.json', 'r') as file:
                user_data = json.load(file)
        except FileNotFoundError:
            await ctx.send("User data not found.")
            return
        
        # Check if the gifter has enough redeems
        gifter_data = user_data.get(str(ctx.author.id))
        if not gifter_data or gifter_data["redeems"] < amount:
            await ctx.send("You don't have enough redeems to gift.")
            return
        
        # Update gifter's redeem balance
        gifter_data["redeems"] -= amount
        
        # Update recipient's redeem balance
        recipient_data = user_data.get(str(user.id))
        if not recipient_data:
            user_data[str(user.id)] = {"redeems": 0}
            recipient_data = user_data[str(user.id)]
        recipient_data["redeems"] += amount
        
        # Save updated user data to file
        with open('user_data.json', 'w') as file:
            json.dump(user_data, file, indent=4)
        
        await ctx.send(f"You have gifted {amount} redeems to {user.mention}.")
    
    @commands.command()
    async def gift(self,ctx, user: discord.Member, amount: int):
        
        # Check if the user is trying to gift to themselves
        if ctx.author == user:
            await ctx.send("You cannot gift tokens to yourself.")
            return
        
        # Check if the amount is negative
        if amount <= 0:
            await ctx.send("Please provide a positive amount of tokens to gift.")
            return
        
        # Load user data from file
        try:
            with open('user_data.json', 'r') as file:
                user_data = json.load(file)
        except FileNotFoundError:
            await ctx.send("User data not found.")
            return
        
        # Check if the gifter has enough tokens
        gifter_data = user_data.get(str(ctx.author.id))
        if not gifter_data or gifter_data["tokens"] < amount:
            await ctx.send("You don't have enough tokens to gift.")
            return
        
        # Update gifter's token balance
        gifter_data["tokens"] -= amount
        
        # Update recipient's token balance
        recipient_data = user_data.get(str(user.id))
        if not recipient_data:
            user_data[str(user.id)] = {"tokens": 0}
            recipient_data = user_data[str(user.id)]
        recipient_data["tokens"] += amount
        
        # Save updated user data to file
        with open('user_data.json', 'w') as file:
            json.dump(user_data, file, indent=4)
        
        await ctx.send(f"You have gifted {amount} tokens to {user.mention}.")

        

async def setup(bot):
    await bot.add_cog(Trading(bot))

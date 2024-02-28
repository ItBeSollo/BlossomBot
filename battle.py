import disnake
from disnake.ext import commands
import random
import asyncio
import json

class Battle(commands.Cog):
    """
    A cog for managing Pokémon battles between users.
    """

    def __init__(self, bot):
        """
        Initialize the Battle cog.
        
        Parameters:
        - bot (disnake.ext.commands.Bot): The bot instance.
        """
        self.bot = bot

    def get_user_pokemon(self, user_id):
        """
        Get the Pokémon collection of a user.
        
        Parameters:
        - user_id (str): The ID of the user.
        
        Returns:
        - list: The list of Pokémon in the user's collection.
        """
        # Load the user's Pokémon collection from collections.json
        try:
            with open('collections.json', 'r') as file:
                collections_data = json.load(file)
        except FileNotFoundError:
            return []

        # Get the user's Pokémon from their collection
        user_pokemon = collections_data.get(str(user_id), [])
        return user_pokemon

    @commands.command()
    async def battle(self, ctx, opponent: disnake.Member):
        """
        Initiate a Pokémon battle between the user and an opponent.
        
        Parameters:
        - ctx (disnake.ext.commands.Context): The context of the command.
        - opponent (disnake.Member): The opponent to battle against.
        """
        # Check if the opponent is valid and not the user themselves
        if opponent == ctx.author:
            await ctx.send("You can't battle yourself!")
            return

        # Get the user and opponent's Pokémon collections
        user_id = str(ctx.author.id)
        opponent_id = str(opponent.id)

        user_pokemon = self.get_user_pokemon(user_id)
        opponent_pokemon = self.get_user_pokemon(opponent_id)

        if not user_pokemon or not opponent_pokemon:
            await ctx.send("Both players need to have Pokémon to battle!")
            return

        # Confirm participation from both players
        await ctx.send(f"{opponent.mention}, do you accept {ctx.author.mention}'s challenge to a Pokémon battle? (yes/no)")

        def check(m):
            return m.author == opponent and m.channel == ctx.channel and m.content.lower() in ['yes', 'no']

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send(f"{opponent.mention} took too long to respond. Battle cancelled.")
            return

        if msg.content.lower() == 'yes':
            await ctx.send("Battle begins!")

            # Simulate the battle
            user_pokemon = random.choice(user_pokemon)
            opponent_pokemon = random.choice(opponent_pokemon)

            # Determine the winner based on random chance
            winner = random.choice([ctx.author, opponent])
            loser = ctx.author if winner == opponent else opponent

            await ctx.send(f"The winner of the battle is {winner.mention}!")
        else:
            await ctx.send("Battle declined. Maybe next time!")

def setup(bot):
    """
    Add the Battle cog to the bot.
    
    Parameters:
    - bot (disnake.ext.commands.Bot): The bot instance.
    """
    bot.add_cog(Battle(bot))

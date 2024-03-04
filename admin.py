import discord
import json
from discord.ext import commands

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @commands.command(aliases=["yeet"])
    @commands.is_owner()
    async def wipe(self, ctx, user_id: int):
        """Deletes a user from the database."""
        # Delete user data
        with open('user_data.json', 'r') as f:
            user_data = json.load(f)
        if str(user_id) in user_data:
            del user_data[str(user_id)]
            with open('user_data.json', 'w') as f:
                json.dump(user_data, f, indent=4)
            await ctx.send(f"Successfully removed user entry with ID: {user_id} from user_data.json.")
        else:
            await ctx.send(f"No user entry found with ID: {user_id}.")

        # Delete data from collections.json
        with open('collections.json', 'r') as f:
            collections_data = json.load(f)
        if str(user_id) in collections_data:
            del collections_data[str(user_id)]
            with open('collections.json', 'w') as f:
                json.dump(collections_data, f, indent=4)
            await ctx.send(f"Successfully removed user entry with ID: {user_id} from collections.json.")

        # Delete data from user_scores.json
        with open('user_scores.json', 'r') as f:
            user_scores_data = json.load(f)
        if str(user_id) in user_scores_data:
            del user_scores_data[str(user_id)]
            with open('user_scores.json', 'w') as f:
                json.dump(user_scores_data, f, indent=4)
            await ctx.send(f"Successfully removed user entry with ID: {user_id} from user_scores.json.")

        # Delete data from expedition_levels.json
        with open('expedition_levels.json', 'r') as f:
            expedition_levels_data = json.load(f)
        if str(user_id) in expedition_levels_data:
            del expedition_levels_data[str(user_id)]
            with open('expedition_levels.json', 'w') as f:
                json.dump(expedition_levels_data, f, indent=4)
            await ctx.send(f"Successfully removed user entry with ID: {user_id} from expedition_levels.json.")
        
        # Delete data from inventory.json
        with open('inventory.json', 'r') as f:
            inventory_data = json.load(f)
        if str(user_id) in inventory_data:
            del inventory_data[str(user_id)]
            with open('inventory.json', 'w') as f:
                json.dump(inventory_data, f, indent=4)
            await ctx.send(f"Successfully removed user entry with ID: {user_id} from inventory.json.")
        else:
            await ctx.send(f"No user entry found with ID: {user_id} in inventory.json.")

        # Delete data from teams.json
        with open('teams.json', 'r') as f:
            teams_data = json.load(f)
        if str(user_id) in teams_data:
            del teams_data[str(user_id)]
            with open('teams.json', 'w') as f:
                json.dump(teams_data, f, indent=4)
            await ctx.send(f"Successfully removed user entry with ID: {user_id} from teams.json.")
        else:
            await ctx.send(f"No user entry found with ID: {user_id} in teams.json.")
    @commands.is_owner()
    @commands.command(aliases=["addr"])
    async def addredeems(self, ctx, amount: int, user_id: int):
        """Add redeems to a user's balance."""
        try:
            with open('user_data.json', 'r') as file:
                user_data = json.load(file)
        except FileNotFoundError:
            user_data = {}

        # Check if the user_id exists in user_data.json
        if str(user_id) not in user_data:
            await ctx.send("User not found.")
            return

        # Add redeems to the user's balance
        user_data[str(user_id)]['redeems'] = user_data.get(str(user_id), {}).get('tokens', 0) + amount

        # Save the updated user data
        with open('user_data.json', 'w') as file:
            json.dump(user_data, file, indent=4)

        await ctx.send(f"Successfully added {amount} redeems to user {user_id}'s balance.")

    @commands.is_owner()
    @commands.command(aliases=["givecoins"])
    async def addtokens(self, ctx, amount: int, user_id: int):
        """Add tokens to a user's balance."""
        try:
            with open('user_data.json', 'r') as file:
                user_data = json.load(file)
        except FileNotFoundError:
            user_data = {}

        # Check if the user_id exists in user_data.json
        if str(user_id) not in user_data:
            await ctx.send("User not found.")
            return

        # Add tokens to the user's balance
        user_data[str(user_id)]['tokens'] = user_data.get(str(user_id), {}).get('tokens', 0) + amount

        # Save the updated user data
        with open('user_data.json', 'w') as file:
            json.dump(user_data, file, indent=4)

        await ctx.send(f"Successfully added {amount} tokens to user {user_id}'s balance.")

async def setup(bot):
    await bot.add_cog(Admin(bot))

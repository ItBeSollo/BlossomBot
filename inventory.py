import json
import discord
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
        if user_id in user_data and user_data[user_id]['started']:
            return True
        else:
            await ctx.send("You haven't started yet!")
            return False
    return commands.check(predicate)

class Inventory(commands.Cog):
    """
    A cog for handling shop-related commands and operations.
    """
    def __init__(self, bot):
        """
        Initializes the Shop cog.

        Parameters:
            bot (commands.Bot): The bot instance.
        """
        self.bot = bot

    @commands.command()
    @has_started()
    async def bag(self, ctx):
        """
        Displays the user's bag containing items.

        Retrieves the user's inventory from user_data.json and sends an embed
        displaying the items and their quantities.

        Parameters:
            ctx (commands.Context): The context in which the command is being invoked.
        """
        user_id = str(ctx.author.id)

        try:
            with open('user_data.json', 'r') as file:
                user_data = json.load(file)
        except FileNotFoundError:
            await ctx.send("User data not found.")
            return

        user_inventory = user_data.get(user_id, {}).get('inventory', {})
        if not user_inventory:
            await ctx.send("You don't have any items in your bag yet.")
            return

        # Create an embed to display the inventory
        embed = discord.Embed(title=f"{ctx.author.name}'s Bag", color=discord.Color.blurple())

        for item_name, quantity in user_inventory.items():
            embed.add_field(name=item_name, value=f"Quantity: {quantity}", inline=False)

        await ctx.send(embed=embed)
    @commands.command()
    @has_started()
    async def buy(self, ctx, item: str, quantity: int):
        """
        Allows users to buy items from the shop.

        Retrieves the shop items from shop_items.json, checks if the requested
        item is available and if the user has enough tokens to buy it. If so,
        deducts the appropriate tokens from the user and adds the item to their
        inventory.

        Parameters:
            ctx (commands.Context): The context in which the command is being invoked.
            item (str): The name of the item to buy.
            quantity (int): The quantity of the item to buy.
        """
        # Load shop items from shop_items.json
        try:
            with open('shop_items.json', 'r') as file:
                shop_items = json.load(file)
        except FileNotFoundError:
            await ctx.send("Error: Shop items not found.")
            return

        # Check if the item exists in the shop
        if item not in shop_items:
            await ctx.send(f"Error: {item} is not available in the shop.")
            return

        # Check if the user has enough tokens to buy the item
        user_id = str(ctx.author.id)
        user_data = self.load_user_data()
        if 'tokens' not in user_data[user_id]:
            await ctx.send("Error: You don't have enough tokens to buy this item.")
            return

        item_price = shop_items[item]['price']
        total_cost = item_price * quantity
        if user_data[user_id]['tokens'] < total_cost:
            await ctx.send("Error: You don't have enough tokens to buy this quantity of the item.")
            return

        # Subtract the total cost from the user's tokens
        user_data[user_id]['tokens'] -= total_cost

        # Add the item to the user's inventory with the specified quantity
        if 'inventory' not in user_data[user_id]:
            user_data[user_id]['inventory'] = {}

        if item in user_data[user_id]['inventory']:
            user_data[user_id]['inventory'][item] += quantity
        else:
            user_data[user_id]['inventory'][item] = quantity

        # Save the updated user data
        self.save_user_data(user_data)

        await ctx.send(f"Successfully bought {quantity} {item}(s) for {total_cost} tokens.")

    def load_user_data(self):
        """
        Loads user data from the user_data.json file.

        If the file is not found, it returns an empty dictionary.

        Returns:
            dict: The user data loaded from the file or an empty dictionary if the
                file is not found.
        """
        try:
            with open('user_data.json', 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def save_user_data(self, user_data):
        """
        Saves user data to the user_data.json file.

        Parameters:
            user_data (dict): The user data to be saved.
        """
        with open('user_data.json', 'w') as file:
            json.dump(user_data, file, indent=4)

async def setup(bot):
    await bot.add_cog(Inventory(bot))

import discord
from datetime import datetime
import json
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

class Users(commands.Cog):
    """
    A cog for managing user-related commands such as displaying trainer information
    and starting a new user profile.
    """
    def __init__(self, bot):
        """
        Initializes the UsersCog.

        Parameters:
            bot (commands.Bot): The Discord bot instance.
        """
        self.bot = bot

    @commands.command(aliases=["bal"])
    @has_started()
    async def trainer(self, ctx):
        """
        Displays the trainer card of the user who invoked the command.

        Parameters:
            ctx (commands.Context): The context in which the command was invoked.
        """
        user_id = str(ctx.author.id)  # Get the Discord ID of the user who invoked the command
        
        # Load collections data from JSON file
        try:
            with open('collections.json', 'r') as file:
                collections_data = json.load(file)
        except FileNotFoundError:
            await ctx.send("Collections data file not found.")
            return

        # Check if user ID exists in collections data
        if user_id not in collections_data:
            await ctx.send("User not found in collections.")
            return

        # Get the list of Pokémon caught by the user
        user_pokemon = collections_data[user_id]

        # Get the total number of Pokémon caught by the user
        total_pokemon_caught = len(user_pokemon)
        
        # Load user data from JSON file
        try:
            with open('user_data.json', 'r') as file:
                user_data = json.load(file)
        except FileNotFoundError:
            await ctx.send("User data file not found.")
            return

        # Check if user ID exists in user data
        if user_id not in user_data:
            await ctx.send("User not found.")
            return

        # Get user information
        user_info = user_data[user_id]

        # Create embed to display user information
        embed = discord.Embed(
            title=f"{ctx.author.name}'s Trainer Card",
            description=f"Trainer Nick: {user_info.get('nickname', 'N/A')}",
            colour=0x00b0f4,
            timestamp=datetime.now()
        )
        embed.add_field(
            name="General Info",
            value=f"`Pokemon Caught`: {total_pokemon_caught}\n`Active Region`: {user_info.get('activeregion', 'N/A')}\n`EV Points`: {user_info.get('evpoints', 'N/A'):,d}",
            inline=True
        )
        embed.add_field(
            name="Balances",
            value=f"`Tokens`: {user_info.get('tokens', 'N/A'):,d}\n`Redeems`: {user_info.get('redeems', 'N/A') :,d}\n`BP`: {user_info.get('battlepoints', 'N/A') :,d}",
            inline=True
        )
        embed.set_footer(text="Trainer Card", icon_url=ctx.author.avatar)

        await ctx.send(embed=embed)


    @commands.command()
    async def start(self, ctx):
        """
        Starts a new user profile.

        Parameters:
            ctx (commands.Context): The context in which the command was invoked.
        """
        user_id = str(ctx.author.id)
        user_data = self.load_user_data()

        # Check if user data already exists
        if user_id in user_data:
            await ctx.send("You have already started!")
        else:
            # Create new user profile
            new_profile = {
                "user_id": user_id,
                "redeems": 0,
                "nickname": str(ctx.author),
                "selected": "",
                "tokens": 0,
                "pokemoncaught": 0,
                "battlepoints": 0,
                "evpoints": 0,
                "activeregion": "Kanto",
                "exlevel": 0
            }
            user_data[user_id] = new_profile
            self.save_user_data(user_data)
            
            # Add an entry to inventory.json for the new user
            self.add_user_to_inventory(user_id)
            
            # Add an entry to teams.json for the new user
            self.add_user_to_teams(user_id)

            # Add an entry to collections.json for the new user
            self.add_user_to_collections(user_id)
            
            await ctx.send("Welcome! Your adventure begins now.")
            
    def add_user_to_teams(self, user_id):
        """
        Adds a new user to the teams data.

        Parameters:
            user_id (str): The Discord ID of the user.
        """
        with open('teams.json', 'r+') as f:
            teams_data = json.load(f)
            if user_id not in teams_data:
                teams_data[user_id] = {"1": None, "2": None, "3": None, "4": None, "5": None, "6": None}
                f.seek(0)
                json.dump(teams_data, f, indent=4)
                f.truncate()

    def add_user_to_collections(self, user_id):
        """
        Adds a new user to the collections data.

        Parameters:
            user_id (str): The Discord ID of the user.
        """
        with open('collections.json', 'r+') as f:
            collections_data = json.load(f)
            if user_id not in collections_data:
                collections_data[user_id] = []
                f.seek(0)
                json.dump(collections_data, f, indent=4)
                f.truncate()

    def load_user_data(self):
        """
        Loads user data from the user_data.json file.

        Returns:
            dict: The user data loaded from the file.
        """
        with open('user_data.json', 'r') as f:
            return json.load(f)

    def save_user_data(self, user_data):
        """
        Saves user data to the user_data.json file.

        Parameters:
            user_data (dict): The user data to be saved.
        """
        with open('user_data.json', 'w') as f:
            json.dump(user_data, f, indent=4)

    def add_user_to_inventory(self, user_id):
        """
        Adds a new user to the inventory data.

        Parameters:
            user_id (str): The Discord ID of the user.
        """
        with open('inventory.json', 'r+') as f:
            inventory_data = json.load(f)
            if user_id not in inventory_data:
                inventory_data[user_id] = []
                f.seek(0)
                json.dump(inventory_data, f, indent=4)
                f.truncate()
            
    def add_user_to_teams(self, user_id):
        """
    Adds a new user to the teams data.

    If the user ID is not already present in the teams data, it adds a new entry
    with default values for each team slot.

    Parameters:
        user_id (str): The Discord ID of the user.
    """
        with open('teams.json', 'r+') as f:
            teams_data = json.load(f)
            if user_id not in teams_data:
                teams_data[user_id] = {"1": None, "2": None, "3": None, "4": None, "5": None, "6": None}
                f.seek(0)
                json.dump(teams_data, f, indent=4)
                f.truncate()

    def load_user_data(self):
        """
    Loads user data from the user_data.json file.

    Returns:
        dict: The user data loaded from the file.
    """
        with open('user_data.json', 'r') as f:
            return json.load(f)

    def save_user_data(self, user_data):
        """
    Saves user data to the user_data.json file.

    Parameters:
        user_data (dict): The user data to be saved.
    """
        with open('user_data.json', 'w') as f:
            json.dump(user_data, f, indent=4)

    def add_user_to_inventory(self, user_id):
        """
    Adds a new user to the inventory data.

    If the user ID is not already present in the inventory data, it adds a new
    entry with an empty list.

    Parameters:
        user_id (str): The Discord ID of the user.
    """
        with open('inventory.json', 'r+') as f:
            inventory_data = json.load(f)
            if user_id not in inventory_data:
                inventory_data[user_id] = []
                f.seek(0)
                json.dump(inventory_data, f, indent=4)
                f.truncate()

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
    
    def add_user_to_inventory(self, user_id):
        """
    Adds a new user to the inventory data.

    If the user ID is not already present in the inventory data, it adds a new
    entry with an empty dictionary.

    Parameters:
        user_id (str): The Discord ID of the user.
    """
        try:
            with open('inventory.json', 'r') as file:
                inventory_data = json.load(file)
        except FileNotFoundError:
            inventory_data = {}
        
        if user_id not in inventory_data:
            inventory_data[user_id] = {}
            
        with open('inventory.json', 'w') as file:
            json.dump(inventory_data, file, indent=4)
            
async def setup(bot):
    await bot.add_cog(Users(bot))

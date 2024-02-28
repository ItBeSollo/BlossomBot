import disnake, asyncio
from disnake.ext import commands
import json
import random
from datetime import datetime

intents = disnake.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=';', intents=intents)

# Load starter Pokémon data from JSON
def load_starter_data():
    """
    Load starter Pokémon data from a JSON file.

    Returns:
    - dict: The loaded starter Pokémon data.
    """
    with open('starter_data.json', 'r') as file:
        return json.load(file)

class PokemonCog(commands.Cog):
    """
    A cog for managing Pokémon-related commands.
    """
    def __init__(self, bot):
        """
        Initialize the PokemonCog cog.

        Parameters:
        - bot (disnake.ext.commands.Bot): The bot instance.
        """
        self.bot = bot
        self.pokemon_data = self.load_pokemon_data()

    def load_pokemon_data(self):
        """
        Load Pokémon data from a JSON file.

        Returns:
        - dict: The loaded Pokémon data.
        """
        with open('pokedata.json', 'r') as file:
            return json.load(file)
    @commands.command()
    async def pokedex(self, ctx, pokemon_name: str):
        """
        Get information about a Pokémon from the Pokédex.

        Parameters:
        - ctx (disnake.ext.commands.Context): The context of the command.
        - pokemon_name (str): The name of the Pokémon.
        """
        # Load data from pokedata.json
        with open('pokedata.json', 'r') as file:
            pokedata = json.load(file)

        # Check if the provided Pokémon name exists in the pokedex
        if pokemon_name.lower() not in pokedata:
            await ctx.send("Pokémon not found in the Pokédex.")
            return

        pokemon_info = pokedata[pokemon_name.lower()]

        # Extract information
        types = ", ".join(pokemon_info["types"])
        abilities = ", ".join(pokemon_info["abilities"])
        stats = pokemon_info["stats"]

        # Create the embed
        embed = disnake.Embed(title=pokemon_name.capitalize(), color=disnake.Color.green())
        embed.add_field(name="Types", value=types, inline=False)
        embed.add_field(name="Abilities", value=abilities, inline=False)
        embed.add_field(name="Stats", value=f"HP: {stats['hp']}\nAttack: {stats['attack']}\nDefense: {stats['defense']}\nSpecial Attack: {stats['special_attack']}\nSpecial Defense: {stats['special_defense']}\nSpeed: {stats['speed']}", inline=False)

        await ctx.send(embed=embed)
    @commands.command(aliases=["Team"])
    async def team(self, ctx):
        """
        Displays the user's current Pokémon team.

        Parameters:
            ctx (commands.Context): The context in which the command was invoked.
        """
        with open('teams.json', 'r') as file:
            teams_data = json.load(file)

        user_id = str(ctx.author.id)
        user_team = teams_data.get(user_id, {})

        # Load Pokémon data from collections.json
        with open('collections.json', 'r') as file:
            pokemon_data = json.load(file)

        embed = disnake.Embed(title="Your Current Team!", color=0xeee647)

        for slot in range(1, 7):
            pokemon_id = user_team.get(str(slot))
            if pokemon_id:
                pokemon_info = next((p for p in pokemon_data.get(user_id, []) if p['id'] == pokemon_id), None)
                if pokemon_info:
                    pokemon_name = pokemon_info['name']
                    embed.add_field(name=f"Slot {slot} Pokemon", value=f"ID: {pokemon_id}\nName: {pokemon_name}", inline=False)
            else:
                embed.add_field(name=f"Slot {slot} Pokemon", value="None", inline=False)

        await ctx.send(embed=embed)
    @commands.command(aliases=["teamr"])
    async def teamremove(self, ctx, slot: int):
        """
        Removes a Pokémon from the user's team in the specified slot.

        Parameters:
            ctx (commands.Context): The context in which the command was invoked.
            slot (int): The slot number from which to remove the Pokémon.
        """
        if not 1 <= slot <= 6:
            await ctx.send("Invalid slot number. Please choose a slot between 1 and 6.")
            return

        # Load user's team data from teams.json
        with open('teams.json', 'r') as file:
            teams_data = json.load(file)

        user_id = str(ctx.author.id)
        user_team = teams_data.get(user_id, {})

        # Check if the slot is already empty
        if str(slot) not in user_team:
            await ctx.send(f"Slot {slot} is already empty.")
            return

        # Remove the Pokémon from the user's team in the specified slot
        removed_pokemon_id = user_team.pop(str(slot))

        # Update the teams.json file with the modified team data
        teams_data[user_id] = user_team
        with open('teams.json', 'w') as file:
            json.dump(teams_data, file, indent=4)

        # Load Pokémon data from collections.json
        with open('collections.json', 'r') as file:
            pokemon_data = json.load(file)

        # Find the name of the removed Pokémon
        removed_pokemon_info = next((p for p in pokemon_data.get(user_id, []) if p['id'] == removed_pokemon_id), None)
        if removed_pokemon_info is None:
            await ctx.send("Failed to find the removed Pokemon's information.")
            return

        removed_pokemon_name = removed_pokemon_info['name']
        await ctx.send(f"Successfully removed {removed_pokemon_name} from slot {slot} of your team.")

    @commands.command(aliases=["teama"])
    async def teamadd(self, ctx, slot: int, pokemon_id: int):
        """
        Adds a Pokémon to the user's team in the specified slot.

        Parameters:
            ctx (commands.Context): The context in which the command was invoked.
            slot (int): The slot number to which to add the Pokémon.
            pokemon_id (int): The ID of the Pokémon to add.
        """
        if not 1 <= slot <= 6:
            await ctx.send("Invalid slot number. Please choose a slot between 1 and 6.")
            return

        # Load user's team data from teams.json
        with open('teams.json', 'r') as file:
            teams_data = json.load(file)

        user_id = str(ctx.author.id)
        user_team = teams_data.get(user_id, {})

        # Check if the slot is already occupied
        if str(slot) in user_team:
            await ctx.send(f"Slot {slot} is already occupied. Please choose an empty slot.")
            return

        # Check if the given pokemon_id is already in the user's team
        if pokemon_id in user_team.values():
            await ctx.send("This Pokemon is already in your team. Please choose another Pokemon.")
            return

        # Load Pokémon data from collections.json
        with open('collections.json', 'r') as file:
            pokemon_data = json.load(file)

        # Check if the given pokemon_id is valid
        pokemon_info = next((p for p in pokemon_data.get(user_id, []) if p['id'] == pokemon_id), None)
        if pokemon_info is None:
            await ctx.send("Invalid Pokemon ID.")
            return

        # Add the Pokemon to the user's team in the specified slot
        user_team[str(slot)] = pokemon_id

        # Update the teams.json file with the modified team data
        teams_data[user_id] = user_team
        with open('teams.json', 'w') as file:
            json.dump(teams_data, file, indent=4)

        pokemon_name = pokemon_info['name']
        await ctx.send(f"Successfully added {pokemon_name} to slot {slot} of your team.")


    @commands.command()
    async def release(self, ctx, *pokemon_ids: int):
        """
        Releases Pokémon from the user's collection.

        Parameters:
            ctx (commands.Context): The context in which the command was invoked.
            *pokemon_ids (int): Variable number of Pokémon IDs to release.
        """
        user_id = str(ctx.author.id)

        try:
            with open('collections.json', 'r') as file:
                collections = json.load(file)
        except FileNotFoundError:
            await ctx.send("You haven't caught any Pokémon yet!")
            return

        user_pokemon = collections.get(user_id, [])
        removed_pokemon = [pokemon for pokemon in user_pokemon if pokemon.get('id') in pokemon_ids]

        if not removed_pokemon:
            await ctx.send("You don't have any Pokémon with the specified IDs in your collection!")
            return

        # Ask the user for confirmation
        await ctx.send(f"Are you sure you want to release all Pokémon with IDs {', '.join(map(str, pokemon_ids))}? (yes/no)")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['yes', 'no']

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=30)  # Wait for 30 seconds for a response
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Release cancelled.")
            return

        if msg.content.lower() == 'yes':
            user_pokemon = [pokemon for pokemon in user_pokemon if pokemon not in removed_pokemon]
            user_pokemon = await self.update_pokemon_ids(user_id, user_pokemon)
            collections[user_id] = user_pokemon

            with open('collections.json', 'w') as file:
                json.dump(collections, file, indent=4)

            await ctx.send(f"All Pokémon with the specified IDs have been released from your collection.")
        else:
            await ctx.send("Release cancelled.")
    @commands.command(name='mypokemon', aliases=['mypokes'])
    async def mypokemon(self, ctx):
        """
        Displays the user's Pokémon collection.

        Parameters:
            ctx (commands.Context): The context in which the command was invoked.
        """
        user_id = str(ctx.author.id)
        try:
            with open('collections.json', 'r') as file:
                collections = json.load(file)
        except FileNotFoundError:
            await ctx.send("You haven't caught any Pokémon yet!")
            return

        user_pokemon = collections.get(user_id, [])
        if not user_pokemon:
            await ctx.send("You haven't caught any Pokémon yet!")
            return

        embed = disnake.Embed(title=f"{ctx.author.name}'s Pokémon Collection", color=disnake.Color.green())
        for pokemon in user_pokemon:
            # Extract ID, name, and level from each Pokémon object
            pokemon_id = pokemon.get('id')
            pokemon_name = pokemon.get('name')
            pokemon_level = pokemon.get('level')

            # Add ID, name, and level to the embed as fields
            embed.add_field(name="Pokémon", value=f"ID: {pokemon_id}\nName: {pokemon_name}\nLevel: {pokemon_level}")

        await ctx.send(embed=embed)

    @commands.command()
    async def info(self, ctx, pokemon_id: int = None):
        """
        Displays information about a Pokémon.

        Parameters:
            ctx (commands.Context): The context in which the command was invoked.
            pokemon_id (int, optional): The ID of the Pokémon to display information about.
        """
        user_id = str(ctx.author.id)  # Get the Discord ID of the command invoker

        try:
            with open('collections.json', 'r') as file:
                collections = json.load(file)
        except FileNotFoundError:
            await ctx.send("Pokemon data not found.")
            return

        user_pokemon = collections.get(user_id, [])  # Get the user's Pokémon collection

        # If no pokemon_id is provided, find the selected pokemon
        if pokemon_id is None:
            for pokemon in user_pokemon:
                if pokemon.get('selected', False):
                    # Found the selected Pokémon
                    embed = disnake.Embed(title=f"Level {pokemon.get('level', 'Unknown')} {pokemon.get('name', 'Unknown')}", color=disnake.Color.blue(), timestamp=datetime.now())
                    embed.set_author(name=f"{ctx.author.name}'s Mon", icon_url=ctx.author.avatar)
                    embed.add_field(name="Statistics",
                                    value=f"**ATK**: {pokemon.get('ATK', 'Unknown')}\n**DEF**: {pokemon.get('DEF', 'Unknown')}",
                                    inline=False)
                    embed.add_field(name="Move 1", value=pokemon.get('move 1', 'Unknown'), inline=False)
                    embed.add_field(name="Move 2", value=pokemon.get('move 2', 'Unknown'), inline=False)
                    embed.set_image(url=pokemon.get('image_url', ''))
                    embed.set_footer(text=f"ID: {pokemon.get('id', 'Unknown')}/{len(user_pokemon)}")
                    await ctx.send(embed=embed)
                    return
            
            # If no selected pokemon is found, send a message
            await ctx.send("No Pokémon is currently selected.")
            return

        # If a pokemon_id is provided, display information about the specified Pokémon
        for pokemon in user_pokemon:
            if pokemon['id'] == pokemon_id:
                # Found the Pokémon with the given ID
                embed = disnake.Embed(title=f"Level {pokemon.get('level', 'Unknown')} {pokemon.get('name', 'Unknown')}", color=disnake.Color.blue(), timestamp=datetime.now())
                embed.set_author(name=f"{ctx.author.name}'s Mon", icon_url=ctx.author.avatar)
                embed.add_field(name="Statistics",
                                value=f"**ATK**: {pokemon.get('ATK', 'Unknown')}\n**DEF**: {pokemon.get('DEF', 'Unknown')}",
                                inline=False)
                embed.add_field(name="Move 1", value=pokemon.get('move 1', 'Unknown'), inline=False)
                embed.add_field(name="Move 2", value=pokemon.get('move 2', 'Unknown'), inline=False)
                embed.set_image(url=pokemon.get('image_url', ''))
                embed.set_footer(text=f"ID: {pokemon.get('id', 'Unknown')}/{len(user_pokemon)}")
                await ctx.send(embed=embed)
                return

        # If the loop finishes without finding the Pokémon, send a message
        await ctx.send(f"No information found for Pokémon with ID {pokemon_id}.")

    @commands.command()
    async def select_starter(self, ctx):
        """
        Allows the user to select a starter Pokémon.

        Parameters:
            ctx (commands.Context): The context in which the command was invoked.
        """
    # Check if the user has already selected a starter
        user_id = str(ctx.author.id)
        with open('user_data.json', 'r') as f:
            user_data = json.load(f)
        if user_id in user_data and user_data[user_id]['selected']:
            await ctx.send("You have already selected a starter!")
            return

        # Load starter data
        with open('starter_data.json', 'r') as f:
            starter_data = json.load(f)

        # Create embed with starter pokemon information
        embed = disnake.Embed(title="Select a Starter!", color=0x00ff00)
        embed.set_thumbnail(url="https://archives.bulbagarden.net/media/upload/thumb/7/76/25th_Anniversary_key_art.png/375px-25th_Anniversary_key_art.png")
        embed.set_image(url="https://archives.bulbagarden.net/media/upload/thumb/7/76/25th_Anniversary_key_art.png/375px-25th_Anniversary_key_art.png")
        embed.description = "Choose your starter Pokémon:"
        for emoji, info in starter_data.items():
            embed.add_field(name=f"{info['name']} ({info['type']})", value=info['description'], inline=False)

        # Send the embed to the channel
        message = await ctx.send(embed=embed)

        # Function to check message and return corresponding starter
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        try:
            # Wait for user message
            response = await self.bot.wait_for('message', timeout=30.0, check=check)

            # Check if the response is a valid starter
            selected_starter = None
            for emoji, info in starter_data.items():
                if response.content.lower() == info['name'].lower():
                    selected_starter = info
                    break

            # If a valid starter is selected
            if selected_starter:
                # Update user_data.json with selected starter
                with open('user_data.json', 'r+') as f:
                    user_data[user_id]['selected'] = selected_starter['name']
                    f.seek(0)
                    json.dump(user_data, f, indent=4)

                # Generate IVs (Individual Values) and nature
                iv = random.randint(0, 31)
                nature = random.choice(["Hardy", "Lonely", "Adamant", "Naughty", "Brave", 
                                        "Bold", "Docile", "Impish", "Lax", "Relaxed", 
                                        "Modest", "Mild", "Bashful", "Rash", "Quiet", 
                                        "Calm", "Gentle", "Careful", "Quirky", "Sassy", 
                                        "Timid", "Hasty", "Jolly", "Naive", "Serious"])
                starter_level = 5

                # Update pokes.json with selected starter
                with open('pokes.json', 'r+') as f:
                    pokes_data = json.load(f)
                    pokes_data[user_id] = {
                        "selected": True,
                        "ownerid": user_id,
                        "pokname": selected_starter['name'],
                        "hpiv": iv,
                        "atkiv": iv,
                        "defiv": iv,
                        "spatkiv": iv,
                        "spdefiv": iv,
                        "speediv": iv,
                        "hpev": 0,
                        "atkev": 0,
                        "defev": 0,
                        "spatkev": 0,
                        "spdefev": 0,
                        "speedev": 0,
                        "pokelevel": starter_level,
                        "pnum": 1,
                        "move1": "Tackle",
                        "move2": "Tackle",
                        "move3": "Tackle",
                        "move4": "Tackle",
                        "poknick": "None",
                        "exp": 0,
                        "nature": nature,
                        "expcap": 35,
                        "hitem": "None"
                    }
                    f.seek(0)
                    json.dump(pokes_data, f, indent=4)

                # Send confirmation message
                await ctx.send(f"You have selected {selected_starter['name']} as your starter Pokémon!")

                # Send direct message with additional information and instructions
                await ctx.author.send("Thank you for selecting your starter Pokémon! Get ready for an adventure!")

            else:
                await ctx.send("Invalid starter Pokémon. Please choose one of the available starters.")

        except asyncio.TimeoutError:
            # Handle timeout error
            await ctx.send("You took too long to select your starter Pokémon. Please try again.")

def setup(bot):
    """
    Add the PokemonCog cog to the bot.

    Parameters:
    - bot (disnake.ext.commands.Bot): The bot instance.
    """
    bot.add_cog(PokemonCog(bot))

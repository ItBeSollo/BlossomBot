import json
import random
import requests
import math
import discord
from typing import Union
import asyncio
from datetime import datetime
from discord.ext import commands
from safari import natlist

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

class Pokemon(commands.Cog):
    """
    A cog for managing Pokémon-related commands.
    """
    def __init__(self, bot):
        """
        Initialize the PokemonCog cog.

        Parameters:
        - bot (discord.ext.commands.Bot): The bot instance.
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
    
    def get_pokemon_image_url(self, pokemon_name):
        """Get the image URL for a Pokémon from PokeAPI."""
        pokemon_url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"
        response = requests.get(pokemon_url)
        if response.status_code == 200:
            pokemon_data = response.json()
            return pokemon_data['sprites']['other']['official-artwork']['front_default']
        else:
            return None
    
    @has_started()
    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def redeem(self, ctx, value: str, amount: int):
        if amount > 10:
            await ctx.send("You can only redeem up to 10 at a time.")
            return
        user_id = str(ctx.author.id)

        # Load Pokémon names from pokemonnames.json
        with open('pokemonnames.json', 'r') as file:
            pokemon_names = json.load(file)

        # Check if the value is a Pokémon name
        if value.lower() in [name.lower() for name in pokemon_names]:
            # Redeem Pokémon
            try:
                with open('user_data.json', 'r+') as file:  # Open in read/write mode
                    user_data = json.load(file)
                    if user_id not in user_data or user_data[user_id]['redeems'] < amount:
                        await ctx.send("You don't have enough redeems left.")
                        return

                    user_data[user_id]['redeems'] -= amount
                    await ctx.send(f"Redeeming {amount} {value}{'s' if amount > 1 else ''}...")

                    # Redeem the specified amount of Pokémon
                    for _ in range(amount):
                        self.save_pokemon_to_collection(user_id, value)

                    # Update user data file
                    file.seek(0)
                    json.dump(user_data, file, indent=4)
                    file.truncate()

                await ctx.send(f"{amount} {value}{'s' if amount > 1 else ''} have been added to your collection!")
            except FileNotFoundError:
                await ctx.send("Error: User data not found.")
        elif value.lower() == "tokens":
            # Add tokens to the user's account
            try:
                with open('user_data.json', 'r+') as file:  # Open in read/write mode
                    user_data = json.load(file)
                    if user_id not in user_data or user_data[user_id]['redeems'] < amount:
                        await ctx.send("You don't have enough redeems left.")
                        return

                    tokens_to_add = amount * 25000
                    user_data[user_id]['redeems'] -= amount
                    user_data[user_id]['tokens'] += tokens_to_add

                    # Update user data file
                    file.seek(0)
                    json.dump(user_data, file, indent=4)
                    file.truncate()

                await ctx.send(f"{tokens_to_add} tokens have been added to your account!")
            except FileNotFoundError:
                await ctx.send("Error: User data not found.")
        else:
            await ctx.send(f"Invalid value: {value}")

    def select_ability(self, pokemon_name, hidden_ability_probability):
        """Select an ability for the Pokémon."""
        
        # Fetch the Pokémon resource based on the name from PokeAPI
        pokemon_url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"
        response = requests.get(pokemon_url)
        if response.status_code == 200:
            pokemon_data = response.json()
            abilities = [ability['ability']['name'] for ability in pokemon_data['abilities']]
        else:
            print(f"Error fetching Pokémon data for {pokemon_name}")
            abilities = []
        
        hidden_abilities = [ability for ability in abilities if self.is_hidden_ability(ability)]

        if hidden_abilities:
            # If hidden abilities are available, randomly select one based on probability
            if random.random() < hidden_ability_probability:
                return random.choice(hidden_abilities)
        
        # If no hidden abilities or probability not met, choose a regular ability
        return random.choice(abilities)

    def is_hidden_ability(self, ability_name):
        """Check if the ability is a hidden ability."""
        ability_url = f"https://pokeapi.co/api/v2/ability/{ability_name}"
        response = requests.get(ability_url)
        if response.status_code == 200:
            ability_data = response.json()
            return ability_data.get("is_hidden", False)
        else:
            print(f"Error fetching ability data for {ability_name}")
            return False
    
    def save_pokemon_to_collection(self, user_id, pokemon_name):
        """Save a found Pokémon to the user's collection."""
        # Load the existing collections from the file
        try:
            with open('collections.json', 'r') as file:
                collections = json.load(file)
        except FileNotFoundError:
            collections = {}

        # Get the user's collection or create an empty list if it doesn't exist
        user_collection = collections.get(str(user_id), [])

        # Generate a unique ID for the new Pokémon
        pokemon_id = len(user_collection) + 1  # IDs start from 1 and increment by 1

        # Get random moves for the Pokémon
        level = random.randint(1, 30)
        move1 = move2 = move3 = move4 = "tackle"

        try:
            # Get the Pokémon data from PokeAPI
            pokemon_url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"
            response = requests.get(pokemon_url)
            if response.status_code == 200:
                pokemon_data = response.json()
                pokemon_species_url = pokemon_data['species']['url']
                species_response = requests.get(pokemon_species_url)
                if species_response.status_code == 200:
                    species_data = species_response.json()
                    abilities = [ability['ability']['name'] for ability in pokemon_data['abilities']]
                    base_experience = pokemon_data['base_experience']
                    gender_rate = species_data['gender_rate']
                    hidden_ability_probability = 0.5  # Example probability for hidden ability
                else:
                    print(f"Error fetching species information for {pokemon_name}")
                    abilities = []
                    base_experience = 0
                    gender_rate = -1
                    hidden_ability_probability = 0.5
            else:
                print(f"Error fetching Pokémon data for {pokemon_name}")
                abilities = []
                base_experience = 0
                gender_rate = -1
                hidden_ability_probability = 0.33
        except Exception as e:
            print(f"Error fetching Pokémon information for {pokemon_name}: {e}")
            abilities = []
            base_experience = 0
            gender_rate = -1
            hidden_ability_probability = 0.33

        # Determine the gender based on gender rate
        if gender_rate == -1:
            gender = None  # Genderless
        elif gender_rate == 0:
            gender = 'Female'
        elif gender_rate == 8:
            gender = 'Male'
        else:
            if random.random() < gender_rate / 8:
                gender = 'Male'
            else:
                gender = 'Female'


        # Randomly select an ability considering hidden abilities
        if abilities:
            ability = self.select_ability(pokemon_name, hidden_ability_probability)  

        # Get image URL for the Pokémon
        image_url = self.get_pokemon_image_url(pokemon_name)

        # Create a Pokémon object
        pokemon_object = {
            "id": pokemon_id,
            "ownerid": user_id,
            "OT": user_id,
            "name": pokemon_name.capitalize(),
            "gender": gender,
            "ability": ability,
            "nickname": "",
            "friendship": 0,
            "favorite": False,
            "level": level,
            "exp": base_experience,
            "expcap": level ** 3,
            "nature": random.choice(natlist),
            "hpiv": random.randint(1, 31),
            "atkiv": random.randint(1, 31),
            "defiv": random.randint(1, 31),
            "spatkiv": random.randint(1, 31),
            "spdiv": random.randint(1, 31),
            "speiv": random.randint(1, 31),
            "hpev": 0,
            "atkev": 0,
            "defev": 0,
            "spatkev": 0,
            "spdefev": 0,
            "speedev": 0,
            "move 1": move1,
            "move 2": move2,
            "move 3": move3,
            "move 4": move4,
            "image_url": image_url,
            "selected": False,
            "helditem": "",
            "is_shiny": False
        }

        # Append the Pokémon object to the user's collection
        user_collection.append(pokemon_object)

        # Update the collections dictionary with the modified user collection
        collections[str(user_id)] = user_collection

        # Save the updated collections back to the file
        with open('collections.json', 'w') as file:
            json.dump(collections, file, indent=4)

    def get_pokemon_image_url(self, pokemon_name):
        """Get the image URL for a Pokémon from PokeAPI."""
        pokemon_url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"
        response = requests.get(pokemon_url)
        if response.status_code == 200:
            pokemon_data = response.json()
            return pokemon_data['sprites']['other']['official-artwork']['front_default']
        else:
            return None
    
    @commands.command(aliases=["dex"])
    async def pokedex(self, ctx, pokemon_name: str):
        """
        Get information about a Pokémon from the Pokédex.

        Parameters:
        - ctx (discord.ext.commands.Context): The context of the command.
        - pokemon_name (str): The name of the Pokémon.
        """
        # Fetch Pokémon data from the PokeAPI
        url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"
        response = requests.get(url)

        if response.status_code != 200:
            await ctx.send("Pokémon not found in the Pokédex.")
            return

        pokemon_data = response.json()

        types = ', '.join([entry['type']['name'] for entry in pokemon_data['types']])
        abilities = ', '.join([entry['ability']['name'] for entry in pokemon_data['abilities']])
        stats = {
            'HP': pokemon_data['stats'][0]['base_stat'],
            'Attack': pokemon_data['stats'][1]['base_stat'],
            'Defense': pokemon_data['stats'][2]['base_stat'],
            'Special Attack': pokemon_data['stats'][3]['base_stat'],
            'Special Defense': pokemon_data['stats'][4]['base_stat'],
            'Speed': pokemon_data['stats'][5]['base_stat']
        }

        # Get the URL for the Pokémon's image
        image_url = pokemon_data['sprites']['other']['official-artwork']['front_default']

        # Create the embed
        embed = discord.Embed(title=pokemon_name.capitalize(), color=discord.Color.green())
        embed.add_field(name="Types", value=types, inline=False)
        embed.add_field(name="Abilities", value=abilities, inline=False)
        embed.add_field(name="Stats", value='\n'.join([f"{stat}: {value}" for stat, value in stats.items()]), inline=False)
        embed.set_image(url=image_url)  # Set the image URL for the embed

        await ctx.send(embed=embed)
    @has_started()
    @commands.command(name='moves')
    async def moves(self, ctx):
        try:
            with open('collections.json', 'r') as file:
                collections = json.load(file)
        except FileNotFoundError:
            await ctx.send("No Pokémon data found.")
            return

        user_id = str(ctx.author.id)
        user_pokemon = collections.get(user_id, [])
        if not user_pokemon:
            await ctx.send("You haven't caught any Pokémon yet.")
            return

        selected_pokemon_moves = []
        for pokemon in user_pokemon:
            if pokemon.get('selected', False):
                selected_pokemon_moves = [pokemon.get(f'move {i}', 'None') for i in range(1, 5)]
                break

        if not selected_pokemon_moves:
            await ctx.send("You haven't selected a Pokémon.")
            return

        embed = discord.Embed(title="Moves", description="\n".join(selected_pokemon_moves), color=discord.Color.blue())
        await ctx.send(embed=embed)
    @has_started()
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

        embed = discord.Embed(title="Your Current Team!", color=0xeee647)

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
    @has_started()
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

    @has_started()
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

    @has_started()
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
    @commands.command(name='movedex')
    async def movedex(self, ctx, *, move_name: str):
        try:
            # Fetch move data from the PokeAPI
            move_response = requests.get(f"https://pokeapi.co/api/v2/move/{move_name.lower()}/")
            move_response.raise_for_status()  # Check for any HTTP errors
            move_data = move_response.json()

            # Extract move details
            move_type = move_data['type']['name'].capitalize()
            move_accuracy = move_data['accuracy'] if move_data['accuracy'] is not None else "N/A"
            move_effect_entries = [entry['effect'] for entry in move_data['effect_entries'] if entry['language']['name'] == 'en']

            # Construct the embed
            embed = discord.Embed(title=f"Move: {move_name.capitalize()}", color=discord.Color.blue())
            embed.add_field(name="Type", value=move_type, inline=False)
            embed.add_field(name="Accuracy", value=move_accuracy, inline=False)
            embed.add_field(name="Effect", value="\n".join(move_effect_entries), inline=False)

            await ctx.send(embed=embed)

        except requests.RequestException as e:
            await ctx.send(f"Error fetching move data: {e}")
        except KeyError:
            await ctx.send("Move not found.")
    @has_started()
    @commands.command(name='moveset')
    async def moveset(self, ctx):
        try:
            with open('collections.json', 'r') as file:
                collections = json.load(file)
        except FileNotFoundError:
            await ctx.send("No Pokémon data found.")
            return

        user_id = str(ctx.author.id)
        user_pokemon = collections.get(user_id, [])
        if not user_pokemon:
            await ctx.send("You haven't caught any Pokémon yet.")
            return

        selected_pokemon = None
        for pokemon in user_pokemon:
            if pokemon.get('selected', False):
                selected_pokemon = pokemon
                break

        if not selected_pokemon:
            await ctx.send("You haven't selected a Pokémon.")
            return

        pokemon_name = selected_pokemon.get('name', '')

        try:
            r = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}/")
            r.raise_for_status()  # Check for any HTTP errors
            pokemon_data = r.json()

            moves = [move['move']['name'] for move in pokemon_data['moves']]
            max_pages = (len(moves) + 24) // 25  # Calculate the total number of pages

            def create_embed(page_num):
                start_idx = (page_num - 1) * 25
                end_idx = min(start_idx + 25, len(moves))
                embed = discord.Embed(title=f"{pokemon_name}'s Moveset (Page {page_num}/{max_pages})", color=discord.Color.blue())
                for move in moves[start_idx:end_idx]:
                    embed.add_field(name=move, value="Type: Check Movedex", inline=False)  # Type information not available from PokeAPI
                return embed

            current_page = 1
            message = await ctx.send(embed=create_embed(current_page))
            await message.add_reaction('⬅️')
            await message.add_reaction('➡️')

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ['⬅️', '➡️']

            while True:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                    if str(reaction.emoji) == '⬅️' and current_page > 1:
                        current_page -= 1
                        await message.edit(embed=create_embed(current_page))
                        await message.remove_reaction(reaction, user)
                    elif str(reaction.emoji) == '➡️' and current_page < max_pages:
                        current_page += 1
                        await message.edit(embed=create_embed(current_page))
                        await message.remove_reaction(reaction, user)
                    else:
                        await message.remove_reaction(reaction, user)
                except:
                    break

            await message.clear_reactions()

        except requests.RequestException as e:
            await ctx.send(f"Error fetching Pokémon data: {e}")
    @has_started()
    @commands.command(name='mypokemon', aliases=['mypokes'])
    async def mypokemon(self, ctx, *args):
        """
        Displays the user's Pokémon collection.

        Parameters:
            ctx (commands.Context): The context in which the command was invoked.
            *args: Optional arguments to filter the Pokémon collection.
                Accepted arguments: 'name', 'nick', 'male', 'female', 'iv a', 'iv d', 'level'
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

        filtered_pokemon = user_pokemon

        if args:
            sort_iv_asc = False
            sort_iv_desc = False
            for idx, arg in enumerate(args):
                if arg.lower() == 'iv':
                    if idx + 1 < len(args):
                        next_arg = args[idx + 1].lower()
                        if next_arg == 'a':
                            sort_iv_asc = True
                        elif next_arg == 'd':
                            sort_iv_desc = True
            for arg in args:
                if arg.lower() == 'name':
                    name = args[args.index('name') + 1].lower()
                    filtered_pokemon = [p for p in filtered_pokemon if p.get('name', '').lower() == name]
                elif arg.lower() == 'nick':
                    nickname = args[args.index('nick') + 1].lower()
                    filtered_pokemon = [p for p in filtered_pokemon if p.get('nickname', '').lower() == nickname]
                elif arg.lower() == 'male':
                    filtered_pokemon = [p for p in filtered_pokemon if p.get('gender', '').lower() == 'male']
                elif arg.lower() == 'female':
                    filtered_pokemon = [p for p in filtered_pokemon if p.get('gender', '').lower() == 'female']
                elif arg.lower() == 'level':
                    level = int(args[args.index('level') + 1])
                    filtered_pokemon = [p for p in filtered_pokemon if p.get('level', 0) == level]

            if sort_iv_asc:
                filtered_pokemon.sort(key=lambda p: sum(p.get(f'{stat}iv', 0) for stat in ['hp', 'atk', 'def', 'spatk', 'spdef', 'spe']))
            elif sort_iv_desc:
                filtered_pokemon.sort(key=lambda p: sum(p.get(f'{stat}iv', 0) for stat in ['hp', 'atk', 'def', 'spatk', 'spdef', 'spe']), reverse=True)
            else:
                # Sort the filtered_pokemon list based on IVs if no other sorting criteria is applied
                filtered_pokemon.sort(key=lambda p: sum(p.get(f'{stat}iv', 0) for stat in ['hp', 'atk', 'def', 'spatk', 'spdef', 'spe']))

        max_pages = math.ceil(len(filtered_pokemon) / 10)
        current_page = 1

        def create_embed(page):
            start_idx = (page - 1) * 10
            end_idx = start_idx + 10
            embed = discord.Embed(title=f"{ctx.author.name}'s Pokémon Collection (Page {page}/{max_pages})", color=discord.Color.green())
            for pokemon in filtered_pokemon[start_idx:end_idx]:
                pokemon_id = pokemon.get('id')
                pokemon_name = pokemon.get('name')
                pokemon_level = pokemon.get('level')
                total_ivs = sum(pokemon.get(f'{stat}iv', 0) for stat in ['hp', 'atk', 'def', 'spatk', 'spd', 'spe'])
                iv_percentage = round((total_ivs / 186) * 100)
                embed.add_field(name="Pokémon", value=f"ID: {pokemon_id} Name: {pokemon_name} Level: {pokemon_level} IV%: {iv_percentage}%", inline=False)
            return embed

        message = await ctx.send(embed=create_embed(current_page))
        await message.add_reaction('⬅️')
        await message.add_reaction('➡️')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['⬅️', '➡️']

        while True:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                if str(reaction.emoji) == '⬅️' and current_page > 1:
                    current_page -= 1
                    await message.edit(embed=create_embed(current_page))
                    await message.remove_reaction(reaction, user)
                elif str(reaction.emoji) == '➡️' and current_page < max_pages:
                    current_page += 1
                    await message.edit(embed=create_embed(current_page))
                    await message.remove_reaction(reaction, user)
                else:
                    await message.remove_reaction(reaction, user)
            except:
                break

        await message.clear_reactions()
    @has_started()
    @commands.command()
    async def learn(self, ctx, move_name: str, slot_number: int):
        """Teach a Pokémon a new move."""
        user_id = str(ctx.author.id)
        # Load user's Pokémon collection from collections.json
        try:
            with open('collections.json', 'r') as file:
                collections = json.load(file)
        except FileNotFoundError:
            await ctx.send("Error: Collections data not found.")
            return

        # Check if the user has any Pokémon
        if user_id not in collections or not collections[user_id]:
            await ctx.send("You don't have any Pokémon in your collection.")
            return

        # Check if the specified slot number is valid (1 to 4)
        if slot_number < 1 or slot_number > 4:
            await ctx.send("Invalid slot number. Slot number must be between 1 and 4.")
            return

        # Get the selected Pokémon's name
        selected_pokemon = None
        for pokemon in collections[user_id]:
            if pokemon['selected']:
                selected_pokemon = pokemon
                break

        if not selected_pokemon:
            await ctx.send("You haven't selected a Pokémon.")
            return

        # Fetch the Pokémon's moves from the PokeAPI
        pokemon_name = selected_pokemon['name'].lower()
        url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name}/"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            moves = [move['move']['name'] for move in data['moves']]
            if move_name.lower() not in moves:
                await ctx.send(f"The move '{move_name}' is not available for {pokemon_name.capitalize()}.")
                return
        else:
            await ctx.send("Failed to fetch Pokémon data.")
            return

        # Update the move in the selected slot
        selected_pokemon[f"move {slot_number}"] = move_name.lower()

        # Save the updated collection back to collections.json
        collections[user_id] = collections.get(user_id, [])
        with open('collections.json', 'w') as file:
            json.dump(collections, file, indent=4)

        await ctx.send(f"{pokemon_name.capitalize()} has learned {move_name.capitalize()} in slot {slot_number}!")

    @has_started()
    @commands.command(aliases=['abildex'])
    async def abilitydex(self, ctx, ability_name):
        """Fetch information about a Pokémon ability."""
        # Construct the URL for the ability API endpoint
        url = f"https://pokeapi.co/api/v2/ability/{ability_name.lower()}/"

        # Fetch data from the PokeAPI
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Extract the English effect entry
            effect_entry = None
            for entry in data['effect_entries']:
                if entry['language']['name'] == 'en':
                    effect_entry = entry['effect']
                    break
            if effect_entry:
                # Create an embed to display the ability information
                embed = discord.Embed(title=f"Ability: {ability_name}", description=effect_entry, color=0x00ff00)
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"No English effect entry found for {ability_name}.")
        else:
            await ctx.send(f"Failed to fetch data for {ability_name}.")
    
    async def display_pokemon_info(self, ctx, pokemon, user_pokemon):
        pokemon_name = pokemon.get('name', 'Unknown')
        pokemon_data = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}/").json()
        types = ', '.join(entry['type']['name'].capitalize() for entry in pokemon_data['types'])
        ability_name = pokemon.get('ability', 'Unknown')

        # Calculate stats based on IVs and EVs
        stats = pokemon_data['stats']
        hp_base = stats[0]['base_stat']
        atk_base = stats[1]['base_stat']
        def_base = stats[2]['base_stat']
        spa_base = stats[3]['base_stat']
        spd_base = stats[4]['base_stat']
        spe_base = stats[5]['base_stat']

        hp_iv = pokemon.get('hpiv', 0)
        atk_iv = pokemon.get('atkiv', 0)
        def_iv = pokemon.get('defiv', 0)
        spa_iv = pokemon.get('spatkiv', 0)
        spd_iv = pokemon.get('spdiv', 0)
        spe_iv = pokemon.get('speiv', 0)

        hp_ev = pokemon.get('hpev', 0)
        atk_ev = pokemon.get('atkev', 0)
        def_ev = pokemon.get('defev', 0)
        spa_ev = pokemon.get('spatkev', 0)
        spd_ev = pokemon.get('spdefev', 0)
        spe_ev = pokemon.get('speedev', 0)

        level = pokemon.get('level', 50)

        hp = ((2 * hp_base + hp_iv + (hp_ev / 4)) * level) / 100 + level + 10
        atk = ((2 * atk_base + atk_iv + (atk_ev / 4)) * level) / 100 + 5
        defense = ((2 * def_base + def_iv + (def_ev / 4)) * level) / 100 + 5
        spa = ((2 * spa_base + spa_iv + (spa_ev / 4)) * level) / 100 + 5
        spd = ((2 * spd_base + spd_iv + (spd_ev / 4)) * level) / 100 + 5
        spe = ((2 * spe_base + spe_iv + (spe_ev / 4)) * level) / 100 + 5

        iv_total = hp_iv + atk_iv + def_iv + spa_iv + spd_iv + spe_iv
        iv_percentage = round((iv_total / 186) * 100)

        nature = pokemon.get("nature", "None")
        ot = ctx.guild.get_member(int(pokemon.get("OT", "None")))
        # Handle nature effects
        if nature == 'Adamant':
            atk *= 1.1
            spa *= 0.9
        elif nature == 'Bold':
            defense *= 1.1
            atk *= 0.9
        elif nature == 'Brave':
            atk *= 1.1
            spe *= 0.9
        elif nature == 'Calm':
            spd *= 1.1
            atk *= 0.9
        elif nature == 'careful':
            spd *= 1.1
            spa *= 0.9
        elif nature == 'Gentle':
            spd *= 1.1
            defense *= 0.9
        elif nature == 'Hasty':
            spe *= 1.1
            defense *= 0.9
        elif nature == 'Impish':
            defense *= 1.1
            spa *= 0.9
        elif nature == 'Jolly':
            spe *= 1.1
            spa *= 0.9
        elif nature == 'Lax':
            defense *= 1.1
            spd *= 0.9
        elif nature == 'Lonely':
            atk *= 1.1
            defense *= 0.9
        elif nature == 'Mild':
            spa *= 1.1
            defense *= 0.9
        elif nature == 'Modest':
            spa *= 1.1
            atk *= 0.9
        elif nature == 'Naive':
            spe *= 1.1
            spd *= 0.9
        elif nature == 'Naughty':
            atk *= 1.1
            spd *= 0.9
        elif nature == 'Quiet':
            spa *= 1.1
            spe *= 0.9
        elif nature == 'Rash':
            spa *= 1.1
            spd *= 0.9
        elif nature == 'Relaxed':
            defense *= 1.1
            spe *= 0.9
        elif nature == 'Sassy':
            spd *= 1.1
            spe *= 0.9
        elif nature == 'Timid':
            spe *= 1.1
            atk *= 0.9

        embed = discord.Embed(title=f"{pokemon.get('gender', 'Unknown')} Lvl {level} {pokemon_name.capitalize()}",
                                description=f"OT: <@{ot.id}>\n Nickname: {pokemon.get('nickname', 'None')}\nExp: {pokemon.get('exp', 'Unknown')}/{pokemon.get('expcap', 'Unknown')}\nFriendship: {pokemon.get('friendship', 'Unknown')}\nPokemon Info\nAbility: {ability_name}\n Nature: {pokemon.get('nature', 'Unknown')}\nTypes: {types}",
                                colour=0x00b0f4,
                                timestamp=datetime.now())
        embed.add_field(name=f"Stats         Total    IVS | EVS",
                            value=f"""`HP:       {round(hp)} - {hp_iv} / {hp_ev}`
                                    `Attack:   {round(atk)} - {atk_iv} / {atk_ev}`
                                    `Defense:  {round(defense)} - {def_iv} / {def_ev}`
                                    `Sp. Atk:  {round(spa)} - {spa_iv} / {spa_ev}`
                                    `Sp. Def:  {round(spd)} - {spd_iv} / {spd_ev}`
                                    `Speed:    {round(spe)} - {spe_iv} / {spe_ev}`
                                    `IV %`:    `{iv_percentage}%`""",
                            inline=False)
        embed.set_thumbnail(url=ctx.author.avatar)
        embed.set_image(url=pokemon.get('image_url', ''))
        embed.set_footer(text=f"ID: {pokemon.get('id', 'Unknown')}/{len(user_pokemon)} Held Item: {pokemon.get('helditem', 'Unknown')}")

        await ctx.send(embed=embed)
    @has_started()
    @commands.command(name='info', aliases=['i'])
    async def info(self, ctx, query: Union[int, str] = None):
        """
        Displays information about a Pokémon.

        Parameters:
            ctx (commands.Context): The context in which the command was invoked.
            query (Union[int, str], optional): The ID or query to display information about.
        """
        user_id = str(ctx.author.id)  # Get the Discord ID of the command invoker

        try:
            with open('collections.json', 'r') as file:
                collections = json.load(file)
        except FileNotFoundError:
            await ctx.send("Pokemon data not found.")
            return

        user_pokemon = collections.get(user_id, [])  # Get the user's Pokémon collection

        # If no query is provided, display the user's selected Pokémon
        if query is None:
            if not user_pokemon:
                await ctx.send("You don't have any Pokémon in your collection.")
                return

            # Find the selected Pokémon
            for pokemon in user_pokemon:
                if pokemon.get('selected', False):
                    await self.display_pokemon_info(ctx, pokemon, user_pokemon)
                    return

            await ctx.send("No Pokémon is currently selected.")
            return

        # If a query is provided, check if it's an integer (ID) or a string (name)
        if isinstance(query, int):
            # If the query is an ID, display information about the specified Pokémon
            for pokemon in user_pokemon:
                if pokemon['id'] == query:
                    await self.display_pokemon_info(ctx, pokemon, user_pokemon)
                    return

            await ctx.send(f"No information found for Pokémon with ID {query}.")
        elif isinstance(query, str):
    # If the query is a string, check if it's "last" or "latest"
            if query.lower() == "last" or query.lower() == "latest":
                if not user_pokemon:
                    await ctx.send("You don't have any Pokémon in your collection.")
                    return

                latest_pokemon = user_pokemon[-1]
                await self.display_pokemon_info(ctx, latest_pokemon, user_pokemon)
                return
            await ctx.send(f"No information found for Pokémon with name '{query}'.")
        else:
            await ctx.send("Invalid query format. Please specify the Pokémon ID or name.")
            return
async def setup(bot):
    await bot.add_cog(Pokemon(bot))

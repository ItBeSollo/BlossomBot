import json
import math
import discord
import asyncio
import pokebase as pb
from datetime import datetime
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
        """Get the image URL for a Pokémon."""
        # Get the Pokemon species object based on the name
        pokemon_species = pb.pokemon(pokemon_name.lower())

        # Get the URL for the official artwork
        official_artwork_url = pokemon_species.sprites.other.official_artwork.front_default
        return official_artwork_url
    
    @commands.command(aliases=["dex"])
    async def pokedex(self, ctx, pokemon_name: str):
        """
        Get information about a Pokémon from the Pokédex.

        Parameters:
        - ctx (discord.ext.commands.Context): The context of the command.
        - pokemon_name (str): The name of the Pokémon.
        """
        # Fetch Pokémon data from the PokeAPI
        pokemon = pb.pokemon(pokemon_name.lower())

        if not pokemon:
            await ctx.send("Pokémon not found in the Pokédex.")
            return

        types = ', '.join([type_entry.type.name for type_entry in pokemon.types])
        abilities = ', '.join([ability_entry.ability.name for ability_entry in pokemon.abilities])
        stats = {
            'HP': pokemon.stats[0].base_stat,
            'Attack': pokemon.stats[1].base_stat,
            'Defense': pokemon.stats[2].base_stat,
            'Special Attack': pokemon.stats[3].base_stat,
            'Special Defense': pokemon.stats[4].base_stat,
            'Speed': pokemon.stats[5].base_stat
        }
        
         # Get the URL for the Pokémon's image
        image_url = self.get_pokemon_image_url(pokemon_name)
        # Create the embed
        embed = discord.Embed(title=pokemon_name.capitalize(), color=discord.Color.green())
        embed.add_field(name="Types", value=types, inline=False)
        embed.add_field(name="Abilities", value=abilities, inline=False)
        embed.add_field(name="Stats", value='\n'.join([f"{stat}: {value}" for stat, value in stats.items()]), inline=False)
        embed.set_image(url=image_url)  # Set the image URL for the embed

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
                total_ivs = sum(pokemon.get(f'{stat}iv', 0) for stat in ['hp', 'atk', 'def', 'spatk', 'spdef', 'spe'])
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
    @commands.command(name='info', aliases=['i'])
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
                    pokemon_data = pb.pokemon(pokemon.get('name', 'Unknown').lower())
                    types = ', '.join(t.type.name for t in pokemon_data.types)
                    ability_name = pokemon.get('ability', 'Unknown')
                    level = pokemon.get('level', 'Unknown')

                    # Calculate stats based on IVs and EVs
                    hp_base = pokemon_data.stats[0].base_stat
                    atk_base = pokemon_data.stats[1].base_stat
                    def_base = pokemon_data.stats[2].base_stat
                    spa_base = pokemon_data.stats[3].base_stat
                    spd_base = pokemon_data.stats[4].base_stat
                    spe_base = pokemon_data.stats[5].base_stat

                    nature = pokemon.get("nature", "None")

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

                    hp = round((((2 * hp_base + hp_iv + (hp_ev / 4)) * level) / 100) + level + 10)
                    attack = round((((2 * atk_base + atk_iv + (atk_ev / 4)) * level) / 100) + 5)
                    defense = round((((2 * def_base + def_iv + (def_ev / 4)) * level) / 100) + 5)
                    special_attack = round((((2 * spa_base + spa_iv + (spa_ev / 4)) * level) / 100) + 5)
                    special_defense = round((((2 * spd_base + spd_iv + (spd_ev / 4)) * level) / 100) + 5)
                    speed = round((((2 * spe_base + spe_iv + (spe_ev / 4)) * level) / 100) + 5)

                    total_ivs = hp_iv + atk_iv + def_iv + spa_iv + spd_iv + spe_iv
                    iv_percentage = round((total_ivs / 186) * 100)
                    
                    if nature == 'Adamant':
                        attack *= 1.1
                        special_attack *= 0.9
                    elif nature == 'Bold':
                        defense *= 1.1
                        attack *= 0.9
                    elif nature == 'Brave':
                        attack *= 1.1
                        speed *= 0.9
                    elif nature == 'Calm':
                        special_defense *= 1.1
                        attack *= 0.9
                    elif nature == 'careful':
                        special_defense *= 1.1
                        special_attack *= 0.9
                    elif nature == 'Gentle':
                        special_defense *= 1.1
                        defense *= 0.9
                    elif nature == 'Hasty':
                        speed *= 1.1
                        defense *= 0.9
                    elif nature == 'Impish':
                        defense *= 1.1
                        special_attack *= 0.9
                    elif nature == 'Jolly':
                        speed *= 1.1
                        special_attack *= 0.9
                    elif nature == 'Lax':
                        defense *= 1.1
                        special_defense *= 0.9
                    elif nature == 'Lonely':
                        attack *= 1.1
                        defense *= 0.9
                    elif nature == 'Mild':
                        special_attack *= 1.1
                        defense *= 0.9
                    elif nature == 'Modest':
                        special_attack *= 1.1
                        attack *= 0.9
                    elif nature == 'Naive':
                        speed *= 1.1
                        special_defense *= 0.9
                    elif nature == 'Naughty':
                        attack *= 1.1
                        special_defense *= 0.9
                    elif nature == 'Quiet':
                        special_attack *= 1.1
                        speed *= 0.9
                    elif nature == 'Rash':
                        special_attack *= 1.1
                        special_defense *= 0.9
                    elif nature == 'Relaxed':
                        defense *= 1.1
                        speed *= 0.9
                    elif nature == 'Sassy':
                        special_defense *= 1.1
                        speed *= 0.9
                    elif nature == 'Tired':
                        speed *= 1.1
                        attack *= 0.9

                    embed = discord.Embed(title=f"{pokemon.get('gender', 'Unknown')} Lvl {level} {pokemon.get('name', 'Unknown')}",
                    description=f"{pokemon.get('nickname', 'None')}\nExp: {pokemon.get('exp', 'Unknown')}/{pokemon.get('expcap', 'Unknown')}\nFriendship: {pokemon.get('friendship', 'Unknown')}\nPokemon Info\nAbility: {ability_name}\nNature: {pokemon.get('nature', 'Unknown')}\nTypes: {types}",
                    colour=0x00b0f4,
                    timestamp=datetime.now())
                    embed.add_field(name=f"Stats         Total    IVS | EVS",
                                    value = f"""`HP:       {hp} - {hp_iv} / {hp_ev}`
                                    `Attack:   {int(attack)} - {atk_iv} / {atk_ev}`
                                    `Defense:  {int(defense)} - {def_iv} / {def_ev}`
                                    `Sp. Atk:  {int(special_attack)} - {spa_iv} / {spa_ev}`
                                    `Sp. Def:  {int(special_defense)} - {spd_iv} / {spd_ev}`
                                    `Speed:    {int(speed)} - {spe_iv} / {spe_ev}`
                                    `IV %`                           `{iv_percentage}%`""",inline=False)
                    embed.set_thumbnail(url=ctx.author.avatar)
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
                pokemon_data = pb.pokemon(pokemon.get('name', 'Unknown').lower())
                types = ', '.join(t.type.name for t in pokemon_data.types)
                ability_name = pokemon.get('ability', 'Unknown')
                level = pokemon.get('level', 'Unknown')

                # Calculate stats based on IVs and EVs
                hp_base = pokemon_data.stats[0].base_stat
                atk_base = pokemon_data.stats[1].base_stat
                def_base = pokemon_data.stats[2].base_stat
                spa_base = pokemon_data.stats[3].base_stat
                spd_base = pokemon_data.stats[4].base_stat
                spe_base = pokemon_data.stats[5].base_stat

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

                hp = round((((2 * hp_base + hp_iv + (hp_ev / 4)) * level) / 100) + level + 10)
                attack = round((((2 * atk_base + atk_iv + (atk_ev / 4)) * level) / 100) + 5)
                defense = round((((2 * def_base + def_iv + (def_ev / 4)) * level) / 100) + 5)
                special_attack = round((((2 * spa_base + spa_iv + (spa_ev / 4)) * level) / 100) + 5)
                special_defense = round((((2 * spd_base + spd_iv + (spd_ev / 4)) * level) / 100) + 5)
                speed = round((((2 * spe_base + spe_iv + (spe_ev / 4)) * level) / 100) + 5)

                total_ivs = hp_iv + atk_iv + def_iv + spa_iv + spd_iv + spe_iv
                iv_percentage = round((total_ivs / 186) * 100)

                embed = discord.Embed(title=f"{pokemon.get('gender', 'Unknown')} Lvl {level} {pokemon.get('name', 'Unknown')}",
                description=f"{pokemon.get('nickname', 'None')}\nExp: {pokemon.get('exp', 'Unknown')}/{pokemon.get('expcap', 'Unknown')}\nFriendship: {pokemon.get('friendship', 'Unknown')}\nPokemon Info\nAbility: {ability_name}\nNature: {pokemon.get('nature', 'Unknown')}\nTypes: {types}",
                colour=0x00b0f4,
                timestamp=datetime.now())
                embed.add_field(name=f"Stats         Total    IVS | EVS",
                                    value = f"""`HP:       {hp} - {hp_iv} / {hp_ev}`
                                    `Attack:   {int(attack)} - {atk_iv} / {atk_ev}`
                                    `Defense:  {int(defense)} - {def_iv} / {def_ev}`
                                    `Sp. Atk:  {int(special_attack)} - {spa_iv} / {spa_ev}`
                                    `Sp. Def:  {int(special_defense)} - {spd_iv} / {spd_ev}`
                                    `Speed:    {int(speed)} - {spe_iv} / {spe_ev}`
                                    `IV %`                           `{iv_percentage}%`""",inline=False)
                embed.set_thumbnail(url=ctx.author.avatar)
                embed.set_image(url=pokemon.get('image_url', ''))
                embed.set_footer(text=f"ID: {pokemon.get('id', 'Unknown')}/{len(user_pokemon)}")
                await ctx.send(embed=embed)
                return

        # If the loop finishes without finding the Pokémon, send a message
        await ctx.send(f"No information found for Pokémon with ID {pokemon_id}.")

async def setup(bot):
    await bot.add_cog(Pokemon(bot))

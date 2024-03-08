import json
import discord
import math
import asyncio
from datetime import datetime
import requests
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

class Market(commands.Cog):
    """
    A cog for managing market-related commands.
    """
    def __init__(self, bot):
        """
        Initialize the Market cog.

        Parameters:
        - bot (discord.ext.commands.Bot): The bot instance.
        """
        self.bot = bot
    @commands.command(aliases=['mshow'])
    async def market(self, ctx, page: int = 1):
        # Load market data
        with open('market.json', 'r') as file:
            market_data = json.load(file)

        # Calculate total pages
        total_pages = math.ceil(len(market_data['pokemon']) / 10)

        # Check if the requested page is within the range
        if page < 1 or page > total_pages:
            await ctx.send(f"Invalid page number. Please provide a page between 1 and {total_pages}.")
            return

        # Create an embed to display market information
        embed = discord.Embed(title="Market", color=discord.Color.blue())

        # Determine start and end index for the page
        start_index = (page - 1) * 10
        end_index = min(start_index + 10, len(market_data['pokemon']))

        # Add fields for each pokemon in the market
        for pokemon in market_data['pokemon'][start_index:end_index]:
            name = pokemon['name']
            owner_id = pokemon['ownerid']
            owner_member = ctx.guild.get_member(int(owner_id))  # Get discord.Member object
            
            # Determine the owner's name or display name
            if owner_member:
                owner_name = owner_member.display_name
            else:
                owner_name = pokemon.get('owner_name', f"Unknown User ({owner_id})")
            
            # Calculate IV percentages
            iv_total = pokemon['hpiv'] + pokemon['atkiv'] + pokemon['defiv'] + pokemon['spatkiv'] + pokemon['spdiv'] + pokemon['speiv']
            iv_percentage = round((iv_total / 186) * 100)
            
            iv_percentages = f"IV: {iv_percentage}%"
            embed.add_field(name=f"**{name}** (Owner: {owner_name})", value=iv_percentages, inline=False)

        # Add page information to the embed
        embed.set_footer(text=f"Page {page}/{total_pages}")

        # Send the embed and add reaction controls
        message = await ctx.send(embed=embed)
        if total_pages > 1:
            await message.add_reaction('⬅️')  # Left arrow
            await message.add_reaction('➡️')  # Right arrow

        # Reaction handling function
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['⬅️', '➡️']

        # Reaction control loop
        while True:
            try:
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                if str(reaction.emoji) == '⬅️':
                    page = max(page - 1, 1)
                elif str(reaction.emoji) == '➡️':
                    page = min(page + 1, total_pages)
                await message.delete()
                await self.market(ctx, page)
                break
            except asyncio.TimeoutError:
                await message.clear_reactions()
                break

    @has_started()
    @commands.command(aliases=['mremove'])
    async def marketremove(self, ctx, pokemon_id: int):
        # Load market data
        with open('market.json', 'r') as file:
            market_data = json.load(file)

        # Find the pokemon in the market by ID
        found_pokemon = None
        for pokemon in market_data['pokemon']:
            if pokemon.get('id') == pokemon_id:
                found_pokemon = pokemon
                break

        if found_pokemon is None:
            await ctx.send("Pokemon not found in the market.")
            return

        # Check if the owner of the pokemon is the buyer
        buyer_id = str(ctx.author.id)
        if found_pokemon['ownerid'] != buyer_id:
            await ctx.send("You don't own this Pokémon.")
            return

        # Remove the pokemon from the market
        market_data['pokemon'].remove(found_pokemon)

        # Save the updated data back to market.json
        with open('market.json', 'w') as file:
            json.dump(market_data, file, indent=4)

        await ctx.send(f"{found_pokemon['name']} has been removed from the market.")
    @has_started()
    @commands.command(aliases=['mbuy'])
    async def marketbuy(self, ctx, pokemon_id: int):
        # Load market data
        with open('market.json', 'r') as file:
            market_data = json.load(file)

        # Find the pokemon in the market by ID
        found_pokemon = None
        for pokemon in market_data['pokemon']:
            if pokemon.get('id') == pokemon_id:
                found_pokemon = pokemon
                break

        if found_pokemon is None:
            await ctx.send("Pokemon not found in the market.")
            return

        # Get the buyer's user ID
        buyer_id = str(ctx.author.id)

        # Load user data
        with open('user_data.json', 'r') as file:
            user_data = json.load(file)

        # Check if the buyer has enough tokens to buy the pokemon
        if user_data[buyer_id]['tokens'] < found_pokemon['price']:
            await ctx.send("You don't have enough tokens to buy this pokemon.")
            return

        # Check if the owner of the pokemon is not the buyer
        if found_pokemon['ownerid'] == buyer_id:
            await ctx.send("You cannot buy your own Pokémon.")
            return

        # Remove the bought pokemon from market
        market_data['pokemon'].remove(found_pokemon)

        # Update buyer's tokens and save the updated user data
        user_data[buyer_id]['tokens'] -= found_pokemon['price']
        with open('user_data.json', 'w') as file:
            json.dump(user_data, file, indent=4)

        # Update the original trainer's tokens and save the updated user data
        ot_id = found_pokemon['OT']
        user_data[ot_id]['tokens'] += found_pokemon['price']
        with open('user_data.json', 'w') as file:
            json.dump(user_data, file, indent=4)

        # Remove the bought pokemon from the original trainer's collection
        self.remove_pokemon_from_collection(ot_id, found_pokemon['id'])

        # Update the ownerid to the buyer's id
        found_pokemon['ownerid'] = buyer_id

        # Add the bought pokemon to the buyer's collection with a unique ID
        self.save_pokemon_to_collection(buyer_id, found_pokemon)

        # Save the updated data back to market.json
        with open('market.json', 'w') as file:
            json.dump(market_data, file, indent=4)

        await ctx.send(f"Congratulations! You've successfully bought {found_pokemon['name']}.")

    def remove_pokemon_from_collection(self, user_id, pokemon_id):
        # Load collections data
        with open('collections.json', 'r') as file:
            collections_data = json.load(file)

        # Find the user's collection
        user_collection = collections_data.get(str(user_id), [])

        # Remove the pokemon from the collection
        removed_pokemon = None
        for pokemon in user_collection:
            if pokemon['id'] == pokemon_id:
                removed_pokemon = pokemon
                user_collection.remove(pokemon)
                break

        if removed_pokemon is None:
            return  # Pokemon not found in the user's collection

        # Update the IDs of the remaining pokemon
        for index, pokemon in enumerate(user_collection, start=1):
            pokemon['id'] = index

        # Update the collections data
        collections_data[str(user_id)] = user_collection

        # Save the updated collections data back to collections.json
        with open('collections.json', 'w') as file:
            json.dump(collections_data, file, indent=4)

    def save_pokemon_to_collection(self, user_id, pokemon_object):
        # Load the existing collections from the file
        try:
            with open('collections.json', 'r') as file:
                collections = json.load(file)
        except FileNotFoundError:
            collections = {}

        # Get the user's collection or create an empty list if it doesn't exist
        user_collection = collections.get(str(user_id), [])

        # Generate a unique ID for the new Pokémon
        pokemon_id = len(user_collection) + 1

        # Update the ID of the pokemon_object
        pokemon_object['id'] = pokemon_id

        # Append the Pokémon object to the user's collection
        user_collection.append(pokemon_object)

        # Update the collections dictionary with the modified user collection
        collections[str(user_id)] = user_collection

        # Save the updated collections back to the file
        with open('collections.json', 'w') as file:
            json.dump(collections, file, indent=4)

    @has_started()
    @commands.command(aliases=['madd'])
    async def market_add(self, ctx, pokemon_id: int, price: int):
        # Load user's collection
        with open('collections.json', 'r') as file:
            collections_data = json.load(file)

        # Check if the invoker's ID is in the collections data
        user_id = str(ctx.author.id)
        if user_id not in collections_data:
            await ctx.send("You don't have any Pokemon in your collection.")
            return

        # Check if the provided pokemon_id exists in the user's collection
        user_collection = collections_data[user_id]
        found_pokemon = None
        for pokemon in user_collection:
            if pokemon.get('id') == pokemon_id:
                found_pokemon = pokemon
                break

        if found_pokemon is None:
            await ctx.send("You don't have the specified Pokemon in your collection.")
            return

        # Add the Pokemon details to the market
        with open('market.json', 'r') as file:
            market_data = json.load(file)

        # Confirm with the user before adding the Pokemon to the market
        confirmation_message = f"Do you want to add {found_pokemon['name']} to the market for {price}?"
        confirmation = await ctx.send(confirmation_message)
        await confirmation.add_reaction('✅')  # Add check mark reaction
        await confirmation.add_reaction('❌')  # Add cross mark reaction

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['✅', '❌']

        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            if str(reaction.emoji) == '✅':
                # Update Pokemon details
                found_pokemon.update({
                    "id": len(market_data['pokemon']) + 1,  # Adjust ID
                    "ownerid": user_id,
                    "OT": user_id,
                    "nickname": "",
                    "friendship": 0,
                    "favorite": False,
                    "level": found_pokemon.get("level", "None"),
                    "exp": found_pokemon.get('exp', 0),
                    "expcap": found_pokemon.get("expcap", 0),
                    "nature": found_pokemon.get("nature", "None"),
                    "hpiv": found_pokemon.get("hpiv", 0),
                    "atkiv": found_pokemon.get("atkiv", 0),
                    "defiv": found_pokemon.get("defiv", 0),
                    "spatkiv": found_pokemon.get("spatkiv", 0),
                    "spdiv": found_pokemon.get("spdiv", 0),
                    "speiv": found_pokemon.get("speiv", 0),
                    "hpev": found_pokemon.get("hpev", 0),
                    "atkev": found_pokemon.get("atkev", 0),
                    "defev": found_pokemon.get("defev", 0),
                    "spatkev": found_pokemon.get("spatkev", 0),
                    "spdefev": found_pokemon.get("spdefev", 0),
                    "speedev": found_pokemon.get("speedev", 0),
                    "image_url": found_pokemon.get('image_url', ''),
                    "helditem": "",
                    "is_shiny": False,
                    "price": price
                })
                market_data['pokemon'].append(found_pokemon)
                with open('market.json', 'w') as file:
                    json.dump(market_data, file, indent=4)
                await ctx.send(f"{found_pokemon['name']} has been added to the market for {price}.")
            else:
                await ctx.send("Operation cancelled.")
        except TimeoutError:
            await ctx.send("Timed out. Please try again later.")
    @commands.command(aliases=['minfo'])
    async def marketinfo(self, ctx, market_id: int):
        with open('market.json', 'r') as file:
            market_data = json.load(file)

        # Search for the provided market ID in the market data
        found_pokemon = None
        for pokemon in market_data['pokemon']:
            if pokemon.get('id') == market_id:
                found_pokemon = pokemon
                break

        if found_pokemon is None:
            await ctx.send("Pokemon not found in the market.")
            return

        # Call the display_pokemon_info function to display the Pokemon's info
        await self.display_pokemon_info(ctx, found_pokemon, market_data['pokemon'])

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
                                description=f"OT: <@{ot.id}>\n Nickname: {pokemon.get('nickname', 'None')}\nExp: {pokemon.get('exp', 'Unknown')}/{pokemon.get('expcap', 'Unknown')}\nPokemon Info\nAbility: {ability_name}\n Nature: {pokemon.get('nature', 'Unknown')}\nTypes: {types}\nPrice: {pokemon.get('price', 'Unknown'):,d}",
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


async def setup(bot):
    await bot.add_cog(Market(bot))

import pokebase as pb
import random
from discord.ext import commands, tasks
import json
import asyncio

natlist = ['Lonely', 'Brave', 'Adamant', 'Naughty', 'Bold', 'Relaxed', 'Impish', 'Lax', 'Timid', 'Hasty', 'Jolly', 'Naive', 'Modest', 'Mild', 'Quiet', 'Rash', 'Calm', 'Gentle', 'Sassy', 'Careful', 'Bashful', 'Quirky', 'Serious', 'Docile', 'Hardy']

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

class Safari(commands.Cog):
    """A cog for managing expeditions and encounters in the safari adventure game."""
    
    def __init__(self, bot):
        """Initialize the Safari cog."""
        self.bot = bot
        self.expedition_running = {}  # Dictionary to track running expeditions for each user
        self.encounter_rates = self.load_encounter_rates()  # Load encounter rates from JSON file
        self.expedition_levels = self.load_expedition_levels()  # Load expedition levels from JSON file
        self.expedition_locations = {}  # Stores expedition locations for each user

        # Start the passive encounter task
        self.passive_encounter_task.start()

    def select_ability(self, pokemon_name, hidden_ability_probability):
        """Select an ability for the Pokémon."""
        
        # Fetch the Pokémon resource based on the name
        pokemon = pb.pokemon(pokemon_name.lower())
        
        # Fetch abilities from species information
        hidden_abilities = []
        regular_abilities = []
        for ability in pokemon.abilities:
            # Check if the ability is a hidden ability (introduced in Gen 5 or later and not main series)
            if ability.is_hidden:
                hidden_abilities.append(ability.ability.name)
            else:
                regular_abilities.append(ability.ability.name)
        
        if hidden_abilities:
            # If hidden abilities are available, randomly select one based on probability
            if random.random() < hidden_ability_probability:
                return random.choice(hidden_abilities)
        
        # If no hidden abilities or probability not met, choose a regular ability
        return random.choice(regular_abilities)
    
    async def update_pokemon_ids(self, user_id, user_pokemon):
        """Update the IDs of Pokémon in a user's collection."""
        for index, pokemon in enumerate(user_pokemon, start=1):
            pokemon['id'] = index
        return user_pokemon
    
    def load_encounter_rates(self):
        """Load encounter rates from the encounter_rates.json file."""
        try:
            with open('encounter_rates.json', 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def cog_unload(self):
        """Cleanup tasks when the cog is unloaded."""
        # Stop the passive encounter task when the cog is unloaded
        self.passive_encounter_task.cancel()

    @tasks.loop(minutes=0.5)  # Trigger every 0.5 minutes
    async def passive_encounter_task(self):
        """Task to trigger passive encounters for users on expeditions."""
        for user_id in self.expedition_running.keys():
            # Trigger passive encounter for each user on an expedition
            await self.trigger_passive_encounter(user_id)

    async def trigger_passive_encounter(self, user_id):
        """Trigger a passive encounter for a user on an expedition."""
        # Get expedition location and level for the user
        expedition_location = self.expedition_locations.get(user_id, "forest")
        expedition_level = self.expedition_levels.get(user_id, 1)

        # Get encounter rates for the specified location and level
        location_encounter_rates = self.encounter_rates.get(expedition_location, {}).get(str(expedition_level), {})
        
        # Determine encounter probabilities for each Pokémon species
        total_encounter_rate = sum(location_encounter_rates.values())
        encounter_probabilities = {pokemon: rate / total_encounter_rate for pokemon, rate in location_encounter_rates.items()}
        
        # Randomly select a Pokémon species based on encounter probabilities
        pokemon_found = random.choices(list(encounter_probabilities.keys()), weights=list(encounter_probabilities.values()))[0]

        # Save the found Pokémon to the user's collection
        self.save_pokemon_to_collection(user_id, pokemon_found)

        # Inform the user about the passive encounter
        user = await self.bot.fetch_user(user_id)
        if user:
            await user.send(f"A wild {pokemon_found} appeared during your expedition in the {expedition_location}!")

    def load_expedition_levels(self):
        """Load expedition levels from the expedition_levels.json file."""
        try:
            with open('expedition_levels.json', 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def save_expedition_levels(self):
        """Save expedition levels to the expedition_levels.json file."""
        with open('expedition_levels.json', 'w') as file:
            json.dump(self.expedition_levels, file, indent=4)

    @commands.command()
    @has_started()
    async def safari(self, ctx, location: str):
        """Start an expedition in the specified location."""
        user_id = ctx.author.id

        # Check if the user has an entry in user_data.json
        if not self.has_user_data(user_id):
            await ctx.send("You need to start your adventure first before going on a safari!")
            return

        if user_id in self.expedition_running:
            await ctx.send("You're already on an expedition. Please wait for it to finish.")
            return

        # Check if the specified location is valid
        if location.lower() not in ["forest", "mountain", "cave"]:
            await ctx.send("Invalid safari location. Please choose from 'forest', 'mountain', or 'cave'.")
            return

        # Set initial expedition level and location for the user if not already set
        if str(user_id) in self.expedition_levels:
            self.expedition_locations[user_id] = location.lower()
            self.save_expedition_levels()  # Save updated expedition levels to JSON file
        else:
            # If user doesn't already have an entry, save the location and level    
            self.expedition_levels[user_id] = 1
            self.expedition_locations[user_id] = location.lower()
            self.save_expedition_levels()  # Save updated expedition location to JSON file

        await ctx.send(f"Starting an expedition in the {location.lower()}...")

        # Simulate expedition duration (e.g., 10 seconds for demonstration)
        await asyncio.sleep(10)

        # Generate a random Pokémon based on expedition level and location
        pokemon_found = await self.generate_pokemon(user_id)

        await ctx.send(f"You found a wild {pokemon_found}!")

        # Add the user to the list of running expeditions
        self.expedition_running[user_id] = True

        # End expedition after 24 hours
        await asyncio.sleep(0.5 * 60 * 60)  # 24*60*60

        await ctx.send("Expedition completed!")

        # Remove user from running expeditions
        del self.expedition_running[user_id]

    def has_user_data(self, user_id):
        """Check if the user has an entry in user_data.json."""
        try:
            with open('user_data.json', 'r') as file:
                user_data = json.load(file)
                return str(user_id) in user_data
        except FileNotFoundError:
            return False

    async def generate_pokemon(self, user_id, passive=False):
        """Generate a random Pokémon based on expedition level and location."""
        if passive:
            # Passive encounter: Generate Pokémon without expedition context
            expedition_location = random.choice(list(self.encounter_rates.keys()))
            expedition_level = random.choice(list(self.encounter_rates[expedition_location].keys()))
        else:
            # Active encounter: Use the user's expedition location and level
            expedition_location = self.expedition_locations.get(user_id, "forest")
            expedition_level = self.expedition_levels.get(user_id, 1)

        # Get encounter rates for the specified location and level
        location_encounter_rates = self.encounter_rates.get(expedition_location, {}).get(str(expedition_level), {})
        
        # Determine encounter probabilities for each Pokémon species
        total_encounter_rate = sum(location_encounter_rates.values())
        encounter_probabilities = {pokemon: rate / total_encounter_rate for pokemon, rate in location_encounter_rates.items()}
        
        # Randomly select a Pokémon species based on encounter probabilities
        pokemon_found = random.choices(list(encounter_probabilities.keys()), weights=list(encounter_probabilities.values()))[0]

        # Save the found Pokémon to the user's collection
        self.save_pokemon_to_collection(user_id, pokemon_found)

        return pokemon_found

    def get_pokemon_image_url(self, pokemon_name):
        """Get the image URL for a Pokémon."""
        # Get the Pokemon species object based on the name
        pokemon_species = pb.pokemon(pokemon_name.lower())

        # Get the URL for the official artwork
        official_artwork_url = pokemon_species.sprites.other.official_artwork.front_default
        return official_artwork_url
    
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
        level = random.randint(1, 100)
        move1 = move2 = move3 = move4 = "tackle"

        try: 
            # Get the Pokémon species object
            pokemon_species = pb.pokemon(pokemon_name.lower())
            pokemon_specie = pb.pokemon_species(pokemon_name.lower())
            # Fetch abilities from species information
            abilities = [ability.ability.name for ability in pokemon_species.abilities]
            # Fetch base experience from species information
            base_experience = pokemon_species.base_experience
            # Fetch gender rate
            gender_rate = pokemon_specie.gender_rate
            # Assign probabilities for hidden abilities
            hidden_ability_probability = 0.33  # Example probability for hidden ability

        except Exception as e:
            print(f"Error fetching species information for {pokemon_name}: {e}")
            # Default values if an error occurs
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
            "name": pokemon_name,
            "gender": gender,
            "ability": ability,
            "nickname": "",
            "friendship": 0,
            "favorite": False,
            "level": random.randint(1, 30),
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
        }

        # Append the Pokémon object to the user's collection
        user_collection.append(pokemon_object)

        # Update the collections dictionary with the modified user collection
        collections[str(user_id)] = user_collection

        # Save the updated collections back to the file
        with open('collections.json', 'w') as file:
            json.dump(collections, file, indent=4)

async def setup(bot):
    await bot.add_cog(Safari(bot))

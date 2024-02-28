import disnake
import random
from disnake.ext import commands, tasks
import random
import json
import asyncio
from datetime import datetime, timedelta

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
        # Load data from JSON file that holds available moves, names of Pokémon, and image URLs
        with open('pokemon_data.json', 'r') as file:
            pokemon_data = json.load(file)
        
        # Find the image URL for the given Pokémon name
        for entry in pokemon_data:
            if entry["name"] == pokemon_name:
                return entry["image_url"]
            
    def get_random_moves(self, pokemon_name):
        """Get random moves for a Pokémon."""
        try:
            with open('moves.json', 'r') as file:
                moves_data = json.load(file)
                moves = moves_data.get(pokemon_name, [])
                if len(moves) >= 2:
                    return random.sample(moves, 2)
                elif moves:
                    return moves, moves[0]  # If only one move available, use it for both move slots
                else:
                    return ["Tackle", "Tackle"]  # Default moves if no moves data is available
        except FileNotFoundError:
            return ["Tackle", "Tackle"]  # Default moves if moves.json file is not found

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
        move1, move2 = self.get_random_moves(pokemon_name)

        # Get image URL for the Pokémon
        image_url = self.get_pokemon_image_url(pokemon_name)

        # Create a Pokémon object
        pokemon_object = {
            "id": pokemon_id,
            "name": pokemon_name,
            "level": random.randint(1, 30),
            "move 1": move1,
            "move 2": move2,
            "image_url": image_url,
            "HP": 100,
            "ATK": random.randint(1,31),
            "DEF": random.randint(1,31),
            "selected": False
        }

        # Append the Pokémon object to the user's collection
        user_collection.append(pokemon_object)

        # Update the collections dictionary with the modified user collection
        collections[str(user_id)] = user_collection

        # Save the updated collections back to the file
        with open('collections.json', 'w') as file:
            json.dump(collections, file, indent=4)

def setup(bot):
    """Add the Safari cog to the bot."""
    bot.add_cog(Safari(bot))

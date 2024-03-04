from discord.ext import commands, tasks
import pokebase as pb
import random
import json

class Raids(commands.Cog):
    """
    A cog for managing raids, including auto-attacks, joining raids, and battling raid bosses.
    """
    def __init__(self, bot):
        """
        Initializes the Raid cog.

        Parameters:
            bot (commands.Bot): The bot instance.
        """
        self.bot = bot
        self.load_raid_bosses()
        self.ongoing_raids = {}  # Dictionary to store ongoing raids
        self.selected_pokemon = {} # Dictionary to store selected Pokémon by users
        self.attack_task = self.auto_attack_task  # Assign auto_attack_task to attack_task

    @commands.command()
    async def auto_attack(self, ctx, action: str):
        """
        Starts or stops the auto-attack task.

        Parameters:
            ctx (commands.Context): The context in which the command is being invoked.
            action (str): Either 'start' to start the auto-attack or 'stop' to stop it.
        """
        if action.lower() == 'start':
            if self.attack_task and not self.attack_task.is_running():
                self.attack_task.start()  # Start the attack task if not already running
                await ctx.send("Auto-attack started.")
            else:
                await ctx.send("Auto-attack is already running.")
        elif action.lower() == 'stop':
            if self.attack_task and self.attack_task.is_running():
                self.attack_task.cancel()  # Cancel the attack task if running
                await ctx.send("Auto-attack stopped.")
            else:
                await ctx.send("Auto-attack is not running.")
        else:
            await ctx.send("Invalid action. Please use 'start' or 'stop'.")

    @tasks.loop(minutes=0.25)
    async def auto_attack_task(self):
        """
        Performs automated attacks on ongoing raid bosses.

        Loops through ongoing raids and processes attacks from participants.
        """
        print("Auto attack task started")
        print("Ongoing raids:", self.ongoing_raids.items())
        
        # Load data from collections.json
        try:
            with open('collections.json', 'r') as file:
                collections_data = json.load(file)
        except FileNotFoundError:
            print("Error: collections.json not found.")
            return
        
        for channel_id, raid_info in self.ongoing_raids.items():
            print(f"Processing raid in channel {channel_id}")
            if raid_info['participants']:
                print("Participants found")
                for participant_id in raid_info['participants']:
                    print(f"Processing participant {participant_id}")
                    
                    # Get the participant's collection data
                    participant_collection = collections_data.get(str(participant_id), [])
                    
                    # Filter out the selected Pokémon
                    selected_pokemon = next((pokemon for pokemon in participant_collection if pokemon.get('selected', False)), None)
                    
                    if selected_pokemon:
                        print("Pokemon found for participant")
                        attack_stat = selected_pokemon.get('ATK', 0)
                        damage = random.randint(attack_stat // 2, attack_stat)  # Calculate damage based on attack stat
                        raid_boss_hp = raid_info['hp']
                        raid_boss_hp -= damage
                        raid_info['hp'] = max(0, raid_boss_hp)  # Ensure HP doesn't go below 0

                        if raid_boss_hp <= 0:
                            print("Raid boss defeated!")
                            channel = await self.bot.fetch_channel(channel_id)
                            message = await channel.fetch_message(raid_info['message_id'])
                            await self.end_raid(message.channel.id, winner=self.bot.get_user(participant_id).name)
                        else:
                            print("Raid boss survived the attack")
                            channel = await self.bot.fetch_channel(channel_id)
                            message = await channel.fetch_message(raid_info['message_id'])
                            await message.channel.send(f"{self.bot.get_user(participant_id).name} attacked the raid boss with {selected_pokemon['name']}! Raid boss HP: {raid_boss_hp}")
                            print("Attack message sent")
                    else:
                        print("No Pokémon found for participant")
                        # Handle the case where the participant hasn't selected a Pokémon

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Listener that executes when the bot is fully ready.
        """
        print('Bot is ready.')

    @auto_attack_task.before_loop
    async def before_auto_attack_task(self):
        """
        Waits until the bot is fully ready before starting the auto-attack loop.
        """
        await self.bot.wait_until_ready()  # Wait until the bot is fully ready before starting the loop

    def load_raid_bosses(self):
        """
        Loads raid bosses from the raid_bosses.json file.
        """
        try:
            with open('raid_bosses.json', 'r') as file:
                self.raid_bosses = json.load(file)
        except FileNotFoundError:
            self.raid_bosses = []

    async def end_raid(self, channel_id, winner=None):
        """
        Ends an ongoing raid.

        Parameters:
            channel_id (int): The ID of the channel where the raid is happening.
            winner (str, optional): The name of the winner of the raid. Defaults to None.
        """
        if channel_id in self.ongoing_raids:
            raid_data = self.ongoing_raids.pop(channel_id)
            if raid_data['participants']:
                for participant_id in raid_data['participants']:
                    participant = self.bot.get_user(participant_id)
                    if participant:
                        self.save_pokemon_to_collection(participant.id, raid_data['boss'])
                        await participant.send(f"{participant.display_name} caught the raid boss!")

            if winner:
                await self.bot.get_channel(channel_id).send(f"The raid has ended! {winner} caught the raid boss!")
            else:
                await self.bot.get_channel(channel_id).send("The raid has ended! No one caught the raid boss.")

    @commands.command()
    async def select(self, ctx, pokemon_id: int):
        """
        Selects a Pokémon from the user's collection.

        Parameters:
            ctx (commands.Context): The context in which the command is being invoked.
            pokemon_id (int): The ID of the Pokémon to select.
        """
        user_id = str(ctx.author.id)  # Get the Discord ID of the user who invoked the command

        if self.is_raid_ongoing(ctx.channel.id):
            await ctx.send("You cannot select a Pokémon while a raid is ongoing.")
            return

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

        # Check if the provided pokemon_id is valid
        if pokemon_id < 1 or pokemon_id > len(user_pokemon):
            await ctx.send("Invalid pokemon ID.")
            return

        # Unselect any previously selected pokemon
        for pokemon in user_pokemon:
            pokemon['selected'] = False

        # Select the new pokemon
        selected_pokemon = user_pokemon[pokemon_id - 1]
        selected_pokemon['selected'] = True

        # Save the updated collections data back to the JSON file
        try:
            with open('collections.json', 'w') as file:
                json.dump(collections_data, file, indent=4)
        except Exception as e:
            print(e)
            await ctx.send("Failed to update selected pokemon.")
            return

        await ctx.send(f"Successfully selected {selected_pokemon['name']}.")

    def is_raid_ongoing(self, channel_id):
        return channel_id in self.ongoing_raids

    @commands.command()
    async def start_raid(self, ctx):
        """
        Starts a raid in the current channel.
        """
        if not self.raid_bosses:
            await ctx.send("No raid bosses available. Please add raid bosses first.")
            return

        if ctx.channel.id in self.ongoing_raids:
            await ctx.send("A raid is already ongoing in this channel.")
            return

        raid_boss = random.choice(self.raid_bosses)
        raid_level = random.randint(1, 5)
        raid_hp = raid_level * 100
        raid_message = await ctx.send(f"A level {raid_level} {raid_boss} appeared with {raid_hp} HP! Join the raid with ';join_raid'.")
        
        self.ongoing_raids[ctx.channel.id] = {
            'boss': raid_boss,
            'level': raid_level,
            'hp': raid_hp,
            'participants': [],
            'message_id': raid_message.id
        }

    def get_selected_pokemon(self, user_id):
        # Load collections data from JSON file
        try:
            with open('collections.json', 'r') as file:
                collections_data = json.load(file)
        except FileNotFoundError:
            return None

        user_pokemon = collections_data.get(user_id, [])
        for pokemon in user_pokemon:
            if pokemon.get('selected', False):
                return pokemon

        return None
    
    @commands.command()
    async def join_raid(self, ctx):
        """
        Allows a user to join an ongoing raid.
        """
        if ctx.channel.id not in self.ongoing_raids:
            await ctx.send("No raid is ongoing in this channel.")
            return

        if ctx.author.id in self.ongoing_raids[ctx.channel.id]['participants']:
            await ctx.send("You're already in the raid!")
            return

        user_id = str(ctx.author.id)
        user_pokemon = self.get_selected_pokemon(user_id)
        if user_pokemon:
            self.ongoing_raids[ctx.channel.id]['participants'].append(ctx.author.id)
            await ctx.send(f"{ctx.author.name} joined the raid!")
        else:
            await ctx.send("You haven't selected a Pokémon.")

    @commands.command()
    async def raidattack(self, ctx):
        """
        Allows a user to attack the raid boss during a raid.
        """
        if ctx.channel.id not in self.ongoing_raids:
            await ctx.send("No raid is ongoing in this channel.")
            return

        if ctx.author.id not in self.ongoing_raids[ctx.channel.id]['participants']:
            await ctx.send("You're not in the raid!")
            return

        # Load collections data from JSON file
        try:
            with open('collections.json', 'r') as file:
                collections_data = json.load(file)
        except FileNotFoundError:
            await ctx.send("Collections data file not found.")
            return

        user_id = str(ctx.author.id)
        user_pokemon = collections_data.get(user_id, [])
        
        # Check if the user has a selected Pokémon
        selected_pokemon = None
        for pokemon in user_pokemon:
            if pokemon.get('selected', False):
                selected_pokemon = pokemon
                break
        
        if not selected_pokemon:
            await ctx.send("You haven't selected a Pokémon.")
            return

        # Calculate damage based on the selected Pokémon's attack stat
        attack_stat = selected_pokemon.get('ATK', 0)
        damage = random.randint(attack_stat // 2, attack_stat)  # Calculate damage based on attack stat
        raid_boss_hp = self.ongoing_raids[ctx.channel.id]['hp']
        raid_boss_hp -= damage
        self.ongoing_raids[ctx.channel.id]['hp'] = max(0, raid_boss_hp)  # Ensure HP doesn't go below 0

        if raid_boss_hp <= 0:
            await self.end_raid(ctx, winner=ctx.author.name)
        else:
            await ctx.send(f"{ctx.author.name} attacked the raid boss with {selected_pokemon['name']}! Raid boss HP: {raid_boss_hp}")

    def save_pokemon_to_collection(self, user_id, pokemon_name):
        """
        Saves a captured Pokémon to the user's collection.

        Parameters:
            user_id (int): The ID of the user.
            pokemon_name (str): The name of the Pokémon to save.
        """
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
            "ATK": random.randint(20,31),
            "DEF": random.randint(20,31),
            "selected": False
        }

        # Append the Pokémon object to the user's collection
        user_collection.append(pokemon_object)

        # Update the collections dictionary with the modified user collection
        collections[str(user_id)] = user_collection

        # Save the updated collections back to the file
        with open('collections.json', 'w') as file:
            json.dump(collections, file, indent=4)

    def get_random_moves(self, pokemon_name):
        """
        Gets random moves for a Pokémon.

        Parameters:
            pokemon_name (str): The name of the Pokémon.

        Returns:
            tuple: A tuple containing two random moves.
        """
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

    def get_pokemon_image_url(self, pokemon_name):
        """Get the image URL for a Pokémon."""
        # Get the Pokemon species object based on the name
        pokemon_species = pb.pokemon(pokemon_name.lower())

        # Get the URL for the official artwork
        official_artwork_url = pokemon_species.sprites.other.pokemon_species.sprites.official_artwork.front_default
        return official_artwork_url

async def setup(bot):
    await bot.add_cog(Raids(bot))

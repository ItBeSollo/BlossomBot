import discord
import json
from discord.ui import Button, View
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

class OptionsView(discord.ui.View):
    def __init__(self,challenger_moves, opponent_moves, challenger_id,opponent_id, battle_instance ):
        super().__init__()
        self.challenger_moves = challenger_moves
        self.opponent_moves = opponent_moves
        self.challenger_id = challenger_id
        self.opponent_id = opponent_id
        self.battle_instance = battle_instance  # Add battle_instance attribute
    @discord.ui.button(label="Your Options", style=discord.ButtonStyle.primary)
    async def options_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="Your Pokémon's Moves", color=0x00ff00)
        if interaction.user.id == self.challenger_id:
            for move_num, move_name in enumerate(self.challenger_moves, start=1):
                embed.add_field(name=f"Move {move_num}", value=move_name, inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif interaction.user.id == self.opponent_id:
            for move_num, move_name in enumerate(self.opponent_moves, start=1):
                embed.add_field(name=f"Move {move_num}", value=move_name, inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("You can only view your own Pokémon's moves!", ephemeral=True)
            

                                                
class Battle(commands.Cog):
    class BattleButtonView(View):
        def __init__(self, challenger, opponent, battle_instance, ctx):
            super().__init__()

            self.challenger = challenger
            self.opponent = opponent
            self.accepted = False
            self.battle_instance = battle_instance
            self.ctx = ctx # Store the ctx object

        async def interaction_check(self, interaction: discord.Interaction):
            return interaction.user == self.opponent
        
        @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
        async def accept_button(self, interaction: discord.Interaction, child: discord.ui.Button):
            if await self.interaction_check(interaction):
                for child in self.children:
                    child.disabled=True
                self.accepted = True
                await interaction.response.defer()
                await interaction.followup.send("You have accepted the battle request!", ephemeral=True)
                await interaction.edit_original_response(view=self)
                
                self.battle_instance.battle_participants[self.challenger.id] = self.opponent.id
                self.battle_instance.battle_participants[self.opponent.id] = self.challenger.id

                # Call update_battle_info after the start_battle to update the battle information
                await self.battle_instance.update_battle_info(self.ctx)

        @discord.ui.button(label="Reject", style=discord.ButtonStyle.red)
        async def reject_button(self, interaction: discord.Interaction, child: discord.ui.Button):
            for child in self.children:
                child.disabled=True
            await interaction.response.defer()
            await interaction.followup.send("You have declined the battle request!")
            await interaction.edit_original_response(view=self)


        async def start_battle(self):
            self.accept_button.disabled = True
            self.reject_button.disabled = True

    def __init__(self, bot):
        self.bot = bot
        self.current_turn = None
        self.battle_participants = {}
        self.move_power_levels = {}
        self.opponent = None

    def get_user_selected_pokemon(self, user_id):
        try:
            with open('collections.json', 'r') as file:
                collections_data = json.load(file)
        except FileNotFoundError:
            return []  # Return empty list if file not found
        except json.JSONDecodeError:
            print("Error: collections.json is not valid JSON.")
            return []  # Return empty list if JSON decoding error occurs

        user_pokemon = collections_data.get(str(user_id), [])
        selected_pokemon = [pokemon for pokemon in user_pokemon if pokemon.get('selected', False)]
        return selected_pokemon
    
    async def update_battle_info(self, ctx):
        challenger_id = ctx.author.id
        opponent_id = self.battle_participants[challenger_id]
        
        challenger = ctx.guild.get_member(challenger_id)
        opponent = ctx.guild.get_member(opponent_id)
        
        challenger_pokemon = self.get_user_selected_pokemon(challenger_id)
        opponent_pokemon = self.get_user_selected_pokemon(opponent_id)
        
        challenger_moves = [challenger_pokemon[0]["move 1"], challenger_pokemon[0]["move 2"]]
        opponent_moves = [opponent_pokemon[0]["move 1"], opponent_pokemon[0]["move 2"]]
        view = OptionsView(challenger_moves, opponent_moves, challenger_id, opponent_id, self)

        embed = discord.Embed(title="Battle Information", color=0x00ff00)
        embed.add_field(name=f"{challenger.display_name}'s Pokémon", value=f"HP: {challenger_pokemon[0]['HP']}")
        embed.add_field(name=f"{opponent.display_name}'s Pokémon", value=f"HP: {opponent_pokemon[0]['HP']}")

        message = await ctx.send(embed=embed, view=view)
        return message
    @commands.command()
    @has_started()
    async def challenge(self, ctx, opponent: discord.Member):
        self.opponent = opponent
    
        if ctx.author.bot:
            await ctx.send("Bots cannot initiate battles.")
            return

        if opponent == ctx.author:
            await ctx.send("You can't challenge yourself!")
            return
        
        challenger_id = str(ctx.author.id)
        challenger_pokemon = self.get_user_selected_pokemon(challenger_id)
        if not challenger_pokemon:
            await ctx.send("You haven't selected a Pokémon!")
            return

        opponent_id = str(opponent.id)
        opponent_pokemon = self.get_user_selected_pokemon(opponent_id)
        if not opponent_pokemon:
            await ctx.send(f"{opponent.mention} doesn't have any Pokémon!")
            return
        
        self.battle_participants[ctx.author.id] = opponent.id
        self.current_turn = ctx.author  # Set current turn to the challenger
        await ctx.send(f"{opponent.mention}, you have been challenged to a battle by {ctx.author.mention}!", view=self.BattleButtonView(ctx.author, opponent, self, ctx))
        async def button_check(self, button, user):
            return user == button.author


    def is_in_battle(self, player):
        return player.id in self.battle_participants
    
    async def calculate_damage(self, attacker_stats, defender_stats, power_level):
        attacker_attack = attacker_stats.get("ATK", 0)
        defender_defense = defender_stats.get("DEF", 0)
        damage = int((attacker_attack * power_level) / defender_defense)
        return damage
    
    @commands.command()
    @has_started()
    async def attack(self, ctx, move_num: int):
        if not self.is_in_battle(ctx.author):
            await ctx.send("You are not currently in a battle!")
            return 
        if self.current_turn != ctx.author:
            await ctx.send("It's not your turn to attack!")
            return     

        attacker_id = str(ctx.author.id)
        attacker_data = self.get_user_selected_pokemon(attacker_id)

        if not attacker_data:
            await ctx.send("You don't have any Pokémon!")
            return

        if 1 <= move_num <= 2: 
            move = attacker_data[0].get(f"move {move_num}", "")
            if move:
                if not self.move_power_levels:
                    try:
                        with open('move_powers.json', 'r') as file:
                            self.move_power_levels = json.load(file)
                    except FileNotFoundError:
                        await ctx.send("Move power levels data not found!")
                        return

                power_level = self.move_power_levels.get(move, 0)
                opponent_id = str(self.battle_participants[ctx.author.id])
                opponent_data = self.get_user_selected_pokemon(opponent_id)

                attacker_stats = attacker_data[0]  
                defender_stats = opponent_data[0]  

                damage = await self.calculate_damage(attacker_stats, defender_stats, power_level)
                await ctx.send(f"{ctx.author.mention} uses {move} and deals {damage} damage!")

                opponent_pokemon = self.get_user_selected_pokemon(opponent_id)
                opponent_pokemon[0]['HP'] -= damage
                if opponent_pokemon[0]['HP'] <= 0:
                    await ctx.send(f"{self.opponent.mention}'s Pokémon fainted!")
                    self.end_battle()  # Call end_battle method when opponent's Pokémon faints
                    return

                try:
                    with open('collections.json', 'r') as file:
                        collections_data = json.load(file)
                except (FileNotFoundError, json.JSONDecodeError):
                    await ctx.send("Error loading or parsing collections data.")
                    return
                
                collections_data[opponent_id][0]['HP'] = opponent_pokemon[0]['HP']
                with open('collections.json', 'w') as file:
                    json.dump(collections_data, file)

                await self.update_battle_info(ctx)
                await ctx.send(f"Opponent's Pokémon now has {opponent_pokemon[0]['HP']} HP remaining.")

                # Swap turns to the opponent
                self.current_turn = opponent_id
                
            else:
                await ctx.send("Invalid move number.")
        else:
            await ctx.send("Invalid move number.")
    def end_battle(self):
        self.current_turn = None
        self.battle_participants.clear()
    @commands.command()
    @has_started()
    async def use_item(self, ctx, item_name: str):
        if not self.is_in_battle(ctx.author):
            await ctx.send("You are not currently in a battle!")
            return
        if self.current_turn != ctx.author:
            await ctx.send("It's not your turn to use an item!")
            return
        await ctx.send(f"{ctx.author.mention} uses {item_name}!")
        self.current_turn = self.battle_participants[ctx.author]
        await self.update_battle_info(ctx)  

    @commands.command()
    @has_started()
    async def forfeit(self, ctx):
        if not self.is_in_battle(ctx.author):
            await ctx.send("You are not currently in a battle!")
            return
        await ctx.send(f"{ctx.author.mention} forfeits the battle!")
        self.end_battle()  # Call end_battle method when player forfeits
        self.current_turn = None

async def setup(bot):
    await bot.add_cog(Battle(bot))

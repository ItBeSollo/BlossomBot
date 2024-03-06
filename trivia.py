import discord
import json
import asyncio
import random
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
class Trivia(commands.Cog):
    """
    A cog for managing trivia games, including starting games, answering questions, and displaying leaderboards.
    """
    def __init__(self, bot):
        """
        Initializes the TriviaCog.

        Parameters:
            bot (commands.Bot): The bot instance.
        """
        self.bot = bot
        self.trivia_data = self.load_trivia_data()
        self.trivia_in_progress = {}
        self.user_scores = self.load_user_scores()
        self.user_scores = self.load_user_scores()

    def load_user_scores(self):
        """
        Loads user scores from the 'user_scores.json' file.

        Returns:
            dict: A dictionary containing user scores.
        """
        try:
            with open('user_scores.json', 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}  # Return an empty dictionary if the file doesn't exist
    def load_trivia_data(self):
        """
        Loads trivia questions from a JSON file.

        Returns:
            dict: A dictionary containing trivia questions.
        """
        # Load trivia questions from a JSON file
        with open('trivia_questions.json', 'r') as file:
            return json.load(file)

    @commands.command()
    @has_started()
    async def trivia(self, ctx, difficulty: str = 'medium'):
        """
        Starts a trivia game.

        Parameters:
            ctx (commands.Context): The context in which the command is being invoked.
            difficulty (str, optional): The difficulty level of the trivia game. Defaults to 'medium'.
        """
        # Check if a trivia game is already in progress for the user
        if ctx.author.id in self.trivia_in_progress:
            await ctx.send("You're already playing a trivia game. Please wait for it to finish.")
            return

        # Define token rewards based on difficulty
        token_rewards = {'easy': 100, 'medium': 200, 'hard': 500}

        # Check if the specified difficulty is valid
        if difficulty.lower() not in token_rewards:
            await ctx.send("Invalid difficulty. Please choose from 'easy', 'medium', or 'hard'.")
            return

        # Get trivia questions based on the specified difficulty
        questions = self.trivia_data.get(difficulty.lower(), [])
        if not questions:
            await ctx.send("No questions available for the specified difficulty.")
            return

        # Select a random question from the available questions
        question = random.choice(questions)

        # Send the question to the user
        embed = discord.Embed(title="Trivia Question", description=question['question'], color=discord.Color.blue())
        await ctx.send(embed=embed)

        # Add user to trivia in progress
        self.trivia_in_progress[ctx.author.id] = True

        # Listen for the user's answer
        def check_answer(message):
            return message.author == ctx.author and message.channel == ctx.channel

        try:
            user_answer = await self.bot.wait_for('message', timeout=30.0, check=check_answer)
        except asyncio.TimeoutError:
            await ctx.send("Time's up! You didn't answer in time.")
            del self.trivia_in_progress[ctx.author.id]
            return

        # Check if the user's answer is correct
        if user_answer.content.lower() == question['answer'].lower():
            await ctx.send("Correct answer! Well done!")
            # Update user tokens
            self.update_user_tokens(ctx.author.id, token_rewards[difficulty.lower()])
            await ctx.send(f"You earned {token_rewards[difficulty.lower()]} tokens!")
        else:
            await ctx.send("Sorry, that's incorrect. The correct answer was: " + question['answer'])
        
        # Add a point for each question answered to user's score
        self.update_user_scores(ctx.author.id, 1)

        # Remove user from trivia in progress
        del self.trivia_in_progress[ctx.author.id]

    def update_user_tokens(self, user_id, tokens):
        """
        Updates the token count for a user.

        Parameters:
            user_id (int): The ID of the user.
            tokens (int): The number of tokens to add to the user's count.
        """
        # Load user data from JSON file
        with open('user_data.json', 'r') as file:
            user_data = json.load(file)
        
        # Update user's token count
        user_data[str(user_id)]['tokens'] = user_data.get(str(user_id), {}).get('tokens', 0) + tokens
        
        # Save updated user data to JSON file
        with open('user_data.json', 'w') as file:
            json.dump(user_data, file, indent=4)

    def update_user_scores(self, user_id, points):
        """
        Updates the score for a user.

        Parameters:
            user_id (int): The ID of the user.
            points (int): The number of points to add to the user's score.
        """
        # Load user scores from JSON file
        with open('user_scores.json', 'r') as file:
            user_scores = json.load(file)
        
        # Update user's score
        user_scores[str(user_id)] = user_scores.get(str(user_id), 0) + points
        
        # Save updated user scores to JSON file
        with open('user_scores.json', 'w') as file:
            json.dump(user_scores, file, indent=4)

    @commands.command()
    @has_started()
    async def leaderboard(self, ctx):
        """
        Displays the trivia leaderboard.
        
        Parameters:
            ctx (commands.Context): The context in which the command is being invoked.
        """
        # Load user scores from JSON file
        with open('user_scores.json', 'r') as file:
            user_scores = json.load(file)
        
        # Sort users by score
        sorted_scores = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)

        # Create leaderboard embed
        embed = discord.Embed(title="Trivia Leaderboard", color=discord.Color.gold())
        for idx, (user_id, score) in enumerate(sorted_scores[:5], start=1):
            try:
                member = await ctx.guild.fetch_member(int(user_id))
                if member:
                    embed.add_field(name=f"{idx}. {member.display_name}", value=f"Score: {score}", inline=False)
            except discord.NotFound:
                # Handle the case where the member is not found
                embed.add_field(name=f"{idx}. User (ID: {user_id})", value=f"Score: {score}", inline=False)

        await ctx.send(embed=embed)
async def setup(bot):
    await bot.add_cog(Trivia(bot))

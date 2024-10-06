from Bot._Init_ import *
from Bot.Utils.GuildManager import GuildManager as GM
from Bot.Utils.AdaptiveThresholds import *
from Bot.Utils.Rest import *

atexit.register(lambda: GM().save_guild_data(bot.guild_data))

class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.tree = app_commands.CommandTree(self)
        self.guild_data = GM().load_guild_data()

    async def on_ready(self):
        print(f'Logged in as {self.user}!')
        print(f'im in {len(self.guilds)} guilds')
        await self.change_presence(activity=discord.Game(name='Developed by Tips'))
        clear_histories.start()

    async def on_guild_join(self, guild):
        try:
            if guild.system_channel is not None:
                await guild.system_channel.send(
                    "Hello, I'm the new automod! :fire: :fire: :fire: :fire:"
                )
            else:
                print(f"Joined {guild.name}, but no system channel to send a message.")
        except Exception as e:
            print(f"Failed to send system message to {guild.name}.")

    async def setup_hook(self):
        await self.tree.sync()

    async def close(self):
        GM().save_guild_data(bot.guild_data)
        await super().close()

bot = MyBot()

def get_guild_data(guild_id):
    if guild_id not in bot.guild_data:
        bot.guild_data[guild_id] = {
            'profanity_list': ["cp", "childporn", "c.p", 'raid', 'token', 'furrycum', '.gg/'],
            'user_message_history': defaultdict(lambda: deque(maxlen=100)),
            'group_message_history': deque(maxlen=200),
            'mention_history': defaultdict(lambda: deque(maxlen=50)),
            'adaptive_thresholds': AdaptiveThresholds(),
            'anti_raid': True
        }
    return bot.guild_data[guild_id]

@bot.tree.command(name="purge", description="Purge messages from the channel")
@app_commands.checks.has_permissions(manage_messages=True)
async def purge(interaction: discord.Interaction, limit: int):
    await interaction.response.defer(ephemeral=True)
    if limit < 1:
        await interaction.followup.send("Cannot purge less than 1 message at a time.", ephemeral=True)
        return
    
    elif limit > 500:
        await interaction.followup.send("Cannot purge more than 500 messages at a time.", ephemeral=True)
        return
    
    try:
        deleted = await interaction.channel.purge(limit=limit)
        await interaction.followup.send(f"Successfully purged {len(deleted)} messages.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Failed to purge messages: {str(e)}", ephemeral=True)

@bot.tree.command(name="ping", description="Returns the bot's latency.")
async def ping(interaction: discord.Interaction):
    await interaction.response.defer()
    latency = bot.latency * 1000
    await interaction.followup.send(f'Pong! Latency: {latency:.2f}ms')

@bot.tree.command(name="help", description="List all available commands.")
async def help_command(interaction: discord.Interaction):
    commands_list = [
        "/ping - Returns the bot's latency.",
        "/purge <limit> - Purge messages from the channel.",
        "/automod <action> <word> - Manage profanity filter.",
        "/anti_raid <on|off> - Enable or disable anti-raid protection."
    ]
    help_message = "\n".join(commands_list)
    await interaction.response.send_message(f"Available Commands:\n{help_message}", ephemeral=True)

@bot.tree.command(name="automod", description="Manage profanity filter.")
@app_commands.describe(
    action="Action to perform: add, remove, list",
    word="Comma-separated words to add/remove, if applicable."
)
@app_commands.checks.has_permissions(administrator=True)
async def automod(interaction: discord.Interaction, action: str, word: str = None):
    guild_data = get_guild_data(interaction.guild.id)
    action = action.lower().strip()

    if action == "list":
        profanity_list = guild_data['profanity_list']
        if not profanity_list:
            await interaction.response.send_message("The profanity filter is currently empty.", ephemeral=True)
            return
        await interaction.response.send_message(f"Profanity filter: {', '.join(profanity_list)}", ephemeral=True)

    elif action == "add" and word:
        new_words = [w.strip() for w in word.split(",") if w.strip()]
        guild_data['profanity_list'].extend(new_words)
        await interaction.response.send_message(f"Added words: {', '.join(new_words)}", ephemeral=True)

    elif action == "remove" and word:
        words_to_remove = [w.strip() for w in word.split(",") if w.strip()]
        for w in words_to_remove:
            if w in guild_data['profanity_list']:
                guild_data['profanity_list'].remove(w)
        await interaction.response.send_message(f"Removed words: {', '.join(words_to_remove)}", ephemeral=True)

    else:
        await interaction.response.send_message("Invalid action or missing word.", ephemeral=True)

@bot.tree.command(name="anti_raid", description="Enable or disable anti-raid protection.")
@app_commands.describe(
    status="Enable or disable anti-raid: 'on' or 'off'."
)
@app_commands.checks.has_permissions(administrator=True)
async def anti_raid(interaction: discord.Interaction, status: str):
    guild_data = get_guild_data(interaction.guild.id)
    status = status.lower().strip()

    if status == "on":
        guild_data['anti_raid'] = True
        await interaction.response.send_message("Anti-raid protection is now **enabled**.", ephemeral=True)
    elif status == "off":
        guild_data['anti_raid'] = False
        await interaction.response.send_message("Anti-raid protection is now **disabled**.", ephemeral=True)
    else:
        await interaction.response.send_message("Invalid status. Please use 'on' or 'off'.", ephemeral=True)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    guild_data = get_guild_data(message.guild.id)

    if guild_data['anti_raid']:
        if detect_spam(guild_data, message.author.id, message):
            await asyncio.gather(
                purge_spam_messages(message.channel, message.author, limit=125),
                timeout_user(guild_data, message.author, duration=300)
            )
            return

        if is_patterned_spam(message.content):
            await asyncio.gather(
                purge_spam_messages(message.channel, message.author, limit=125),
                timeout_user(message.author, duration=300)
            )
            return

        pattern = build_pattern(message.content)
        observed_patterns[pattern] += 1

        if any(profanity in message.content.lower() for profanity in (word.lower() for word in guild_data['profanity_list'])):
            await message.delete()
            return
        
        calculate_activity_level(guild_data, message.guild.id)

@bot.tree.error
async def on_app_command_error(interaction: Interaction, error: Exception):
    if isinstance(error, CheckFailure):
        await interaction.response.send_message("You do not have the required permissions to use this command.", ephemeral=True)
    else:
        await interaction.response.send_message(f"An error occurred: {str(error)}", ephemeral=True)

@tasks.loop(seconds=30)
async def clear_histories():
    global message_cache, observed_patterns, permission_denied_users
    message_cache.clear()
    observed_patterns.clear()
    permission_denied_users.clear()

    for guild_data in bot.guild_data.values():
        guild_data['user_message_history'] = {}

        guild_data['group_message_history'] = {}

        guild_data['mention_history'] = {}

if __name__ == '__main__':
    bot.run(toke)
from Bot._Init_ import *
from Bot.Utils.AdaptiveThresholds import *
from Bot.Utils.Rest import *

class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.tree = app_commands.CommandTree(self)
        self.guild_data = {}

    async def on_ready(self):
        print(f'Logged in as {self.user}!')
        print(f'In {len(self.guilds)} guilds.')
        await self.change_presence(activity=discord.Game(name='Developed by Tips'))
        clear_histories.start()

    async def on_guild_join(self, guild):
        try:
            system_channel = guild.system_channel
            if system_channel:
                await system_channel.send("Hello, I'm the new automod! :fire: :fire: :fire: :fire:")
            else:
                print(f"Joined {guild.name}, but no system channel found.")
        except Exception as e:
            print(f"Failed to send system message to {guild.name}: {str(e)}")

    async def setup_hook(self):
        await self.tree.sync()

    async def close(self):
        await super().close()

bot = MyBot()

def get_guild_data(guild_id):
    return bot.guild_data.setdefault(guild_id, {
        'profanity_list': ["cp", "childporn", "c.p", 'raid', 'token', 'furrycum', '.gg/'],
        'user_message_history': defaultdict(lambda: deque(maxlen=100)),
        'group_message_history': deque(maxlen=200),
        'mention_history': defaultdict(lambda: deque(maxlen=50)),
        'adaptive_thresholds': AdaptiveThresholds(),
        'anti_raid': True
    })

@bot.tree.command(name="purge", description="Purge messages from the channel")
@app_commands.checks.has_permissions(manage_messages=True)
async def purge(interaction: discord.Interaction, limit: int):
    await interaction.response.defer(ephemeral=True)

    if limit < 1 or limit > 500:
        await interaction.followup.send("Purge limit must be between 1 and 500 messages.", ephemeral=True)
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
@app_commands.describe(action="Action to perform: add, remove, list", word="Comma-separated words to add/remove, if applicable.")
@app_commands.checks.has_permissions(administrator=True)
async def automod(interaction: discord.Interaction, action: str, word: str = None):
    guild_data = get_guild_data(interaction.guild.id)
    action = action.lower().strip()

    if action == "list":
        profanity_list = guild_data['profanity_list']
        message = "The profanity filter is currently empty." if not profanity_list else f"Profanity filter: {', '.join(profanity_list)}"
        await interaction.response.send_message(message, ephemeral=True)

    elif action in {"add", "remove"} and word:
        words = {w.strip() for w in word.split(",") if w.strip()}
        if action == "add":
            guild_data['profanity_list'].extend(words)
            await interaction.response.send_message(f"Added words: {', '.join(words)}", ephemeral=True)
        elif action == "remove":
            removed_words = [w for w in words if w in guild_data['profanity_list']]
            guild_data['profanity_list'] = [w for w in guild_data['profanity_list'] if w not in removed_words]
            message = f"Removed words: {', '.join(removed_words)}" if removed_words else "No matching words found in profanity list."
            await interaction.response.send_message(message, ephemeral=True)
    else:
        await interaction.response.send_message("Invalid action or missing word.", ephemeral=True)

@bot.tree.command(name="anti_raid", description="Enable or disable anti-raid protection.")
@app_commands.describe(status="Enable or disable anti-raid: 'on' or 'off'.")
@app_commands.checks.has_permissions(administrator=True)
async def anti_raid(interaction: discord.Interaction, status: str):
    guild_data = get_guild_data(interaction.guild.id)
    status = status.lower().strip()

    if status in {"on", "off"}:
        guild_data['anti_raid'] = (status == "on")
        await interaction.response.send_message(f"Anti-raid protection is now **{status}**.", ephemeral=True)
    else:
        await interaction.response.send_message("Invalid status. Please use 'on' or 'off'.", ephemeral=True)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    guild_data = get_guild_data(message.guild.id)
    
    if guild_data['anti_raid'] and (detect_spam(guild_data, message.author.id, message) or is_patterned_spam(message.content)):
        await asyncio.gather(
            purge_spam_messages(message.channel, message.author, limit=125),
            timeout_user(message.author, duration=300)
        )
        return

    if any(word in message.content.lower().split() for word in guild_data['profanity_list']):
        await message.delete()

    pattern = build_pattern(message.content)
    observed_patterns[pattern] += 1
    calculate_activity_level(guild_data, message.guild.id)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: Exception):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("You lack the required permissions to use this command.", ephemeral=True)
    else:
        await interaction.response.send_message(f"An error occurred: {str(error)}", ephemeral=True)

@tasks.loop(seconds=30)
async def clear_histories():
    message_cache.clear()
    observed_patterns.clear()
    permission_denied_users.clear()

    for guild_data in bot.guild_data.values():
        guild_data['user_message_history'].clear()
        guild_data['group_message_history'].clear()
        guild_data['mention_history'].clear()

if __name__ == '__main__':
    bot.run(token)
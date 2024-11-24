from Bot import *
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
                pass
        except Exception as e:
            pass

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

@bot.tree.command(name="purge", description="Purge messages from the channel.")
@app_commands.checks.has_permissions(manage_messages=True)
async def purge(interaction: discord.Interaction, limit: int):
    if limit < 1 or limit > 500:
        embed = discord.Embed(
            title="Invalid Limit",
            description="Purge limit must be between **1** and **500** messages.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Developed by Tips | Adjust the limit and try again.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    confirm_embed = discord.Embed(
        title="Confirm Purge",
        description=f"You are about to purge **{limit}** messages from this channel. Confirm to proceed.",
        color=discord.Color.orange()
    )
    confirm_embed.set_footer(text="Developed by Tips | This action cannot be undone.")

    async def confirm_callback(inner_interaction: discord.Interaction):
        await inner_interaction.response.defer(ephemeral=True)
        try:
            deleted = await interaction.channel.purge(limit=limit)
            success_embed = discord.Embed(
                title="Purge Successful",
                description=f"Successfully purged **{len(deleted)}** messages.",
                color=discord.Color.green()
            )
            success_embed.set_footer(text="Developed by Tips")
            await interaction.followup.send(embed=success_embed, ephemeral=True)
        except Exception as e:
            error_embed = discord.Embed(
                title="Purge Failed",
                description=f"An error occurred: **{str(e)}**",
                color=discord.Color.red()
            )
            error_embed.set_footer(text="Developed by Tips")
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    async def cancel_callback(interaction: discord.Interaction):
        cancel_embed = discord.Embed(
            title="Purge Cancelled",
            description="No messages were purged.",
            color=discord.Color.blue()
        )
        cancel_embed.set_footer(text="Developed by Tips")
        await interaction.response.edit_message(embed=cancel_embed, view=None)

    view = discord.ui.View(timeout=30)
    confirm_button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.danger)
    cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.secondary)

    confirm_button.callback = confirm_callback
    cancel_button.callback = cancel_callback

    view.add_item(confirm_button)
    view.add_item(cancel_button)

    await interaction.response.send_message(embed=confirm_embed, view=view, ephemeral=True)

@bot.tree.command(name="ping", description="Returns the bot's latency.")
async def ping(interaction: discord.Interaction):
    latency = bot.latency * 1000
    embed = discord.Embed(
        title="Pong! 🏓",
        description=f"Latency: `{latency:.2f}ms`",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="help", description="List all available commands.")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Help - Available Commands",
        description="Here are the commands you can use with the bot.",
        color=discord.Color.blue()
    )
    embed.add_field(name="/ping", value="Returns the bot's latency.", inline=False)
    embed.add_field(name="/purge <limit>", value="Purge messages from the channel.", inline=False)
    embed.add_field(name="/automod <action> <word>", value="Manage the profanity filter.", inline=False)
    embed.add_field(name="/anti_raid <on|off>", value="Enable or disable anti-raid protection.", inline=False)
    embed.set_footer(text="Developed by Tips | Enjoy!")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="automod", description="Manage profanity filter interactively.")
@app_commands.checks.has_permissions(manage_guild=True)
async def automod(interaction: discord.Interaction):
    guild_data = get_guild_data(interaction.guild.id)

    class AutomodModal(discord.ui.Modal, title="Automod - Manage Profanity Filter"):
        words = discord.ui.TextInput(
            label="Words",
            style=discord.TextStyle.paragraph,
            placeholder="Enter words separated by commas (e.g., spam, troll)",
            required=True
        )
        action = None

        async def on_submit(self, inner_interaction: discord.Interaction):
            words_list = {word.strip() for word in self.words.value.split(",") if word.strip()}
            response = []

            if self.action == "add":
                added_words = []
                for word in words_list:
                    if word not in guild_data['profanity_list']:
                        guild_data['profanity_list'].append(word)
                        added_words.append(word)
                response = f"**Added Words:** {', '.join(added_words)}" if added_words else "No new words were added."

            elif self.action == "remove":
                removed_words = [word for word in words_list if word in guild_data['profanity_list']]
                guild_data['profanity_list'] = [word for word in guild_data['profanity_list'] if word not in removed_words]
                response = f"**Removed Words:** {', '.join(removed_words)}" if removed_words else "No matching words were removed."

            embed = discord.Embed(
                title="Automod Update",
                description=response,
                color=discord.Color.green()
            )
            await inner_interaction.response.send_message(embed=embed, ephemeral=True)

    async def list_callback(inner_interaction: discord.Interaction):
        profanity_list = guild_data['profanity_list']
        embed = discord.Embed(
            title="Profanity Filter - Current Words",
            description=f"Words: {', '.join(profanity_list)}" if profanity_list else "The profanity filter is currently empty.",
            color=discord.Color.blue()
        )
        await inner_interaction.response.edit_message(embed=embed, view=view)

    async def add_callback(inner_interaction: discord.Interaction):
        modal = AutomodModal()
        modal.action = "add"
        await inner_interaction.response.send_modal(modal)

    async def remove_callback(inner_interaction: discord.Interaction):
        modal = AutomodModal()
        modal.action = "remove"
        await inner_interaction.response.send_modal(modal)

    view = discord.ui.View(timeout=60)
    list_button = discord.ui.Button(label="List", style=discord.ButtonStyle.primary)
    add_button = discord.ui.Button(label="Add", style=discord.ButtonStyle.success)
    remove_button = discord.ui.Button(label="Remove", style=discord.ButtonStyle.danger)

    list_button.callback = list_callback
    add_button.callback = add_callback
    remove_button.callback = remove_callback

    view.add_item(list_button)
    view.add_item(add_button)
    view.add_item(remove_button)

    embed = discord.Embed(
        title="Automod Interface",
        description="Use the buttons below to manage the profanity filter.",
        color=discord.Color.orange()
    )
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="anti_raid", description="Enable or disable anti-raid protection.")
@app_commands.checks.has_permissions(manage_guild=True)
async def anti_raid(interaction: discord.Interaction):
    guild_data = get_guild_data(interaction.guild.id)

    async def toggle_callback(interaction: discord.Interaction):
        guild_data['anti_raid'] = not guild_data['anti_raid']
        new_status = "Enabled" if guild_data['anti_raid'] else "Disabled"
        color = discord.Color.green() if guild_data['anti_raid'] else discord.Color.red()

        embed = discord.Embed(
            title="Anti-Raid Protection",
            description=f"Anti-raid protection is now **{new_status}**.",
            color=color
        )
        embed.set_footer(text="Developed by Tips")

        toggle_button.label = "Disable" if guild_data['anti_raid'] else "Enable"
        toggle_button.style = discord.ButtonStyle.danger if guild_data['anti_raid'] else discord.ButtonStyle.success
        await interaction.response.edit_message(embed=embed, view=view)

    current_status = "Enabled" if guild_data['anti_raid'] else "Disabled"
    embed = discord.Embed(
        title="Anti-Raid Protection",
        description=f"Current Status: **{current_status}**.",
        color=discord.Color.green() if guild_data['anti_raid'] else discord.Color.red()
    )
    embed.set_footer(text="Developed by Tips")

    toggle_button = discord.ui.Button(
        label="Disable" if guild_data['anti_raid'] else "Enable",
        style=discord.ButtonStyle.danger if guild_data['anti_raid'] else discord.ButtonStyle.success
    )
    toggle_button.callback = toggle_callback

    view = discord.ui.View(timeout=60)
    view.add_item(toggle_button)

    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    guild_data = get_guild_data(message.guild.id)
    
    if guild_data['anti_raid'] and (detect_spam(guild_data, message.author.id, message) or is_patterned_spam(message.content)):
        await asyncio.gather(
            timeout_user(message.author, duration=600),
            purge_spam_messages(message.channel, message.author, limit=200)
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
    purging_users.clear()

    for guild_data in bot.guild_data.values():
        guild_data['user_message_history'].clear()
        guild_data['group_message_history'].clear()
        guild_data['mention_history'].clear()

if __name__ == '__main__':
    bot.run(token)
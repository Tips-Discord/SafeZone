from Bot._Init_ import *
from Bot.Utils.AdaptiveThresholds import *

class GuildManager:
    @staticmethod
    def load_guild_data():
        if os.path.exists('Bot/Data/guild_data.json'):
            try:
                with open('Bot/Data/guild_data.json', 'r') as file:
                    data = json.load(file)
                    return {guild_id: GuildManager.convert_loaded_data(guild_data) for guild_id, guild_data in data.items()}
            except (json.JSONDecodeError, KeyError):
                print("Error loading guild data. Starting with empty data.")
        return {}

    @staticmethod
    def save_guild_data(guild_data):
        with open('Bot/Data/guild_data.json', 'w') as file:
            json.dump({guild_id: GuildManager.prepare_data_for_saving(guild_data) for guild_id, guild_data in guild_data.items()}, file, indent=4)

    @staticmethod
    def prepare_data_for_saving(data):
        def convert(value):
            if isinstance(value, defaultdict):
                return {k: convert(v) for k, v in value.items()}
            elif isinstance(value, deque):
                return list(value)
            elif isinstance(value, AdaptiveThresholds):
                return {
                    'spam_threshold': value.spam_threshold,
                    'similarity_threshold': value.similarity_threshold,
                    'ping_threshold': value.ping_threshold,
                    'group_threshold': value.group_threshold,
                    'time_window': value.time_window,
                    'activity_level': value.activity_level
                }
            elif isinstance(value, dict):
                return {k: convert(v) for k, v in value.items()}
            return value

        return convert(data)

    @staticmethod
    def convert_loaded_data(data):
        def convert(value):
            if isinstance(value, dict) and 'profanity_list' in value:
                return {
                    'profanity_list': value.get('profanity_list', []),
                    'user_message_history': defaultdict(lambda: deque(maxlen=100),
                                                        {k: deque(v, maxlen=100) for k, v in value['user_message_history'].items()}),
                    'group_message_history': deque(value['group_message_history'], maxlen=200),
                    'mention_history': defaultdict(lambda: deque(maxlen=50),
                                                {k: deque(v, maxlen=50) for k, v in value['mention_history'].items()}),
                    'adaptive_thresholds': AdaptiveThresholds(
                        value['adaptive_thresholds']['spam_threshold'],
                        value['adaptive_thresholds']['similarity_threshold'],
                        value['adaptive_thresholds']['ping_threshold'],
                        value['adaptive_thresholds']['group_threshold'],
                        value['adaptive_thresholds']['time_window'],
                        value['adaptive_thresholds']['activity_level']
                    ),
                    'anti_raid': value.get('anti_raid', True)
                }
            return value

        return convert(data)

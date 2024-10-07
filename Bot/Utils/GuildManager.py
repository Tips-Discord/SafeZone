from Bot._Init_ import *
from Bot.Utils.AdaptiveThresholds import *

class GuildManager:
    def __init__(self):
        self.guild_data = self.load_guild_data()

    @staticmethod
    def load_guild_data():
        file_path = 'Bot/Data/guild_data.json'
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as file:
                    data = json.load(file)

                    if isinstance(data, dict):
                        return {guild_id: GuildManager.convert_loaded_data(guild_data) for guild_id, guild_data in data.items()}
                    elif isinstance(data, list):
                        return {str(index): GuildManager.convert_loaded_data(guild_data) for index, guild_data in enumerate(data)}
                    else:
                        print("Unknown data format in guild_data.json.")
                        return {}
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading guild data: {e}. Starting with empty data.")
        else:
            print(f"File {file_path} does not exist.")
        return {}


    @staticmethod
    def convert_loaded_data(data):
        def convert(value):
            if isinstance(value, dict) and 'profanity_list' in value:
                return {
                    'profanity_list': value.get('profanity_list', ["cp", "childporn", "c.p", 'raid', 'token', 'furrycum', '.gg/']),
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

    def get_all_guild_data_as_list(self):
        guild_data_list = []
        
        for guild_id, guild_info in self.guild_data.items():
            guild_info['guild_id'] = guild_id
            guild_data_list.append(guild_info)
        
        return guild_data_list

    
    @staticmethod
    def save_guild_data(guild_data):
        temp_filename = 'Bot/Data/temp_guild_data.json'
        final_filename = 'Bot/Data/guild_data.json'

        os.makedirs('Bot/Data', exist_ok=True)
        
        unique_guild_data = {}
        
        for guild_id, data in guild_data.items():
            unique_guild_data[guild_id] = GuildManager.prepare_data_for_saving(data)

        if unique_guild_data:
            try:
                with open(temp_filename, 'w') as temp_file:
                    json.dump(unique_guild_data, temp_file, indent=4)

                os.replace(temp_filename, final_filename)
                print("Guild data saved successfully.")
            except Exception as e:
                print(f"Error saving guild data: {e}")
        else:
            print("No unique guild data to save.")

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
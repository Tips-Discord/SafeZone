from Bot import *
from Bot.Utils.AdaptiveThresholds import AdaptiveThresholds

file_path = "settings.json"


# made by ai my beloved!

class SettingsManager:
    _last_saved_data = None

    @staticmethod
    def _are_settings_equal(data1, data2):
        if data1 is None or data2 is None:
            return False
        
        try:
            data1_serial = SettingsManager._extract_essential_settings(data1)
            data2_serial = SettingsManager._extract_essential_settings(data2)
            return data1_serial == data2_serial
        except:
            return False

    @staticmethod
    def _extract_essential_settings(data):
        if not isinstance(data, dict):
            return data
        
        result = {}
        for guild_id, guild_data in data.items():
            if isinstance(guild_data, dict):
                result[guild_id] = {
                    'profanity_list': guild_data.get('profanity_list', []),
                    'anti_raid': guild_data.get('anti_raid', True)
                }
        return result

    @staticmethod
    def _convert_after_load(data):
        if isinstance(data, dict):
            result = {}
            for k, v in data.items():
                new_k = int(k) if k.isdigit() else k
                if isinstance(v, dict):
                    guild_data = {
                        'profanity_list': v.get('profanity_list', []),
                        'user_message_history': defaultdict(lambda: deque(maxlen=100)),
                        'group_message_history': deque(maxlen=200),
                        'mention_history': defaultdict(lambda: deque(maxlen=50)),
                        'adaptive_thresholds': AdaptiveThresholds(),
                        'anti_raid': v.get('anti_raid', True)
                    }
                    result[new_k] = guild_data
            return result
        return data

    @staticmethod
    def save(data):
        if SettingsManager._are_settings_equal(data, SettingsManager._last_saved_data):
            return

        try:
            serializable_data = SettingsManager._extract_essential_settings(data)
            with open(file_path, "w") as file:
                json.dump(serializable_data, file, indent=4)
            SettingsManager._last_saved_data = data
        except Exception as e:
            print(f"Error saving settings: {e}")

    @staticmethod
    def load():
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as file:
                    data = json.load(file)
                return SettingsManager._convert_after_load(data)
            except Exception as e:
                print(f"Error loading settings: {e}")
                return {}
        else:
            return {}
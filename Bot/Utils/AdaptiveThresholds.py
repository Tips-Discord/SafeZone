from Bot import *

class AdaptiveThresholds:
    def __init__(self, spam_threshold=20, similarity_threshold=0.4, ping_threshold=10, group_threshold=15, time_window=30):
        self.default_spam_threshold = spam_threshold
        self.default_similarity_threshold = similarity_threshold
        self.default_time_window = time_window
        self.spam_threshold = spam_threshold
        self.similarity_threshold = similarity_threshold
        self.ping_threshold = ping_threshold
        self.group_threshold = group_threshold
        self.time_window = time_window

    def adjust(self, activity_level):
        scale_factor = max(0.5, min(3.0, activity_level / 100))
        self.spam_threshold = int(self.default_spam_threshold * scale_factor)
        self.similarity_threshold = self.default_similarity_threshold * scale_factor
        self.ping_threshold = int(10 * scale_factor)
        self.group_threshold = int(15 * scale_factor)
        self.time_window = int(30 / scale_factor) 

def calculate_activity_level(guild_data, guild_id):
    current_time = time.time()
    user_message_history = guild_data['user_message_history']
    
    total_messages = sum(len(history) for history in user_message_history.values())
    recent_messages = sum(len([msg for msg, time in history if current_time - time < 60])
                          for history in user_message_history.values())
    
    activity_level = (recent_messages / total_messages) * 100 if total_messages else 0
    guild_data['adaptive_thresholds'].adjust(activity_level)
from Bot import *

class AdaptiveThresholds:
    def __init__(self, spam_threshold: int = 20, similarity_threshold: float = 0.4, ping_threshold: int = 10, group_threshold: int = 15, time_window: int = 30, scale_min: float = 0.5, scale_max: float = 3.0):
        self.default_spam_threshold = spam_threshold
        self.default_similarity_threshold = similarity_threshold
        self.default_time_window = time_window

        self.spam_threshold = spam_threshold
        self.similarity_threshold = similarity_threshold
        self.ping_threshold = ping_threshold
        self.group_threshold = group_threshold
        self.time_window = time_window

        self.scale_min = scale_min
        self.scale_max = scale_max

    def adjust(self, activity_level: float) -> None:
        scale_factor = max(self.scale_min, min(self.scale_max, activity_level / 100))

        new_spam_threshold = max(1, int(self.default_spam_threshold * scale_factor))
        new_similarity_threshold = max(0.1, self.default_similarity_threshold * scale_factor)
        new_ping_threshold = max(1, int(self.ping_threshold * scale_factor))
        new_group_threshold = max(1, int(self.group_threshold * scale_factor))
        new_time_window = max(5, int(self.default_time_window / scale_factor))

        if (self.spam_threshold != new_spam_threshold or
            self.similarity_threshold != new_similarity_threshold or
            self.ping_threshold != new_ping_threshold or
            self.group_threshold != new_group_threshold or
            self.time_window != new_time_window):

            self.spam_threshold = new_spam_threshold
            self.similarity_threshold = new_similarity_threshold
            self.ping_threshold = new_ping_threshold
            self.group_threshold = new_group_threshold
            self.time_window = new_time_window

    def __repr__(self):
        return (f"AdaptiveThresholds(spam_threshold={self.spam_threshold}, "
                f"similarity_threshold={self.similarity_threshold}, "
                f"ping_threshold={self.ping_threshold}, "
                f"group_threshold={self.group_threshold}, "
                f"time_window={self.time_window}, "
                f"scale_min={self.scale_min}, scale_max={self.scale_max})")

def calculate_activity_level(guild_data: Dict[str, Any], guild_id: int) -> None:
    current_time = time.time()
    user_message_history = guild_data.get('user_message_history', {})

    total_messages = sum(len(history) for history in user_message_history.values())
    recent_messages = sum(
        len([msg_time for _, msg_time in history if current_time - msg_time < 60])
        for history in user_message_history.values()
    )

    activity_level = (recent_messages / total_messages * 100) if total_messages > 0 else 0

    adaptive_thresholds = guild_data.get('adaptive_thresholds')
    if adaptive_thresholds:
        adaptive_thresholds.adjust(activity_level)
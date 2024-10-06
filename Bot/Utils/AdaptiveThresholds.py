from Bot._Init_ import *

class AdaptiveThresholds:
    def __init__(self, spam_threshold=20, similarity_threshold=0.4, ping_threshold=10, 
                 group_threshold=15, time_window=30, activity_level=100):
        self.spam_threshold = spam_threshold
        self.similarity_threshold = similarity_threshold
        self.ping_threshold = ping_threshold
        self.group_threshold = group_threshold
        self.time_window = time_window
        self.activity_level = activity_level

    def adjust(self, activity_level):
        scale_factor = min(4.0, max(0.3, activity_level / 100))
        self.spam_threshold = int(20 * scale_factor)
        self.similarity_threshold = 0.4 * scale_factor
        self.ping_threshold = int(10 * scale_factor)
        self.group_threshold = int(15 * scale_factor)
        self.time_window = int(30 / scale_factor)
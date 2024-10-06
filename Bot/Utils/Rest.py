from Bot._Init_ import *
from Bot.Utils.AdaptiveThresholds import *

def clean_message(message):
    return re.sub(r"[^\w\s']", '', message.lower()).strip()

def tokenize(message):
    if message in message_cache:
        return message_cache[message]
    
    tokens = clean_message(message).split()
    message_cache[message] = tokens
    return tokens

def bigrams(tokens):
    return zip(tokens, tokens[1:])

def similarity_score(msg1, msg2):
    tokens1 = tokenize(msg1)
    tokens2 = tokenize(msg2)
    
    if not tokens1 or not tokens2:
        return 0.0

    if len(tokens1) == 1 or len(tokens2) == 1:
        return 1.0 if tokens1 == tokens2 else 0.0

    bigrams1 = list(bigrams(tokens1))
    bigrams2 = list(bigrams(tokens2))

    counter1 = Counter(tokens1 + bigrams1)
    counter2 = Counter(tokens2 + bigrams2)

    common_elements = set(counter1.keys()).intersection(counter2.keys())
    dot_product = sum(min(counter1[term], counter2[term]) for term in common_elements)

    magnitude1 = math.sqrt(sum(count**2 for count in counter1.values()))
    magnitude2 = math.sqrt(sum(count**2 for count in counter2.values()))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)

def detect_spam(guild_data, user_id, message):
    current_time = time.time()
    
    if user_id not in guild_data['user_message_history']:
        guild_data['user_message_history'][user_id] = []
    
    history = [(msg_content, msg_time) for msg_content, msg_time in guild_data['user_message_history'][user_id]
               if current_time - msg_time < guild_data['adaptive_thresholds'].time_window]

    similar_count = sum(1 for msg_content, _ in history
                        if similarity_score(msg_content, message.content) > guild_data['adaptive_thresholds'].similarity_threshold)

    guild_data['user_message_history'][user_id].append((message.content, current_time))

    return similar_count >= guild_data['adaptive_thresholds'].spam_threshold

def build_pattern(message):
    return re.sub(r'[a-zA-Z0-9]', '[a-zA-Z0-9]', message)

def is_patterned_spam(message, threshold=5):
    for pattern, count in observed_patterns.items():
        if count >= threshold and re.fullmatch(pattern, message):
            return True
    return False

async def timeout_user(member, duration):
    if member.id in permission_denied_users:
        return
    try:
        await member.timeout(discord.utils.utcnow() + timedelta(seconds=duration))
    except (discord.Forbidden, discord.HTTPException):
        permission_denied_users.add(member.id)

async def purge_spam_messages(channel, user, limit):
    if user.id in permission_denied_users:
        return
    try:
        await channel.purge(limit=limit, check=lambda message: message.author == user)
    except (discord.Forbidden, discord.HTTPException):
        permission_denied_users.add(user.id)
    except discord.RateLimited:
        pass

observed_patterns = defaultdict(int)
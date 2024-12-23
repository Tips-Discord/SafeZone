from Bot import *

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

    return dot_product / (magnitude1 * magnitude2) if magnitude1 and magnitude2 else 0.0

def detect_spam(guild_data, user_id, message):
    current_time = time.time()
    
    if user_id not in guild_data['user_message_history']:
        guild_data['user_message_history'][user_id] = deque()

    user_history = guild_data['user_message_history'][user_id]

    filtered_history = [(msg, t) for msg, t in user_history if current_time - t < guild_data['adaptive_thresholds'].time_window]

    user_history.clear()
    user_history.extend(filtered_history)

    similar_count = sum(1 for msg, _ in user_history if similarity_score(msg, message.content) > guild_data['adaptive_thresholds'].similarity_threshold)

    user_history.append((message.content, current_time))

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
    semaphore = purging_users[user.id]

    async with semaphore:
        try:
            await channel.purge(limit=limit, check=lambda msg: msg.author == user)
        except discord.RateLimited:
            pass
        except Exception as e:
            print(f"Error during purging messages for user {user.id}: {str(e)}")
        finally:
            pass

def calculate_bot_probability(member):
    probability = 0

    if member.bot:
        return 100

    age = (datetime.now(timezone.utc) - member.created_at).days
    name = member.name.lower()
    
    if age < 7:
        probability += 25
    elif age < 30:
        probability += 10

    if len(name) <= 2:
        probability += 10

    if member.default_avatar:
        probability += 10

    if "xx" in name or name.startswith("_") or name.endswith("_"):
        probability += 5

    if name[-2:].isdigit():
        probability += 10

    if any(name.count(char) > 3 for char in set(name)):
        probability += 5

    if name.startswith(("!", ".", "-")):
        probability += 10

    if any(substring in name for substring in [".com", "http", ".net"]):
        probability += 15

    return min(probability, 100)
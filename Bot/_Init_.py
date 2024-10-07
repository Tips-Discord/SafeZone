from collections import deque, Counter, defaultdict
from datetime import timedelta
from discord import app_commands, Interaction
from discord.app_commands import CheckFailure
from discord.ext import tasks
import asyncio
import atexit
import discord
import json
import math
import os
import re
import sys
import time

sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
toke = "MTI5MTM5ODA3NDY3MzEzNTcxMA.Gj9iXr.tAXAEr1lz7oJ2I7CzO4g52ZHeSm_9mzQtBCJso"
test_toke = 'MTE5NjUxNTgzOTgzNTM3MzU4OA.GupGaQ.S0LumYbtyoyM3hsga2IGxOiqGp5sH8KknCBCBM'
permission_denied_users = set()
message_cache = {}
observed_patterns = defaultdict(int)
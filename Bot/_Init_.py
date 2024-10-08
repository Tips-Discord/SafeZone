from collections import deque,Counter, defaultdict
from datetime import timedelta
from discord import app_commands, Interaction
from discord.app_commands import CheckFailure
from discord.ext import tasks
import asyncio
import discord
import json
import math
import os
import re
import sys
import time

token = "yourdiscordtokenhere"
permission_denied_users = set()
message_cache = {}
observed_patterns = defaultdict(int)
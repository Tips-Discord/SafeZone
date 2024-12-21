from collections import deque, Counter, defaultdict
from datetime import timedelta
from discord import app_commands, ui, Interaction, Embed, TextStyle, Color
from discord.app_commands import CheckFailure
from discord.ext import tasks, commands
import asyncio
import discord
import json
import math
import os
import random
import re
import sys
import time

token = "yourdiscordtoken"
purging_users = defaultdict(lambda: asyncio.Semaphore(5))
permission_denied_users = set()
message_cache = {}
observed_patterns = defaultdict(int)
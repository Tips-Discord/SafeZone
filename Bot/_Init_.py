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
token = "MTI5MTM5ODA3NDY3MzEzNTcxMA.G_WqPj.ZAbgTSUL6kOK4p87GdTGPwcu5hBmoOXN_0wDLw"
permission_denied_users = set()
message_cache = {}
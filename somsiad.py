#!/usr/bin/env python3

# Copyright 2018 Habchy, ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import discord
from discord.ext import commands
import platform
import sys
import os
import traceback
import logging
import datetime
from version import __version__
from somsiad_helper import *
from plugins import *

logging.basicConfig(filename='somsiad.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Informator:
    with_preposition_variant = staticmethod(lambda number : 'ze' if number >= 100 and number < 200 else 'z')
    noun_variant = staticmethod(lambda number, singular, plural : singular if number == 1 else plural)

    @staticmethod
    def separator(block_major, block_minor, width):
        """Generates a separator string to the specified length out of given blocks."""
        block = block_major + block_minor
        pattern = block * int((width - len(block_major)) / len(block)) + block_major
        return pattern

    def info(self, lines, verbose=False):
        """Takes a list of lines containing bot information and returns a string ready for printing.
            Can print to the console."""
        info = ''
        separator = self.separator('==', ' ', os.get_terminal_size()[0])
        if verbose: print(separator)
        for line in lines:
            info += line + '\n'
            if verbose: print(line)
        if verbose: print(separator)
        return info.strip('\n')

# This is what happens every time the bot launches
# In this case, it prints information like the user count, server count, and the bot's ID in the console

def print_info():

    informator = Informator()

    number_of_users = len(set(client.get_all_members()))
    servers = sorted(client.guilds, key=lambda server: len(server.members), reverse=True)
    number_of_servers = len(client.guilds)
    longest_server_name_length = 0
    longest_days_since_joining_info_length = 0
    list_of_servers = ''

    for server in servers:
        if server.me is not None:
            if len(server.name) > longest_server_name_length:
                longest_server_name_length = len(server.name)
            date_of_joining = server.me.joined_at.replace(tzinfo=datetime.timezone.utc).astimezone()
            days_since_joining = (datetime.datetime.now().astimezone() - date_of_joining).days
            days_since_joining_info = (f'{days_since_joining} '
                f'{informator.noun_variant(days_since_joining, "dnia", "dni")}')
            if len(days_since_joining_info) > longest_days_since_joining_info_length:
                longest_days_since_joining_info_length = len(days_since_joining_info)

    for server in servers:
        if server.me is not None:
            date_of_joining = server.me.joined_at.replace(tzinfo=datetime.timezone.utc).astimezone()
            days_since_joining = (datetime.datetime.now().astimezone() - date_of_joining).days
            days_since_joining_info = (f'{days_since_joining} '
                f'{informator.noun_variant(days_since_joining, "dnia", "dni")}')
            list_of_servers += (f'{server.name.ljust(longest_server_name_length)} - '
                f'od {days_since_joining_info.ljust(longest_days_since_joining_info_length)} - '
                f'{str(len(server.members))} '
                f'{informator.noun_variant(number_of_users, "użytkownik", "użytkowników")}\n')
    list_of_servers = list_of_servers.strip('\n')

    info_lines = (
        f'Obudzono Somsiada (ID {str(client.user.id)}).',
        '',
        f'Połączono {informator.with_preposition_variant(number_of_users)} {number_of_users} '
        f'{informator.noun_variant(number_of_users, "użytkownikiem", "użytkownikami")} na {number_of_servers} '
        f'{informator.noun_variant(number_of_servers, "serwerze", "serwerach")}:',
        list_of_servers,
        '',
        'Link do zaproszenia bota:',
        f'https://discordapp.com/oauth2/authorize?client_id={str(client.user.id)}&scope=bot&permissions=536083543',
        '',
        configurator.info(),
        '',
        f'Somsiad {__version__} • discord.py {discord.__version__} • Python {platform.python_version()}',
        '',
        'Copyright 2018 Habchy, ondondil & Twixes',
    )

    informator.info(info_lines, verbose=True)

@client.event
async def on_ready():
    """Does things once the bot comes online."""
    print_info()
    return await client.change_presence(activity=discord.Game(name=f'Kiedyś to było | {conf["command_prefix"]}pomocy'))

@client.event
async def on_server_join(server):
    """Does things whenever the bot joins a server."""
    print_info()

@client.event
async def on_command_error(ctx, error):
    """Handles command errors."""
    ignored = (commands.CommandNotFound, commands.UserInputError)
    if isinstance(error, ignored):
        return
    elif isinstance(error, commands.DisabledCommand):
        return await ctx.send(f'Komenda {ctx.command} została wyłączona.')
    elif isinstance(error, commands.NoPrivateMessage):
        try:
            return await ctx.author.send(f'Komenda {ctx.command} nie może zostać użyta w prywatnej wiadomości.')
        except:
            pass
    print(f'Ignorowanie wyjątku w komendzie {ctx.command}:', file=sys.stderr)
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

client.run(conf['discord_token'])

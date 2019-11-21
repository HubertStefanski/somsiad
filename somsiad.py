# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import Union
import os
import sys
import asyncio
import platform
import logging
import random
import datetime as dt
import discord
from discord.ext.commands import Bot
from version import __version__
from utilities import Configurator, Setting, TextFormatter

COPYRIGHT = '© 2018-2019 Twixes, ondondil et al.'

class Somsiad:
    color = 0x7289da
    user_agent = f'SomsiadBot/{__version__}'

    bot_dir_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    conf_dir_path = os.path.join(os.path.expanduser('~'), '.config')
    conf_file_path = os.path.join(conf_dir_path, 'somsiad.json')
    storage_dir_path = os.path.join(os.path.expanduser('~'), '.local', 'share', 'somsiad')
    cache_dir_path = os.path.join(os.path.expanduser('~'), '.cache', 'somsiad')

    message_autodestruction_time_in_seconds = 5
    message_autodestruction_notice = (
        'Ta wiadomość ulegnie autodestrukcji w ciągu '
        f'{TextFormatter.word_number_variant(message_autodestruction_time_in_seconds, "sekundy", "sekund")} od wysłania.'
    )

    required_settings = [
        Setting(
            'discord_token', description='Token bota', input_instruction='Wprowadź discordowy token bota',
            value_type='str'
        ),
        Setting(
            'command_prefix', description='Prefiks komend', input_instruction='Wprowadź prefiks komend',
            value_type='str', default_value='!'
        ),
        Setting(
            'command_cooldown_per_user_in_seconds', description='Cooldown wywołania komendy przez użytkownika',
            input_instruction='Wprowadź cooldown wywołania komendy przez użytkownika w sekundach',
            unit=('sekunda', 'sekund'), value_type='float', default_value=1.0
        )
    ]

    def __init__(self, additional_required_settings: Union[list, tuple] = None):
        self.run_datetime = None
        self.logger = logging.getLogger('Somsiad')
        logging.basicConfig(
            filename=os.path.join(self.bot_dir_path, 'somsiad.log'),
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        if not os.path.exists(self.conf_dir_path):
            os.makedirs(self.conf_dir_path)
        if not os.path.exists(self.storage_dir_path):
            os.makedirs(self.storage_dir_path)
        if not os.path.exists(self.cache_dir_path):
            os.makedirs(self.cache_dir_path)
        self.required_settings.extend(additional_required_settings)
        self.configurator = Configurator(self.conf_file_path, self.required_settings)
        self.bot = Bot(
            command_prefix=self.prefix_callable, help_command=None, description='Zawsze pomocny Somsiad',
            case_insensitive=True
        )
        self.member_converter = discord.ext.commands.MemberConverter()

    def run(self):
        """Launches the bot."""
        self.run_datetime = dt.datetime.now()
        try:
            self.bot.run(self.conf['discord_token'], reconnect=True)
        except discord.errors.ClientException:
            self.logger.critical('Client could not come online! The Discord bot token provided may be faulty.')
        else:
            self.logger.info('Client started.')

    def prefix_callable(self, bot, message):
        user_id = bot.user.id
        prefixes = [f'<@!{user_id}> ', f'<@{user_id}> ', self.conf['command_prefix']]
        return prefixes

    @property
    def conf(self):
        """Returns current configuration of the bot."""
        return self.configurator.configuration

    @property
    def invite_url(self):
        """Returns the invitation URL of the bot."""
        try:
            return discord.utils.oauth_url(self.bot.user.id, discord.Permissions(305392727))
        except discord.errors.ClientException:
            return None


# Plugin settings
ADDITIONAL_REQUIRED_SETTINGS = (
    Setting(
        'google_key', description='Klucz API Google', input_instruction='Wprowadź klucz API Google', value_type='str'
    ),
    Setting(
        'google_custom_search_engine_id', description='Identyfikator CSE Google',
        input_instruction='Wprowadź identyfikator CSE Google', value_type='str'
    ),
    Setting(
        'goodreads_key', description='Klucz API Goodreads', input_instruction='Wprowadź klucz API Goodreads',
        value_type='str'
    ),
    Setting(
        'omdb_key', description='Klucz API OMDb', input_instruction='Wprowadź klucz API OMDb', value_type='str'
    ),
    Setting(
        'last_fm_key', description='Klucz API Last.fm', input_instruction='Wprowadź klucz API Last.fm', value_type='str'
    ),
    Setting(
        'yandex_translate_key', description='Klucz API Yandex Translate',
        input_instruction='Wprowadź klucz API Yandex Translate', value_type='str'
    ),
    Setting(
        'reddit_id', description='ID aplikacji redditowej', input_instruction='Wprowadź ID aplikacji redditowej',
        value_type='str'
    ),
    Setting(
        'reddit_secret', description='Szyfr aplikacji redditowej',
        input_instruction='Wprowadź szyfr aplikacji redditowej', value_type='str'
    ),
    Setting(
        'reddit_username', description='Redditowa nazwa użytkownika',
        input_instruction='Wprowadź redditową nazwę użytkownika', value_type='str'
    ),
    Setting(
        'reddit_password', description='Hasło do konta na Reddicie',
        input_instruction='Wprowadź hasło do konta na Reddicie', value_type='str'
    ),
    Setting(
        'disco_max_file_size_in_mib', description='Maksymalny rozmiar pliku utworu disco',
        input_instruction='Wprowadź maksymalny rozmiar pliku utworu disco', unit='MiB', value_type='int',
        default_value=16
    )
)


somsiad = Somsiad(ADDITIONAL_REQUIRED_SETTINGS)


@somsiad.bot.command(aliases=['nope', 'nie'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def no(ctx, member: discord.Member = None):
    """Removes the last message sent by the bot in the channel on the requesting user's request."""
    member = member or ctx.author

    if member == ctx.author or ctx.author.permissions_in(ctx.channel).manage_messages:
        async for message in ctx.history(limit=10):
            if message.author == ctx.me and member in message.mentions:
                await message.delete()
                break


@somsiad.bot.command(aliases=['wersja', 'v'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def version(ctx):
    """Responds with current version of the bot."""
    EMOJIS = [
        'b', 'fire', 'frog', 'thinking', 'angry', 'boom', 'ok_hand', 'poop', 'rabbit', 'rabbit2', 'eagle',
        'upside_down', 'blush', 'slight_smile', 'nerd', 'scream', 'japanese_ogre', 'japanese_goblin', 'robot',
        'raised_hands', 'wave', 'muscle', 'eyes', 'construction_worker', 'spy', 'dancer', 'tophat', 'cowboy', 'dog',
        'cat', 'hamster', 'koala', 'pig', 'octopus', 'penguin', 'chicken', 'horse', 'unicorn', 'bee', 'beetle',
        'turtle', 'dolphin', 'whale', 'goat', 'racehorse', 'pig2', 'cactus', 'sunflower', 'sun_with_face', 'comet',
        'zap', 'duck', 'owl', 'fox', 'apple', 'banana', 'watermelon', 'grapes', 'peach', 'pineapple', 'eggplant',
        'bread', 'cheese', 'fries', 'ramen', 'cake', 'candy', 'lollipop', 'cookie', 'avocado', 'potato', 'egg', 'art',
        'saxophone', 'trumpet', 'space_invader', 'dart', 'drum', 'bike', 'rocket', 'satellite_orbital', 'anchor',
        'beach', 'sparkler', 'fireworks', 'rainbow', 'bulb', 'barber', 'telescope', 'balloon', 'ribbon', 'tada', '100',
        'gift_heart', 'radioactive', 'biohazard', 'sos', 'hotsprings'
    ]
    embed = discord.Embed(
        title=f':{random.choice(EMOJIS)}: Somsiad {__version__}',
        url='https://somsiad.twixes.com',
        color=somsiad.color
    )
    embed.set_footer(text=COPYRIGHT)
    await ctx.send(ctx.author.mention, embed=embed)


@somsiad.bot.command(aliases=['informacje'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def info(ctx):
    """Responds with current version of the bot."""
    embed = discord.Embed(
        title=f':information_source: Somsiad {__version__}',
        url='https://somsiad.twixes.com',
        color=somsiad.color
    )
    embed.add_field(name='Liczba serwerów', value=len(somsiad.bot.guilds))
    embed.add_field(name='Liczba użytkowników', value=len(set(somsiad.bot.get_all_members())))
    embed.add_field(
        name='Czas pracy', value=TextFormatter.human_readable_time(dt.datetime.now() - somsiad.run_datetime)
    )
    embed.add_field(name='Właściciel instancji', value=(await somsiad.bot.application_info()).owner.mention)
    embed.set_footer(text=COPYRIGHT)
    await ctx.send(ctx.author.mention, embed=embed)


@somsiad.bot.command()
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def ping(ctx):
    """Pong!"""
    embed = discord.Embed(
        title=':ping_pong: Pong!',
        color=somsiad.color
    )
    await ctx.send(ctx.author.mention, embed=embed)


@somsiad.bot.event
async def on_ready():
    """Does things once the bot comes online."""
    number_of_users = len(set(somsiad.bot.get_all_members()))
    number_of_servers = len(somsiad.bot.guilds)

    info_lines = [
        f'Obudzono Somsiada (ID {somsiad.bot.user.id}).',
        '',
        f'Połączono {TextFormatter.with_preposition_variant(number_of_users)} '
        f'{TextFormatter.word_number_variant(number_of_users, "użytkownikiem", "użytkownikami")} '
        f'na {TextFormatter.word_number_variant(number_of_servers, "serwerze", "serwerach")}.',
        '',
        'Link do zaproszenia bota:',
        somsiad.invite_url,
        '',
        somsiad.configurator.info(),
        '',
        f'Somsiad {__version__} • discord.py {discord.__version__} • Python {platform.python_version()}',
        '',
        COPYRIGHT
    ]

    print('\n'.join(info_lines))

    while True:
        # necessary due to presence randomly disappearing if not refreshed
        await somsiad.bot.change_presence(
            activity=discord.Game(name=f'Kiedyś to było | {somsiad.conf["command_prefix"]}pomocy')
        )
        await asyncio.sleep(600)


@somsiad.bot.event
async def on_command_error(ctx, error):
    """Handles command errors."""
    ignored_errors = (
        discord.ext.commands.CommandNotFound,
        discord.ext.commands.MissingRequiredArgument,
        discord.ext.commands.BadArgument
    )

    if isinstance(error, ignored_errors):
        pass
    elif isinstance(error, discord.ext.commands.NoPrivateMessage):
        embed = discord.Embed(
            title=f':warning: Ta komenda nie może być użyta w prywatnych wiadomościach!',
            color=somsiad.color
        )
        await ctx.send(embed=embed)
    elif isinstance(error, discord.ext.commands.DisabledCommand):
        embed = discord.Embed(
            title=f':warning: Ta komenda jest wyłączona!',
            color=somsiad.color
        )
        await ctx.send(ctx.author.mention, embed=embed)
    else:
        prefixed_command_qualified_name = f'{somsiad.conf["command_prefix"]}{ctx.command.qualified_name}'
        if ctx.guild is None:
            log_entry = (
                f'Ignoring {type(error).__name__} type exception in command {prefixed_command_qualified_name} '
                f'used by {ctx.author} (ID {ctx.author.id}) in direct messages: "{error}"'
            )
        else:
            log_entry = (
                f'Ignoring {type(error).__name__} type exception in command {prefixed_command_qualified_name} '
                f'used by {ctx.author} (ID {ctx.author.id}) on server {ctx.guild} (ID {ctx.guild.id}): "{error}"'
            )
        somsiad.logger.error(log_entry)

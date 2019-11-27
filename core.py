# Copyright 2018-2019 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import Optional, Union, Sequence, Tuple, List
import os
import sys
import asyncio
import platform
import random
import itertools
import datetime as dt
import sentry_sdk
import discord
from discord.ext.commands import Bot
from version import __version__, __copyright__
from utilities import word_number_form, human_amount_of_time
from configuration import configuration
import data


class Somsiad(Bot):
    COLOR = 0x7289da
    USER_AGENT = f'SomsiadBot/{__version__}'
    WEBSITE_URL = 'https://somsiad.net'
    EMOJIS = [
        '🐜', '🅱️', '🔥', '🐸', '🤔', '💥', '👌', '💩', '🐇', '🐰', '🦅', '🙃', '😎', '😩', '👹', '👺', '🤖', '✌️',
        '🙌', '👋', '💪', '👀', '👷', '🕵️', '💃', '🎩', '🤠', '🐕', '🐈', '🐹', '🐨', '🐽', '🐙', '🐧', '🐔', '🐎',
        '🦄', '🐝', '🐢', '🐬', '🐋', '🐐', '🌵', '🌻', '🌞', '☄️', '⚡', '🦆', '🦉', '🦊', '🍎', '🍉', '🍇', '🍑',
        '🍍', '🍆', '🍞', '🧀', '🍟', '🎂', '🍬', '🍭', '🍪', '🥑', '🥔', '🎨', '🎷', '🎺', '👾', '🎯', '🥁', '🚀',
        '🛰️', '⚓', '🏖️', '✨', '🌈', '💡', '💈', '🔭', '🎈', '🎉', '💯', '💝', '☢️', '🆘', '♨️', '💭'
    ]
    IGNORED_ERRORS = (
        discord.ext.commands.CommandOnCooldown,
        discord.ext.commands.CommandNotFound,
        discord.ext.commands.MissingRequiredArgument,
        discord.ext.commands.BadArgument
    )
    MESSAGE_AUTODESTRUCTION_TIME_IN_SECONDS = 5
    MESSAGE_AUTODESTRUCTION_NOTICE = (
        'Ta wiadomość ulegnie autodestrukcji w ciągu '
        f'{word_number_form(MESSAGE_AUTODESTRUCTION_TIME_IN_SECONDS, "sekundy", "sekund")} od wysłania.'
    )

    bot_dir_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    storage_dir_path = os.path.join(os.path.expanduser('~'), '.local', 'share', 'somsiad')
    cache_dir_path = os.path.join(os.path.expanduser('~'), '.cache', 'somsiad')

    def __init__(self):
        super().__init__(
            command_prefix=self._get_prefix, help_command=None, description='Zawsze pomocny Somsiad',
            case_insensitive=True
        )
        self.run_datetime = None
        if not os.path.exists(self.storage_dir_path):
            os.makedirs(self.storage_dir_path)
        if not os.path.exists(self.cache_dir_path):
            os.makedirs(self.cache_dir_path)
        self.prefix_safe_commands = tuple((
            variant
            for command in
            ('help', 'pomocy', 'pomoc', 'prefix', 'prefiks', 'przedrostek', 'info', 'informacje', 'ping')
            for variant in
            (f'{configuration["command_prefix"]} {command}', f'{configuration["command_prefix"]}{command}')
        ))

    async def on_ready(self):
        print(self.info())
        data.Server.register_all(self.guilds)
        await self.cycle_presence()

    async def on_command_error(self, ctx, error):
        if isinstance(error, self.IGNORED_ERRORS):
            pass
        elif isinstance(error, discord.ext.commands.NoPrivateMessage):
            embed = discord.Embed(
                title=f':warning: Ta komenda nie może być użyta w prywatnych wiadomościach',
                color=self.COLOR
            )
            await ctx.send(embed=embed)
        elif isinstance(error, discord.ext.commands.DisabledCommand):
            embed = discord.Embed(
                title=f':warning: Ta komenda jest wyłączona',
                color=self.COLOR
            )
            await ctx.send(ctx.author.mention, embed=embed)
        else:
            self.handle_error(ctx, error)

    async def on_guild_join(self, server):
        data.Server.register(server)

    def controlled_run(self):
        self.run_datetime = dt.datetime.now()
        self.run(configuration['discord_token'], reconnect=True)

    def invite_url(self) -> str:
        """Return the invitation URL of the bot."""
        return discord.utils.oauth_url(self.user.id, discord.Permissions(305392727))

    def info(self) -> str:
        """Return a block of bot information."""
        number_of_users = len(set(self.get_all_members()))
        number_of_servers = len(self.guilds)
        info_lines = [
            f'Obudzono Somsiada (ID {self.user.id}).',
            '',
            f'Połączono '
            f'{word_number_form(number_of_users, "użytkownikiem", "użytkownikami", include_with=True)} '
            f'na {word_number_form(number_of_servers, "serwerze", "serwerach")}.',
            '',
            'Link do zaproszenia bota:',
            self.invite_url(),
            '',
            *map(str, configuration.settings.values()),
            '',
            f'Somsiad {__version__} • discord.py {discord.__version__} • Python {platform.python_version()}',
            '',
            __copyright__
        ]
        return '\n'.join(info_lines)

    async def cycle_presence(self):
        """Cycle through prefix safe commands in the presence."""
        prefix_safe_commands = ('pomocy', 'prefiks', 'info', 'ping')
        for command in itertools.cycle(prefix_safe_commands):
            await self.change_presence(
                activity=discord.Game(name=f'Kiedyś to było | {configuration["command_prefix"]}{command}')
            )
            await asyncio.sleep(15)

    def handle_error(self, ctx, error):
        if configuration['sentry_dsn'] is None: raise error
        with sentry_sdk.push_scope() as scope:
            scope.user = {
                'id': ctx.author.id, 'username': str(ctx.author),
                'activities': (
                    ', '.join((activity.name for activity in ctx.author.activities))
                    if ctx.guild is not None else None
                )
            }
            scope.set_tag('command', ctx.command.qualified_name)
            scope.set_tag('root_command', ctx.command.root_parent or ctx.command.qualified_name)
            scope.set_context('message', {
                'prefix': ctx.prefix, 'content': ctx.message.content,
                'attachments': ', '.join((attachment.url for attachment in ctx.message.attachments))
            })
            scope.set_context('channel', {
                'id': ctx.channel.id, 'name': str(ctx.channel)
            })
            if ctx.guild is not None:
                scope.set_context('server', {
                    'id': ctx.guild.id, 'name': str(ctx.guild)
                })
            sentry_sdk.capture_exception(error)

    def _get_prefix(self, bot: Bot, message: discord.Message) -> List[str]:
        user_id = bot.user.id
        prefixes = [f'<@!{user_id}> ', f'<@{user_id}> ']
        if message.guild is not None:
            session = data.Session()
            data_server = session.query(data.Server).get(message.guild.id)
            session.close()
        else:
            data_server = None
        does_server_have_custom_command_prefix = data_server is not None and data_server.command_prefix is not None
        is_message_a_prefix_safe_command = message.content.startswith(self.prefix_safe_commands)
        if does_server_have_custom_command_prefix:
            prefixes.append(data_server.command_prefix + ' ')
            prefixes.append(data_server.command_prefix)
        if not does_server_have_custom_command_prefix or is_message_a_prefix_safe_command:
            prefixes.append(configuration['command_prefix'] + ' ')
            prefixes.append(configuration['command_prefix'])
        return prefixes


class Help:
    """A help message generator."""
    class Command:
        "A command model."
        __slots__ = ('_aliases', '_arguments', '_description')

        def __init__(self, aliases: Union[Tuple[str], str], arguments: Union[Tuple[str], str], description: str):
            self._aliases = aliases if isinstance(aliases, tuple) else (aliases,)
            self._arguments = arguments if isinstance(arguments, tuple) else (arguments,)
            self._description = description

        def __str__(self) -> str:
            return ' '.join(filter(None, (self.name, self.aliases, self.arguments)))

        @property
        def name(self) -> str:
            return self._aliases[0]

        @property
        def aliases(self) -> Optional[str]:
            return f'({", ".join(self._aliases[1:])})' if len(self._aliases) > 1 else None

        @property
        def arguments(self) -> Optional[str]:
            return " ".join(f"<{argument}>" for argument in self._arguments) if self._arguments else None

        @property
        def description(self) -> str:
            return self._description

    __slots__ = ('group', 'embeds')

    def __init__(
            self, commands: Sequence[Command], *,
            title: Optional[str] = None, description: Optional[str] = None, group: Optional[Command] = None
    ):
        self.group = group
        if group is not None and title is None:
            title = f'Dostępne podkomendy {" ".join(filter(None, (group.name, group.aliases)))}'
        if description is None:
            description = (
                'Używając ich pamiętaj o prefiksie (możesz zawsze sprawdzić go za pomocą '
                f'`{configuration["command_prefix"]}prefiks sprawdź`).\n'
                'W (nawiasach okrągłych) podane są aliasy komend.\n'
                'W <nawiasach ostrokątnych> podane są argumenty komend. Jeśli przed nazwą argumentu jest ?pytajnik, '
                'oznacza to, że jest to argument opcjonalny.'
            )
        self.embeds = [discord.Embed(title=title, description=description, color=somsiad.COLOR)]
        for command in commands:
            self.append(command)

    def append(self, command: Command):
        if len(self.embeds[-1].fields) >= 25:
            self.embeds.append(discord.Embed(color=somsiad.COLOR))
        self.embeds[-1].add_field(
            name=str(command) if self.group is None else f'{self.group.name} {command}',
            value=command.description,
            inline=False
        )

    async def send(self, ctx: discord.ext.commands.Context, *, privately: bool = False):
        destination = ctx.author if privately else ctx.channel
        if privately and not isinstance(ctx.channel, discord.abc.PrivateChannel):
            await ctx.message.add_reaction('📫')
        await destination.send(None if privately else ctx.author.mention, embed=self.embeds[0])
        for embed in self.embeds[1:]:
            await destination.send(embed=embed)


somsiad = Somsiad()


@somsiad.command(aliases=['nope', 'nie'])
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def no(ctx, member: discord.Member = None):
    """Removes the last message sent by the bot in the channel on the requesting user's request."""
    member = member or ctx.author

    if member == ctx.author or ctx.author.permissions_in(ctx.channel).manage_messages:
        async for message in ctx.history(limit=10):
            if message.author == ctx.me and member in message.mentions:
                await message.delete()
                break


GROUP = Help.Command(('prefiks', 'prefix', 'przedrostek'), (), 'Grupa komend związanych z prefiksem.')
COMMANDS = (
    Help.Command(('sprawdź', 'sprawdz'), (), 'Pokazuje obowiązujący prefiks.'),
    Help.Command(('ustaw'), (), 'Ustawia na serwerze podany prefiks.'),
    Help.Command(('usuń', 'usun'), (), 'Przywraca na serwerze domyślny prefiks.')
)
HELP = Help(COMMANDS, group=GROUP)

prefix_usage_example = lambda example_prefix: f'Przykład użycia: `{example_prefix}wersja` lub `{example_prefix} oof`.'


@somsiad.group(aliases=['prefiks', 'przedrostek'], invoke_without_command=True)
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def prefix(ctx):
    """Command prefix commands."""
    await HELP.send(ctx)


@prefix.command(aliases=['sprawdź', 'sprawdz'])
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.default
)
async def prefix_check(ctx):
    """Presents the current command prefix."""
    session = data.Session()
    data_server = session.query(data.Server).get(ctx.guild.id) if ctx.guild is not None else None
    is_prefix_custom = data_server is not None and data_server.command_prefix is not None
    current_prefix = data_server.command_prefix if is_prefix_custom else configuration["command_prefix"]
    embed = discord.Embed(
        title=':wrench: Obowiązujący prefiks to '
        f'"{current_prefix}"{" (wartość domyślna)" if not is_prefix_custom else ""}',
        description=prefix_usage_example(current_prefix),
        color=somsiad.COLOR
    )
    session.close()
    await ctx.send(ctx.author.mention, embed=embed)


@prefix.command(aliases=['ustaw'])
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.default
)
@discord.ext.commands.guild_only()
@discord.ext.commands.has_permissions(administrator=True)
async def prefix_set(ctx, *, new_prefix: str):
    """Sets a new command prefix."""
    session = data.Session()
    data_server = session.query(data.Server).get(ctx.guild.id)
    if len(new_prefix) > data.Server.COMMAND_PREFIX_MAX_LENGTH:
        session.close()
        raise discord.ext.commands.BadArgument
    data_server.command_prefix = new_prefix
    session.commit()
    embed = discord.Embed(
        title=f':white_check_mark: Ustawiono nowy prefiks "{new_prefix}"',
        description=prefix_usage_example(new_prefix),
        color=somsiad.COLOR
    )
    session.close()
    await ctx.send(ctx.author.mention, embed=embed)


@prefix_set.error
async def prefix_set_error(ctx, error):
    """Handles new command prefix setting errors."""
    embed = None
    if isinstance(error, discord.ext.commands.MissingPermissions):
        embed = discord.Embed(
            title=':warning: Do ustawienia prefiksu potrzebne są uprawnienia adminstratora',
            color=somsiad.COLOR
        )
    elif isinstance(error, discord.ext.commands.MissingRequiredArgument):
        embed = discord.Embed(
            title=':warning: Nie podano nowego prefiksu',
            color=somsiad.COLOR
        )
    elif isinstance(error, discord.ext.commands.BadArgument):
        embed = discord.Embed(
            title=':warning: Nowy prefiks nie może być dłuższy niż '
            f'{word_number_form(data.Server.COMMAND_PREFIX_MAX_LENGTH, "znak", "znaki", "znaków")}',
            color=somsiad.COLOR
        )
    if embed is not None:
        await ctx.send(ctx.author.mention, embed=embed)


@prefix.command(aliases=['usuń', 'usun'])
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.default
)
@discord.ext.commands.guild_only()
@discord.ext.commands.has_permissions(administrator=True)
async def prefix_remove(ctx):
    """Reverts to the default command prefix."""
    session = data.Session()
    data_server = session.query(data.Server).get(ctx.guild.id)
    data_server.command_prefix = None
    session.commit()
    new_prefix = configuration['command_prefix']
    embed = discord.Embed(
        title=f':white_check_mark: Przywrócono domyślny prefiks "{new_prefix}"',
        description=prefix_usage_example(new_prefix),
        color=somsiad.COLOR
    )
    session.close()
    await ctx.send(ctx.author.mention, embed=embed)


@prefix_remove.error
async def prefix_remove_error(ctx, error):
    """Handles reverting to the default command prefix errors."""
    embed = None
    if isinstance(error, discord.ext.commands.MissingPermissions):
        embed = discord.Embed(
            title=':warning: Do usunięcia prefiksu potrzebne są uprawnienia adminstratora',
            color=somsiad.COLOR
        )
    if embed is not None:
        await ctx.send(ctx.author.mention, embed=embed)


@somsiad.command(aliases=['wersja', 'v'])
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def version(ctx):
    """Responds with current version of the bot."""
    embed = discord.Embed(
        title=f'{random.choice(somsiad.EMOJIS)} Somsiad {__version__}',
        url=somsiad.WEBSITE_URL,
        color=somsiad.COLOR
    )
    embed.set_footer(text=__copyright__)
    await ctx.send(ctx.author.mention, embed=embed)


@somsiad.command(aliases=['informacje'])
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def info(ctx):
    """Responds with current version of the bot."""
    embed = discord.Embed(
        title=f':information_source: Somsiad {__version__}',
        url=somsiad.WEBSITE_URL,
        color=somsiad.COLOR
    )
    embed.add_field(name='Liczba serwerów', value=len(somsiad.guilds))
    embed.add_field(name='Liczba użytkowników', value=len(set(somsiad.get_all_members())))
    embed.add_field(
        name='Czas pracy', value=human_amount_of_time(dt.datetime.now() - somsiad.run_datetime)
    )
    embed.add_field(name='Właściciel instancji', value=(await somsiad.application_info()).owner.mention)
    embed.set_footer(text=__copyright__)
    await ctx.send(ctx.author.mention, embed=embed)


@somsiad.command()
@discord.ext.commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
async def ping(ctx):
    """Pong!"""
    embed = discord.Embed(
        title=':ping_pong: Pong!',
        color=somsiad.COLOR
    )
    await ctx.send(ctx.author.mention, embed=embed)

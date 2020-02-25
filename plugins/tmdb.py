# Copyright 2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import Optional
import datetime as dt
import aiohttp
import discord
from discord.ext import commands
from core import Help, somsiad
from configuration import configuration


class TMDb(commands.Cog):
    GROUP = Help.Command('tmdb', (), 'Grupa komend związanych z kinem i telewizją.')
    COMMANDS = (
        Help.Command(('film', 'kino'), 'zapytanie', 'Zwraca najlepiej pasujący do <zapytania> film.'),
        Help.Command(
            ('serial', 'seria', 'telewizja', 'tv'), 'zapytanie', 'Zwraca najlepiej pasujący do <zapytania> serial.'
        ),
        Help.Command('osoba', 'zapytanie', 'Zwraca najlepiej pasującą do <zapytania> osobę.')
    )
    HELP = Help(COMMANDS, group=GROUP)
    PROFESSIONS = {
        'Acting': '🎭', 'Art': '🎨', 'Camera': '🎥', 'Costume': '👗', 'Creator': '🧠', 'Crew': '🔧', 'Directing': '🎬',
        'Editing': '✂️', 'Lighting': '💡', 'Production': '📈', 'Sound': '🎙', 'Visual Effects': '🎇', 'Writing': '🖋'
    }

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def fetch_result_and_generate_embed(self, query: str, media_type: Optional[str] = None) -> discord.Embed:
        params = {'api_key': configuration['tmdb_key'], 'query': query, 'language': 'pl-PL', 'region': 'PL'}
        url = f'https://api.themoviedb.org/3/search/{media_type or "multi"}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.bot.HEADERS, params=params) as request:
                if request.status != 200:
                    embed = self.bot.generate_embed('⚠️', f'Nie udało się połączyć z serwisem')
                else:
                    response = await request.json()
                    if not response['total_results']:
                        embed = self.bot.generate_embed('🙁', f'Brak wyników dla zapytania "{query}"')
                    else:
                        result = response['results'][0]
                        media_type = media_type or result['media_type']
                        if media_type == 'person':
                            embed = self.generate_person_embed(result)
                        elif media_type == 'movie':
                            embed = self.generate_movie_embed(result)
                        elif media_type == 'tv':
                            embed = self.generate_tv_embed(result)
        embed.set_footer(
            text='TMDb',
            icon_url='https://www.themoviedb.org/assets/2/v4/logos/'
            '208x226-stacked-green-9484383bd9853615c113f020def5cbe27f6d08a84ff834f41371f223ebad4a3c.png'
        )
        return embed

    def generate_person_embed(self, result: dict) -> discord.Embed:
        is_female = result['gender'] == 1
        emoji = self.PROFESSIONS.get(result['known_for_department']) or ('👩' if is_female else '👨')
        embed = self.bot.generate_embed(emoji, result['name'], url=f'https://www.themoviedb.org/person/{result["id"]}')
        known_for_parts = (
            f'📺 {production["name"]} ({production["first_air_date"][:4]})'
            if production['media_type'] == 'tv' else
            f'🎞 {production["title"]} ({production["release_date"][:4]})'
            for production in result['known_for']
        )
        embed.add_field(
            name='Znana z' if is_female else 'Znany z', value='\n'.join(known_for_parts), inline=False
        )
        if result['profile_path']:
            embed.set_thumbnail(url=f'https://image.tmdb.org/t/p/w342{result["profile_path"]}')
        if result['known_for'] and result['known_for'][0].get('backdrop_path'):
            embed.set_image(url=f'https://image.tmdb.org/t/p/w780{result["known_for"][0]["backdrop_path"]}')
        return embed

    def generate_movie_embed(self, result: dict) -> discord.Embed:
        release_date = dt.datetime.strptime(result['release_date'], '%Y-%m-%d').date()
        embed = self.bot.generate_embed(
            '🎞', f'{result["title"]} ({result["release_date"][:4]})',
            url=f'https://www.themoviedb.org/person/{result["id"]}'
        )
        if result.get('original_title') != result['title']:
            embed.add_field(name='Tytuł oryginalny', value=result['original_title'], inline=False)
        embed.add_field(name='Data premiery', value=release_date.strftime('%-d %B %Y'))
        embed.add_field(name='Średnia ocen', value=f'{result["vote_average"]:n} / 10')
        embed.add_field(name='Liczba głosów', value=f'{result["vote_count"]:n}')
        embed.add_field(name='Opis', value=result['overview'], inline=False)
        if result.get('poster_path'):
            embed.set_thumbnail(url=f'https://image.tmdb.org/t/p/w342{result["poster_path"]}')
        if result.get('backdrop_path'):
            embed.set_image(url=f'https://image.tmdb.org/t/p/w780{result["backdrop_path"]}')
        return embed

    def generate_tv_embed(self, result: dict) -> discord.Embed:
        first_air_date = dt.datetime.strptime(result['first_air_date'], '%Y-%m-%d').date()
        embed = self.bot.generate_embed(
            '📺', f'{result["name"]} ({result["first_air_date"][:4]})',
            url=f'https://www.themoviedb.org/person/{result["id"]}'
        )
        if result.get('original_name') != result['name']:
            embed.add_field(name='Tytuł oryginalny', value=result['original_name'], inline=False)
        embed.add_field(name='Data premiery', value=first_air_date.strftime('%-d %B %Y'))
        embed.add_field(name='Średnia ocen', value=f'{result["vote_average"]:n} / 10')
        embed.add_field(name='Liczba głosów', value=f'{result["vote_count"]:n}')
        embed.add_field(name='Opis', value=result['overview'], inline=False)
        if result.get('poster_path'):
            embed.set_thumbnail(url=f'https://image.tmdb.org/t/p/w342{result["poster_path"]}')
        if result.get('backdrop_path'):
            embed.set_image(url=f'https://image.tmdb.org/t/p/w780{result["backdrop_path"]}')
        return embed

    @commands.group(invoke_without_command=True)
    @commands.cooldown(1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.default)
    async def tmdb(self, ctx, *, query):
        """Responds with the most popular movie/series/person matching the query."""
        async with ctx.typing():
            embed = await self.fetch_result_and_generate_embed(query)
            await self.bot.send(ctx, embed=embed)

    @tmdb.error
    async def tmdb_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await somsiad.send(ctx, embeds=self.HELP.embeds)

    @tmdb.command(aliases=['film', 'kino'])
    @commands.cooldown(1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.default)
    async def movie(self, ctx, *, query):
        """Responds with the most popular movie matching the query."""
        async with ctx.typing():
            embed = await self.fetch_result_and_generate_embed(query, 'movie')
            await self.bot.send(ctx, embed=embed)

    @tmdb.command(aliases=['serial', 'seria', 'telewizja'])
    @commands.cooldown(1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.default)
    async def tv(self, ctx, *, query):
        """Responds with the most popular TV series matching the query."""
        async with ctx.typing():
            embed = await self.fetch_result_and_generate_embed(query, 'tv')
            await self.bot.send(ctx, embed=embed)

    @tmdb.command(aliases=['osoba'])
    @commands.cooldown(1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.default)
    async def person(self, ctx, *, query):
        """Responds with the most popular person matching the query."""
        async with ctx.typing():
            embed = await self.fetch_result_and_generate_embed(query, 'person')
            await self.bot.send(ctx, embed=embed)


somsiad.add_cog(TMDb(somsiad))

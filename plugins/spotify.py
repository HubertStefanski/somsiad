# Copyright 2018-2019 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from difflib import SequenceMatcher
import discord
from discord.ext import commands
from core import somsiad
from utilities import human_amount_of_time
from configuration import configuration
from plugins.youtube import youtube


@somsiad.command()
@commands.cooldown(
    1, configuration['command_cooldown_per_user_in_seconds'], commands.BucketType.user
)
@commands.guild_only()
async def spotify(ctx, member: discord.Member = None):
    """Shares the song currently played on Spotify by the provided user (or if not provided, by the invoking user)."""
    member = member or ctx.author

    spotify_activity = None
    for activity in member.activities:
        if isinstance(activity, discord.activity.Spotify):
            spotify_activity = activity
            break

    if spotify_activity is None:
        embed = discord.Embed(
            title=':stop_button: W tym momencie '
            f'{"nie słuchasz" if member == ctx.author else f"{member.display_name} nie słucha"} niczego na Spotify',
            color=somsiad.COLOR
        )
    else:
        embed = discord.Embed(
            title=f':arrow_forward: {spotify_activity.title}',
            url=f'https://open.spotify.com/go?uri=spotify:track:{spotify_activity.track_id}',
            color=somsiad.COLOR
        )
        embed.set_thumbnail(url=spotify_activity.album_cover_url)
        embed.add_field(name='W wykonaniu', value=', '.join(spotify_activity.artists))
        embed.add_field(name='Z albumu', value=spotify_activity.album)
        embed.add_field(
            name='Długość', value=human_amount_of_time(spotify_activity.duration.total_seconds())
        )

        # Search for the song on YouTube
        youtube_search_query = f'{spotify_activity.title} {" ".join(spotify_activity.artists)}'
        youtube_search_result = youtube.search(youtube_search_query)
        # Add a link to a YouTube video if a match was found
        if (
                youtube_search_result and
                SequenceMatcher(None, youtube_search_query, youtube_search_result[0]['snippet']['title']).ratio() > 0.25
        ):
            video_id = youtube_search_result[0]['id']['videoId']
            video_thumbnail_url = youtube_search_result[0]['snippet']['thumbnails']['medium']['url']
            embed.add_field(
                name='Posłuchaj na YouTube', value=f'https://www.youtube.com/watch?v={video_id}', inline=False
            )
            embed.set_image(url=video_thumbnail_url)

        embed.set_footer(
            text='Spotify',
            icon_url='https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/'
            'Spotify_logo_without_text.svg/60px-Spotify_logo_without_text.svg.png'
        )

    await somsiad.send(ctx, embed=embed)

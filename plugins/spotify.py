# Copyright 2018 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import discord
from somsiad import somsiad
from utilities import TextFormatter
from plugins.youtube import youtube


@somsiad.bot.command(aliases=['kanał', 'kanal'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def spotify(ctx):
    """Shares the song currently played on Spotify."""
    if isinstance(ctx.author.activity, discord.activity.Spotify):
        embed = discord.Embed(
            title=f':arrow_forward: {ctx.author.activity.title}',
            color=somsiad.color
        )
        embed.set_thumbnail(url=ctx.author.activity.album_cover_url)
        embed.add_field(name='Autorstwa', value=', '.join(ctx.author.activity.artists))
        embed.add_field(name='Z albumu', value=ctx.author.activity.album)
        embed.add_field(name='Przesłuchaj na Spotify', value=f'https://open.spotify.com/track/{ctx.author.activity.track_id}')

        youtube_search_result = youtube.search(f'{ctx.author.activity.title} {" ".join(ctx.author.activity.artists)}')
        if youtube_search_result:
            video_id = youtube_search_result[0]['id']['videoId']
            embed.add_field(name='Przesłuchaj na YouTube', value=f'https://www.youtube.com/watch?v={video_id}')

        embed.set_footer(text='Spotify', icon_url='https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Spotify_logo_without_text.svg/60px-Spotify_logo_without_text.svg.png')
    else:
        embed = discord.Embed(
            title=f':stop_button: Obecnie nie słuchasz niczego na Spotify',
            color=somsiad.color
        )

    await ctx.send(f'{ctx.author.mention}', embed=embed)
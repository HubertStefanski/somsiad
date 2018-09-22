# Copyright 2018 ondondil & Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

import os
import random
import json
import discord
from somsiad import somsiad

class Ball:
    with open(os.path.join(somsiad.bot_dir_path, 'data', 'eightball_answers.json')) as f:
        eightball_answers = json.load(f)

    categories = ['affirmative' for _ in range(2)] + ['negative' for _ in range(2)] + ['enigmatic']

    @classmethod
    def ask(cls) -> str:
        category = random.choice(cls.categories)
        answer = random.choice(cls.eightball_answers[category])
        return answer

    @classmethod
    def AsK(cls) -> str:
        aNSwEr = ''.join(random.choice([letter.lower(), letter.upper()]) for letter in cls.ask())
        return aNSwEr



@somsiad.client.command(aliases=['8ball', '8-ball', '8'])
@discord.ext.commands.cooldown(
    1, somsiad.conf['command_cooldown_per_user_in_seconds'], discord.ext.commands.BucketType.user
)
@discord.ext.commands.guild_only()
async def eightball(ctx, *args):
    """Returns an 8-Ball answer."""
    question = ' '.join(args)
    question = question.strip('`~!@#$%^&*()-_=+[{]}\\|;:\'",<.>/?')
    if question != '':
        if 'fccchk' in question.lower():
            await ctx.send(f'{ctx.author.mention}\n:japanese_goblin: {Ball.AsK()}')
        else:
            await ctx.send(f'{ctx.author.mention}\n:8ball: {Ball.ask()}')
    else:
        await ctx.send(
            f'{ctx.author.mention}\nMagiczna kula potrafi odpowiadać tylko na pytania! '
            'Aby zadać pytanie musisz użyć *słów*.'
        )

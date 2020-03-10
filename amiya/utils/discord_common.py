import asyncio
import functools
import logging
from datetime import datetime
from pytz import timezone

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

_INFO_WHITE = 0xF0F0F0
_ERROR_RED = 0xFF0000


def embed_info(desc):
    return discord.Embed(description=str(desc), color=_INFO_WHITE)


def embed_error(desc="An unexpected error has occurred"):
    return discord.Embed(description=str(desc), color=_ERROR_RED)


def attach_image(embed, img_file):
    embed.set_image(url=f"attachment://{img_file.filename}")


def set_author_footer(embed, user):
    embed.set_footer(text=f"Requested by {user}", icon_url=user.avatar_url)


def send_error_if(*error_cls):
    """Decorator for `cog_command_error` methods. Decorated methods send the error in an alert embed
    when the error is an instance of one of the specified errors, otherwise the wrapped function is
    invoked.
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(cog, ctx, error):
            if isinstance(error, error_cls):
                await ctx.send(embed=embed_error(error))
                error.handled = True
            else:
                await func(cog, ctx, error)

        return wrapper

    return decorator


async def bot_error_handler(ctx, exception):
    if getattr(exception, "handled", False):
        # Errors already handled in cogs should have .handled = True
        return

    elif isinstance(exception, commands.NoPrivateMessage):
        await ctx.send(embed=embed_error("Commands are disabled in private channels"))
    elif isinstance(exception, commands.DisabledCommand):
        await ctx.send(embed=embed_error("Sorry, this command is temporarily disabled"))
    else:
        exc_info = type(exception), exception, exception.__traceback__
        logger.exception(
            "Ignoring exception in command {}:".format(
                ctx.command), exc_info=exc_info)


async def presence(bot):
    """ Discord presence """
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening, name="your commands"
        )
    )
    await asyncio.sleep(30)

    while True:
        # Get current time in PST format
        current_time = datetime.now(tz=timezone('US/Pacific'))
        await bot.change_presence(
            activity=discord.Game(
                name=f'{current_time.strftime("%I:%M %p PST")}'
            )
        )
        await asyncio.sleep(60 - current_time.second)

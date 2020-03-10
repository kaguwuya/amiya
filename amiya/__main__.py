import asyncio
import logging
import os
from pathlib import Path

from discord.ext import commands
from dotenv import load_dotenv

from amiya.utils import constants, discord_common

load_dotenv()


def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logging.error("Discord Token required")
        return

    # Config logging
    logging.basicConfig(
        format="[{asctime}][{levelname}][{name}] {message}",
        style="{",
        datefmt="%d-%m-%Y %H:%M:%S",
        level=logging.INFO,
    )

    # Auto shard
    bot = commands.AutoShardedBot(
        command_prefix=commands.when_mentioned_or(os.getenv("PREFIX"))
    )

    cogs = [file.stem for file in Path("amiya", "cogs").glob("*.py")]
    # Load extensions
    for extension in cogs:
        bot.load_extension(f"amiya.cogs.{extension}")
    logging.info(f'Cogs loaded: {", ".join(bot.cogs)}')

    # Load constants
    constants.setup()
    logging.info(f'Constants loaded: {", ".join(filter(lambda x: x.isupper(), dir(constants)))}')

    def no_dm_check(ctx):
        """ Check for DMs """
        if ctx.guild is None:
            raise commands.NoPrivateMessage("Private messages not permitted.")
        return True

    # Restrict bot usage to inside guild channels only.
    bot.add_check(no_dm_check)

    @bot.event
    async def on_ready():
        asyncio.create_task(discord_common.presence(bot))
        logging.info("Successfully logged in and booted...!")

    bot.run(token)


if __name__ == "__main__":
    main()

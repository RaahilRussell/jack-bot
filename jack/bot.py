"""One bot, one HTTP session, and extensions loaded once per startup."""

import argparse
import asyncio
import logging

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

from .api import API
from .config import Settings
from .storage import Store

EXTENSIONS = ("errors", "community", "fun", "moderation", "hypixel", "leaderboards")


class EmbedHelp(commands.MinimalHelpCommand):
    async def send_pages(self):
        for page in self.paginator.pages:
            await self.get_destination().send(embed=discord.Embed(description=page))


class JackBot(commands.Bot):
    session: aiohttp.ClientSession
    api: API

    def __init__(self, settings: Settings, *, offline: bool = False):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(
            command_prefix=settings.prefix,
            intents=intents,
            help_command=EmbedHelp(),
            case_insensitive=True,
            activity=discord.Game(name="Mango... | " + settings.prefix + "help"),
            allowed_mentions=discord.AllowedMentions.none(),
        )
        self.settings = settings
        self.offline = offline
        self.store = Store(settings.data_dir / "jack.sqlite3")

    async def setup_hook(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20))
        self.api = API(self.session, self.settings.hypixel_key)
        for name in EXTENSIONS:
            await self.load_extension(f"jack.cogs.{name}")

    async def close(self):
        for extension in list(self.extensions):
            await self.unload_extension(extension)
        if hasattr(self, "session"):
            await self.session.close()
        await super().close()

    async def on_ready(self):
        logging.getLogger(__name__).info(
            "Jack is connected; %d command groups loaded.", len(self.cogs)
        )


async def check_startup(settings: Settings) -> int:
    async with JackBot(settings, offline=True) as bot:
        await bot.setup_hook()
        count = len(list(bot.walk_commands()))
        print(
            f"Startup check passed: {len(bot.cogs)} command groups, {count} commands. No login or external requests."
        )
        return count


def main():
    parser = argparse.ArgumentParser(description="Jack Discord bot")
    parser.add_argument(
        "--check", action="store_true", help="Load every command without connecting to Discord"
    )
    args = parser.parse_args()
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        settings = Settings.from_env()
    except ValueError as error:
        parser.error(str(error))
    if args.check:
        asyncio.run(check_startup(settings))
    elif not settings.token:
        parser.error("Set DISCORD_TOKEN in .env before running Jack (or use --check).")
    else:
        try:
            JackBot(settings).run(settings.token, log_handler=None)
        except discord.LoginFailure:
            parser.error("Discord rejected DISCORD_TOKEN. Check your bot token.")


if __name__ == "__main__":
    main()

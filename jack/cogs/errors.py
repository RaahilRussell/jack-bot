import logging

import discord
from discord.ext import commands

from jack.api import ServiceError

log = logging.getLogger(__name__)


class Errors(commands.Cog):
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        error = getattr(error, "original", error)
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.CommandOnCooldown):
            message = f"Try again in {error.retry_after:.1f} seconds."
        elif isinstance(error, commands.BotMissingPermissions):
            message = "Jack needs these permissions: " + ", ".join(error.missing_permissions)
        elif isinstance(error, commands.NoPrivateMessage):
            message = "Use this command in a server."
        elif isinstance(error, commands.MissingPermissions):
            message = "You need these permissions: " + ", ".join(error.missing_permissions)
        elif isinstance(error, commands.UserInputError):
            message = f"{error}\nSee `{ctx.clean_prefix}help {ctx.command}` for usage."
        elif isinstance(error, (commands.CheckFailure, ServiceError)):
            message = str(error)
        elif isinstance(error, discord.Forbidden):
            message = "Discord denied that action. Check Jack's permissions and role position."
        elif isinstance(error, discord.HTTPException):
            message = "Discord could not complete that action. Please try again."
        else:
            message = "Something went wrong while running that command."
            # Log the failure type without dumping message content or credentials.
            log.error("Command %s failed (%s)", ctx.command, type(error).__name__)
        await ctx.send(
            embed=discord.Embed(
                title="Oops!", description=message[:3900], colour=discord.Colour.red()
            )
        )


async def setup(bot):
    await bot.add_cog(Errors())

"""Shared permission and display helpers."""

import discord
from discord.ext import commands


def staff_only():
    async def predicate(ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        if ctx.author.guild_permissions.manage_guild or any(
            role.name == ctx.bot.settings.staff_role for role in ctx.author.roles
        ):
            return True
        raise commands.CheckFailure(
            "This command requires the configured staff role or Manage Server."
        )

    return commands.check(predicate)


def require_role(guild, name: str, *, editable: bool = True):
    role = discord.utils.get(guild.roles, name=name)
    if role is None:
        raise commands.BadArgument(f"Create the {name!r} role or update the bot configuration.")
    if role.is_default() or (editable and (role.managed or role >= guild.me.top_role)):
        raise commands.BadArgument(f"The {name!r} role must be editable and below Jack's role.")
    return role


def require_channel(guild, name: str):
    channel = discord.utils.get(guild.text_channels, name=name)
    if channel is None:
        raise commands.BadArgument(f"Create #{name} or update the bot configuration.")
    return channel


async def send_lines(ctx, title: str, lines: list[str]):
    # Leave space below Discord's embed description limit, including markdown.
    page = ""
    for line in lines or ["No entries yet."]:
        if len(page) + len(line) + 1 > 3900:
            await ctx.send(embed=discord.Embed(title=title, description=page))
            page = ""
        page += line + "\n"
    if page:
        await ctx.send(embed=discord.Embed(title=title, description=page))

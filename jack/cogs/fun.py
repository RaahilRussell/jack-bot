import discord
from discord.ext import commands

from jack.api import ServiceError


class Fun(commands.Cog):
    """Small animal breaks and the original silly command."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="cat", aliases=["rpanda", "panda", "bird", "koala", "duck", "penguin"])
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def animal(self, ctx):
        """Show a random animal: cat, rpanda, panda, bird, koala, duck, penguin."""
        animal = (ctx.invoked_with or "cat").lower()
        if animal == "duck":
            data = await self.bot.api.json("https://random-d.uk/api/random")
            url = data.get("url")
        elif animal == "penguin":
            # Retain the original external image without old Discord attachment IDs.
            url = "https://images.unsplash.com/photo-1602587365437-5d02d274b3cc?w=1000&q=80"
        else:
            animal = {"rpanda": "red_panda", "bird": "bird"}.get(animal, animal)
            data = await self.bot.api.json(f"https://api.some-random-api.com/animal/{animal}")
            url = data.get("image")
        if not isinstance(url, str) or not url.startswith("https://"):
            raise ServiceError("The image service did not return a usable image.")
        embed = discord.Embed(
            title=f"{animal.replace('_', ' ').title()}!", colour=discord.Colour.purple()
        )
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    @commands.command()
    async def fart(self, ctx):
        """A very sophisticated sound effect."""
        await ctx.send(
            embed=discord.Embed(
                title="ewww", description=f"Ewwww {ctx.author.display_name} farted!"
            )
        )


async def setup(bot):
    await bot.add_cog(Fun(bot))

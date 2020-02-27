import logging
import re

from discord import Embed
from discord.ext import commands

from amiya.utils import arknights, discord_common

occurence = {
    "ALWAYS": "Fixed",
    "OFTEN": "Rare",
    "SOMETIMES": "Uncommon",
    "USUAL": "Chance Drop",
}

drop_type = {
    1: ["First Clear"],
    2: ["Fixed", "Rare"],
    3: ["Uncommon"],
    4: ["Chance Drop"],
    8: ["First Clear"],
}


class GeneralCogError(commands.CommandError):
    pass


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief="Shows infos of a stage", usage="[stage] [+cm]")
    async def stage(self, ctx, *stage: str):
        """
        Detailed information of a stage (add +cm to get challenge mode)

        E.g: ;stage 4-7 +cm
        """
        if stage is None:
            raise GeneralCogError("You need to provide a stage name or id!")
        info = arknights.get_stage(stage)
        title = f'[{info["code"]}] {info["name"]} {"(Challenge Mode)" if "+cm" in stage else ""}'
        if info["bossMark"] is True:
            title += " (Boss Stage)"
        if "+cm" in stage:
            title += " (Challenge Mode)"
        pattern = re.compile(r"<@.+?>(<?[^>]*>?)</>", re.DOTALL)
        description = pattern.sub(r"**\1**", info["description"])
        embed = Embed(
            title=title,
            description=f'Recommend Operator Lv. **[{info["dangerLevel"]}]**\n{description}',
        )
        # details = f'• **Sanity Cost** : {info["apCost"]} (**Retreat refund** : {info["apFailReturn"]})\n• **Practice Ticket Cost** : {info["practiceTicketCost"]}\n• **EXP Gain** : {info["expGain"]}\n• **LMD Gain** : {info["goldGain"]}\n• **Favor Gain** : {info["completeFavor"]} (**2 stars** : {info["passFavor"]})'
        details = f'• Sanity Cost : {info["apCost"]} (Retreat refund : {info["apFailReturn"]})\n• Practice Ticket Cost : {max(0, info["practiceTicketCost"])}\n• EXP Gain : {info["expGain"]}\n• LMD Gain : {info["goldGain"]}\n• Favor Gain : {info["completeFavor"]} (2 stars : {info["passFavor"]})'
        if info["slProgress"] > 0:
            details += f'\n• Storyline progress : {info["slProgress"]}%'
        embed.add_field(name="Details", value=details, inline=False)
        first = [
            f'• {x["name"]} (`{x["itemId"]}`)'
            for x in [
                arknights.get_item(y["id"])
                for y in info["stageDropInfo"]["displayRewards"]
                if y["dropType"] == 8
            ]
        ]
        first.extend(
            [
                f'• {x["name"]} (`{x["itemId"]}`)'
                for x in [
                    arknights.get_item(y["id"])
                    for y in info["stageDropInfo"]["displayRewards"]
                    if y["dropType"] == 1
                    and y["type"] != "TKT_RECRUIT"
                    and y["type"] != "FURN"
                ]
            ]
        )
        first.extend(
            [
                f'• {x["name"]}'
                for x in [
                    arknights.get_operator_info(y["id"])
                    for y in info["stageDropInfo"]["displayRewards"]
                    if y["dropType"] == 1 and y["type"] == "TKT_RECRUIT"
                ]
            ]
        )
        first.extend(
            [
                f'• {x["name"]}'
                for x in [
                    arknights.get_furniture(y["id"])
                    for y in info["stageDropInfo"]["displayRewards"]
                    if y["dropType"] == 1 and y["type"] == "FURN"
                ]
            ]
        )
        if len(first) > 0:
            embed.add_field(name="First Clear", value="\n".join(first), inline=False)
        regular = [
            f'• {x["name"]} (`{x["itemId"]}`)'
            for x in [
                arknights.get_item(y["id"])
                for y in info["stageDropInfo"]["displayRewards"]
                if y["dropType"] == 2
            ]
        ]
        if len(regular) > 0:
            embed.add_field(
                name="Regular Drops", value="\n".join(regular), inline=False
            )
        special = [
            f'• {x["name"]} (`{x["itemId"]}`)'
            for x in [
                arknights.get_item(y["id"])
                for y in info["stageDropInfo"]["displayRewards"]
                if y["dropType"] == 3
            ]
        ]
        if len(special) > 0:
            embed.add_field(
                name="Special Drops", value="\n".join(special), inline=False
            )
        extra = [
            f'• {x["name"]} (`{x["itemId"]}`)'
            for x in [
                arknights.get_item(y["id"])
                for y in info["stageDropInfo"]["displayDetailRewards"]
                if y["dropType"] == 4
            ]
        ]
        if len(extra) > 0:
            embed.add_field(
                name="Extra Drops (Small Chance)", value="\n".join(extra), inline=False
            )
        await ctx.send(embed=embed)

    @commands.command(brief="Shows infos of an item", usage="[item]")
    async def item(self, ctx, *, item=None):
        """
        Detailed information of an item

        E.g: ;info Originite Prime
        """
        if item is None:
            raise GeneralCogError("You need to provide an item name!")
        info = arknights.get_item(item)
        embed = Embed(
            title=f'{info["name"]} (`{info["itemId"]}`)',
            description=f'{info["usage"]}\n_{info["description"]}_\n**Rarity** : {"☆" * (info["rarity"] + 1)}\n**How to obtain** : {info["obtainApproach"] or ""}',
        )
        """
        stages = [
            f'• **[{x["code"]}]** {x["name"]}{" (Challenge Mode)" if x["difficulty"] == "FOUR_STAR" else ""} [{occurence[y["occPer"]]}]'
            for x, y in [
                (arknights.get_stage(y["stageId"]), y) for y in info["stageDropList"]
            ]
        ]
        """
        stages = [
            f'• **[{x["code"]}]** {x["name"]}{" (Challenge Mode)" if x["difficulty"] == "FOUR_STAR" else ""} [{drop_type[y][1 if info["rarity"] > 1 and y == 2 else 0]}]'
            for x, y in arknights.get_stage_with_item(info["itemId"])
            if y != 4
        ]
        if len(stages) > 0 and info["itemId"] != "4002":
            embed.add_field(name="Stages", value="\n".join(stages))
        base = [f'• {x["roomType"].title()}' for x in info["buildingProductList"]]
        if len(base) > 0:
            embed.add_field(name="Base production", value="\n".join(base))
        embed.set_thumbnail(
            url=f'https://raw.githubusercontent.com/Aceship/AN-EN-Tags/master/img/items/{info["iconId"]}.png'
        )
        await ctx.send(embed=embed)

    @commands.command(brief="Shows infos of a furniture", usage="[furniture]")
    async def furniture(self, ctx, *, furniture=None):
        """
        Detailed infos of a furniture
        """
        if furniture is None:
            raise GeneralCogError("You need to provide a furniture name!")
        info = arknights.get_furniture(furniture)
        embed = Embed(
            title=info["name"],
            description=f'{info["usage"]}\n_{info["description"]}_\n**Rarity** : {"☆" * (info["rarity"] + 1)}\n**How to obtain** : {info["obtainApproach"] or ""}',
        )
        details = f'• Type : {info["type"].title()}\n• Location : {info["location"].title()}\n• Category : {info["category"].title()}'
        embed.add_field(name="Details", value=details, inline=False)
        measurements = f'• Width : {info["width"]}\n• Depth : {info["depth"]}\n• Height : {info["height"]}\n• Ambience : {info["comfort"]}'
        embed.add_field(name="Measurements", value=measurements, inline=False)
        embed.set_thumbnail(url=f'https://raw.githubusercontent.com/Aceship/AN-EN-Tags/master/img/furniture/{info["id"]}.png')
        await ctx.send(embed=embed)

    @commands.command(brief="Shows some tips", usage="[category]")
    async def tip(self, ctx, *, category=None):
        """
        Useful tips
        """
        categories = ["BATTLE", "BUILDING", "GACHA", "MISC"]
        if category is not None and category.upper() not in categories:
            raise GeneralCogError(f'Category must be one of {", ".join([x.lower() for x in categories])}')
        else:
            info = arknights.get_tips(category)
            embed = Embed(description=f'**[{info["category"]}]** {info["tip"]}.')
            await ctx.send(embed=embed)

    @discord_common.send_error_if(GeneralCogError)
    async def cog_command_error(self, ctx, error):
        logging.exception(error)
        pass


def setup(bot):
    bot.add_cog(General(bot))

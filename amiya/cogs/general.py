import logging
import re
from itertools import combinations

from discord import Embed
from discord.ext import commands

from amiya.utils import arknights, discord_common

# Item occurrence
occurrence = {
    "ALWAYS": "Fixed",
    "OFTEN": "Rare",
    "SOMETIMES": "Uncommon",
    "USUAL": "Chance Drop",
}

# Item drop probability
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
        # Get stage info
        info = arknights.get_stage(stage)
        title = f'[{info["code"]}] {info["name"]} {"(Challenge Mode)" if "+cm" in stage else ""}'
        # Check if stage is boss stage
        if info["bossMark"] is True:
            title += " (Boss Stage)"
        if "+cm" in stage:
            title += " (Challenge Mode)"
        # Regex for stuffs like <@lv.item><Fixed Squad></>
        pattern = re.compile(r"<@.+?>(<?[^>]*>?)</>", re.DOTALL)
        description = pattern.sub(r"**\1**", info["description"])
        embed = Embed(
            title=title,
            description=f'Recommend Operator Lv. **[{info["dangerLevel"]}]**\n{description}',
        )
        details = f'• Sanity Cost : {info["apCost"]} (Retreat refund : {info["apFailReturn"]})\n• Practice Ticket Cost : {max(0, info["practiceTicketCost"])}\n• EXP Gain : {info["expGain"]}\n• LMD Gain : {info["goldGain"]}\n• Favor Gain : {info["completeFavor"]} (2 stars : {info["passFavor"]})'
        if info["slProgress"] > 0:
            details += f'\n• Storyline progress : {info["slProgress"]}%'
        embed.add_field(name="Details", value=details, inline=False)
        first = [
            f'• {x["name"]} (`{x["itemId"]}`)'
            for x in [
                arknights.get_item(y["id"])
                for y in info["stageDropInfo"]["displayRewards"]
                if y["dropType"] == 8  # First clear item (Originite Prime)
            ]
        ]
        first.extend(
            [
                f'• {x["name"]} (`{x["itemId"]}`)'
                for x in [
                    arknights.get_item(y["id"])
                    for y in info["stageDropInfo"]["displayRewards"]
                    if y["dropType"] == 1  # First clear (others)
                    and y["type"] != "TKT_RECRUIT"  # Operator
                    and y["type"] != "FURN"  # Furniture
                ]
            ]
        )
        first.extend(
            [
                f'• {x["name"]}'
                for x in [
                    arknights.get_operator_info(y["id"])
                    for y in info["stageDropInfo"]["displayRewards"]
                    if y["dropType"] == 1 and y["type"] == "TKT_RECRUIT"  # Operator
                ]
            ]
        )
        first.extend(
            [
                f'• {x["name"]}'
                for x in [
                    arknights.get_furniture(y["id"])
                    for y in info["stageDropInfo"]["displayRewards"]
                    if y["dropType"] == 1 and y["type"] == "FURN"  # Furniture
                ]
            ]
        )
        # Always check for length
        if len(first) > 0:
            embed.add_field(name="First Clear", value="\n".join(first), inline=False)
        regular = [
            f'• {x["name"]} (`{x["itemId"]}`)'
            for x in [
                arknights.get_item(y["id"])
                for y in info["stageDropInfo"]["displayRewards"]
                if y["dropType"] == 2  # Fixed
            ]
        ]
        # Always check for length
        if len(regular) > 0:
            embed.add_field(
                name="Regular Drops", value="\n".join(regular), inline=False
            )
        special = [
            f'• {x["name"]} (`{x["itemId"]}`)'
            for x in [
                arknights.get_item(y["id"])
                for y in info["stageDropInfo"]["displayRewards"]
                if y["dropType"] == 3  # Special Drops
            ]
        ]
        # Always check for length
        if len(special) > 0:
            embed.add_field(
                name="Special Drops", value="\n".join(special), inline=False
            )
        extra = [
            f'• {x["name"]} (`{x["itemId"]}`)'
            for x in [
                arknights.get_item(y["id"])
                for y in info["stageDropInfo"]["displayDetailRewards"]
                if y["dropType"] == 4  # Extra Drops
            ]
        ]
        # Always check for length
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
        # Get item info
        info = arknights.get_item(item)
        embed = Embed(
            title=f'{info["name"]} (`{info["itemId"]}`)',
            description=f'{info["usage"]}\n_{info["description"]}_\n**Rarity** : {"☆" * (info["rarity"] + 1)}\n**How to obtain** : {info["obtainApproach"] or ""}',
        )

        # Get stages in stage drop list
        # stages = [
        #    f'• **[{x["code"]}]** {x["name"]}{" (Challenge Mode)" if x["difficulty"] == "FOUR_STAR" else ""} [{occurrence[y["occPer"]]}]'
        #    for x, y in [
        #        (arknights.get_stage(y["stageId"]), y) for y in info["stageDropList"]
        #    ]
        # ]

        # Get stages directly
        stages = [
            f'• **[{x["code"]}]** {x["name"]}{" (Challenge Mode)" if x["difficulty"] == "FOUR_STAR" else ""} [{drop_type[y][1 if info["rarity"] > 1 and y == 2 else 0]}]'
            for x, y in arknights.get_stage_with_item(
                info["itemId"]
            )  # Get stage list with item
            if y != 4  # Don't get stage where item is extra drop
        ]
        if len(stages) > 0 and info["itemId"] != "4002":
            embed.add_field(name="Stages", value="\n".join(stages))
        # If item can be produced in base
        base = [f'• {x["roomType"].title()}' for x in info["buildingProductList"]]
        # Always check for length
        if len(base) > 0:
            embed.add_field(name="Base production", value="\n".join(base))
        # Get item image from https://github.com/Aceship/AN-EN-Tags/tree/master/img
        embed.set_thumbnail(
            url=f'https://raw.githubusercontent.com/Aceship/AN-EN-Tags/master/img/items/{info["iconId"]}.png'
        )
        await ctx.send(embed=embed)

    @commands.command(brief="Shows infos of a furniture", usage="[furniture]")
    async def furniture(self, ctx, *, furniture=None):
        """
        Detailed infos of a furniture

        E.g: ;furniture Rabbit-like Bean Bag Sofa
        """
        if furniture is None:
            raise GeneralCogError("You need to provide a furniture name!")
        # Get furniture info
        info = arknights.get_furniture(furniture)
        embed = Embed(
            title=info["name"],
            description=f'{info["usage"]}\n_{info["description"]}_\n**Rarity** : {"☆" * (info["rarity"] + 1)}\n**How to obtain** : {info["obtainApproach"] or ""}',
        )
        # Grab details
        details = f'• Type : {info["type"].title()}\n• Location : {info["location"].title()}\n• Category : {info["category"].title()}'
        embed.add_field(name="Details", value=details, inline=False)
        # Add measurements
        measurements = f'• Width : {info["width"]}\n• Depth : {info["depth"]}\n• Height : {info["height"]}\n• Ambience : {info["comfort"]}'
        embed.add_field(name="Measurements", value=measurements, inline=False)
        # Get furniture image from https://github.com/Aceship/AN-EN-Tags/tree/master/img
        embed.set_thumbnail(
            url=f'https://raw.githubusercontent.com/Aceship/AN-EN-Tags/master/img/furniture/{info["id"]}.png'
        )
        await ctx.send(embed=embed)

    @commands.command(brief="Shows infos of an enemy", usage="[enemy]")
    async def enemy(self, ctx, *, enemy=None):
        """
        Detailed infos of an enemy

        E.g: ;enemy FrostNova
        """
        if enemy is None:
            raise GeneralCogError("You need to provide an enemy name!")
        # Get enemy info
        info = arknights.get_enemy(enemy)
        description = ""
        # Enemy races: Infected Creature, Sarkaz, etc
        if info["enemyRace"] is not None:
            description += f'**Race** : {info["enemyRace"] or "???"}\n'
        # Attack types: Melee, Ranged, Ranged Arts, etc
        description += f'**Attack** : {info["attackType"]}\n{info["description"]}'
        embed = Embed(
            title=f'[{info["enemyIndex"]}] {info["name"]}', description=description
        )
        # Stats
        embed.add_field(
            name="Stats",
            value=f'• HP : {info["endure"]}\n• ATK : {info["attack"]}\n• DEF : {info["defence"]}\n• RES : {info["resistance"]}',
            inline=False,
        )
        # Ability: "Upon death, deals large physical damage in an area", etc
        if info["ability"] is not None:
            embed.add_field(name="Ability", value=info["ability"], inline=False)
        # Get enemy image from https://github.com/Aceship/AN-EN-Tags/tree/master/img
        embed.set_thumbnail(
            url=f'https://raw.githubusercontent.com/Aceship/AN-EN-Tags/master/img/enemy/{info["enemyId"]}.png'
        )
        await ctx.send(embed=embed)

    @commands.command(
        brief="Shows which operators you can get with which tags", usage="[tags]"
    )
    async def recruitment(self, ctx, *tags):
        """
        Shows which operators you can get with which recruitment tags
        Multi-word tags have to be quoted

        E.g: ;operator tag Defense Melee "Crowd Control" "Top Operator" "Senior Operator"
        """
        # Tag list to filter invalid tags
        tag_list = [
            "Starter",
            "Senior Operator",
            "Top Operator",
            "Melee",
            "Ranged",
            "Guard",
            "Medic",
            "Vanguard",
            "Caster",
            "Sniper",
            "Defender",
            "Supporter",
            "Specialist",
            "Healing",
            "Support",
            "DPS",
            "AoE",
            "Slow",
            "Survival",
            "Defense",
            "Debuff",
            "Shift",
            "Crowd Control",
            "Nuker",
            "Summon",
            "Fast-Redeploy",
            "DP-Recovery",
            "Robot",
        ]
        tags = list(tags)
        # Check number of tags
        if len(tags) == 0 or len(tags) > 5:
            raise GeneralCogError(
                "You have to provide at least 1 tag and at most 5 tags!"
            )
        # Check for invalid tags
        if set(tag_list).issubset(tags):
            raise GeneralCogError(f'Tag must be one of {", ".join(tag_list)}')
        # Generate tag combinations
        tags_combi = [
            combi
            for combi_list in [
                [list(x) for x in combinations(tags, i)] for i in range(1, 4)
            ]
            for combi in combi_list
        ][::-1]
        # Create a match table
        match_table = [[] for i in range(len(tags_combi))]
        embed = Embed()
        # Get operator list
        operator_list = arknights.get_operator_by_tags([x.lower() for x in tags])
        for (tag_combi, match_list) in zip(tags_combi, match_table):
            # Adding operators
            match_list.extend(
                [
                    (operator["name"], operator["rarity"] + 1)
                    for operator in operator_list
                    # Check if operator tag list has tag combinations
                    if (set(tag_combi).issubset(set(operator["tagList"])))
                    # Only show 6* if "Top Operator" is in query
                    and not (
                        "Top Operator" not in tags
                        and "Top Operator" in operator["tagList"]
                    )
                ][::-1]
            )
            # If match found
            if len(match_list) > 0:
                embed.add_field(
                    name=" ".join(tag_combi),
                    value=f'{" ".join([f"`[{op[1]}☆] {op[0]}`" for op in match_list])}',
                    inline=False,
                )
        await ctx.send(embed=embed)

    @commands.command(brief="Shows some tips", usage="[category]")
    async def tip(self, ctx, *, category=None):
        """
        Display a random (useful) tips
        """
        # Category list to filter
        categories = ["BATTLE", "BUILDING", "GACHA", "MISC"]
        # Filter invalid category
        if category.upper() not in categories if category is not None else True:
            raise GeneralCogError(
                f'Category must be one of {", ".join([x.title() for x in categories])}'
            )
        # Get random tip
        info = arknights.get_tips(category)
        embed = Embed(description=f'**[{info["category"]}]** {info["tip"]}.')
        await ctx.send(embed=embed)

    @discord_common.send_error_if(GeneralCogError)
    async def cog_command_error(self, ctx, error):
        logging.exception(error)
        pass


def setup(bot):
    bot.add_cog(General(bot))

import logging
import re
from itertools import combinations

from discord import Embed
from discord.ext import commands

from amiya.utils import arknights, constants, discord_common


class GeneralCogError(commands.CommandError):
    pass


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief="Shows infos of a stage", usage="[stage]")
    async def stage(self, ctx, *stage: str):
        """
        Detailed information of a stage

        E.g: ;stage 4-7
        """

        if stage is None:
            raise GeneralCogError("You need to provide a stage name or id!")

        # Get stage info
        info, extra_info, anni_info = arknights.get_stage(stage)

        title = f'[{info["code"]}] {info["name"]} {"(Challenge Mode)" if "+cm" in stage else ""}'

        # Check if stage is boss stage
        if info["bossMark"] is True:
            title += " (Boss Stage)"

        # Regex for stuffs like <@lv.item><Fixed Squad></>
        pattern = re.compile(r"<@.+?>(<?[^>]*>?)</>", re.DOTALL)
        description = pattern.sub(r"**\1**", info["description"])

        embed = Embed(
            title=title,
            description=f'Recommend Operator Lv. **[{info["dangerLevel"]}]**\n{description}',
        )

        # General info
        general = ""
        if anni_info is None:
            general += f'• Sanity Cost : {info["apCost"]}\n• Practice Ticket Cost : {max(0, info["practiceTicketCost"])}\n• EXP Gain : {info["expGain"]}\n• LMD Gain : {info["goldGain"]}\n• Favor Gain : {info["completeFavor"]}'
        if len(info["unlockCondition"]) > 0:
            unlock_condition = [
                f'{"Clear" if st["completeState"] == 2 else "Perfect"} **{arknights.get_stage(st["stageId"])[0]["code"]}**' for st in info["unlockCondition"]]
            general += f'\n• Unlock Conditions : {", ".join(unlock_condition)}'
        if info["slProgress"] > 0:
            general += f'\n• Storyline Progress : {info["slProgress"]}%'
        embed.add_field(name="General Information",
                        value=general, inline=False)

        # Challenge Mode info
        if info["hardStagedId"] is not None:
            challenge_mode = arknights.get_stage(info["hardStagedId"])[0]
            challenge_general = ""
            if len(challenge_mode["unlockCondition"]) > 0:
                unlock_condition = [
                    f'{"Clear" if st["completeState"] == 2 else "Perfect"} **{arknights.get_stage(st["stageId"])[0]["code"]}**' for st in challenge_mode["unlockCondition"]]
                challenge_general += f'• Unlock Conditions : {", ".join(unlock_condition)}'
            challenge_description = pattern.sub(
                r"**\1**", challenge_mode["description"])
            embed.add_field(name="Challenge Mode Information",
                            value=f'{challenge_description}\n{challenge_general}', inline=False)

        # Map info
        extra_options = extra_info["options"]
        stage_info = f'• Deployment Limit : {extra_options["characterLimit"]}\n• Life Points : {extra_options["maxLifePoint"]}\n• Initial DP : {extra_options["initialCost"]}'
        embed.add_field(name="Map Information", value=stage_info, inline=False)

        # Enemies info
        # Count enemies by extracting waves
        # I can't really find a better way to do this, maybe the database is missing some parts ?
        enemies_waves = extra_info["waves"]
        enemies_count = {}
        for wave in enemies_waves:
            for fragment in wave["fragments"]:
                for action in fragment["actions"]:
                    if action["actionType"] == 0:
                        enemy = arknights.get_enemy(action["key"])
                        if enemy["name"] not in enemies_count:
                            enemies_count[enemy["name"]] = {
                                "sort": enemy["sortId"],
                                "count": 0
                            }
                        enemies_count[enemy["name"]
                                      ]["count"] += action["count"]
        enemies_count = {k: v for k, v in sorted(
            enemies_count.items(), key=lambda item: item[1]["sort"])}
        embed.add_field(name="Enemies", value="\n".join(
            [f'• {enemy[1]["count"]}x {enemy[0]}' for enemy in enemies_count.items()]), inline=False)

        # Filter Originite Prime
        first = [
            f'• {x["name"]} (`{x["itemId"]}`)'
            for x in [
                arknights.get_item(y["id"])
                for y in info["stageDropInfo"]["displayRewards"]
                if y["dropType"] == 8  # First clear item (Originite Prime)
            ]
        ]
        # Filter items
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
        # Filter operator
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
        # Filter furniture
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
            embed.add_field(
                name="First Clear",
                value="\n".join(first),
                inline=False)

        # Filter regular drops
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

        # Filter special drops
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

        # Filter extra drops
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
                name="Extra Drops (Small Chance)",
                value="\n".join(extra),
                inline=False)

        # Annihilatio
        if anni_info is not None:
            # First clear rewards
            first_clear = anni_info["breakLadders"]
            endl = "\n"  # Backslashes may not appear inside the expression portions of f-strings
            embed.add_field(name="First Clear", value=endl.join(
                [f'''**{ladder["killCnt"]}** kills\n{endl.join([f"• {reward['count']} {arknights.get_item(reward['id'])['name']} (`{reward['id']}`)" for reward in ladder["rewards"]])}{f"{endl}• Weekly Orundum Reward Limit : +{ladder['breakFeeAdd']}" if ladder["breakFeeAdd"] > 0 else ""}''' for ladder in first_clear]), inline=False)
            # Sanity Return Rule
            gain_ladder = anni_info["gainLadders"]
            embed.add_field(name="Sanity Return Rule", value="\n".join(
                [f'**{ladder["killCnt"]}** kills\n• Sanity Refund : {ladder["apFailReturn"]}\n• EXP Gain : {ladder["expGain"]}\n• LMD Gain : {ladder["goldGain"]}\n• Favor Gain : {ladder["favor"]}' for ladder in gain_ladder]), inline=False)

        # Unreliable image source
        embed.set_image(
            url=f'https://gamepress.gg/arknights/sites/arknights/files/game-images/mission_maps/{info["stageId"]}.png')

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
        #    f'• **[{x["code"]}]** {x["name"]}{" (Challenge Mode)" if x["difficulty"] == "FOUR_STAR" else ""} [{constants.OCCURRENCE[y["occPer"]]}]'
        #    for x, y in [
        #        (arknights.get_stage(y["stageId"])[0], y) for y in info["stageDropList"]
        #    ]
        # ]

        # Get stages directly
        stages = [
            f'• **[{x["code"]}]** {x["name"]}{" (Challenge Mode)" if x["difficulty"] == "FOUR_STAR" else ""} [{constants.DROP_TYPE[y][1 if info["rarity"] > 1 and y == 2 else 0]}]'
            for x, y in arknights.get_stage_with_item(
                info["itemId"]
            )  # Get stage list with item
            if y != 4  # Don't get stage where item is extra drop
        ]
        if len(
                stages) > 0 and info["itemId"] != "4002":  # Filter Originite Prime
            embed.add_field(name="Stages", value="\n".join(stages))

        # If item can be produced in base
        base = [
            f'• {x["roomType"].title()}' for x in info["buildingProductList"]]
        # Always check for length
        if len(base) > 0:
            embed.add_field(name="Base production", value="\n".join(base))

        # Get item image from
        # https://github.com/Aceship/AN-EN-Tags/tree/master/img
        embed.set_thumbnail(
            url=f'https://raw.githubusercontent.com/Aceship/AN-EN-Tags/master/img/items/{info["iconId"]}.png')

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

        # Grab general
        general = f'• Type : {info["type"].title()}\n• Location : {info["location"].title()}\n• Category : {info["category"].title()}'
        embed.add_field(name="Details", value=general, inline=False)

        # Add measurements
        measurements = f'• Width : {info["width"]}\n• Depth : {info["depth"]}\n• Height : {info["height"]}\n• Ambience : {info["comfort"]}'
        embed.add_field(name="Measurements", value=measurements, inline=False)

        # Get furniture image from
        # https://github.com/Aceship/AN-EN-Tags/tree/master/img
        embed.set_thumbnail(
            url=f'https://raw.githubusercontent.com/Aceship/AN-EN-Tags/master/img/furniture/{info["id"]}.png')

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
        description += f'''**Attack** : {info["attackType"] or "Doesn't Attack"}\n{info["description"]}'''
        embed = Embed(
            title=f'[{info["enemyIndex"]}] {info["name"]}',
            description=description)

        # Stats
        embed.add_field(
            name="Stats",
            value=f'• HP : {info["endure"]}\n• ATK : {info["attack"]}\n• DEF : {info["defence"]}\n• RES : {info["resistance"]}',
            inline=False,
        )

        # Ability: "Upon death, deals large physical damage in an area", etc
        if info["ability"] is not None:
            embed.add_field(
                name="Ability",
                value=info["ability"],
                inline=False)

        # Get enemy image from
        # https://github.com/Aceship/AN-EN-Tags/tree/master/img
        embed.set_thumbnail(
            url=f'https://raw.githubusercontent.com/Aceship/AN-EN-Tags/master/img/enemy/{info["enemyId"]}.png')

        await ctx.send(embed=embed)

    @commands.command(
        brief="Shows which operators you can get with which tags",
        usage="[tags]")
    async def recruit(self, ctx, *tags):
        """
        Shows which operators you can get with which recruitment tags
        Multi-word tags have to be quoted

        E.g: ;operator tag Defense Melee "Crowd Control" "Top Operator" "Senior Operator"
        """

        tags = list(tags)
        # Check number of tags
        if len(tags) == 0 or len(tags) > 5:
            raise GeneralCogError(
                "You have to provide at least 1 tag and at most 5 tags!"
            )
        # Check for invalid tags
        if set(constants.TAG_LIST).issubset(tags):
            raise GeneralCogError(
                f'Tag must be one of {", ".join(constants.TAG_LIST)}')

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
        operator_list = arknights.get_operator_by_tags(
            [x.lower() for x in tags])

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

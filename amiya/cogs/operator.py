import logging
import re
import xml.etree.ElementTree as ET
from itertools import combinations
from urllib.request import pathname2url

from discord import Embed
from discord.ext import commands

from amiya.utils import arknights, discord_common, paginator


class OperatorCogError(commands.CommandError):
    pass


class Operator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def operator(self, ctx):
        """
        Operator commands
        """
        await ctx.send_help(ctx.command)

    @operator.command(brief="Shows info of an operator", usage="[operator]")
    async def info(self, ctx, *, operator=None):
        """
        Detailed informations of an operator
        """
        if operator is None:
            raise OperatorCogError("You need to provide an operator name!")
        info = arknights.get_operator_info(operator)
        print(info)
        await ctx.send(embed=discord_common.embed_info("Command under construction"))

    @operator.command(
        brief="Shows which operators you can get with which tags", usage="[tags]"
    )
    async def tags(self, ctx, *tags):
        """
        Shows which operators you can get with which tags
        Multi-word tags have to be quoted

        E.g: ;operator tag Defense Melee "Crowd Control" "Top Operator" "Senior Operator"
        """
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
        if len(tags) == 0 or len(tags) > 5:
            raise OperatorCogError("You have to provide at least 1 tag and at most 5 tags!")
        if set(tag_list).issubset(tags):
            raise OperatorCogError(f'Tag must be one of {", ".join(tag_list)}')
        tags_combi = [
            combi
            for combi_list in [
                [list(x) for x in combinations(tags, i)] for i in range(1, 4)
            ]
            for combi in combi_list
        ][::-1]
        match_table = [[] for i in range(len(tags_combi))]
        embed = Embed()
        operator_list = arknights.get_operator_by_tags([x.lower() for x in tags])
        for (tag_combi, match_list) in zip(tags_combi, match_table):
            match_list.extend(
                [
                    (operator["name"], operator["rarity"] + 1)
                    for operator in operator_list
                    if (set(tag_combi).issubset(set(operator["tagList"])))
                    and not (
                        "Top Operator" not in tags
                        and "Top Operator" in operator["tagList"]
                    )
                ][::-1]
            )
            if len(match_list) > 0:
                embed.add_field(
                    name=" ".join(tag_combi),
                    value=f'{" ".join([f"`[{op[1]}☆] {op[0]}`" for op in match_list])}',
                    inline=False,
                )
        await ctx.send(embed=embed)

    @operator.command(brief="Shows operator's skins info", usage="[operator]")
    async def skins(self, ctx, *, operator=None):
        """
        Detailed informations of specified operator's skins
        """
        if operator is None:
            raise OperatorCogError("You need to provide an operator name!")
        info = arknights.get_operator_skins(operator)
        embeds = []
        for skin in info:
            color = 0x000000
            content = skin["displaySkin"]["content"]
            if content is not None:
                pattern = re.compile(r"<color name=(#[0-9a-f]{6})>(.*)</color>", re.DOTALL)
                m = pattern.match(content)
                if m is not None:
                    color = int(m.group(1).replace("#", "0x"), 16)
                    content = m.group(2)

            embed = Embed(
                title=f'{skin["displaySkin"]["skinName"] or skin["displaySkin"]["modelName"]} ({skin["displaySkin"]["skinGroupName"]})',
                description=(content or "No description available"),
                color=color
            )
            details = f'• Model : {skin["displaySkin"]["modelName"]}\n• Design : {skin["displaySkin"]["drawerName"]}\n'
            if skin["displaySkin"]["dialog"] is not None and skin["displaySkin"]["dialog"] not in content:
                details += f'• Dialog : {skin["displaySkin"]["dialog"]}\n'
            if skin["displaySkin"]["usage"] is not None:
                details += f'• Usage : {skin["displaySkin"]["usage"]}\n'
            if skin["displaySkin"]["description"] is not None:
                details += f'• Description : {skin["displaySkin"]["description"]}\n'
            if skin["displaySkin"]["obtainApproach"] is not None:
                details += f'• How to obtain : {skin["displaySkin"]["obtainApproach"]}\n'
            embed.add_field(name="Details", value=details, inline=False)
            embed.set_image(url=f'https://raw.githubusercontent.com/Aceship/AN-EN-Tags/master/img/characters/{pathname2url(skin["portraitId"])}.png')
            embed.set_thumbnail(url=f'https://raw.githubusercontent.com/Aceship/AN-EN-Tags/master/img/portraits/{pathname2url(skin["portraitId"].replace("+", "a").replace("#", "b" if skin["displaySkin"]["modelName"] == "Amiya" else ""))}.png')
            embeds.append(embed)
        pgnt = paginator.BotEmbedPaginator(ctx, embeds)
        await pgnt.run()

    @operator.command(brief="Shows operator's skills info", usage="[operator]")
    async def skills(self, ctx, *, operator=None):
        """
        Detailed informations of specified operator's skins
        """
        if operator is None:
            raise OperatorCogError("You need to provide an operator name!")
        info = arknights.get_operator_skills(operator)



    @discord_common.send_error_if(OperatorCogError)
    async def cog_command_error(self, ctx, error):
        logging.exception(error)
        pass


def setup(bot):
    bot.add_cog(Operator(bot))

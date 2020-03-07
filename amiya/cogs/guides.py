import logging

from discord import Embed
from discord.ext import commands

from amiya.utils import arknights, discord_common


class GuidesCogError(commands.CommandError):
    pass


class Guides(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief="Material cheatsheet")
    async def material(self, ctx):
        """
        Gives link to material cheatsheet

        All credits goes to Shaw bot in Arknights Official server (Invite link: https://discord.gg/arknights)
        """

        await ctx.send(
            embed=Embed(
                title="**Arknights Farming Guide and Important Drop Rates** (By Fvr_Vain#3466)",
                url="https://docs.google.com/spreadsheets/d/1Fhz24nSxUef3FWplZtwPMRldyrNMc45DOcN0yaSTPaw",
            )
            .set_image(url="https://i.imgur.com/09j7thP.png")
            .set_footer(
                text="All credits goes to Shaw bot in Arknights Official server"
            )
        )

    @commands.command(brief="Banner infos")
    async def banner(self, ctx):
        """
        Gives link to past CN banners

        All credits goes to Shaw bot in Arknights Official server (Invite link: https://discord.gg/arknights)
        """

        await ctx.send(
            embed=Embed(
                title="Past banners in CN Sequence, EN seems not to be following CN's sequence.",
                url="https://i.imgur.com/0sgPqNa.jpg",
            )
            .set_image(url="https://i.imgur.com/0sgPqNa.jpg")
            .set_footer(
                text="All credits goes to Shaw bot in Arknights Official server"
            )
        )

    @commands.command(brief="Team-building guides")
    async def teambuilding(self, ctx):
        """
        Detailed team-building guides

        All credits goes to Shaw bot in Arknights Official server (Invite link: https://discord.gg/arknights)
        """

        await ctx.send(
            embed=Embed(
                title="The Rule of Thumb of Team Building:",
                description="2 <:ClassVanguard:682894479539175425> | 2 <:ClassDefender:682894461256073216> | 2 <:ClassSniper:682894444399165451> | 2 <:ClassMedic:682894424497192973> | 2 <:ClassCaster:682894408819015685> | 2 <:ClassGuard:682894380482166856>\n\nFor <:ClassVanguard:682894479539175425>, either bring both with regen cost on skill prompt or change one of them to regen cost on kill. Bringing one regen cost on kill (Single block <:ClassVanguard:682894479539175425> against light armored enemy such as slimes) in a stages that have lots of them is advised.\nFor <:ClassDefender:682894461256073216>, try to bring 1 with Def up skill and 1 with Heal skill.\nFor <:ClassSniper:682894444399165451>, bring whoever you like, depending on the map, you might need an AoE <:ClassSniper:682894444399165451> to kill enmassed enemy.\nFor <:ClassMedic:682894424497192973>, bring 1 Single Target (ST) unit and 1 Area of Effect (AoE) unit who can heal multiple allies.\nFor <:ClassCaster:682894408819015685>, bring 1 Single Target (ST) unit and 1 Area of Effect (AoE) unit who can damage multiple enemies.\nFor <:ClassGuard:682894380482166856>, bring whoever you like, depending on the map, you might need to bring Duelist 1v1 <:ClassGuard:682894380482166856> such as Melantha to kill enemy Caster as soon as possible.\n\nChange any of the class to <:ClassSpecialist:682894364405792768> or <:ClassSupport:682894349230800959> as you see fit, but the usual option is to substitute 1 <:ClassGuard:682894380482166856> and 1 <:ClassCaster:682894408819015685> to another class depending to the map that you're trying to clear. Sometimes a map will need only Melee units or only Ranged unit such as the CA stages or because of Challenge mode modifier.\nDon't be afraid to try unique combinations such as 4 <:ClassDefender:682894461256073216> or 4 <:ClassSniper:682894444399165451> in 1 team because the only thing stopping you from clearing a stage is your own creativity.",
            ).set_footer(
                text="All credits goes to Shaw bot in Arknights Official server"
            )
        )

    @commands.command(brief="Is it good?")
    async def isitgood(self, ctx):
        """
        Is it good?

        All credits goes to Shaw bot in Arknights Official server (Invite link: https://discord.gg/arknights)
        """
        
        await ctx.send(
            embed=Embed(
                description='_"There are no bad Operators, only bad Doctors."_\n\n[Arknights Operator\'s Category Guide by depe#2300](https://docs.google.com/spreadsheets/d/1_SBmO9HR0IcOIBFkKSJ-8eERblemY2ykLwxGtaTuZdU/)\n\n[Character Cheat Sheet by Botzu ( ˘▽˘) ⅽ[ː̠̈ː̠̈ː̠̈] ͌#7103](https://docs.google.com/spreadsheets/d/1L5smDJR2_4JCLvDJpT2Cz94inl8MFtRXH-xEOyuahIA/)'
            ).set_footer(
                text="All credits goes to Shaw bot in Arknights Official server"
            )
        )

    @discord_common.send_error_if(GuidesCogError)
    async def cog_command_error(self, ctx, error):
        logging.exception(error)
        pass


def setup(bot):
    bot.add_cog(Guides(bot))

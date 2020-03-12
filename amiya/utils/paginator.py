# Credits goes to https://github.com/LiBa001/disputils

import asyncio
from abc import ABC
from copy import deepcopy
from typing import List

import discord
from discord.ext import commands


class Dialog(ABC):
    def __init__(self, *args, **kwargs):
        self._embed: discord.Embed = None
        self.message: discord.Message = None
        self.color: hex = kwargs.get(
            "color") or kwargs.get("colour") or 0x000000

    async def quit(self, text: str = None):
        """
        Quit the dialog.

        Args:
            text (str, optional): Quit text. Defaults to None.
        """

        if text is None:
            await self.message.delete()
        else:
            await self.message.edit(content=text, embed=None)
            await self.message.clear_reactions()

    async def update(self, text: str, color: hex = None, hide_author: bool = False):
        """
        This will update the confirmation embed.

        Args:
            text (str): The new text.
            color (hex, optional): The new embed color.. Defaults to None.
            hide_author (bool, optional): True if you want to hide the embed author. Default's to False.
        """

        if color is None:
            color = self.color

        self._embed.colour = color
        self._embed.title = text

        if hide_author:
            self._embed.set_author(name="")

        await self.display(embed=self._embed)

    async def display(self, text: str = None, embed: discord.Embed = None):
        """
        This will edit the confirmation message.
        
        Args:
            text (str, optional): The new text.. Defaults to None.
            embed (discord.Embed, optional): The new embed.. Defaults to None.
        """

        await self.message.edit(content=text, embed=embed)


class EmbedPaginator(Dialog):
    """ Represents an interactive menu containing multiple embeds. """

    def __init__(
        self,
        client: discord.Client,
        pages: [discord.Embed],
        message: discord.Message = None,
    ):
        """
        Initialize a new EmbedPaginator.
        
        Args:
            client (discord.Client): The :class:`discord.Client` to use.
            pages ([type]):  A list of :class:`discord.Embed` to paginate through.
            message (discord.Message, optional): An optional :class:`discord.Message` to edit. Otherwise a new message will be sent. Defaults to None.
        """
        super().__init__()

        self._client = client
        self.pages = pages
        self.message = message

        self.control_emojis = ("⏮", "◀", "▶", "⏭", "⏹")

    @property
    def formatted_pages(self):
        pages = deepcopy(self.pages)  # copy by value not reference
        for page in pages:
            if page.footer.text == discord.Embed.Empty:
                page.set_footer(text=f"({pages.index(page)+1}/{len(pages)})")
            else:
                if page.footer.icon_url == discord.Embed.Empty:
                    page.set_footer(
                        text=f"{page.footer.text} - ({pages.index(page)+1}/{len(pages)})")
                else:
                    page.set_footer(
                        icon_url=page.footer.icon_url,
                        text=f"{page.footer.text} - ({pages.index(page)+1}/{len(pages)})",
                    )
        return pages

    async def run(self, users: List[discord.User], channel: discord.TextChannel = None):
        """
        Runs the paginator.
        
        Args:
            users (List[discord.User]): A list of :class:`discord.User` that can control the pagination. Passing an empty list will grant access to all users. (Not recommended.)
            channel (discord.TextChannel, optional): The text channel to send the embed to. Must only be specified if `self.message` is `None`. Defaults to None.
        
        Raises:
            TypeError: 
        """

        if channel is None and self.message is not None:
            channel = self.message.channel
        elif channel is None:
            raise TypeError(
                "Missing argument. You need to specify a target channel.")

        self._embed = self.pages[0]

        if len(self.pages) == 1:  # no pagination needed in this case
            self.message = await channel.send(embed=self._embed)
            return

        self.message = await channel.send(embed=self.formatted_pages[0])
        current_page_index = 0

        for emoji in self.control_emojis:
            await self.message.add_reaction(emoji)

        def check(r: discord.Reaction, u: discord.User):
            res = (
                r.message.id == self.message.id) and (
                r.emoji in self.control_emojis)

            if len(users) > 0:
                res = res and u.id in [u1.id for u1 in users]

            return res

        while True:
            try:
                reaction, user = await self._client.wait_for(
                    "reaction_add", check=check, timeout=600
                )
            except asyncio.TimeoutError:
                await self.message.clear_reactions()
                return

            emoji = reaction.emoji
            max_index = len(self.pages) - 1  # index for the last page

            if emoji == self.control_emojis[0]:
                load_page_index = 0

            elif emoji == self.control_emojis[1]:
                load_page_index = (
                    current_page_index - 1
                    if current_page_index > 0
                    else current_page_index
                )

            elif emoji == self.control_emojis[2]:
                load_page_index = (
                    current_page_index + 1
                    if current_page_index < max_index
                    else current_page_index
                )

            elif emoji == self.control_emojis[3]:
                load_page_index = max_index

            else:
                await self.message.delete()
                return

            await self.message.edit(embed=self.formatted_pages[load_page_index])
            await self.message.remove_reaction(reaction, user)

            current_page_index = load_page_index

    @staticmethod
    def generate_sub_lists(l: list) -> [list]:
        if len(l) > 25:
            sub_lists = []

            while len(l) > 20:
                sub_lists.append(l[:20])
                del l[:20]

            sub_lists.append(l)

        else:
            sub_lists = [l]

        return sub_lists


class BotEmbedPaginator(EmbedPaginator):
    def __init__(
        self,
        ctx: commands.Context,
        pages: [discord.Embed],
        message: discord.Message = None,
    ):
        """
        Initialize a new EmbedPaginator.
        
        Args:
            ctx (commands.Context): The :class:`discord.ext.commands.Context` to use.
            pages ([type]): A list of :class:`discord.Embed` to paginate through.
            message (discord.Message, optional): An optional :class:`discord.Message` to edit. Otherwise a new message will be sent. Defaults to None.
        """
        self._ctx = ctx

        super(BotEmbedPaginator, self).__init__(ctx.bot, pages, message)

    async def run(
        self, channel: discord.TextChannel = None, users: List[discord.User] = None
    ):
        """
        Runs the paginator.
        
        Args:
            channel (discord.TextChannel, optional): The text channel to send the embed to. Default is the context channel.
            users (List[discord.User], optional):  A list of :class:`discord.User` that can control the pagination. Default is the context author. Passing an empty list will grant access to all users. (Not recommended)
        """

        if users is None:
            users = [self._ctx.author]

        if self.message is None and channel is None:
            channel = self._ctx.channel

        await super().run(users, channel)

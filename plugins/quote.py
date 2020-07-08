from plugin import Plugin
from typing import Dict
import time
import random
from chat_functions import send_text_to_room

import logging
logger = logging.getLogger(__name__)

plugin = Plugin("quote", "General", "Store (more or less) funny quotes and access them randomly or by search term")


async def quote_command(command):

    quotes: Dict[int, Quote] = plugin.read_data("quotes")
    quote_id, quote = random.random(quotes)
    await send_text_to_room(command.client, command.room.room_id, quote.display_text(), False)


async def quote_add_command(command):
    quotes: Dict[int, Quote] = plugin.read_data("quotes")


async def quote_del_command(command):
    pass


async def quote_edit_command(command):
    pass


async def quote_detail_command(command):
    pass


class Quote:

    def __init__(self, quote_type: str = "local", text: str = "", url: str = "",
                 channel: str = "", mxroom: str = "",
                 user: str = "", mxuser: str = "",
                 date: float = time.time(), rank: int = 0,
                 reactions: Dict[str, int] = {}
                 ):
        """
        A textual quote and all its parameters
        :param quote_type: type of the quote (local or remote)
        :param text: the actual text of the local quote, usually a single line or a conversation in multiple lines
        :param url: an url to a remote quote
        :param channel: (legacy) IRC-channel name, room-Name for Quotes added in matrix
        :param mxroom: matrix room id
        :param user: (legacy) IRC-username of the user who added the quote
        :param mxuser: matrix username of the user who added the quote
        :param rank: rank of the quote, used to be the number of times the quote has been displayed
        :param reactions: Dict of reactions (emoji) and their respective counts a quote has received
        """

        # self.id =
        self.type: str = quote_type
        self.text: str = text
        self.url: str = url
        self.date: float = date
        self.chan: str = channel
        self.mxroom: str = mxroom
        self.user: str = user
        self.mxuser: str = mxuser
        self.rank: int = rank
        self.reactions: Dict[str, int] = reactions

    def display_text(self) -> str:
        """
        Build the default textual representation of a randomly called quote
        :return: the textual representation of the quote
        """

        quote_text: str = self.text.replace("|", "\n")
        reactions_text: str = ""
        for reaction, count in self.reactions:
            reactions_text += f"{reaction} ({count})"

        return f"{quote_text}\n\n{reactions_text}"

    def display_details(self) -> str:
        """
        Build the textual output of a quotes' full details
        :return: the detailed textual representation of the quote
        """

        full_text: str = f"{self.display_text()}\n\n" \
                         f"Date: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.date))}\n" \
                         f"Added by: {self.user} / {self.mxuser}\n" \
                         f"Added on: {self.chan} / {self.mxroom}\n" \
                         f"Rank: {self.rank}\n"
        return full_text


plugin.add_command("quote", quote_command, "Add, delete or post quotes")

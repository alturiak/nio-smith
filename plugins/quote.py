from plugin import Plugin
from typing import Dict, List
import time
import random
from chat_functions import send_text_to_room
from re import match

import logging
logger = logging.getLogger(__name__)

""""""
quote_tags: List[str] = [""]

plugin = Plugin("quote", "General", "Store (more or less) funny quotes and access them randomly or by search term")


def __display_text(self) -> str:
    """
    Build the default textual representation of a randomly called quote
    :return: the textual representation of the quote
    """

    quote_text: str = self.text.replace("|", "\n")
    reactions_text: str = ""
    for reaction, count in self.reactions:
        reactions_text += f"{reaction} ({count})"

    return f"{quote_text}\n\n{reactions_text}"


def __display_details(self) -> str:
    """
    Build the textual output of a quotes' full details
    :return: the detailed textual representation of the quote
    """

    full_text: str = f"{self.__display_text()}\n\n" \
                     f"Date: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.date))}\n" \
                     f"Added by: {self.user} / {self.mxuser}\n" \
                     f"Added on: {self.chan} / {self.mxroom}\n" \
                     f"Rank: {self.rank}\n"
    return full_text


async def quote_command(command):
    """
    Display a quote, either randomly selected or by specific id or search terms
    :param command:
    :return: -
    """

    quotes: Dict[int, Quote] = plugin.read_data("quotes")

    if len(command.args) == 0:
        """no id or search term supplied, randomly select a quote"""
        quote_id, quote = random.random(quotes)
        await plugin.message(command.client, command.room.room_id, quote.__display_text(), False)

    elif len(command.args == 1) and int(command.args[0]) < len(quotes):
        """specific quote requested by id"""
        try:
            quote: Quote = quotes[command.args[0]]
            await plugin.message(command.client, command.room.room_id, quote.__display_text(), False)
        except ValueError:
            await plugin.message(command.client, command.room.room_id, f"Quote {command.args[0]} not found", False)

    else:
        """search quote by search term"""
        matching_quotes: List[Quote] = []
        for quote_id, quote in quotes:
            if quote.match(command.args):
                matching_quotes.append(quote)

        chosen_quote = random.random(matching_quotes)
        await send_text_to_room(command.client, command.room.room_id, chosen_quote.__display_text(), False)


async def quote_detail_command(command):
    pass


def match(self, search_terms: List[str]) -> bool:

    search_term: str
    for search_term in search_terms:
        if search_term.lower() not in self.text.lower():
            return False
    return True


async def quote_add_command(command):
    quotes: Dict[int, Quote] = plugin.read_data("quotes")


async def quote_del_command(command):
    quotes: Dict[int, Quote] = plugin.read_data("quotes")
    try:
        if quotes[command.args[0]].type != "deleted":
            quotes[command.args[0]].type = "deleted"
            plugin.notice(f"Quote {command.args[0]} deleted")
        else:
            plugin.notice(f"Quote {command.args[0]} is already deleted")
    except (KeyError, ValueError):
        plugin.notice(f"Quote {command.args[0]} not found")


async def quote_restore_command(command):
    quotes: Dict[int, Quote] = plugin.read_data("quotes")
    try:
        quotes[command.args[0]].type = "deleted"
    except (KeyError, ValueError):
        plugin.notice(command, f"Quote {command.args[0]} not found")
    plugin.notice(command, f"Quote {command.args[0]} deleted")


async def quote_edit_command(command):
    pass




class Quote:

    def __init__(self, quote_type: str = "local", text: str = "", url: str = "",
                 channel: str = "", mxroom: str = "",
                 user: str = "", mxuser: str = "",
                 date: float = time.time()
                 ):
        """
        A textual quote and all its parameters
        :param quote_type: type of the quote (local, remote or deleted)
        :param text: the actual text of the local quote, usually a single line or a conversation in multiple lines
        :param url: an url to a remote quote
        :param channel: (legacy) IRC-channel name, room-Name for Quotes added in matrix
        :param mxroom: matrix room id
        :param user: (legacy) IRC-username of the user who added the quote
        :param mxuser: matrix username of the user who added the quote
        """

        self.id = max(plugin.read_data("quotes").keys()+1)
        """id of the quote, automatically set to currently highest id + 1"""
        self.type: str = quote_type
        self.text: str = text
        self.url: str = url
        self.date: float = date
        self.chan: str = channel
        self.mxroom: str = mxroom
        self.user: str = user
        self.mxuser: str = mxuser

        self.rank: int = 0
        """rank of the quote, used to be the number of times the quote has been displayed"""

        self.reactions: Dict[str, int] = {}
        """Dict of reactions (emoji) and their respective counts a quote has received"""

        self.members: List[str] = ""
        """List of people participating in the quote"""


plugin.add_command("quote", quote_command, "Post quotes, either randomly, by id, by search string or by tags")
plugin.add_command("quote_detail", quote_detail_command, "View a detailed output of a specific quote")
plugin.add_command("quote_add", quote_add_command, "Add a quote")
plugin.add_command("quote_del", quote_del_command, "Delete a quote")

from plugin import Plugin
from typing import Dict, List
import time
import random

import logging
logger = logging.getLogger(__name__)

quote_attributes: List[str] = ["user", "members"]
"""valid attributes to select quotes by"""

plugin = Plugin("quote", "General", "Store (more or less) funny quotes and access them randomly or by search term")


class Quote:

    def __init__(self, quote_type: str = "local", text: str = "", url: str = "",
                 channel: str = "", mxroom: str = "",
                 user: str = "", mxuser: str = "",
                 date: float = time.time()
                 ):
        """
        A textual quote and all its parameters
        :param quote_type: type of the quote (local, remote)
        :param text: the actual text of the local quote, usually a single line or a conversation in multiple lines
        :param url: an url to a remote quote
        :param channel: (legacy) IRC-channel name, room-Name for Quotes added in matrix
        :param mxroom: matrix room id
        :param user: (legacy) IRC-username of the user who added the quote
        :param mxuser: matrix username of the user who added the quote
        """

        try:
            self.id = max(plugin.read_data("quotes").keys())+1
        except KeyError:
            self.id = 1

        """id of the quote, automatically set to currently highest id + 1"""
        self.type: str = quote_type
        self.text: str = text
        self.url: str = url
        self.date: float = date
        self.chan: str = channel
        self.mxroom: str = mxroom
        self.user: str = user
        self.mxuser: str = mxuser

        self.deleted: bool = False
        """Flag to mark a quote as deleted"""

        self.rank: int = 0
        """rank of the quote, used to be the number of times the quote has been displayed"""

        self.reactions: Dict[str, int] = {}
        """Dict of reactions (emoji) and their respective counts a quote has received"""

        self.members: List[str] = []
        """List of people participating in the quote"""

    async def display_text(self) -> str:
        """
        Build the default textual representation of a randomly called quote
        :return: the textual representation of the quote
        """

        quote_text: str = self.text.replace("|", "\n")
        reactions_text: str = ""
        for reaction, count in self.reactions:
            reactions_text += f"{reaction} ({count})"

        return f"**Q {self.id}**:\n{quote_text}\n\n{reactions_text}"

    async def display_details(self) -> str:
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

    async def match(self, search_terms: List[str]) -> bool:

        search_term: str
        for search_term in search_terms:
            if search_term.lower() not in self.text.lower():
                return False
        return True


async def quote_command(command):
    """
    Display a quote, either randomly selected or by specific id, search terms or attributes
    :param command:
    :return: -
    """

    """Load all active (quote.deleted == False) quotes"""
    quotes: Dict[int, Quote]
    try:
        quotes = plugin.read_data("quotes")
        # TODO: check if this needs fixing
        quotes = dict(filter(lambda item: not item[1].deleted, quotes.items()))
    except KeyError:
        await plugin.reply_notice(command, "Error: no quotes stored")
        return False

    print(f"Quotes: {quotes}")

    quote_id: int
    quote: Quote

    if len(command.args) == 0:
        """no id or search term supplied, randomly select a quote"""
        quote_id, quote = random.choice(list(quotes.items()))
        await plugin.reply(command, await quote.display_text())

    elif len(command.args) == 1 and command.args[0].isdigit():
        print(f"Quotes stored: {len(quotes)}, Quote requested: {command.args[0]}, Type: {type(command.args[0])}")
        """specific quote requested by id"""
        try:
            quote = quotes[int(command.args[0])]
            await plugin.reply(command, await quote.display_text())
        except KeyError:
            await plugin.reply_notice(command, f"Quote {command.args[0]} not found")

    else:
        """Find quote by search term"""

        terms: List[str]
        match_id: int

        if command.args[-1].isdigit():
            """check if a specific match is requested"""
            terms = command.args[:-1]
            match_id = command.args[-1]
            quote = await find_quote_by_search_term(quotes, terms, match_id)

        else:
            terms = command.args
            quote = await find_quote_by_search_term(quotes, terms)

        if quote:
            await plugin.reply(command, await quote.display_text())
        else:
            await plugin.reply_notice(command, f"No quote found matching {terms}")


async def find_quote_by_search_term(quotes: Dict[int, Quote], terms: List[str], match_id: int = 0) -> Quote:
    """
    Search for a matching quote by search terms
    :param quotes: Dict of quotes
    :param terms: search terms the quotes must match
    :param match_id: optionally provide a number to return the n'th match to the search terms
    :return: a randomquote matching the search terms
    """

    matching_quotes: List[Quote] = []

    for quote_id, quote in quotes.items():
        if await quote.match(terms):
            matching_quotes.append(quote)

    if matching_quotes:
        if 0 < match_id <= len(matching_quotes):
            return random.random(matching_quotes)
        else:
            return matching_quotes[match_id-1]
    else:
        return None


async def find_quote_by_attributes(quotes: Dict[int, Quote]) -> Quote:

    # TODO: implement this :)
    pass


async def quote_detail_command(command):

    # TODO: implement this :)
    pass


async def quote_add_command(command):

    if len(command.args) > 0:
        quotes: Dict[int, Quote]
        try:
            quotes = plugin.read_data("quotes")
        except KeyError:
            quotes = {}
        quote_text: str = " ".join(command.args)
        new_quote: Quote = Quote("local", text=quote_text, mxroom=command.room.room_id)
        quotes[new_quote.id] = new_quote
        plugin.store_data("quotes", quotes)
        await plugin.reply_notice(command, f"Quote {new_quote.id} added")
    else:
        await plugin.reply_notice(command, "Usage: quote_add <quote_text>")


async def quote_delete_command(command):
    """
    Handle the command to delete a quote (sets quote.deleted-flag to True)
    :param command: Command containing the delete_command
    :return:
    """

    quotes: Dict[int, Quote]
    try:
        quotes = plugin.read_data("quotes")
    except KeyError:
        quotes = {}

    if len(command.args) > 1:
        await plugin.reply_notice(command, f"Usage: quote_delete <quote_id>")

    elif len(command.args) == 1 and command.args[0].isdigit():
        quote_id: int = int(command.args[0])
        try:
            if not quotes[quote_id].deleted:
                quotes[quote_id].deleted = True
                plugin.store_data("quotes", quotes)
                await plugin.reply_notice(command, f"Quote {quote_id} deleted")
        except KeyError:
            await plugin.reply_notice(command, f"Quote {quote_id} not found")
    else:
        await plugin.reply(command, f"Usage: quote_delete <id>")


async def quote_restore_command(command):
    """
    Handle the command to restore a quote (sets the quote.deleted-flag to False)
    :param command: Command containing the restore_command
    :return:
    """

    quotes: Dict[int, Quote]
    try:
        quotes = plugin.read_data("quotes")
    except KeyError:
        quotes = {}

    if len(command.args) > 1:
        await plugin.reply_notice(command, f"Usage: quote_restore <quote_id>")

    elif len(command.args) == 1 and command.args[0].isdigit():
        quote_id: int = int(command.args[0])
        try:
            if quotes[quote_id].deleted:
                quotes[quote_id].deleted = False
                plugin.store_data("quotes", quotes)
                await plugin.reply_notice(command, f"Quote {quote_id} restored")
        except KeyError:
            await plugin.reply_notice(command, f"Quote {quote_id} not found")
    else:
        await plugin.reply(command, f"Usage: quote_restore <id>")


plugin.add_command("testquote", quote_command, "Post quotes, either randomly, by id, or by search string")
# plugin.add_command("quote_detail", quote_detail_command, "View a detailed output of a specific quote")
plugin.add_command("testquote_add", quote_add_command, "Add a quote")
plugin.add_command("testquote_del", quote_delete_command, "Delete a quote (can be restored)")
plugin.add_command("testquote_restore", quote_restore_command, "Restore a quote")

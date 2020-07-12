from plugin import Plugin
from typing import Dict, List
import time
import random
from re import compile

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

    async def display_text(self, command) -> str:
        """
        Build the default textual representation of a randomly called quote
        :return: the textual representation of the quote
        """

        quote_text: str = self.text.replace(" | ", "  \n")
        p = compile(r'<(\S+)>')
        nick_list: List[str] = p.findall(quote_text)

        """replace problematic characters"""
        quote_text = quote_text.replace("<", "&lt;")
        quote_text = quote_text.replace(">", "&gt;")
        quote_text = quote_text.replace("`", "&#96;")

        """replace nicknames by userlinks"""
        if plugin.read_data("nick_links"):
            nick: str
            nick_link: str
            for nick in nick_list:
                if nick_link := await plugin.link_user(command, nick):
                    quote_text = quote_text.replace(f"&lt;{nick}&gt;", nick_link)

        reactions_text: str = ""
        for reaction, count in self.reactions.items():
            if count == 1:
                reactions_text += f"{reaction} "
            else:
                reactions_text += f"{reaction}({count}) "

        return f"**Quote {self.id}**:  \n{quote_text}  \n{reactions_text}"

    async def display_details(self, command) -> str:
        """
        Build the textual output of a quotes' full details
        :return: the detailed textual representation of the quote
        """

        full_text: str = f"{self.display_text(command)}\n  " \
                         f"Date: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.date))}\n" \
                         f"Added by: {self.user} / {self.mxuser}\n" \
                         f"Added on: {self.chan} / {self.mxroom}\n" \
                         f"Rank: {self.rank}\n"
        return full_text

    async def match(self, search_terms: List[str]) -> bool:
        """
        Check if the quote matches a list of search terms
        :param search_terms: list of search terms
        :return:    True, if it matches
                    False, if it does not match
        """

        search_term: str
        for search_term in search_terms:
            if search_term.lower() not in self.text.lower():
                return False
        return True

    async def quote_add_reaction(self, reaction: str):
        """
        Add a reaction to a quote
        :param reaction: the reaction that should be added to the quote
        :return:
        """

        if reaction in self.reactions.keys():
            self.reactions[reaction] += 1
        else:
            self.reactions[reaction] = 1


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

    quote_id: int
    quote_object: Quote

    if len(command.args) == 0:
        """no id or search term supplied, randomly select a quote"""
        quote_id, quote_object = random.choice(list(quotes.items()))
        await plugin.reply(command, await quote_object.display_text(command))

    elif len(command.args) == 1 and command.args[0].isdigit():
        """specific quote requested by id"""

        if quote_object := await find_quote_by_id(quotes, int(command.args[0])):
            await plugin.reply(command, await quote_object.display_text(command))
        else:
            await plugin.reply_notice(command, f"Quote {command.args[0]} not found")

    else:
        """Find quote by search term"""

        terms: List[str]
        match_id: int

        if command.args[-1].isdigit():
            """check if a specific match is requested"""
            terms = command.args[:-1]
            match_id = int(command.args[-1])
            quote_object = await find_quote_by_search_term(quotes, terms, match_id)

        else:
            terms = command.args
            quote_object = await find_quote_by_search_term(quotes, terms)

        if quote_object:
            await plugin.reply(command, await quote_object.display_text(command))
        else:
            await plugin.reply_notice(command, f"No quote found matching {terms}")


async def find_quote_by_search_term(quotes: Dict[int, Quote], terms: List[str], match_id: int = 0) -> Quote or None:
    """
    Search for a matching quote by search terms
    :param quotes: Dict of quotes
    :param terms: search terms the quotes must match
    :param match_id: optionally provide a number to return the n'th match to the search terms
    :return: a randomquote matching the search terms
    """

    matching_quotes: List[Quote] = []

    for quote_id, quote_object in quotes.items():
        if await quote_object.match(terms):
            matching_quotes.append(quote_object)

    if matching_quotes:
        if int(match_id) != 0 and match_id <= len(matching_quotes):
            return matching_quotes[match_id-1]
        else:
            return random.choice(matching_quotes)
    else:
        return None


async def find_quote_by_id(quotes: Dict[int, Quote], quote_id: int) -> Quote or None:
    """
    Find a quote by its id
    :param quotes: The dict containing all current quotes
    :param quote_id: the id of the quote to find
    :return: the Quote that has been found, None otherwise
    """
    try:
        quote_object: Quote = quotes[quote_id]
        return quote_object
    except KeyError:
        return None


async def find_quote_by_attributes(quotes: Dict[int, Quote], attribute: str, values: List[str]) -> Quote or None:
    """
    Find a quote by its attributes
    :param quotes: The dict containing all current quotes
    :param attribute: the attribute by which to find the quote
    :param values: the values of the attribute the quote has to match
    :return: the Quote that has been found, None otherwise
    """

    # TODO: implement this :)
    return None


async def quote_detail_command(command):
    """
    Display a detailed output of the quote
    :param command:
    :return:
    """

    # TODO: implement this :)
    pass


async def quote_add_command(command):
    """
    Add a new quote
    :param command:
    :return:
    """

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


async def quote_add_reaction_command(command):
    """
    Add a reaction to a quote
    :param command:
    :return:
    """

    quotes: Dict[int, Quote]
    try:
        quotes = plugin.read_data("quotes")
    except KeyError:
        quotes = {}

    if len(command.args) == 2 and command.args[0].isdigit():
        quote: Quote = await find_quote_by_id(quotes, int(command.args[0]))
        if quote:
            await quote.quote_add_reaction(command.args[1])
            quotes[quote.id] = quote
            plugin.store_data("quotes", quotes)
            await plugin.reply_notice(command, f"Reaction {command.args[1]} added to quote {command.args[0]}")
        else:
            await plugin.reply_notice(command, f"Quote {command.args[0]} not found")

    else:
        await plugin.reply_notice(command, f"Usage: quote_add_reaction <quote_id> <emoji>")


async def quote_links_command(command):
    """
    Toggle linking of nicknames on or off
    :param command:
    :return:
    """

    try:
        plugin.store_data("nick_links", not plugin.read_data("nick_links"))

    except KeyError:
        plugin.store_data("nick_links", False)

    await plugin.reply_notice(command, f"Nick linking {plugin.read_data('nick_links')}")


plugin.add_command("quote", quote_command, "Post quotes, either randomly, by id, or by search string")
# plugin.add_command("quote_detail", quote_detail_command, "View a detailed output of a specific quote")
plugin.add_command("quote_add", quote_add_command, "Add a quote")
plugin.add_command("quote_del", quote_delete_command, "Delete a quote (can be restored)")
plugin.add_command("quote_restore", quote_restore_command, "Restore a quote")
plugin.add_command("quote_add_reaction", quote_add_reaction_command, "Add a reaction to a quote - to be replaced by automatic reaction detection later")
plugin.add_command("quote_links", quote_links_command, "Toggle automatic nickname linking")

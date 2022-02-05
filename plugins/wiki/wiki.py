# -*- coding: utf8 -*-
import logging

import wikipedia
from urllib3.exceptions import NewConnectionError

from core.bot_commands import Command
from core.plugin import Plugin

logger = logging.getLogger(__name__)
plugin = Plugin("wiki", "Lookup", "Lookup keywords in various online encyclopedias")


def setup():
    """
    This just moves the initial setup-commands to the top for better readability
    :return: -
    """
    plugin.add_config("default_lang", default_value="en", is_required=True)
    plugin.add_command("w", lookup_wikipedia_en, "Lookup `keyword` on en.wikipedia.org. Alias for `wiki en <keyword>`.")
    plugin.add_command("wd", lookup_wikipedia_de, "Lookup `keyword` on de.wikipedia.org. Alias for `wiki de <keyword>`.")
    plugin.add_command(
        "wiki",
        lookup_wikipedia,
        f"Lookup a keyword in wikipedia of any language (default: {plugin.read_config('default_lang')})   \nUsage: `wiki [LANG] <keyword>`",
    )


async def lookup_wikipedia(command: Command, lang: str or None = None):
    """
    Check if an optional language has been provided, lookup the keyword(s) and post the results to the room.
    :param command:
    :param lang: optional language of wikipedia to do the lookup in.
    :return:
    """

    wiki: wikipedia = wikipedia
    if not lang and len(command.args) > 1 and len(command.args[0]) == 2:
        lang: str = command.args[0]
        query: str = " ".join(command.args[1:])

    else:
        query: str = " ".join(command.args)

    if lang in wiki.languages():
        wiki.set_lang(lang)
    else:
        wiki.set_lang(plugin.read_config("default_lang"))
        await plugin.respond_notice(command, f"Warning: invalid language specified, defaulting to {plugin.read_config('default_lang')}.")

    try:
        page: wikipedia.WikipediaPage = wiki.page(query)
    except wikipedia.exceptions.DisambiguationError as e:
        await plugin.respond_notice(command, f"Error: Disambiguation. You may want to try {', '.join(e.options)}")
        return
    except wikipedia.exceptions.PageError:
        await plugin.respond_notice(command, "Error: No article found.")
        return
    except (NewConnectionError, ConnectionError):
        await plugin.respond_notice(command, "Error: Error connecting to wikipedia.")
        return

    await plugin.respond_notice(command, f"{page.title}: {wiki.summary(query, sentences=3)}  \n{page.url}")


async def lookup_wikipedia_en(command: Command):
    """
    Command to lookup a keyword in Wikipedia en
    :param command:
    :return:
    """

    await lookup_wikipedia(command, lang="en")


async def lookup_wikipedia_de(command: Command):
    """
    Command to lookup a keyword in Wikipedia de
    :param command:
    :return:
    """

    await lookup_wikipedia(command, lang="de")


setup()

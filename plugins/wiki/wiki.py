# -*- coding: utf8 -*-
import re
import logging
import urllib.request
import urllib.parse
from html.parser import HTMLParser

from core.bot_commands import Command
from core.plugin import Plugin

from typing import Dict, List

logger = logging.getLogger(__name__)
plugin = Plugin("wiki", "Lookup", "Lookup keywords in various online encyclopedias")


def setup():
    """
    This just moves the initial setup-commands to the top for better readability
    :return: -
    """
    plugin.add_command("w", lookup_wikipedia_en, "Lookup a keyword in Wikipedia en")
    plugin.add_command("wd", lookup_wikipedia_de, "Lookup a keyword in Wikipedia de")
    plugin.add_command("wp", lookup_mlp_wikia, "Lookup a keyword in mlp.wikia.com")


async def lookup_wikipedia_en(command: Command):
    """
    Command to lookup a keyword in Wikipedia en
    :param command:
    :return:
    """

    url: str = "https://en.wikipedia.org/wiki/Special:Search?search=%s&go=Go"
    await lookup_generic(command, url)


async def lookup_wikipedia_de(command: Command):
    """
    Command to lookup a keyword in Wikipedia de
    :param command:
    :return:
    """
    url: str = "https://de.wikipedia.org/wiki/Special:Search?search=%s&go=Go"
    await lookup_generic(command, url)


async def lookup_mlp_wikia(command: Command):
    """
    Command to lookup a keyword in mlp.wikia.com
    :param command:
    :return:
    """
    url: str = "http://mlp.wikia.com/wiki/Special:Search?query=%s&go=Go"
    await lookup_generic(command, url)


async def lookup_generic(command: Command, url: str):
    """
    Lookup a keyword in the wiki given by url and respond with the first phrase.
    :param command:
    :param url:
    :return:
    """

    data_storage: List[str] = []

    class MyHTMLParser(HTMLParser):
        def handle_data(self, data):
            if data:
                data_storage.append(str(data))

    headers: Dict[str, str] = {"User-Agent": "Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11"}
    request: urllib.request.Request = urllib.request.Request(url % urllib.parse.quote(" ".join(command.args)), headers=headers)
    with urllib.request.urlopen(request) as url_fd:
        html = url_fd.read()
        html = html.decode()

    if "Es existiert kein Artikel mit dem Namen" in html:
        await plugin.respond_notice(command, "Es existiert kein Artikel mit diesem Namen.")
        return None

    if "There is no page titled" in html:
        await plugin.respond_notice(command, "There is no page with this title.")
        return None

    if "Wikipedia:Disambiguation" in html or "Wikipedia:Begriffskl" in html:
        html = html.replace("\n", " ")
        parsregex = re.compile(r'<p>(.*) id=("Vorlage_Begriffsklaerung"|"disambig")>', re.M)  # @UndefinedVariable
        pars_match = re.search(parsregex, html)
        if pars_match:
            pars = pars_match.group(1)
        else:
            await plugin.respond_notice(command, "Error: Lookup failed.")
            return None

        pars = pars.replace("&#160;", " ")
        pars = pars.replace("</li>", "; </li>")
        parser = MyHTMLParser()
        parser.feed(pars)
        parsed = "".join(data_storage)
        parsed = re.sub(r"\[\d+\]", "", parsed)
        parsed = parsed.replace(" (pronunciation )", "")
        parsed = parsed.replace("[edit] ", "")
        parsed = re.sub(r"//\<\!\[CDATA\[.*?\]\]\> *", "", parsed)

    else:
        while True:
            par_1_match = re.search(r"<p>(.*?)</p>", html, re.DOTALL)
            if par_1_match:
                par_1 = par_1_match.group(1)
                if "." in par_1:
                    break
                else:
                    html = html[html.index("</p>") + 4 :]
            else:
                await plugin.respond_notice(command, "Error: Lookup failed.")
                return None
        par_1 = par_1.replace("&#160;", " ")
        parser = MyHTMLParser()
        parser.feed(par_1)
        parsed = "".join(data_storage)
        parsed = re.sub(r"\[\d+\]", "", parsed)
        parsed = parsed.replace(" (pronunciation )", "")
        parsed_sentences = (parsed + " ").split(". ")
        if parsed_sentences[-1] == "":
            del parsed_sentences[-1]
        while len(parsed_sentences) > 1 and (
            (" " + parsed_sentences[0].lower()).endswith((" e.g", " z.b.", " prof", " mr", " mrs", " ms", " dr", " inc", " esq", " ges.m.b.h", " int"))
            or len(parsed_sentences[0]) < 100
            and len(parsed_sentences[0]) + len(parsed_sentences[1]) <= 200
        ):
            parsed_sentences[0:2] = (". ".join(parsed_sentences[0:2]),)
        parsed = parsed_sentences[0] + "."

    await plugin.respond_notice(command, parsed)


setup()

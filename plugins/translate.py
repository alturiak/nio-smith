# -*- coding: utf8 -*-
from plugin import Plugin
import os.path
import pickle
import googletrans
from nio import AsyncClient
from chat_functions import send_text_to_room
from re import sub

from typing import List

import logging
logger = logging.getLogger(__name__)

allowed_rooms: List = ["!hIWWJKHWQMUcrVPRqW:pack.rocks", "!iAxDarGKqYCIKvNSgu:pack.rocks"]
default_source: List = ['any']
default_dest: str = 'en'
default_bidirectional: bool = False
roomsfile: str = os.path.join(os.path.dirname(__file__), os.path.basename(__file__)[:-3] + ".pickle")

"""
roomsdb = {
    room_id: {
        "source_langs": ['any']
        "dest_lang": 'en'
        "bidirectional": False
    }
}
"""


async def switch(command):
    """Switch translation for room-messages on or off

    Args:
        command (bot_commands.Command): Command used to trigger this method

    """

    try:
        roomsdb: dict = pickle.load(open(roomsfile, "rb"))
        enabled_rooms_list: list = roomsdb.keys()
    except FileNotFoundError:
        roomsdb: dict = {}
        enabled_rooms_list: list = []

    if len(command.args) == 0:
        source_langs: list = default_source
        dest_lang: str = default_dest
        bidirectional: bool = default_bidirectional
    else:
        try:
            if command.args[0] == 'bi':
                bidirectional = True
                source_langs = [command.args[1]]
                dest_lang = command.args[2]
            else:
                bidirectional = False
                source_langs = command.args[:-1]
                dest_lang = command.args[-1]
        except IndexError:
            await send_text_to_room(command.client, command.room.room_id, "Syntax: `!translate [[bi] source_lang... dest_lang]`")
            return False

    if command.room.room_id in enabled_rooms_list:
        del roomsdb[command.room.room_id]
        pickle.dump(roomsdb, (open(roomsfile, "wb")))
        await send_text_to_room(command.client, command.room.room_id, "Translations disabled", notice=False)
    elif command.room.room_id in allowed_rooms:
        if dest_lang in googletrans.LANGUAGES.keys():
            if source_langs == ['any'] or all(elem in googletrans.LANGUAGES.keys() for elem in source_langs):
                roomsdb[command.room.room_id] = {"source_langs": source_langs, "dest_lang": dest_lang, "bidirectional": bidirectional}
                pickle.dump(roomsdb, (open(roomsfile, "wb")))

                if bidirectional:
                    message = "Bidirectional translations (" + source_langs[0] + "<=>" + dest_lang + ") enabled - " \
                                                                                                     "**ATTENTION**: *ALL* future messages in this room will be sent to Google"
                else:
                    source_langs_str = str(source_langs)
                    message = "Unidirectional translations (" + source_langs_str + "=>" + dest_lang + ") enabled - " \
                                                                                                      "**ATTENTION**: *ALL* future messages in this room will be sent to Google"
                await send_text_to_room(command.client, command.room.room_id, message, notice=False)


async def translate(client: AsyncClient, room_id: str, message: str):

    try:
        roomsdb = pickle.load(open(roomsfile, "rb"))
    except FileNotFoundError:
        roomsdb = {}

    if room_id in allowed_rooms and room_id in roomsdb.keys():
        # Remove special characters before translation
        message = sub('[^A-z0-9\-\.\?!:\sÄäÜüÖö]+', '', message)
        trans = googletrans.Translator()
        logger.debug(f"Detecting language for message: {message}")
        message_source_lang = trans.detect(message).lang
        if roomsdb[room_id]["bidirectional"]:
            languages = [roomsdb[room_id]["source_langs"][0], roomsdb[room_id["dest_lang"]]]
            if message_source_lang in languages:
                # there has to be a simpler way, but my brain is tired
                dest_lang = set(languages).difference([message_source_lang])
                if len(dest_lang) == 1:
                    dest_lang = dest_lang.pop()
                    translated = trans.translate(message, dest=dest_lang).text
                    await send_text_to_room(client, room_id, translated)
        else:
            if message_source_lang != roomsdb[room_id]["dest_lang"] and (roomsdb[room_id]["source_langs"] == ['any'] or message_source_lang in roomsdb[room_id]["source_langs"]):
                translated = trans.translate(message, dest=roomsdb[room_id]["dest_lang"]).text
                await send_text_to_room(client, room_id, translated)


plugin = Plugin("translate", "General", "Provide near-realtime translations of all room-messages via Google Translate")
plugin.add_command("translate", switch, "`translate [[bi] source_lang... dest_lang]` - translate text from "
                                        "one or more source_lang to dest_lang", allowed_rooms)
plugin.add_hook("m.room.message", translate, allowed_rooms)

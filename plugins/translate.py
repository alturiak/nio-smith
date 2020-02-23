# -*- coding: utf8 -*-
import os.path
import pickle

import googletrans
from chat_functions import send_text_to_room

allowed_rooms = ["!hIWWJKHWQMUcrVPRqW:pack.rocks", "!iAxDarGKqYCIKvNSgu:pack.rocks"]
default_source = ['any']
default_dest = 'en'
default_bidirectional = False
roomsfile = os.path.join(os.path.dirname(__file__), "translate.pickle")


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

    try:
        roomsdb = pickle.load(open(roomsfile, "rb"))
        enabled_rooms_list = roomsdb.keys()
    except FileNotFoundError:
        roomsdb = {}
        enabled_rooms_list = []

    if len(command.args) == 0:
        source_langs = default_source
        dest_lang = default_dest
        bidirectional = default_bidirectional
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
            await send_text_to_room(command.client, command.room.room_id, "Syntax: `!translate [bi] source_lang... dest_lang`")
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
                    message = "Bidirectional translations (" + source_langs[0] + "<=>" + dest_lang + ") enabled - **ATTENTION**: *ALL* messages in this room will be sent to Google"
                else:
                    source_langs_str = str(source_langs)
                    message = "Unidirectional translations (" + source_langs_str + "=>" + dest_lang + ") enabled - **ATTENTION**: *ALL* messages in this room will be sent to Google"
                await send_text_to_room(command.client, command.room.room_id, message, notice=False)


async def translate(client, room_id, message):

    roomsdb = pickle.load(open(roomsfile, "rb"))
    trans = googletrans.Translator()
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


async def get_enabled_rooms():

    try:
        return pickle.load(open(roomsfile, "rb")).keys()
    except FileNotFoundError:
        return []

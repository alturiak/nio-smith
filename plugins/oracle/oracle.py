from core.plugin import Plugin
import random


async def oracle(command):
    oracles = (
        "Das ist gut m\xf6glich.",
        "Ist das wirklich Ihr Ernst?",
        "Lassen Sie es bleiben.",
        "Wieso w\xfcrde jemand so etwas wollen?",
        "Ja, auf jeden Fall!",
        "Die Aussicht ist sehr gut.",
        "Das ist eine Illusion.",
        "Niemals, niemals, niemals.",
        "Die Zeichen stehen gut.",
        "Absolut!",
        "Die Zeichen stehen gar nicht gut.",
        "Es wird wahrscheinlich passieren.",
        "Tr\xe4umen Sie weiter ...",
        "Sie verschwenden Ihre Zeit mit l\xe4cherlichen Phantasien.",
        "Leider wird es niemals sein.",
        "Mit etwas Gl\xfcck schon.",
        "Das ist nicht klar.",
        "Die Zeichen stehen sehr gut!",
        "Nein, auf gar keinen Fall!",
        "Ja, ja, ja!",
        "Das ist nicht Ihr Ernst?!",
        "Das ist ziemlich sicher.",
        "Fragen Sie in ein paar Wochen nochmal nach.",
        "Wenn Sie daran glauben wollen, bitte ...",
        "Ich w\xfcrde nicht darauf wetten",
        "Wenn Sie sich anstrengen, schon ...",
        "Die Aussicht ist gut.",
        "M\xf6glich w\xe4re es durchaus.",
        "Nicht um alles auf der Welt!",
        "Daran sollten Sie nicht mal denken.",
        "Haben Sie etwas Geduld.",
        "Ich zweifele nicht daran.",
        "Ein definitives Ja.",
        "Vielleicht...",
        "Warum nicht?",
        "Unter Umst\xe4nden schon.",
        "Es k\xf6nnte bald Wirklichkeit werden.",
        "Die Zeit wird es zeigen.",
    )
    message = "**Antwort:** " + random.choice(oracles)
    await plugin.reply(command, message, delay=200)


plugin = Plugin("oracle", "General", "Plugin to provide a simple, randomized !oracle")
plugin.add_command("oracle", oracle, "predict the inevitable future")

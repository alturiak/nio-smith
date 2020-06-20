from plugin import Plugin


async def sample_command(command):
    print("Sample debug output")

plugin = Plugin("Sample", "General", "Just a simple sample.")
plugin.add_command("sample", sample_command, "A simple sample command")

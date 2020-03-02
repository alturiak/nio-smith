from plugin import Plugin

plugin = Plugin("Sample", "General", "Just a simple sample.")


async def sample_command(command):
    print("Sample debug output")


plugin.add_command("sample", sample_command, "A simple sample command")

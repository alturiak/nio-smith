from plugin import Plugin

plugin = Plugin("Sample", "General", "Just a simple sample.")
plugin.add_command("sample", "sample_command", "A simple sample command")


def sample_command():
    print("Sample debug output")

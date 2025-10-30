import os


def is_debug_mode():
    return os.getenv("DEBUG", "").lower() == "true"

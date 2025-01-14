import importlib
import os
import random
from typing import List

from bot import Bot


def load_bots(directory: str) -> List[Bot]:
    bots = []
    for filename in os.listdir(directory):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            module = importlib.import_module(f"{directory}.{module_name}")
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, Bot) and attr != Bot:
                    bot_instance = attr(module_name)
                    bots.append(bot_instance)

    random.shuffle(bots)
    return bots

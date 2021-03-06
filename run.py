import sys

import sc2
from sc2 import Difficulty, Race
from sc2.player import Bot, Computer

from __init__ import run_ladder_game

# Load bot
from SunshineBot import SunshineBot

bot = Bot(Race.Terran, SunshineBot())

# Start game
if __name__ == "__main__":
    if "--LadderServer" in sys.argv:
        # Ladder game started by LadderManager
        print("Starting ladder game...")
        run_ladder_game(bot)
    else:
        # Local game
        print("Starting local game...")
        sc2.run_game(
            sc2.maps.get("Abyssal Reef LE"), [bot, Computer(Race.Protoss, Difficulty.VeryHard)], realtime=False
        )
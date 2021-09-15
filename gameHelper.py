import datetime
import os
import csv


class pyquestHelper:
    def __init__(self):
        self.game_seed = "123"

    def showHelp(self):
        print("command list")
        print("stats - show stats")
        print("play - play the game")
        print("help - show this help file")
        print("exit - exit the game")

    def clearScreen(self):
        os.system("cls" if os.name == "nt" else "clear")

    def createHighScore(self, tileObj, pc):
        with open("highscores.csv", "a") as fio:
            highscore_json = csv.DictReader(fio)
            field_names = ["player_name", "level", "exp points", "tile_id", "date"]
            csv_writer = csv.DictWriter(fio, fieldnames=field_names)
            new_row = {
                "player_name": pc.name,
                "level": pc.chrLevel,
                "exp points": pc.expPoints,
                "tile_id": tileObj.tile_id,
                "date": datetime.datetime.now(),
            }
            csv_writer.writerow(new_row)

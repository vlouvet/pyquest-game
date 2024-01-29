import datetime
import os
import csv


class PyquestHelper:
    def __init__(self):
        self.game_seed = "123"

    def show_help(self):
        print("command list")
        print("stats - show stats")
        print("play - play the game")
        print("help - show this help menu")
        print("exit - exit the game")

    def fight_help(self, player_char):
        print("Fight command list")
        print("[a]ttack")
        if player_char.chrClass == "wiz":
            print("[m]agic")
        print("[h]elp - show this help menu")
        print("[fl]ee")
        print("exit - exit the game")

    def clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")

    def create_highscore(self, tile_obj, player_char):
        with open("highscores.csv", "a") as fio:
            highscore_json = csv.DictReader(fio)
            field_names = ["player_name", "level", "exp points", "tile_id", "date"]
            csv_writer = csv.DictWriter(fio, fieldnames=field_names)
            new_row = {
                "player_name": player_char.name,
                "level": player_char.chrLevel,
                "exp points": player_char.expPoints,
                "tile_id": tile_obj.tile_id,
                "date": datetime.datetime.now(),
            }
            csv_writer.writerow(new_row)

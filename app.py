import json
import random
from flask import Flask, request
import userCharacter
import pqMonsters
import gameTile


app = Flask("__name__")

@app.route("/play", methods=['POST', 'GET'])
def greet_user():
    if request.method == 'POST':
        print(request.data)
    # the code below is executed if the request method
    # was GET or the credentials were invalid
    return greet_hero()

@app.route("/newplayer", methods=['POST', 'GET'])
def new_char():
    if request.method == 'POST':
        req_data = json.loads(request.data.decode('utf-8'))
        player_char = userCharacter.playerCharacter(req_data['name'])
    # the code below is executed if the request method
    # was GET or the credentials were invalid
    return game_intro(player_char)

@app.route("/chooseClass", methods=['POST', 'GET'])
def set_race_and_class():
    if request.method == 'POST':
        req_data = json.loads(request.data.decode('utf-8'))
        player_char = userCharacter.playerCharacter(req_data['pc'])
        player_char.setRace()
        player_char.setClass()
        player_char.setStats()
    return char_start(player_char)
    # gameObj = gameHelper.pyquestHelper()


with open("game_config.ini", "r") as fin:
    config_json = json.load(fin)

tile_config = gameTile.pqGameTile()


def generate_tile():
    # generate a new tile
    # tile can contain monster, loot, or quest_info
    # the first tile in the game is always the same
    if tile_config.tile_id == 1:
        tile_config.tile_id = 2
    else:
        tile_type_list = ["monster", "sign", "scene"]
        tile_config.tile_content_type = random.choice(tile_type_list)
        treasure_found = random.randint(1, 100)
        if treasure_found == 4:
            tile_config.tile_content_type = "treasure"
        tile_config.tile_id += 1
    return tile_config


def greet_hero():
    greet_message = "Hello Weary traveler, I think I've seen you before.\n"
    greet_message += "What was your name again?"
    # while pc.name == "" or pc.name == "player1":
    #     pc.setName()
    return {'greet_message': greet_message}


def move_penalty(player_char):
    player_char.hitpoints = player_char.hitpoints - 1


def game_intro(player_char):
    intro_message = "Welcome to Pyquest!"
    intro_message += "the story begins on a cold dark night..."
    intro_message += f"our hero, {player_char.name}, goes out looking for adventure..."
    intro_message += "when suddenly!"

    return {'intro_message': intro_message,
            'next_page': 'set_raceNclass'}


def char_start(player_char):
    char_message = player_char.getStats()
    return {'charMessage': char_message, 'next_page':'/tile/1'}


def game_loop(player_char, game_obj):
    player_char.setStats()
    current_tile = generate_tile()
    while player_char.hitpoints is not None and player_char.hitpoints > 0:
        char_input = input("What to do Next?")
        if char_input == "rest" or char_input == "r" :
            if player_char.hitpoints < player_char.maxhp:
                print('''Currently Have {player_char.hitpoints}
                 out of {player_char.maxhp} hitpoints''')
                player_char.doRestHP()
                if player_char.expPoints >= player_char.nextLevelExp:
                    player_char.doLevelUp()
                player_char.getStats()
        elif char_input == "move" or  char_input == "m" :
            current_tile = generate_tile()
            print(current_tile.tile_content_type)
            if current_tile.tile_content_type == "monster":
                fight_loop(player_char, current_tile, game_obj)
            elif current_tile.tile_content_type == "scene":
                print(
                    "you find a scenic path, but nothing of interests catches your eye."
                )
        elif char_input == "loot" or char_input == "l" :
            if current_tile.tile_content_type == "treasure":
                print("beautiful treasure!")
            print("you look for loot but find none!")
        elif char_input == "stats" or char_input == "s":
            player_char.getStats()
        elif char_input == "exit":
            print(f"you arrived to tile number: {current_tile.tile_id}")
            # gameObj.createHighScore(current_tile, pc)
            exit()
        elif char_input == "help":
            print("Command list:")
            print("[r]est, [m]ove, [l]oot, [s]tats, exit, [h]elp")
        # enable for faster death!
        # movePenalty(pc)
        # gameObj.clearScreen()
    print("\n\n")
    player_char.getStats()
    player_char.setDead(current_tile)
    game_obj.createHighScore(current_tile, player_char)


def fight_loop(player_char, current_tile, game_obj):
    monster_obj = pqMonsters.NPCMonster()
    print(f"Suddenly a {monster_obj.name} appears!")
    current_tile.tile_content = "FIGHT TO THE DEATH"
    print(f"tile content: {current_tile.tile_content}")
    turn_count = 0
    while player_char.hitpoints > 0 and monster_obj.hitpoints > 0:
        turn_count += 1
        print(f"Turn Count: {turn_count}")
        fight_command = input("What is your next Fight Move?")
        if fight_command == "attack" or fight_command == "a":
            player_char.doAttack(monster_obj)
        elif fight_command == "magic" or fight_command == "m":
            if player_char.chrClass != "wiz":
                print("You have no magic!")
            else:
                player_char.doMagic(monster_obj)
        elif fight_command == "help":
            game_obj.fightHelp(player_char)
        elif fight_command == "flee" or fight_command == "fl":
            if player_char.doFlee(monster_obj):
                break
            else:
                print("You're not able to run away!")
        if monster_obj.hitpoints >0:
            monster_obj.do_attack(player_char)

    if monster_obj.hitpoints <= 0:
        player_char.setExp(monster_obj)

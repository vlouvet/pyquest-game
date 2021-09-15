import json
import gameHelper
import userCharacter
import pqMonsters
import gameTile
import random


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
        treasureFound = random.randint(1, 100)
        if treasureFound == 4:
            tile_config.tile_content_type = "treasure"
        tile_config.tile_id += 1
    return tile_config


def greetHero():
    print("Hello Weary traveler, I think I've seen you before.")
    print("What was your name again?")
    while pc.name == "" or pc.name == "player1":
        pc.setName()


def movePenalty(pc):
    pc.hitpoints = pc.hitpoints - 1


def gameIntro(pc):
    print("Welcome to Pyquest!")
    print("the story begins on a cold dark night...")
    print(f"our hero, {pc.name}, goes out looking for adventure...")
    print("when suddenly!")


def gameLoop(pc, gameObj):
    pc.setStats()
    current_tile = generate_tile()
    while pc.hitpoints is not None and pc.hitpoints > 0:
        getChrInput = input("What to do Next?")
        if getChrInput == "rest":
            if pc.hitpoints < pc.maxhp:
                print(pc.hitpoints)
                print(pc.maxhp)
                pc.doRestHP()
                if pc.expPoints >= pc.nextLevelExp:
                    pc.doLevelUp()
                pc.getStats()
        elif getChrInput == "move":
            current_tile = generate_tile()
            print(current_tile.tile_content_type)
            if current_tile.tile_content_type == "monster":
                fightLoop(pc, current_tile)
            elif current_tile.tile_content_type == "scene":
                print(
                    "you find a scenic path, but nothing of interests catches your eye."
                )
        elif getChrInput == "loot":
            if current_tile.tile_content_type == "treasure":
                print("beautiful treasure!")
            print("you look for loot but find none!")
        elif getChrInput == "stats":
            pc.getStats()
        elif getChrInput == "exit":
            print(f"you arrived to tile number: {current_tile.tile_id}")
            # gameObj.createHighScore(current_tile, pc)
            exit()
        elif getChrInput == "help":
            print("Command list:")
            print("rest, move, loot, stats, exit, help")
        # enable for faster death!
        # movePenalty(pc)
        # gameObj.clearScreen()
    print("\n\n")
    pc.getStats()
    pc.setDead(current_tile)
    gameObj.createHighScore(current_tile, pc)


def fightLoop(pc, current_tile):
    current_tile.tile_content = "FIGHT TO THE DEATH"
    print(f"tile content: {current_tile.tile_content}")
    monsterObj = pqMonsters.npcMonster(pc.chrLevel)
    turnCount = 0
    while pc.hitpoints > 0 and monsterObj.hitpoints > 0:
        turnCount += 1
        print(f"Turn Count: {turnCount}")
        monsterObj.doAttack(pc)
        pc.doAttack(monsterObj)
    if monsterObj.hitpoints <= 0:
        pc.setExp(monsterObj)
    pass


gameObj = gameHelper.pyquestHelper()
pc = userCharacter.playerCharacter("player1")
gameIntro(pc)
greetHero()
pc.setRace()
pc.setClass()

print("Main Menu\nType help for a list of commands\n")
chrCommand = input("")
while chrCommand != "exit":
    if chrCommand == "help":
        gameObj.showHelp()
        chrCommand = input("Main Menu\nType help for a list of commands\n")
    elif chrCommand == "stats":
        pc.getStats()
        chrCommand = input("Main Menu\nType help for a list of commands\n")
    elif chrCommand == "play":
        gameLoop(pc, gameObj)
        chrCommand = input("Main Menu\nType help for a list of commands\n")
    else:
        chrCommand = input("Main Menu\nType help for a list of commands\n")

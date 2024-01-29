import json
import gameHelper
import userCharacter
import pqMonsters
import gameTile
import random
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
db.create_all()
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username


# class User(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     email = db.Column(db.String(120), unique=True)
#     name = db.Column(db.String(80), unique=True, nullable=False)
#     race = db.Column(db.String(80), unique=True)
#     chrClass = db.Column(db.String(80), unique=True)
#     strength = db.Column(db.Integer)
#     intelligence = db.Column(db.Integer)
#     hitpoints = db.Column(db.Integer)
#     maxhp = db.Column(db.Integer)
#     expPoints = db.Column(db.Integer)
#     maxExp = db.Column(db.Integer)
#     stealth = db.Column(db.Integer)
#     chrLevel = db.Column(db.Integer)
#     nextLevelExp = db.Column(db.Integer)


#     def __repr__(self):
#         return '<User %r>' % self.name

app = Flask("__name__")
db.create_all()
@app.route("/play", methods=['POST', 'GET'])
def greet_user():
    error = None
    if request.method == 'POST':
        print(request.data)
    # the code below is executed if the request method
    # was GET or the credentials were invalid
    return greetHero()

@app.route("/newplayer", methods=['POST', 'GET'])
def new_char():
    error = None
    if request.method == 'POST':
        req_data = json.loads(request.data.decode('utf-8'))
        newChar = User()
        newChar.username = req_data['pc']['name']
        db.session.add(newChar)
        db.session.commit()
        print(f"User ID: {newChar.id}")
        pc = userCharacter.playerCharacter(req_data['pc']['name'])
        return gameIntro(pc)
    return greetHero()

@app.route("/chooseRaceClass", methods=['POST', 'GET'])
def set_raceNclass():
    error = None
    if request.method == 'POST':
        req_data = json.loads(request.data.decode('utf-8'))
        pc = userCharacter.playerCharacter(name="things")
        pc.set_name(req_data)
        pc.set_race(req_data)
        pc.set_class(req_data)
        pc.set_stats(req_data)
        return charStart(pc)
    return greetHero()
    # gameObj = gameHelper.pyquestHelper()


@app.route("/game/tile/<int:tileid>/", methods=['POST', 'GET'])
def game_tile(tileid):
    return {'statusCode': 'success'}
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
    greet_message = "Hello Weary traveler, I think I've seen you before.\n"
    greet_message += "What was your name again?"
    # while pc.name == "" or pc.name == "player1":
    #     pc.setName()
    return {'greet_message': greet_message}


def movePenalty(pc):
    pc.hitpoints = pc.hitpoints - 1


def gameIntro(pc):
    intro_message = "Welcome to Pyquest!"
    intro_message += "the story begins on a cold dark night..."
    intro_message += f"our hero, {pc.name}, goes out looking for adventure..."
    intro_message += "when suddenly!"

    return {'intro_message': intro_message,
            'next_page': 'set_raceNclass'}


def charStart(pc):
    CharacterMessage = pc.getStats()
    return {'charMessage': CharacterMessage, 'next_page':'/tile/1'}

def gameLoop(pc, gameObj):
    pc.setStats()
    current_tile = generate_tile()
    while pc.hitpoints is not None and pc.hitpoints > 0:
        getChrInput = input("What to do Next?")
        if getChrInput == "rest" or getChrInput == "r" :
            if pc.hitpoints < pc.maxhp:
                print(f"Currently Have {pc.hitpoints} out of {pc.maxhp} hitpoints")
                pc.doRestHP()
                if pc.expPoints >= pc.nextLevelExp:
                    pc.doLevelUp()
                pc.getStats()
        elif getChrInput == "move" or  getChrInput == "m" :
            current_tile = generate_tile()
            print(current_tile.tile_content_type)
            if current_tile.tile_content_type == "monster":
                fightLoop(pc, current_tile, gameObj)
            elif current_tile.tile_content_type == "scene":
                print(
                    "you find a scenic path, but nothing of interests catches your eye."
                )
        elif getChrInput == "loot" or getChrInput == "l" :
            if current_tile.tile_content_type == "treasure":
                print("beautiful treasure!")
            print("you look for loot but find none!")
        elif getChrInput == "stats" or getChrInput == "s":
            pc.getStats()
        elif getChrInput == "exit":
            print(f"you arrived to tile number: {current_tile.tile_id}")
            # gameObj.createHighScore(current_tile, pc)
            exit()
        elif getChrInput == "help":
            print("Command list:")
            print("[r]est, [m]ove, [l]oot, [s]tats, exit, [h]elp")
        # enable for faster death!
        # movePenalty(pc)
        # gameObj.clearScreen()
    print("\n\n")
    pc.getStats()
    pc.setDead(current_tile)
    gameObj.createHighScore(current_tile, pc)


def fightLoop(pc, current_tile, gameObj):
    monsterObj = pqMonsters.NPCMonster()
    print(f"Suddenly a {monsterObj.name} appears!")
    current_tile.tile_content = "FIGHT TO THE DEATH"
    print(f"tile content: {current_tile.tile_content}")
    turnCount = 0
    while pc.hitpoints > 0 and monsterObj.hitpoints > 0:
        turnCount += 1
        print(f"Turn Count: {turnCount}")
        fightCommand = input("What is your next Fight Move?")
        if fightCommand == "attack" or fightCommand == "a":
            pc.doAttack(monsterObj)
        elif fightCommand == "magic" or fightCommand == "m":
            if pc.chrClass != "wiz":
                print("You have no magic!")
            else:
                pc.doMagic(monsterObj)
        elif fightCommand == "help":
            gameObj.fightHelp(pc)            
        elif fightCommand == "flee" or fightCommand == "fl":
            if pc.doFlee(monsterObj):
                break
            else:
                print("You're not able to run away!")
                pass
        if monsterObj.hitpoints >0:
            monsterObj.do_attack(pc)
        
    if monsterObj.hitpoints <= 0:
        pc.setExp(monsterObj)
    pass




# print("Main Menu\nType help for a list of commands\n")
# chrCommand = input("")
# while chrCommand != "exit":
#     if chrCommand == "help":
#         gameObj.showHelp()
#         chrCommand = input("Main Menu\nType help for a list of commands\n")
#     elif chrCommand == "stats":
#         pc.getStats()
#         chrCommand = input("Main Menu\nType help for a list of commands\n")
#     elif chrCommand == "play":
#         gameLoop(pc, gameObj)
#         chrCommand = input("Main Menu\nType help for a list of commands\n")
#     else:
#         chrCommand = input("Main Menu\nType help for a list of commands\n")

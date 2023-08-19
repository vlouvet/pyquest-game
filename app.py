import json
import gameHelper
import userCharacter
import pqMonsters
import gameTile
import random
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    race = db.Column(db.String(80))
    chrClass = db.Column(db.String(80))
    strength = db.Column(db.Integer)
    intelligence = db.Column(db.Integer)
    hitpoints = db.Column(db.Integer)
    maxhp = db.Column(db.Integer)
    expPoints = db.Column(db.Integer)
    maxExp = db.Column(db.Integer)
    stealth = db.Column(db.Integer)
    chrLevel = db.Column(db.Integer)
    nextLevelExp = db.Column(db.Integer)
    tiles = db.relationship("Tile", backref="user", lazy=True, uselist=False)

    def __repr__(self):
        return "<User %r>" % self.name


class Tile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(255))
    content = db.Column(db.String(255))
    userId = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    monsterId = db.Column(db.Integer, db.ForeignKey("monster.id"))
    nextTile = db.Column(db.String(255))


class Monster(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    race = db.Column(db.String(255))
    strength = db.Column(db.Integer)
    intelligence = db.Column(db.Integer)
    hitpoints = db.Column(db.Integer)
    stealth = db.Column(db.Integer)
    level = db.Column(db.Integer)
    tiles = db.relationship("Tile", backref="monster", lazy=True, uselist=False)


db.create_all()


@app.route("/play", methods=["GET", "POST"])
def greet_user():
    error = None
    if request.method == "POST":
        print(request.data)
    # the code below is executed if the request method
    # was GET or the credentials were invalid
    return greetHero()


@app.route("/newplayer", methods=["GET", "POST"])
def new_char():
    error = None
    if request.method == "POST":
        req_data = json.loads(request.data.decode("utf-8"))
        newChar = User(
            name=req_data["pc"]["name"],
            strength=10,
            intelligence=10,
            hitpoints=100,
            maxhp=100,
            expPoints=1,
            maxExp=100,
            stealth=10,
            chrLevel=1,
            nextLevelExp=100,
        )
        db.session.add(newChar)
        db.session.commit()
        print(f"User ID: {newChar.id}")
        pc = userCharacter.playerCharacter(newChar.name)
    # the code below is executed if the request method
    # was GET or the credentials were invalid
    return gameIntro(pc)


@app.route("/chooseClass", methods=["GET", "POST"])
def set_raceNclass():
    error = None
    if request.method == "POST":
        req_data = json.loads(request.data.decode("utf-8"))
        chariD = req_data["pc"]["id"]
        current_char = User.query.get(int(chariD))
        current_char.chrClass = req_data["pc"]["chrClass"]
        current_char.race = req_data["pc"]["race"]
        db.session.commit()
        setStats(current_char)
    return charStart(current_char)
    # gameObj = gameHelper.pyquestHelper()


@app.route("/game/tile/<int:tileid>/", methods=["GET", "POST"])
def game_tile(tileid):
    error = None
    if request.method == "GET":
        current_tile = Tile.query.get(tileid)
        if current_tile is None:
            req_data = json.loads(request.data.decode("utf-8"))
            print(req_data)
            if req_data["tile"]["userId"] is not None:
                generate_tile(req_data)
            else:
                return {"statusCode": "Please retry with the correct payload format"}
        return {
            "Tile Content": current_tile.content,
            "Content Type": current_tile.content_type,
            "Next Tile": current_tile.nextTile,
        }


@app.route("/game/fight/<int:tileid>/<int:moveid>/", methods=["GET", "POST"])
def fight_loop(tileid):
    current_tile = Tile.query.get(tileid)
    current_monster = Monster(
        name="elephant",
        race="none",
        strength=1,
        intelligence=1,
        hitpoints=2,
        stealth=1,
        level=1,
        tiles=tileid)
    #monsterObj = pqMonsters.npcMonster(pc.chrLevel)
    #tile_message = f"Suddenly a {current_monster.name} appears!"
    current_tile.tile_content = "FIGHT TO THE DEATH"
    #turnCount = 0
    user_char = User.query.get(current_tile.userId)
    while user_char.hitpoints > 0 and current_monster.hitpoints > 0:
        fightCommand = input("What is your next Fight Move?")
        if fightCommand == "attack" or fightCommand == "a":
            pc.doAttack(monsterObj)
        elif fightCommand == "magic" or fightCommand == "m":
            if pc.chrClass != "wiz":
                print("You have no magic!")
            else:
                pc.doMagic(monsterObj)
        elif fightCommand == "flee" or fightCommand == "fl":
            if pc.doFlee(monsterObj):
                break
            else:
                print("You're not able to run away!")
                pass
        elif fightCommand == "help" or fightCommand == "h":
            gameObj.fightHelp(pc)
        
        if current_monster.hitpoints > 0:
            current_monster.doAttack(user_char)
    if current_monster.hitpoints <= 0:
        user_char.setExp(current_monster)


@app.route("/game/end", methods=["GET"])
def end_game(userid):
    pc.getStats()
    pc.setDead(current_tile)
    gameObj.createHighScore(current_tile, pc)


with open("game_config.ini", "r") as fin:
    config_json = json.load(fin)
tile_config = gameTile.pqGameTile()


def generate_tile(req_data):
    current_tile = Tile(content_type=" ", content=" ")
    current_tile.userId = req_data["tile"]["userId"]
    tile_type_list = ["monster", "sign", "scene"]
    current_tile.content_type = random.choice(tile_type_list)
    treasureFound = random.randint(1, 100)
    db.session.add(current_tile)
    db.session.commit()
    if treasureFound == 4:
        current_tile.content_type = "treasure"
    if current_tile.content_type == "scene":
        current_tile.content = (
            "you find a scenic path, but nothing of interests catches your eye."
        )
        current_tile.nextTile = f"/game/tile/{current_tile.id+1}/"
    elif current_tile.content_type == "sign":
        current_tile.content = "there is a sign here!"
        current_tile.nextTile = f"/game/tile/{current_tile.id+1}/"
    elif current_tile.content_type == "monster":
        current_tile.content = "Monster!"
        current_tile.nextTile = f"/game/fight/{current_tile.id+1}/"
    elif current_tile.content_type == "treasure":
        current_tile.nextTile = f"/game/tile/{current_tile.id+1}/"
        current_tile.content = "beautiful treasure!"
    db.session.add(current_tile)
    db.session.commit()


def greetHero():
    greet_message = "Hello Weary traveler, I think I've seen you before.\n"
    greet_message += "What was your name again?"
    # while pc.name == "" or pc.name == "player1":
    #     pc.setName()
    return {"greet_message": greet_message, "next_page": "newplayer"}


def movePenalty(pc):
    pc.hitpoints = pc.hitpoints - 1


def gameIntro(pc):
    intro_message = "Welcome to Pyquest!"
    intro_message += "the story begins on a cold dark night..."
    intro_message += f"our hero, {pc.name}, goes out looking for adventure..."
    intro_message += "when suddenly!"

    return {"intro_message": intro_message, "next_page": "chooseClass"}


def charStart(pc):
    # CharacterMessage = pc.getStats()
    CharacterMessage = "test"
    return {"charMessage": CharacterMessage, "next_page": "/game/tile/1"}


def gameLoop(pc, gameObj):
    # pc.setStats()
    while pc.hitpoints is not None and pc.hitpoints > 0:
        getChrInput = input("What to do Next?")
        if getChrInput == "rest" or getChrInput == "r":
            if pc.hitpoints < pc.maxhp:
                print(f"Currently Have {pc.hitpoints} out of {pc.maxhp} hitpoints")
                pc.doRestHP()
                if pc.expPoints >= pc.nextLevelExp:
                    pc.doLevelUp()
                pc.getStats()
        elif getChrInput == "move" or getChrInput == "m":
            print(current_tile.tile_content_type)
            if current_tile.tile_content_type == "monster":
                fightLoop(pc, current_tile)
            elif current_tile.tile_content_type == "scene":
                print(
                    "you find a scenic path, but nothing of interests catches your eye."
                )
        elif getChrInput == "loot" or getChrInput == "l":
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


def setStats(User):
    # start by setting all stats to default values
    User.strength = 10
    User.intelligence = 10
    User.maxhp = 100
    User.stealth = 10
    User.expPoints = 1
    # elves are weak, smart, and stealth
    if User.race == "elf":
        User.strength -= 5
        User.intelligence += 5
        User.stealth += 5
        User.maxhp = 80
    # Hobbits are midly strong, midly smart, but stealthy
    elif User.race == "hbt":
        User.strength += 2
        User.intelligence -= 1
        User.stealth += 5
        User.maxhp = 100
    # Kajit are strong, dumb, but stealthy
    elif User.race == "kjt":
        User.strength += 5
        User.intelligence -= 5
        User.stealth += 5
        User.maxhp = 120
    # wizards are smart, but gain no strength or stealth bonus
    if User.chrClass == "wiz":
        # hero['stats']['str'] -= 5
        User.intelligence += 5
        # hero['stats']['stl'] += 5
        User.maxhp = User.maxhp * 0.9
    # paladins are midly strong, and midly smart but lack in stealth
    elif User.chrClass == "pldn":
        User.strength += 2
        User.intelligence += 2
        User.stealth -= 5
        User.maxhp = User.maxhp * 1.25
    # Warriors are strong, dumb, and not sneaky. but strong.
    elif User.chrClass == "warr":
        User.strength += 5
        User.intelligence -= 5
        User.stealth -= 5
        User.maxhp = User.maxhp * 1.5
    User.hitpoints = User.maxhp
    db.session.commit()

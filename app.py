import json
import random
from flask import Flask, request, render_template, redirect, url_for

import model
import userCharacter
import gameforms
import pqMonsters
import gameTile



def create_app():
    # create the extension
    
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "7"
    # configure the SQLite database, relative to the app instance folder
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
    # initialize the app with the extension
    model.db.init_app(app)
    with app.app_context():
        model.db.create_all()
        
    @app.route("/play", methods=["POST", "GET"])
    def greet_user():
        form = gameforms.NameForm()
        if request.method == "POST":
            #if form.validate_on_submit():
            new_user = model.User()
            new_user.username = form.name.data
            model.db.session.add(new_user)
            model.db.session.commit()
            return redirect(url_for("setup_char", id=new_user.id))
        else:
            # the code below is executed if the request method
            # was GET or the credentials were invalid
            # greet_hero()
            return render_template("playgame.html", form=form)


    @app.route("/player/<int:id>/setup", methods=["POST", "GET"])
    def setup_char(id):
        user_profile = model.User.query.get(id)
        form = gameforms.CharacterForm(obj=user_profile)
        # TODO: pre-populate the form with the data from database
        if request.method == "POST":
            form.populate_obj(user_profile)
            model.db.session.add(user_profile)
            model.db.session.commit()
            print("profile saved")
            return redirect(url_for("char_start", id=user_profile.id))
        else:
            return render_template("charsetup.html", player_char=user_profile, form=form)


    @app.route("/player/<int:id>/start", methods=["POST","GET"])
    def char_start(id):
        #TODO: query db to get user profile
        char_message = "test message"#player_char.getStats()
        return render_template("charStart.html", charMessage=char_message, next_page="/tile/1")

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
        return {"greet_message": greet_message}


    def move_penalty(player_char):
        player_char.hitpoints = player_char.hitpoints - 1


    def game_intro(player_char):
        intro_message = "Welcome to Pyquest!"
        intro_message += "the story begins on a cold dark night..."
        intro_message += f"our hero, {player_char.name}, goes out looking for adventure..."
        intro_message += "when suddenly!"

        return {"intro_message": intro_message, "next_page": "set_raceNclass"}





    def game_loop(player_char, game_obj):
        player_char.setStats()
        current_tile = generate_tile()
        while player_char.hitpoints is not None and player_char.hitpoints > 0:
            char_input = input("What to do Next?")
            if char_input == "rest" or char_input == "r":
                if player_char.hitpoints < player_char.maxhp:
                    print(
                        """Currently Have {player_char.hitpoints}
                    out of {player_char.maxhp} hitpoints"""
                    )
                    player_char.doRestHP()
                    if player_char.expPoints >= player_char.nextLevelExp:
                        player_char.doLevelUp()
                    player_char.getStats()
            elif char_input == "move" or char_input == "m":
                current_tile = generate_tile()
                print(current_tile.tile_content_type)
                if current_tile.tile_content_type == "monster":
                    fight_loop(player_char, current_tile, game_obj)
                elif current_tile.tile_content_type == "scene":
                    print(
                        "you find a scenic path, but nothing of interests catches your eye."
                    )
            elif char_input == "loot" or char_input == "l":
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
            if monster_obj.hitpoints > 0:
                monster_obj.do_attack(player_char)

        if monster_obj.hitpoints <= 0:
            player_char.setExp(monster_obj)
            
    if __name__ == "__main__":
        with open("game_config.ini", "r") as fin:
            config_json = json.load(fin)
        tile_config = gameTile.pqGameTile()
        app.run()

    return app


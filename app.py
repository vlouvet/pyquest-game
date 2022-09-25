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
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pyquest_game.db"
    # initialize the app with the extension
    model.db.init_app(app)
    with app.app_context():
        model.db.create_all()
        model.init_defaults()

    @app.route("/", methods=["POST", "GET"])
    def greet_user():
        form = gameforms.UserNameForm()
        if request.method == "POST":
            if form.validate_on_submit():
                new_user = model.User()
                new_user.username = form.username.data
                # TODO: confirm that this user doesn't already exist in the database
                # (deduplicate on email)
                model.db.session.add(new_user)
                model.db.session.commit()
            else:
                print("Form did not validate!")
                print(form.errors)
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
        form.charclass.choices = [
                (PlayerClass.id, PlayerClass.name)
                for PlayerClass in model.PlayerClass.query.order_by("name")
            ]
        form.charrace.choices = [
                (PlayerRace.id, PlayerRace.name)
                for PlayerRace in model.PlayerRace.query.order_by("name")
            ]    
        # TODO: pre-populate the form with the data from database
        if request.method == "POST":
            form.populate_obj(user_profile)
            # TODO: move this code into a tile_init() function
            current_tile = model.Tile()
            tile_type_list = [
                (tile_type.name)
                for tile_type in model.TileTypeOption.query.order_by("name")
            ]
            form = gameforms.TileForm()
            form.type.data = random.choice(tile_type_list)
            model.db.session.add(current_tile)
            model.db.session.commit()
            # End tile_init() code
            user_profile.current_tile = current_tile.id
            model.db.session.add(user_profile)
            model.db.session.commit()
            print("profile saved")
            return redirect(url_for("char_start", id=user_profile.id))
        elif request.method == "GET":
            return render_template(
                "charsetup.html", player_char=user_profile, form=form
            )

    @app.route("/player/<int:id>/start", methods=["POST", "GET"])
    def char_start(id):
        # TODO: query db to get user profile
        char_message = "This is a test message to be displayed when the player first starts the game"
        # player_char.getStats()
        return render_template(
            "charStart.html", charMessage=char_message, player_char_id=id)

    @app.route("/player/<int:id>/game/tile/next", methods=["POST", "GET"])
    def generate_tile(id):
        user_profile = model.User.query.get(id)
        tile_details = model.Tile.query.get(user_profile.current_tile)
        # TODO: handle tile_details being null/empty
        form = gameforms.TileForm(obj=tile_details)
        tile_type_list = [
            (tile_type.name)
            for tile_type in model.TileTypeOption.query.order_by("name")
        ]
        form.type.data = random.choice(tile_type_list)

        form.tileaction.choices = [
            (tileaction.id, tileaction.name)
            for tileaction in model.ActionOption.query.order_by("name")
        ]
        # if the request was a POST, generate a new tile then display it using gameTile.html
        if request.method == "POST":
            # start tile_init() code
            current_tile = model.Tile()
            current_tile.type = random.choice(tile_type_list)
            print(f"tileaction: {form.tileaction.data}")
            model.db.session.add(current_tile)
            model.db.session.commit()
            if form.tileaction.data:
                current_tile.action = form.tileaction.data
                # TODO: create a new action record
                currentAction = model.Action()
                # TODO: assign action record to tile
                currentAction.tile = current_tile.id
                # TODO: assign action record details
                currentAction.name = current_tile.action
                # TODO: add and commit action record to db
                model.db.session.add(currentAction)
                model.db.session.commit()
                print(f"action ID:{currentAction.id}")
                print(f"action tile id: {currentAction.tile}")
            user_profile.current_tile = current_tile.id
            model.db.session.add(user_profile)
            model.db.session.commit()
            # end tile_init() code
        return render_template("gameTile.html", player_char=user_profile, form=form)

    @app.route(
        "/player/<int:playerid>/game/tile/<int:tileid>/action/<int:actionID>",
        methods=["POST", "GET"],
    )
    def execute_tile_action(playerid, tileid, actionID):
        tile_record = model.Tile.query.get(tileid)
        tileForm = gameforms.TileForm(obj=tile_record)
        print(f"Tile's action ID: {tile_record.action}")
        if request.method == "POST":
            # validate actionID, return error message if not valid
            if actionID not in [1, 2, 3, 4]:
                return {"Error": "Bad action selected"}
            action_record = model.Action.query.filter_by(id=tileid).first()
            # validate that tile is still 'action-able', meaning it hasn't been 'actioned' yet.
            print(f"Action_record ID: {action_record.id}")
            if not action_record.valid == True:
                return {"Error": "tile has already been actioned"}
            # handle rest
            if actionID == 1:  # if requested action is to rest..
                if tileForm.tilecontent not in [
                    3
                ]:  # if the current tile doesn't have a monster
                    tile_record.action = 1
                    player_record = model.Player.query.get(id=playerid)
                    player_record.hitpoints += 10
                    model.db.session.add(tile_record)
                    model.db.session.add(player_record)
                    model.db.session.commit()
                    # TODO: return JSON blob to be parsed by tile route
            # handle inspect for items/treasure
            # handle fight monster
            if actionID == 3:  # if requested action is to rest..
                if tileForm.tilecontent == 3:  # if the current tile has a monster
                    tile_record.action = 3  # save the action to the tile
                    player_record = model.Player.query.get(
                        id=playerid
                    )  # get the player from the db
                    # TODO: handle actual fight logic here
                    model.db.session.add(tile_record)  # add the tile to the session
                    model.db.session.add(
                        player_record
                    )  # add the player record to the session
                    model.db.session.commit()  # save the results to the db
                    # TODO: return JSON blob to be parsed by tile route
            # handle flee from tile

            pass

    # def game_loop(player_char, game_obj):
    #     player_char.setStats()
    #     current_tile = generate_tile()
    #     while player_char.hitpoints is not None and player_char.hitpoints > 0:
    #         char_input = input("What to do Next?")
    #         if char_input == "rest" or char_input == "r":
    #             if player_char.hitpoints < player_char.maxhp:
    #                 print(
    #                     """Currently Have {player_char.hitpoints}
    #                 out of {player_char.maxhp} hitpoints"""
    #                 )
    #                 player_char.doRestHP()
    #                 if player_char.expPoints >= player_char.nextLevelExp:
    #                     player_char.doLevelUp()
    #                 player_char.getStats()
    #         elif char_input == "move" or char_input == "m":
    #             current_tile = generate_tile()
    #             print(current_tile.tile_content_type)
    #             if current_tile.tile_content_type == "monster":
    #                 fight_loop(player_char, current_tile, game_obj)
    #             elif current_tile.tile_content_type == "scene":
    #                 print(
    #                     "you find a scenic path, but nothing of interests catches your eye."
    #                 )
    #         elif char_input == "loot" or char_input == "l":
    #             if current_tile.tile_content_type == "treasure":
    #                 print("beautiful treasure!")
    #             print("you look for loot but find none!")
    #         elif char_input == "stats" or char_input == "s":
    #             player_char.getStats()
    #         elif char_input == "exit":
    #             print(f"you arrived to tile number: {current_tile.tile_id}")
    #             # gameObj.createHighScore(current_tile, pc)
    #             exit()
    #         elif char_input == "help":
    #             print("Command list:")
    #             print("[r]est, [m]ove, [l]oot, [s]tats, exit, [h]elp")
    #         # enable for faster death!
    #         # movePenalty(pc)
    #         # gameObj.clearScreen()
    #     print("\n\n")
    #     player_char.getStats()
    #     player_char.setDead(current_tile)
    #     game_obj.createHighScore(current_tile, player_char)

    # def fight_loop(player_char, current_tile, game_obj):
    #     monster_obj = pqMonsters.NPCMonster()
    #     print(f"Suddenly a {monster_obj.name} appears!")
    #     current_tile.tile_content = "FIGHT TO THE DEATH"
    #     print(f"tile content: {current_tile.tile_content}")
    #     turn_count = 0
    #     while player_char.hitpoints > 0 and monster_obj.hitpoints > 0:
    #         turn_count += 1
    #         print(f"Turn Count: {turn_count}")
    #         fight_command = input("What is your next Fight Move?")
    #         if fight_command == "attack" or fight_command == "a":
    #             player_char.doAttack(monster_obj)
    #         elif fight_command == "magic" or fight_command == "m":
    #             if player_char.chrClass != "wiz":
    #                 print("You have no magic!")
    #             else:
    #                 player_char.doMagic(monster_obj)
    #         elif fight_command == "help":
    #             game_obj.fightHelp(player_char)
    #         elif fight_command == "flee" or fight_command == "fl":
    #             if player_char.doFlee(monster_obj):
    #                 break
    #             else:
    #                 print("You're not able to run away!")
    #         if monster_obj.hitpoints > 0:
    #             monster_obj.do_attack(player_char)

    #     if monster_obj.hitpoints <= 0:
    #         player_char.setExp(monster_obj)

    if __name__ == "__main__":
        with open("game_config.ini", "r") as fin:
            config_json = json.load(fin)
        tile_config = gameTile.pqGameTile()
        app.run()

    return app

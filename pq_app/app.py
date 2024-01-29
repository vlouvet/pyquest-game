import json
import random
from flask import Flask, request, render_template, redirect, url_for, flash

from . import model, userCharacter, gameforms, pqMonsters, gameTile

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
                # deduplicate the user based on username
                user_exists = model.user_exists(new_user.username)
                
                user_exists = False
                if not model.user_exists(new_user.username):
                    model.db.session.add(new_user)
                    model.db.session.commit()

                else:
                    flash("That user is already taken!")
                    return render_template("playgame.html", form=form)
            else:
                print("Form did not validate!")
                print(form.errors)
            return redirect(url_for("setup_char", playerid=new_user.id))
        else:
            # the code below is executed if the request method
            # was GET or the credentials were invalid
            # greet_hero()
            return render_template("playgame.html", form=form)

    @app.route("/player/<int:playerid>/setup", methods=["POST", "GET"])
    def setup_char(playerid):
        user_profile = model.User.query.get(playerid)
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
                {"name": tile_type.name, "id": tile_type.id}
                for tile_type in model.TileTypeOption.query.order_by("name")
            ]
            form = gameforms.TileForm()
            tile_type = random.choice(tile_type_list)
            form.type.data = tile_type["name"]
            current_tile.user_id = playerid
            current_tile.type = tile_type["id"]
            user_profile.hitpoints = 100
            model.db.session.add(current_tile)
            model.db.session.commit()
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
            "charStart.html", charMessage=char_message, player_char_id=id
        )

    @app.route("/player/<int:player_id>/game/tile/next", methods=["POST", "GET"])
    def generate_tile(player_id):
        user_profile = model.User.query.get(player_id)
        tile_details = (
            model.Tile.query.filter_by(user_id=player_id)
            .order_by(model.Tile.id.desc())
            .first()
        )
        print(f"Queried tile details: {tile_details.id}")
        if tile_details:
            form = gameforms.TileForm(obj=tile_details)
            print(f"Form TileId: {form.tileid}")
            #log form tileid to debug logging:
            app.logger.debug(f"Form TileId: {form.tileid}")
        else:
            print("Tile details empty")
            return {"Error": "Tile details empty"}
        form.tileid = tile_details.id
        
        tile_type_list = [
            {"name": tile_type.name, "id": tile_type.id}
            for tile_type in model.TileTypeOption.query.order_by("name")
        ]
        print(f"Tile_type_List: {tile_type_list}")
        form.type.data = random.choice(tile_type_list)["name"]

        form.tileaction.choices = [
            (tileaction.id, tileaction.name)
            for tileaction in model.ActionOption.query.order_by("name")
        ]
        # if the request was a POST, generate a new tile then display it using gameTile.html
        if request.method == "POST":
            if not tile_details.action_taken:
                return {"Error": "Please action this tile before continuing!"}
            # start tile_init() code
            current_tile = model.Tile()
            current_tile.type = random.choice(tile_type_list)["id"]
            current_tile.user_id = player_id
            if form.tileaction.data:
                current_tile.action = form.tileaction.data
            else:
                print("current tile has no action data!")
            model.db.session.add(current_tile)
            model.db.session.commit()
            model.db.session.add(user_profile)
            model.db.session.commit()
        return render_template("gameTile.html", player_char=user_profile, form=form)

    @app.route(
        "/player/<int:playerid>/game/tile/<int:tileid>/action",
        methods=["POST", "GET"],
    )
    def execute_tile_action(playerid, tileid):
        tile_record = model.Tile.query.get(tileid)
        tileForm = gameforms.TileForm(obj=tile_record)
        action_type_ID = tileForm.data.get("tileaction")
        if request.method == "POST":
            # validate actionID, return error message if not valid
            if action_type_ID not in [1, 2, 3, 4]:
                return {"Error": "Bad action selected"}
            action_record = model.Action.query.filter_by(
                tile=tileid, actionverb=action_type_ID
            ).first()
            if action_record:
                print(f"Action_record ID: {action_record.id}")
            if tile_record.action_taken == True:
                return {"Error": "tile has already been actioned"}
            # handle rest
            player_record = model.User.query.get(playerid)
            print(f"Player_id: {player_record.id}")
            if action_type_ID == 1:  # if requested action is to rest..
                tile_record.action = 1
                player_record.hitpoints += 10
            if action_type_ID == 3:  # if requested action is to fight..
                tile_record.action = 3  # save the action to the tile
            tile_record.user_id = player_record.id
            tile_record.action_taken = True
            model.db.session.add(tile_record)
            model.db.session.add(player_record)
            model.db.session.commit()
            # handle flee from tile
            return {"status_code": 200, "data": "success"}
        else:
            return {
                "status_code": 200,
                "data": {
                    "tile_action": tile_record.action,
                    "action_taken": tile_record.action_taken,
                    "user_id": tile_record.user_id,
                },
            }

    @app.route("/player/<int:id>/profile", methods=["GET"])
    def get_user_profile(id):
        pass

    if __name__ == "__main__":
        with open("game_config.ini", "r") as fin:
            config_json = json.load(fin)
        tile_config = gameTile.pqGameTile()
        app.run()

    return app

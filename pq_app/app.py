import json
import random
import random
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from . import model, userCharacter, gameforms, pqMonsters, gameTile


def create_app():
    # create the extension
    app = Flask(__name__)
    # set the secret key for the session to a random string
    app.config["SECRET_KEY"] = random.randbytes(24).hex()
    # configure the SQLite database, relative to the app instance folder
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pyquest_game.db"
    # initialize the app with the extension
    model.db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"
    with app.app_context():
        model.db.create_all()
        model.init_defaults()

    @login_manager.user_loader
    def load_user(user_id):
        return model.User.query.get(int(user_id))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        form = gameforms.RegisterForm()
        if form.validate_on_submit():
            hashed_password = generate_password_hash(
                form.password.data, method="pbkdf2:sha256"
            )
            new_user = model.User(
                username=form.username.data, password_hash=hashed_password
            )
            model.db.session.add(new_user)
            model.db.session.commit()
            flash("Registration successful! Please log in.")
            return redirect(url_for("login"))
        return render_template("register.html", form=form)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        form = gameforms.LoginForm()
        if form.validate_on_submit():
            user = model.User.query.filter_by(username=form.username.data).first()
            if user and check_password_hash(user.password_hash, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for("greet_user"))
            else:
                flash("Login unsuccessful. Please check your username and password.")
        return render_template("login.html", form=form)

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You have been logged out.")
        return redirect(url_for("login"))

    @app.route("/", methods=["POST", "GET"])
    @login_required
    def greet_user():
        form = gameforms.UserNameForm()
        if request.method == "POST":
            if form.validate_on_submit():
                new_user = (
                    model.User().query.filter_by(username=form.username.data).first()
                )
                return redirect(url_for("setup_char", player_id=new_user.id))
        return render_template("playgame.html", form=form)

    @app.route("/player/<int:player_id>/setup", methods=["POST", "GET"])
    @login_required
    def setup_char(player_id):
        user_profile = model.User.query.get_or_404(player_id)
        user_profile_id = user_profile.id
        form = gameforms.CharacterForm(obj=user_profile)
        form.charclass.choices = [
            (PlayerClass.id, PlayerClass.name)
            for PlayerClass in model.PlayerClass.query.order_by("name")
        ]
        form.charrace.choices = [
            (PlayerRace.id, PlayerRace.name)
            for PlayerRace in model.PlayerRace.query.order_by("name")
        ]
        if request.method == "POST":
            # TODO: pre-populate the form with the data from database
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
            current_tile.user_id = user_profile_id
            current_tile.type = tile_type["id"]
            user_profile.hitpoints = 100
            model.db.session.add(current_tile)
            model.db.session.commit()
            model.db.session.add(user_profile)
            model.db.session.commit()
            print("profile saved")
            return redirect(url_for("char_start", id=user_profile_id))
        elif request.method == "GET":
            return render_template(
                "charsetup.html", player_char=user_profile, form=form
            )
        else:
            return {"Error": "Invalid request method"}

    @app.route("/player/<int:id>/start", methods=["POST", "GET"])
    @login_required
    def char_start(id):
        # TODO: query db to get user profile
        user_profile = model.User.query.get_or_404(id)
        char_message = "This is a test message to be displayed when the player first starts the game"
        return render_template(
            "charStart.html", charMessage=char_message, player_char_id=user_profile.id
        )

    # route for the current tile, using a short url like /play that can be
    # easily accessed by a user that is logged in
    @app.route("/player/<int:player_id>/play", methods=["POST", "GET"])
    @login_required
    def get_tile(player_id):
        user_profile = model.User.query.get(player_id)
        tile_details = (
            model.Tile.query.filter_by(user_id=player_id)
            .order_by(model.Tile.id.desc())
            .first()
        )
        if tile_details:
            form = gameforms.TileForm(obj=tile_details)
        else:
            return redirect(url_for("generate_tile", player_id=player_id))
        form.tileid = tile_details.id
        form.type.data = tile_details.type
        if tile_details.type == "sign":
            form.tilecontent.data = tile_config.generate_signpost()
        if tile_details.type == "monster":
            monster = pqMonsters.NPCMonster()
            form.tilecontent.data = monster.name
        if tile_details.type == "scene":
            form.tilecontent.data = "This is a scene tile"
        if tile_details.type == "treasure":
            form.tilecontent.data = "This is a treasure tile"
        form.tileaction.choices = [
            (tileaction.id, tileaction.name)
            for tileaction in model.ActionOption.query.order_by("name")
        ]
        return render_template("gameTile.html", player_char=user_profile, form=form)

    @app.route("/player/<int:player_id>/game/tile/next", methods=["POST", "GET"])
    @login_required
    def generate_tile(player_id):
        user_profile = model.User.query.get(player_id)
        # save the posted form to a var
        tile_details = gameforms.TileForm()
        # get the tile type list
        tile_type_list = [
            {"name": tile_type.name, "id": tile_type.id}
            for tile_type in model.TileTypeOption.query.order_by("name")
        ]
        # generate a new tile object
        if not tile_details.tileaction:
            # re-render the gameTile template and flash an error message reminding the user to action the tile
            flash("Please action this tile before continuing!")
            return render_template(
                "gameTile.html",
                player_char=user_profile,
                form=tile_details,
                errors=tile_details.errors,
            )
        # generate the NEXT tile details
        current_tile = model.Tile()
        current_tile.type = random.choice(tile_type_list)["id"]
        current_tile.user_id = player_id
        if tile_details.tileaction.data:
            current_tile.action = tile_details.tileaction.data
        else:
            print("current tile has no action data!")
        if request.method == "POST":
            model.db.session.add(current_tile)
            model.db.session.commit()
            model.db.session.add(user_profile)
            model.db.session.commit()
        tile_details = (model.Tile.query.filter_by(user_id=player_id).order_by(model.Tile.id.desc()).first())
        tile_details.tileid = tile_details.id
        return render_template("gameTile.html", player_char=user_profile, form=tile_details)


    @app.route("/player/<int:playerid>/game/tile/<int:tileid>/action", methods=["POST"])
    @login_required
    def execute_tile_action(playerid, tileid):
        tile_record = model.Tile.query.get(tileid)
        tileForm = gameforms.TileForm(obj=tile_record)
        action_type_ID = tileForm.data.get("tileaction")
        if request.method == "POST":
            # validate actionID is in the list of valid actions table
            if not action_type_ID:
                return {"Error": "No action selected"}
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
            # return the generate tile function to display the next tile
            return redirect(url_for("generate_tile", player_id=playerid))
            # return {"status_code": 200, "data": "success"}
        else:
            return {
                "status_code": 402,
            }

    @app.route("/player/<int:player_id>/profile", methods=["GET"])
    @login_required
    def get_user_profile(player_id):
        user_profile = model.User.query.get_or_404(player_id)
        # if user is logged in, get the user profile
        if not user_profile:
            return redirect(url_for("greet_user"))
        return render_template("profile.html", player_char=user_profile)


    # get history
    @app.route("/player/<int:player_id>/game/history", methods=["GET"])
    @login_required
    def get_history(player_id):
        # get current logged in user profile
        user_profile = model.User.query.get(player_id)
        tile_history = model.Tile.query.filter_by(user_id=player_id).all()
        return render_template("gameHistory.html", player_char=user_profile, history=tile_history)

    if __name__ == "__main__":
        with open("game_config.ini", "r") as fin:
            config_json = json.load(fin)
        tile_config = gameTile.pqGameTile()
        # run the app with debuggin enabled
        app.run(debug=True)

    return app

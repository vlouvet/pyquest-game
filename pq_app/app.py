import random
from typing import cast
from datetime import datetime, timezone
from flask import Blueprint, request, render_template, redirect, url_for, flash, abort, jsonify
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from . import model, gameforms, pqMonsters, gameTile
from sqlalchemy import select

# Create Blueprint
main_bp = Blueprint("main", __name__)


@main_bp.route("/register", methods=["GET", "POST"])
def register():
    form = gameforms.RegisterForm()
    if form.validate_on_submit():
        # Prevent duplicate usernames (unique constraint at DB level otherwise raises IntegrityError)
        existing = model.User.query.filter_by(username=form.username.data).first()
        if existing:
            flash("Username already taken. Please choose another.")
            return render_template("register.html", form=form)
        # form.password.data is typed as Optional[str]; cast to str for the password-hash helper
        hashed_password = generate_password_hash(cast(str, form.password.data), method="pbkdf2:sha256")
        new_user = model.User(username=form.username.data, password_hash=hashed_password)
        model.db.session.add(new_user)
        model.db.session.commit()
        flash("Registration successful! Please log in.")
        return redirect(url_for("main.login"))
    return render_template("register.html", form=form)


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    form = gameforms.LoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            user = model.User.query.filter_by(username=form.username.data).first()
            # form.password.data can be Optional[str]; cast to str for the checker
            if user and check_password_hash(user.password_hash, cast(str, form.password.data)):
                login_user(user, remember=form.remember.data)
                return redirect(url_for("main.greet_user"))
            else:
                flash("Login unsuccessful. Please check your username and password.")
        # Always render the login page after POST (whether validation passed or not)
        return render_template("login.html", form=form)
    # For GET and other methods, render the login template
    return render_template("login.html", form=form)


@main_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("main.login"))


@main_bp.route("/", methods=["GET"])
@login_required
def greet_user():
    """Home route - redirects user based on their setup status."""
    # Check if user has completed character setup
    if current_user.playerclass and current_user.playerrace:
        # User is set up, check if they have an active playthrough
        active_play = model.Playthrough.query.filter_by(user_id=current_user.id, ended_at=None).first()
        if active_play:
            return redirect(url_for("main.get_tile", player_id=current_user.id))
        # If no active playthrough, present dashboard allowing user to start a new journey
        user_tiles_exist = model.Tile.query.filter_by(user_id=current_user.id).first() is not None
        start_form = gameforms.RestartForm()
        return render_template("dashboard.html", player_char=current_user, has_tiles=user_tiles_exist, start_form=start_form)
    else:
        # User needs character setup
        return redirect(url_for("main.setup_char", player_id=current_user.id))


@main_bp.route("/player/<int:player_id>/setup", methods=["POST", "GET"])
@login_required
def setup_char(player_id):
    # Authorization check
    if current_user.id != player_id:
        abort(403)

    user_profile = model.db.session.get(model.User, player_id)
    if not user_profile:
        abort(404)

    # Check if player is dead (except during restart)
    if user_profile.hitpoints <= 0 and user_profile.playerclass:
        return redirect(url_for("main.game_over", player_id=player_id))
    user_profile_id = user_profile.id
    form = gameforms.CharacterForm(obj=user_profile)
    form.charclass.choices = [
        (PlayerClass.id, PlayerClass.name) for PlayerClass in model.PlayerClass.query.order_by("name")
    ]
    form.charrace.choices = [(PlayerRace.id, PlayerRace.name) for PlayerRace in model.PlayerRace.query.order_by("name")]
    tile_type_list = [
        {"name": tile_type.name, "id": tile_type.id} for tile_type in model.TileTypeOption.query.order_by("name")
    ]
    tile_type = random.choice(tile_type_list)
    if request.method == "POST":
        # Manually set playerclass and playerrace from form data
        user_profile.playerclass = form.charclass.data
        user_profile.playerrace = form.charrace.data

        # if no tile exists for this user, create a tile
        if not model.Tile.query.filter_by(user_id=user_profile_id).first():
            # create a new playthrough for this user and the initial tile
            new_play = model.Playthrough(user_id=user_profile_id)
            model.db.session.add(new_play)
            model.db.session.flush()

            current_tile = model.Tile()
            current_tile.user_id = user_profile_id
            current_tile.type = tile_type["id"]
            current_tile.playthrough_id = new_play.id
            model.db.session.add(current_tile)
        form = gameforms.TileForm()
        form.type.data = tile_type["name"]
        user_profile.hitpoints = 100
        model.db.session.add(user_profile)
        model.db.session.commit()
        print("profile saved")
        return redirect(url_for("main.char_start", id=user_profile_id))
    elif request.method == "GET":
        return render_template("charsetup.html", player_char=user_profile, form=form)
    else:
        return {"Error": "Invalid request method"}


@main_bp.route("/player/<int:id>/start", methods=["POST", "GET"])
@login_required
def char_start(id):
    # Authorization check
    if current_user.id != id:
        abort(403)
    # TODO: query db to get user profile
    user_profile = model.db.session.get(model.User, id)
    if not user_profile:
        abort(404)

    # Check if player is dead
    if not user_profile or not user_profile.is_alive:
        return redirect(url_for("main.game_over", player_id=id))
    char_message = "This is a test message to be displayed when the player first starts the game"
    return render_template("charStart.html", charMessage=char_message, player_char_id=user_profile.id)


# route for the current tile, using a short url like /play that can be
# easily accessed by a user that is logged in
@main_bp.route("/player/<int:player_id>/play", methods=["GET"])
@login_required
def get_tile(player_id):
    # Authorization check
    if current_user.id != player_id:
        abort(403)

    user_profile = model.db.session.get(model.User, player_id)
    if not user_profile:
        abort(404)

    # Check if player is dead before showing tile
    if not user_profile.is_alive:
        return redirect(url_for("main.game_over", player_id=player_id))

    tile_config = gameTile.pqGameTile()
    tile_details = model.Tile.query.filter_by(user_id=player_id).order_by(model.Tile.id.desc()).first()
    if not tile_details:
        # No tile found for this player; redirect to setup so a tile can be created
        flash("No tile found for this player; please set up your character or generate a tile.")
        return redirect(url_for("main.setup_char", player_id=player_id))
    form = gameforms.TileForm(obj=tile_details)
    # populate the hidden/read-only tile id into the field data so templates can read it
    form.tileid.data = str(tile_details.id)
    # set the form type data to the name value from the TileTypeOption table using tile_details.type as a foreign key
    tile_type_obj = model.db.session.get(model.TileTypeOption, tile_details.type)
    form.type.data = tile_type_obj.name if tile_type_obj else None
    if form.type.data == "sign":
        form.content.data = tile_config.generate_signpost()
    elif form.type.data == "monster":
        monster = pqMonsters.NPCMonster()
        form.content.data = monster.name
    elif form.type.data == "scene":
        form.content.data = "This is a scene tile"
    elif form.type.data == "treasure":
        form.content.data = "This is a treasure tile"
    # if the tile_details exists check if action taken
    # if tile action_taken is not null, render the tile details in read only form
    if tile_details and tile_details.action_taken:
        # set the form action choices to the action option selected for this tile record
        form.action.choices = [
            (action_option.code or str(action_option.id), action_option.name)
            for action_option in model.ActionOption.query.join(
                model.Action, model.Action.actionverb == model.ActionOption.id
            )
            .filter(model.Action.tile == tile_details.id)
            .order_by(model.ActionOption.name)
        ]
        return render_template("gameTile.html", player_char=user_profile, form=form, readonly=True)
    form.action.choices = [
        (tileaction.code or str(tileaction.id), tileaction.name)
        for tileaction in model.ActionOption.query.order_by(model.ActionOption.name)
    ]
    return render_template("gameTile.html", player_char=user_profile, form=form)


@main_bp.route("/player/<int:player_id>/game/tile/next", methods=["POST", "GET"])
@login_required
def generate_tile(player_id):
    # Authorization check
    if current_user.id != player_id:
        abort(403)

    user_profile = model.db.session.get(model.User, player_id)
    if not user_profile:
        abort(404)

    # Check if player is dead
    if not user_profile.is_alive:
        return redirect(url_for("main.game_over", player_id=player_id))
    # get last tile record for the user
    tile_record = model.Tile.query.filter_by(user_id=player_id).order_by(model.Tile.id.desc()).first()
    # if no tile record exists, redirect to the tile page which will handle prompting setup
    if not tile_record:
        return redirect(url_for("main.get_tile", player_id=player_id))
    # if the tile has not been actioned redirect to that tile page
    if not tile_record.action_taken:
        return redirect(url_for("main.get_tile", player_id=player_id))

    # At this point the previous tile was actioned; generate a fresh tile for the player (GET)
    tile_type_list = [
        {"name": tile_type.name, "id": tile_type.id} for tile_type in model.TileTypeOption.query.order_by(model.TileTypeOption.name)
    ]

    current_tile = model.Tile()
    current_tile.type = random.choice(tile_type_list)["id"]
    current_tile.user_id = player_id
    # preserve playthrough from previous tile when generating the next tile
    current_tile.playthrough_id = tile_record.playthrough_id

    model.db.session.add(current_tile)
    model.db.session.commit()

    # Prepare the form for the newly-created tile
    tile_details = gameforms.TileForm(obj=current_tile)
    # populate the hidden/read-only tile id into the field data so templates can read it
    tile_details.tileid.data = str(current_tile.id)
    tile_type_obj = model.db.session.get(model.TileTypeOption, current_tile.type)
    tile_details.type.data = tile_type_obj.name if tile_type_obj else None
    tile_details.action.choices = [
        (tileaction.code or str(tileaction.id), tileaction.name)
        for tileaction in model.ActionOption.query.order_by(model.ActionOption.name)
    ]

    return render_template("gameTile.html", player_char=user_profile, form=tile_details)



@main_bp.route("/player/<int:player_id>/start_journey", methods=["POST"])
@login_required
def start_journey(player_id):
    # Authorization check
    if current_user.id != player_id:
        abort(403)

    user_profile = model.db.session.get(model.User, player_id)
    if not user_profile:
        abort(404)

    # Create a new playthrough and initial tile for this player
    new_play = model.Playthrough(user_id=player_id)
    model.db.session.add(new_play)
    model.db.session.flush()

    # create first tile
    tile_type_list = [
        {"name": tile_type.name, "id": tile_type.id} for tile_type in model.TileTypeOption.query.order_by(model.TileTypeOption.name)
    ]
    current_tile = model.Tile()
    current_tile.type = random.choice(tile_type_list)["id"]
    current_tile.user_id = player_id
    current_tile.playthrough_id = new_play.id
    model.db.session.add(current_tile)
    model.db.session.commit()

    return redirect(url_for("main.get_tile", player_id=player_id))


@main_bp.route("/player/<int:playerid>/game/tile/<int:tile_id>/action", methods=["POST"])
@login_required
def execute_tile_action(playerid, tile_id):
    # Authorization check
    if current_user.id != playerid:
        abort(403)
    # Accept either ActionOption.code (string) or numeric id in the posted `action` field.
    if request.method != "POST":
        return {"status_code": 402}

    # detect AJAX/JSON requests
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.accept_json

    action_post_value = request.form.get("action")
    if not action_post_value:
        if is_ajax:
            return jsonify(error="No action selected"), 400
        abort(400, description="No action selected")

    # Resolve ActionOption: prefer lookup by code; if not found and value is numeric, lookup by id.
    action_option = None
    action_name = None
    # Try lookup by code first
    if action_post_value:
        action_option = model.ActionOption.query.filter_by(code=action_post_value).one_or_none()
    # Fallback to numeric id
    if not action_option and action_post_value and action_post_value.isdigit():
        action_option = model.db.session.get(model.ActionOption, int(action_post_value))
    # Last resort: lookup by name
    if not action_option:
        action_option = model.ActionOption.query.filter_by(name=action_post_value).one_or_none()

    if action_option:
        action_name = action_option.name
    else:
        action_name = "unknown"

    # Use a transactional nested block and acquire a row-level lock on the tile to prevent races
    with model.db.session.begin_nested():
        stmt = select(model.Tile).where(model.Tile.id == tile_id).with_for_update()
        tile_record = model.db.session.execute(stmt).scalar_one_or_none()

        # Ensure the tile exists and hasn't already been actioned
        if not tile_record:
            if is_ajax:
                return jsonify(error="Tile not found"), 400
            abort(400, description="Tile not found")
        if tile_record.action_taken:
            if is_ajax:
                return jsonify(error="tile has already been actioned"), 400
            abort(400, description="tile has already been actioned")

        # Resolve action history existence
        actionverb_id = action_option.id if action_option else None
        action_record = None
        if actionverb_id is not None:
            action_record = model.Action.query.filter_by(tile=tile_id, actionverb=actionverb_id).first()

        # handle player and apply action semantics
        player_record = model.db.session.get(model.User, playerid)
        if not player_record:
            if is_ajax:
                return jsonify(error="Player not found"), 400
            abort(400, description="Player not found")

        # Apply action semantics and capture a short result message
        action_result = None
        if action_name == "rest":
            player_record.heal(10)
            action_result = "You rest and recover 10 HP."
            flash(action_result)

        elif action_name == "fight":
            damage = random.randint(5, 20)
            player_record.take_damage(damage)
            action_result = f"You fought bravely and took {damage} damage!"
            flash(action_result)

        elif action_name == "inspect":
            tile_type = model.db.session.get(model.TileTypeOption, tile_record.type)
            if tile_type and tile_type.name == "monster":
                action_result = "You carefully observe the creature, learning its patterns."
            elif tile_type and tile_type.name == "treasure":
                action_result = "You inspect the area and find hints of treasure nearby."
            else:
                action_result = "You take a moment to examine your surroundings carefully."
            flash(action_result)

        elif action_name == "quit":
            action_result = "You decide to retreat from this challenge."
            flash(action_result)
            # mark the playthrough as ended
            try:
                if tile_record and tile_record.playthrough_id:
                    pt = model.db.session.get(model.Playthrough, tile_record.playthrough_id)
                    if pt:
                        pt.ended_at = datetime.now(timezone.utc)
                        model.db.session.add(pt)
            except Exception:
                # don't let playthrough ending failures block the response
                model.db.session.rollback()

        else:
            action_result = f"Performed action: {action_name}"
            flash(action_result)

        # Create Action record for history tracking (or reuse existing)
        if not action_record:
            new_action = model.Action()
            new_action.name = action_name
            new_action.tile = tile_id
            new_action.actionverb = actionverb_id
            model.db.session.add(new_action)
            model.db.session.flush()
            action_history_id = new_action.id
        else:
            action_history_id = action_record.id

        # Link tile to action history and mark action taken
        tile_record.user_id = player_record.id
        tile_record.action = action_history_id
        tile_record.action_taken = True
        model.db.session.add(tile_record)
        model.db.session.add(player_record)

    # transaction committed here

    # Check if player is still alive after action
    if not player_record.is_alive:
        if is_ajax:
            return jsonify(error="You have fallen in battle..."), 200
        flash("You have fallen in battle...")
        return redirect(url_for("main.game_over", player_id=playerid))

    # If the player chose to quit, end the journey and return to the main/dashboard
    if action_name == "quit":
        if is_ajax:
            return jsonify(ok=True, redirect=url_for("main.greet_user"))
        return redirect(url_for("main.greet_user"))

    # Render readonly tile view including the action result so the user sees the outcome
    tile_details = model.db.session.get(model.Tile, tile_id)
    form = gameforms.TileForm(obj=tile_details)
    form.tileid.data = str(tile_details.id)
    tile_type_obj = model.db.session.get(model.TileTypeOption, tile_details.type)
    form.type.data = tile_type_obj.name if tile_type_obj else None
    form.action.choices = [
        (opt.code or str(opt.id), opt.name)
        for opt in model.ActionOption.query.join(model.Action, model.Action.actionverb == model.ActionOption.id)
        .filter(model.Action.tile == tile_details.id)
        .order_by(model.ActionOption.name)
    ]

    # If the client expects JSON (AJAX), return the action result and an HTML fragment for the updated tile
    if is_ajax:
        tile_html = render_template("_tile_fragment.html", player_char=player_record, form=form, readonly=True, action_result=action_result)
        return jsonify(ok=True, action_result=action_result, tile_html=tile_html)

    return render_template("gameTile.html", player_char=player_record, form=form, readonly=True, action_result=action_result)


@main_bp.route("/player/<int:player_id>/profile", methods=["GET"])
@login_required
def get_user_profile(player_id):
    # Authorization check
    if current_user.id != player_id:
        abort(403)
    user_profile = model.db.session.get(model.User, player_id)
    if not user_profile:
        return redirect(url_for("main.greet_user"))
    return render_template("profile.html", player_char=user_profile)


# get history
@main_bp.route("/player/<int:player_id>/game/history", methods=["GET"])
@login_required
def get_history(player_id):
    # Authorization check
    if current_user.id != player_id:
        abort(403)
    # get current logged in user profile
    user_profile = model.db.session.get(model.User, player_id)
    tile_history = model.Tile.query.filter_by(user_id=player_id).all()
    return render_template("gameHistory.html", player_char=user_profile, history=tile_history)


@main_bp.route("/player/<int:player_id>/gameover", methods=["GET"])
@login_required
def game_over(player_id):
    """Display game over screen when player dies."""
    # Authorization check
    if current_user.id != player_id:
        abort(403)

    user_profile = model.db.session.get(model.User, player_id)
    if not user_profile:
        abort(404)

    # Get player class and race names
    player_class_name = None
    player_race_name = None
    if user_profile.playerclass:
        player_class = model.db.session.get(model.PlayerClass, user_profile.playerclass)
        player_class_name = player_class.name if player_class else "Unknown"
    if user_profile.playerrace:
        player_race = model.db.session.get(model.PlayerRace, user_profile.playerrace)
        player_race_name = player_race.name if player_race else "Unknown"

    # Count tiles explored
    tiles_explored = model.Tile.query.filter_by(user_id=player_id).count()
    # Provide a RestartForm so template can render a POST form with CSRF token
    restart_form = gameforms.RestartForm()

    return render_template(
        "gameover.html",
        player_char=user_profile,
        player_class_name=player_class_name,
        player_race_name=player_race_name,
        tiles_explored=tiles_explored,
        form=restart_form,
    )


@main_bp.route("/player/<int:player_id>/restart", methods=["POST", "GET"])
@login_required
def restart_game(player_id):
    """Reset player stats to start a new game."""
    # Authorization check
    if current_user.id != player_id:
        abort(403)

    user_profile = model.db.session.get(model.User, player_id)
    if not user_profile:
        abort(404)

    # Reset player stats
    user_profile.hitpoints = user_profile.max_hp
    user_profile.exp_points = 0
    user_profile.level = 1
    user_profile.playerclass = None
    user_profile.playerrace = None

    # Delete all old tiles using ORM deletes so cascades and relationships are honored
    with model.db.session.begin_nested():
        tiles = model.Tile.query.filter_by(user_id=player_id).all()
        for t in tiles:
            model.db.session.delete(t)
        model.db.session.add(user_profile)

    # transaction committed by context manager

    flash("Your adventure begins anew!")
    return redirect(url_for("main.setup_char", player_id=player_id))

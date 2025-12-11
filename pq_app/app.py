import random
from typing import cast
from flask import Blueprint, request, render_template, redirect, url_for, flash, abort, jsonify
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from . import model, gameforms, pqMonsters, gameTile
from .services import CombatService, TileService

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
        return render_template(
            "dashboard.html", player_char=current_user, has_tiles=user_tiles_exist, start_form=start_form
        )
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
            # Generate and save content to database based on tile type
            tile_config = gameTile.pqGameTile()
            if tile_type["name"] == "sign":
                current_tile.content = tile_config.generate_signpost()
            elif tile_type["name"] == "monster":
                monster = pqMonsters.NPCMonster()
                current_tile.content = f"{monster.name} ({monster.hitpoints} HP)"
            elif tile_type["name"] == "scene":
                current_tile.content = "This is a scene tile"
            elif tile_type["name"] == "treasure":
                current_tile.content = "This is a treasure tile"
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
    """Display the current tile for a player"""
    # Authorization check
    if current_user.id != player_id:
        abort(403)

    user_profile = model.db.session.get(model.User, player_id)
    if not user_profile:
        abort(404)

    # Check if player is dead before showing tile
    if not user_profile.is_alive:
        return redirect(url_for("main.game_over", player_id=player_id))

    # Initialize tile service
    tile_service = TileService()
    
    # Find the active playthrough
    active_playthrough = tile_service.get_active_playthrough(player_id)
    if not active_playthrough:
        flash("No active journey found. Please start a new journey.")
        return redirect(url_for("main.greet_user"))

    # Get the most recent tile from the active playthrough
    tile_details = tile_service.get_latest_tile(player_id, active_playthrough.id)
    if not tile_details:
        flash("No tile found for this player; please set up your character or generate a tile.")
        return redirect(url_for("main.setup_char", player_id=player_id))
    
    # Get tile data including type and allowed actions
    tile_data = tile_service.get_tile_data(tile_details.id)
    
    # Prepare form
    form = gameforms.TileForm(obj=tile_details)
    form.tileid.data = str(tile_details.id)
    form.type.data = tile_data.tile_type_name
    form.content.data = tile_details.content
    
    # Check if tile has been actioned (readonly mode)
    if tile_details.action_taken:
        # Show the actions that were taken
        form.action.choices = [
            (action_option.code or str(action_option.id), action_option.name)
            for action_option in model.ActionOption.query.join(
                model.Action, model.Action.actionverb == model.ActionOption.id
            )
            .filter(model.Action.tile == tile_details.id)
            .order_by(model.ActionOption.name)
        ]
        return render_template("gameTile.html", player_char=user_profile, form=form, 
                             tile_type_obj=tile_data.tile_type_obj, readonly=True)

    # Active tile - show available actions
    form.action.choices = [
        (action.code or str(action.id), action.name) 
        for action in tile_data.allowed_actions
    ]
    return render_template("gameTile.html", player_char=user_profile, form=form, 
                         tile_type_obj=tile_data.tile_type_obj)


@main_bp.route("/player/<int:player_id>/game/tile/next", methods=["POST", "GET"])
@login_required
def generate_tile(player_id):
    """Generate the next tile for a player"""
    # Authorization check
    if current_user.id != player_id:
        abort(403)

    user_profile = model.db.session.get(model.User, player_id)
    if not user_profile:
        abort(404)

    # Check if player is dead
    if not user_profile.is_alive:
        return redirect(url_for("main.game_over", player_id=player_id))
    
    # Initialize tile service
    tile_service = TileService()
    
    # Get last tile record for the user
    tile_record = tile_service.get_latest_tile(player_id)
    
    # If no tile record exists, redirect to the tile page which will handle prompting setup
    if not tile_record:
        return redirect(url_for("main.get_tile", player_id=player_id))
    
    # If the tile has not been actioned redirect to that tile page
    if not tile_record.action_taken:
        return redirect(url_for("main.get_tile", player_id=player_id))

    # At this point the previous tile was actioned; generate a fresh tile for the player (GET)
    tile_type_list = [
        {"name": tile_type.name, "id": tile_type.id}
        for tile_type in model.TileTypeOption.query.order_by(model.TileTypeOption.name)
    ]

    current_tile = model.Tile()
    current_tile.type = random.choice(tile_type_list)["id"]
    current_tile.user_id = player_id
    # preserve playthrough from previous tile when generating the next tile
    current_tile.playthrough_id = tile_record.playthrough_id

    # Generate and save content based on tile type
    tile_config = gameTile.pqGameTile()
    tile_type_obj = model.db.session.get(model.TileTypeOption, current_tile.type)
    tile_type_name = tile_type_obj.name if tile_type_obj else None
    if tile_type_name == "sign":
        current_tile.content = tile_config.generate_signpost()
    elif tile_type_name == "monster":
        monster = pqMonsters.NPCMonster()
        # Save monster name with HP in parentheses
        current_tile.content = f"{monster.name} ({monster.hitpoints} HP)"
    elif tile_type_name == "scene":
        current_tile.content = "This is a scene tile"
    elif tile_type_name == "treasure":
        current_tile.content = "This is a treasure tile"

    model.db.session.add(current_tile)
    model.db.session.commit()

    # Get tile data for the newly-created tile
    tile_data = tile_service.get_tile_data(current_tile.id)
    
    # Prepare the form
    tile_details = gameforms.TileForm(obj=current_tile)
    tile_details.tileid.data = str(current_tile.id)
    tile_details.type.data = tile_data.tile_type_name
    tile_details.content.data = current_tile.content
    # Filter available actions based on tile type (same as get_tile)
    all_actions = model.ActionOption.query.order_by(model.ActionOption.name).all()
    if tile_details.type.data == "sign":
        # Sign tiles only allow rest, inspect, and quit
        allowed_actions = [a for a in all_actions if a.name in ["rest", "inspect", "quit"]]
    elif tile_details.type.data == "treasure":
        # Treasure tiles disable fight
        allowed_actions = [a for a in all_actions if a.name != "fight"]
    else:
        # Other tile types (monster, scene) allow all actions
        allowed_actions = all_actions

    tile_details.action.choices = [
        (action.code or str(action.id), action.name)
        for action in tile_data.allowed_actions
    ]

    return render_template("gameTile.html", player_char=user_profile, form=tile_details,
                         tile_type_obj=tile_data.tile_type_obj)


@main_bp.route("/player/<int:player_id>/start_journey", methods=["POST"])
@login_required
def start_journey(player_id):
    """Start a new journey/playthrough for a player"""
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

    # create first tile with content
    tile_config = gameTile.pqGameTile()
    tile_type_list = [
        {"name": tile_type.name, "id": tile_type.id}
        for tile_type in model.TileTypeOption.query.order_by(model.TileTypeOption.name)
    ]
    current_tile = model.Tile()
    current_tile.type = random.choice(tile_type_list)["id"]
    current_tile.user_id = player_id
    current_tile.playthrough_id = new_play.id

    # Generate and save content to database based on tile type
    tile_type_obj = model.db.session.get(model.TileTypeOption, current_tile.type)
    tile_type_name = tile_type_obj.name if tile_type_obj else None

    if tile_type_name == "sign":
        current_tile.content = tile_config.generate_signpost()
    elif tile_type_name == "monster":
        monster = pqMonsters.NPCMonster()
        current_tile.content = f"{monster.name} ({monster.hitpoints} HP)"
    elif tile_type_name == "scene":
        current_tile.content = "This is a scene tile"
    elif tile_type_name == "treasure":
        current_tile.content = "This is a treasure tile"
    model.db.session.add(current_tile)
    model.db.session.commit()

    return redirect(url_for("main.get_tile", player_id=player_id))


@main_bp.route("/player/<int:playerid>/game/tile/<int:tile_id>/action", methods=["POST"])
@login_required
def execute_tile_action(playerid, tile_id):
    """Execute an action on a tile using CombatService"""
    # Authorization check
    if current_user.id != playerid:
        abort(403)
    
    # Accept either ActionOption.code (string) or numeric id in the posted `action` field.
    if request.method != "POST":
        return {"status_code": 402}

    # Detect AJAX/JSON requests - only check X-Requested-With header for stricter detection
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    action_post_value = request.form.get("action")
    if not action_post_value:
        if is_ajax:
            return jsonify(error="No action selected"), 400
        abort(400, description="No action selected")

    # Initialize combat service
    combat_service = CombatService()
    
    # Resolve ActionOption
    action_option = combat_service.get_action_by_value(action_post_value)
    action_name = action_option.name if action_option else "unknown"

    # Use a transactional nested block and acquire a row-level lock on the tile to prevent races
    with model.db.session.begin_nested():
        tile_record = combat_service.get_tile_with_lock(tile_id)

        # Validate tile
        is_valid, error_msg = combat_service.validate_tile_action(tile_record)
        if not is_valid:
            if error_msg == "Tile already actioned":
                # Redirect to get_tile to show the tile in readonly mode
                if is_ajax:
                    return jsonify(redirect=url_for("main.get_tile", player_id=playerid)), 200
                return redirect(url_for("main.get_tile", player_id=playerid))
            else:
                # Tile not found or other error
                if is_ajax:
                    return jsonify(error=error_msg), 400
                abort(400, description=error_msg)

        # Get player
        player_record = model.db.session.get(model.User, playerid)
        if not player_record:
            if is_ajax:
                return jsonify(error="Player not found"), 400
            abort(400, description="Player not found")

        # Get tile type
        tile_type = model.db.session.get(model.TileTypeOption, tile_record.type)
        tile_type_name = tile_type.name if tile_type else None

        # Execute action using combat service
        combat_result = combat_service.execute_action(
            player=player_record,
            tile=tile_record,
            action_name=action_name,
            tile_type_name=tile_type_name
        )

        # Get or create action record for history tracking
        action_history_id = combat_service.get_or_create_action_record(
            tile_id=tile_id,
            action_name=action_name,
            action_option=action_option
        )

        # Complete the tile action
        combat_service.complete_tile_action(
            tile=tile_record,
            player=player_record,
            action_history_id=action_history_id
        )

    # Transaction committed here

    # Check if player is still alive after action
    if not combat_result.player_alive:
        if is_ajax:
            return jsonify(error="You have fallen in battle..."), 200
        flash("You have fallen in battle...")
        return redirect(url_for("main.game_over", player_id=playerid))

    # If the player chose to quit, end the journey and return to the main/dashboard
    if combat_result.should_end_playthrough:
        if is_ajax:
            return jsonify(ok=True, redirect=url_for("main.greet_user"))
        return redirect(url_for("main.greet_user"))

    # Render readonly tile view including the action result
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

    # If the client expects JSON (AJAX), return the action result and an HTML fragment
    if is_ajax:
        tile_html = render_template(
            "_tile_fragment.html",
            player_char=player_record,
            form=form,
            tile_type_obj=tile_type_obj,
            readonly=True,
            action_result=combat_result.message
        )
        return jsonify(ok=True, action_result=combat_result.message, tile_html=tile_html)

    return render_template(
        "gameTile.html",
        player_char=player_record,
        form=form,
        tile_type_obj=tile_type_obj,
        readonly=True,
        action_result=combat_result.message
    )


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
    # Check if there's an active playthrough for button logic
    active_playthrough = model.Playthrough.query.filter_by(user_id=player_id, ended_at=None).first()
    return render_template(
        "gameHistory.html", player_char=user_profile, history=tile_history, active_playthrough=active_playthrough
    )


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

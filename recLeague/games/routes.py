import os

from flask import (
    render_template, url_for, flash, redirect, request, abort, Blueprint
)
from flask.typing import ResponseReturnValue
from flask_login import current_user
# Maybe remove numpy usage in future to save memory usage?
from numpy import transpose, stack 

from recLeague import db
from recLeague.models import Game, Season
from recLeague.games.forms import GameForm
from recLeague.games.utils import (
    calculate_stats, set_game, is_game_user_modifiable
)
from recLeague.config import (
    NUM_TEAM_PLAYERS, STAT_CATEGORY_NAMES, SCORECARD_PICS_STATIC_PATH
)


games = Blueprint('games', __name__)


@games.route("/game/new", methods=['GET', 'POST'])
def submit_game() -> ResponseReturnValue:
    """Route to submit a new game.
    """

    # TODO: move to helper function
    season = Season.query.first()
    if season is None or season.is_active() is False:
        abort(403)

    form = GameForm(False)

    # Check if successfully submited new game
    if form.validate_on_submit():
        new_game = Game()
        db.session.add(new_game)
        set_game(form, new_game)
        db.session.commit()
        flash(
            'Your game has been submitted! Game will be counted once it' 
            'is verified.', 'success'
        )
        return redirect(url_for('main.home'))

    # Initialize form with player's team and empty stats if not posting 
    # game data
    elif request.method == 'GET':
        if (current_user.team is not None 
                and len(current_user.team.players) >= 2):
            form.team_1.data = current_user.team.id
        
        form.set_form(None)

    return render_template(
        'submit_game.html', title='Submit Game', form=form, 
        legend='Submit Game', first=(request.method == 'GET'), edit=False
    )


@games.route("/game/<int:game_id>/update", methods=['GET', 'POST'])
def update_game(game_id: int) -> ResponseReturnValue:
    """Route to update game data.
    
    Used for editing information of a published game.
    
    Args:
        game_id (int): ID of game
    """
    game = Game.query.get_or_404(game_id)
    
    if is_game_user_modifiable(game) is False:
        abort(403)

    form = GameForm(True)

    # Check if successfully edited game data
    if form.validate_on_submit():
        if game.verified:
            teams = []
            for team in game.teams:
                teams.append(team)
            players = []
            for player in game.players:
                players.append(player)
            
            set_game(form, game)
            
            # Update season stats for all teams and players before 
            # and after the edit
            teams = list(set(teams) | set(game.teams))
            players = list(set(players) | set(game.players))
            calculate_stats(teams, players)
            
        else:
            set_game(form, game)
        db.session.commit()
        flash('Your game has been updated!', 'success')
        return redirect(url_for('games.game', game_id=game.id))
    elif request.method == 'GET':
        form.set_form(game)

    return render_template(
        'submit_game.html', title='Update Game', form=form, 
        legend='Update Game', first=False, edit=True
    )


@games.route("/game/<int:game_id>")
def game(game_id: int) -> ResponseReturnValue:
    """Route to view a game.
    
    Args:
        game_id (int): ID of game
    """
    game = Game.query.get_or_404(game_id)
    stats = stack(tuple(
        game.player_stats[i].get_stats() 
        for i in range(NUM_TEAM_PLAYERS * 2)
    ))
    img_url = url_for(
        'static', 
        filename=os.path.join(SCORECARD_PICS_STATIC_PATH, game.picture_file)
    )

    return render_template(
        'game.html', game=game, t_stats=transpose(stats),
        stat_names=STAT_CATEGORY_NAMES, img_url=img_url
    )


@games.route("/game/<int:game_id>/delete", methods=['POST'])
def delete_game(game_id: int) -> ResponseReturnValue:
    """Route for deleting a game.
    
    Args:
        game_id (int): ID of game
    """
    game = Game.query.get_or_404(game_id)

    if is_game_user_modifiable(game) is False:
        abort(403)
    db.session.delete(game)
    db.session.commit()

    calculate_stats(game.teams, game.players)
    db.session.commit()
    flash('Your game has been deleted!', 'success')
    
    return (
        redirect(url_for('admin.games')) 
        if current_user.is_admin 
        else redirect(url_for('main.home'))
    )


@games.route("/game/<int:game_id>/verify", methods=['POST'])
def verify_game(game_id: int) -> ResponseReturnValue:
    """Route to verify game.
    
    Args:
        game_id (int): ID of game
    """
    game = Game.query.get_or_404(game_id)
    
    if game.verified:
        flash('Game has already been verified!', 'error')
        return redirect(url_for('games.game', game_id=game.id))
    # Can only delete games if one of players edit before verified or if 
    # the user is admin
    if current_user.is_admin is False:
        abort(403)
    game.verified = True

    calculate_stats(game.teams, game.players)

    db.session.commit()
    flash('Game has been verified!', 'success')
    
    return (
        redirect(url_for('admin.games')) 
        if current_user.is_admin 
        else redirect(url_for('main.home'))
    )

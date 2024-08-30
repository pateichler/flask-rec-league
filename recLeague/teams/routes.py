from flask import (
    render_template, url_for, flash, redirect, request, abort, 
    Blueprint, jsonify
)
from flask.typing import ResponseReturnValue
from flask_login import current_user

from recLeague import db
from recLeague.models import Team, Season
from recLeague.teams.forms import TeamCreateForm, TeamJoinForm
from recLeague.config import (
    NUM_TEAM_PLAYERS
)

teams = Blueprint('teams', __name__)


@teams.route("/team-players/<team_id>")
def _get_team_players(team_id: int) -> ResponseReturnValue:
    """API route for getting players on team.
    
    Args:
        team_id (int): ID of team
    
    Returns:
        json: Array of user IDs on team.
    
    :resheader Content-Type: application/json

    :statuscode 200: Team has players.
    :statuscode 204: Team does not exist.
    :statuscode 400: Not valid team_id.
    """
    try:
        id = int(team_id)
        team = Team.query.get(id)
        if team is not None:
            return jsonify([p.id for p in team.players]) 
        return ('', 204)

    except ValueError:
        return ('', 400)


@teams.route("/teams-latest-game-score")
def _get_teams_latest_game_score() -> ResponseReturnValue:
    """API route gets latest game score between two teams.
    
    Returns:
        json: Object with fields team_1 and team_2 set to the score.

    :query int team-1: ID of team 1.
    :query int team-2: ID of team 2.

    :statuscode 200: Teams have a game between each other.
    :statuscode 204: No game between the teams was found.
    :statuscode 400: Team query parameters not valid.

    """

    # Get team IDs from route arguments
    team_1 = request.args.get('team-1', None, type=int)
    team_2 = request.args.get('team-2', None, type=int)

    if team_1 is not None and team_2 is not None and team_1 != team_2:
        t1 = Team.query.get_or_404(team_1)
        t2 = Team.query.get_or_404(team_2)

        # Search for team 2 in all of team 1's games
        for game in t1.games:
            if t2 in game.teams:
                team_index = game.teams.index(t1)
                scores = [game.team_1_score, game.team_2_score]
                score = {
                    "team_1": scores[team_index],
                    "team_2": scores[1 - team_index]
                }
                return jsonify(score) 

        return ('', 204)

    return ('', 400)


@teams.route("/team/new", methods=['GET', 'POST'])
def create_team() -> ResponseReturnValue:
    """Route for creating a new team.
    """

    if current_user.team is not None and current_user.is_admin is False:
        abort(403)

    form = TeamCreateForm()

    if form.validate_on_submit():
        t = Team(name=form.team_name.data)
        # Add user to new team unless if admin is creating team
        if current_user.is_admin is False:
            t.players.append(current_user)
        db.session.add(t)
        db.session.commit()
        flash('Your team has been created!', 'success')
        if current_user.is_admin:
            return redirect(url_for('admin.teams')) 

        return redirect(url_for('main.home'))
    
    return render_template('create_team.html', title='Create Team', form=form)


@teams.route("/team/<int:team_id>/delete", methods=['POST'])
def delete_team(team_id: int) -> ResponseReturnValue:
    """Route for deleting a team.
    
    Args:
        team_id (int): ID of team
    """

    team = Team.query.get_or_404(team_id)
    
    season = Season.query.first()
    # Player can't delete team when in season
    if (season is not None and season.is_active() 
            and current_user.is_admin is False):
        abort(403)
    # Player can't delete team if they don't have a team (they would 
    # be only a user then)
    if current_user.team is None and current_user.is_admin is False:
        abort(403)
    # Player can't delete another players team
    if (current_user.team is not None and current_user.team.id != team_id 
            and current_user.is_admin is False):
        abort(403)
    # Admin can't delete team if the team has games
    if len(team.games) > 0:
        abort(403)
    db.session.delete(team)
    db.session.commit()

    flash('Team has been deleted!', 'success')
    
    if current_user.is_admin:
        return redirect(url_for('admin.teams'))
    
    return redirect(url_for('main.home'))


@teams.route("/team/leave", methods=['POST'])
def leave_team() -> ResponseReturnValue:
    """Route for leaving a team.
    """

    if current_user.team is None:
        flash('No team to leave.', 'warning')
        return redirect(url_for('main.home'))

    season = Season.query.first()

    # Delete team if we are the only one on it
    if ((season is None or season.is_active() is False) 
            and len(current_user.team.players) == 1):
        # Might not be the best to call directly
        delete_team(current_user.team.id)

    current_user.team = None
    db.session.commit()

    flash('You have left your team!', 'success')
    return redirect(url_for('main.home'))


@teams.route("/team/join", methods=['GET', 'POST'])
def join_team() -> ResponseReturnValue:
    """ Route for joining a team.
    """

    form = TeamJoinForm()

    form.team.choices = [
        (t.id, t.name) 
        for t in Team.query.order_by('name') 
        if len(t.players) < NUM_TEAM_PLAYERS
    ] 

    if form.validate_on_submit():
        t = Team.query.get(form.team.data)
        # Check if players have join since we have selected our team
        if (t is None 
                or len(t.players) >= NUM_TEAM_PLAYERS):
            abort(403)
        t.players.append(current_user)
        db.session.commit()
        return redirect(url_for('main.home'))

    return render_template('team_join.html', title='Join Team', form=form)


@teams.route("/team/<int:team_id>")
def team(team_id: int) -> ResponseReturnValue:
    """Route for viewing a team.
    
    Args:
        team_id (int): ID of team
    """

    team = Team.query.get_or_404(team_id)
    
    return render_template('team.html', team=team, highlight_stat=None)

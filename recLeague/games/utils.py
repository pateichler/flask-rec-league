import os
import secrets
from typing import Iterable

from PIL import Image
from flask import current_app
from flask_login import current_user

from recLeague import db
from recLeague.models import Team, User, Stats, Game
from recLeague.games.forms import GameForm
from recLeague.config import (
    SCORECARD_PICS_STATIC_PATH, STAT_CATEGORY_KEYS, NUM_TEAM_PLAYERS
)


def is_game_user_modifiable(game: Game) -> bool:
    """Returns if the game is able to be modified by the current user.
    
    Can only modify the game if current is user is an admin or if the current 
    user is one of the players is in the game and the game hasn't been 
    verified yet.

    Args:
        game (Game): Game to check if it is editable.
    
    Returns:
        bool: True if game is able to edit by the current user, otherwise False
    """

    return (current_user.is_admin 
            or (current_user in game.players and game.verified is False))


def save_scorecard_picture(form_picture_filepath: str) -> str:
    """Saves scorecard picture as jpeg file at the scorecard static path.
    
    .. note::

        See SCORECARD_PICS_STATIC_PATH for information about the save path.
    
    Args:
        form_picture_filepath (str): Filepath of picture to save.
    
    Returns:
        str: Filepath of saved image file.
    """

    random_hex = secrets.token_hex(8)
    picture_fn = random_hex + ".jpg"
    picture_path = os.path.join(
        current_app.root_path, "static", SCORECARD_PICS_STATIC_PATH, picture_fn
    )

    output_size = (1080, 1080)
    i = Image.open(form_picture_filepath)
    i = i.convert('RGB')
    i.thumbnail(output_size)
    i.save(picture_path, format="jpeg")

    return picture_fn


def set_game(form: GameForm, game: Game) -> None:
    """Sets game object with game form data.
    
    Args:
        form (GameFrom): form to save
        game (Game): game object to save data in
    """     

    if form.picture.data is not None:
        game.picture_file = save_scorecard_picture(form.picture.data)
        # TODO: Optimization, delete old picture_file 
        # if not none to save storage
    
    game.team_1_score = form.team_1_score.data
    game.team_2_score = form.team_2_score.data

    # Flush session with teams and players cleared so order is not 
    # saved in database
    game.teams.clear()
    game.players.clear()
    db.session.flush() 
    
    # Check if game does not have stat objects created ... If so 
    # add empty stat objects
    if game.player_stats is None or len(game.player_stats) == 0:
        for i in range(NUM_TEAM_PLAYERS * 2):
            game.player_stats.append(Stats())    

    # Set stats
    for i in range(NUM_TEAM_PLAYERS * 2):
        stats = [
            getattr(form.stats, key).data[i] 
            for key in STAT_CATEGORY_KEYS
        ]
        game.player_stats[i].set_stats(stats, 1)

    # Set teams
    game.teams.append(Team.query.get(form.team_1.data))
    game.teams.append(Team.query.get(form.team_2.data))

    # Set players
    for player in (form.team_1_players.data + form.team_2_players.data):
        game.players.append(User.query.get(player))

    if form.comment.data is not None:
        game.comment = form.comment.data

    # Set boolean array for if player is a sub 
    is_sub = [False] * (NUM_TEAM_PLAYERS * 2)
    for i in range(NUM_TEAM_PLAYERS * 2):
        player_team_id = game.teams[0 if i < NUM_TEAM_PLAYERS else 1].id
        is_sub[i] = (
            game.players[i].team is None 
            or game.players[i].team.id != player_team_id
        )

    game.is_sub = is_sub


def calculate_team_stats(teams: Iterable[Team]) -> None:
    """ Calculates the running total of current season stats for teams.
    
    Args:
        teams (Iterable[Team]): List of teams to calcuate stats
    """

    # Loop through all teams
    for team in teams:
        wins = 0
        losses = 0
        
        div_wins = 0
        div_losses = 0

        streak = 0
        score_diff = 0

        # Loop through all games in teams season
        for game in team.games:
            if game.verified:
                divisional = (
                    game.teams[0].division is not None 
                    and game.teams[1].division is not None 
                    and (game.teams[0].division.id == game.teams[1].division.id)
                )

                # Check if this team won the game
                if (game.teams.index(team) == 0) == (game.did_team_1_win()):
                    wins += 1
                    if divisional:
                        div_wins += 1
                    streak = streak + 1 if streak >= 0 else 1
                else:
                    losses += 1
                    if divisional:
                        div_losses += 1
                    streak = streak - 1 if streak <= 0 else -1

                diff = game.team_1_score - game.team_2_score
                score_diff += (diff if game.teams.index(team) == 0 else -diff)

        # Set team stats
        team.wins = wins
        team.losses = losses
        team.div_wins = div_wins
        team.div_losses = div_losses
        team.streak = streak
        team.score_diff = score_diff


def calculate_player_stats(players: Iterable[User]) -> None:
    """ Calculates the running total of current season stats for players.
    
    Args:
        players (Iterable[Player]): List of players to calcuate stats
    """

    for player in players:
        # Init stat data if set to None
        if player.season_stats is None:
            player.season_stats = Stats()
        else:
            # TODO: Replace with config NUM_STATS
            player.season_stats.set_stats(
                [0]*len(STAT_CATEGORY_KEYS), 0
            )

        if player.season_high_stats is None:
            player.season_high_stats = Stats()
        else:
            player.season_high_stats.set_stats(
                [0]*len(STAT_CATEGORY_KEYS), 0
            )
        
        # Loop through all players current season games
        for game in player.games:
            if game.verified:
                player.season_stats.add_stats(
                    game.player_stats[game.players.index(player)]
                )
                player.season_high_stats.max_stats(
                    game.player_stats[game.players.index(player)]
                )


def calculate_stats(teams: Iterable[Team], players: Iterable[User]) -> None:
    """ Calculates the running total of current season stats for teams 
    and players.
    
    Args:
        teams (Iterable[Team]): List of teams to calcuate stats
        players (Iterable[Player]): List of players to calcuate stats
    """

    calculate_team_stats(teams)
    calculate_player_stats(players)

from flask import (
    render_template, request, abort, Blueprint
)
from flask.typing import ResponseReturnValue

from recLeague.models import Team, User, Season, Division
from recLeague.config import (
    MIN_SEASON_AVERAGE_GAMES, MIN_LIFETIME_AVERAGE_GAMES, STAT_CATEGORY_KEYS, 
    STAT_CATEGORY_NAMES
)

stats = Blueprint('stats', __name__)


@stats.route("/standings")
def standings() -> ResponseReturnValue:
    """Route to view the current standings.
    """

    division = request.args.get('division', 0, type=int)
    divisions = Division.query.all()
    if division < 0 or division > len(divisions):
        abort(404)
    
    places = []
    cur_tie = -1

    # Standings based on overall record
    if division == 0:
        teams = Team.query.order_by(
            Team.wins.desc(), Team.losses.desc(), Team.score_diff.desc()
        )
        
        for i, team in enumerate(teams):
            if (cur_tie < 0 or team.wins != teams[cur_tie].wins 
                    or len(team.games) != len(teams[cur_tie].games)):
                cur_tie = i

            places.append(str(cur_tie+1))
    # Standing based on divisonal record
    else:
        teams = Team.query.filter(Team.division_id == division).order_by(
            Team.div_wins.desc(), 
            Team.wins.desc(), 
            Team.losses.desc(), 
            Team.score_diff.desc(),
        )
        
        for i, team in enumerate(teams):
            if (cur_tie < 0 or team.div_wins != teams[cur_tie].div_wins 
                    or team.wins != teams[cur_tie].wins 
                    or len(team.games) != len(teams[cur_tie].games)):
                cur_tie = i

            places.append(str(cur_tie+1))

    return render_template(
        'standings.html', title='Standings', teams=teams, 
        divisions=divisions, places=places
    )


# Leaderboard stat types
# TODO: Probably should be moved somewhere
board_stats = {
    "Game": {
        "description": "Best stats in a single game.",
        "period_1": "season_high_stats",
        "period_2": "prev_season_high_stats",
        "combine_max": True
    },
    "Current Season": {
        "description": "Best stats in the current season only.",
        "period_1": "season_stats"
    },
    "Season": {
        "description": "Best stats in a single season.",
        "period_1": "season_stats",
        "period_2": "prev_season_best_stats",
        "combine_max": True
    },
    "Lifetime": {
        "description": "Best stats for all seasons combined.",
        "period_1": "season_stats",
        "period_2": "prev_season_stats"
    },
    "Current Season Average": {
        "description": f"Average game stats in the current season only. \
        Must have played over {MIN_SEASON_AVERAGE_GAMES} games.",
        "period_1": "season_stats",
        "min_games": MIN_SEASON_AVERAGE_GAMES,
        "div_by_games": True
    },
    "Lifetime Average": {
        "description": f"Average game stats for all seasons combined. \
        Must have played over {MIN_LIFETIME_AVERAGE_GAMES} games.",
        "period_1": "season_stats",
        "period_2": "prev_season_stats",
        "min_games": MIN_LIFETIME_AVERAGE_GAMES,
        "div_by_games": True
    }
}


@stats.route("/leaderboard")
def leaderboard() -> ResponseReturnValue:
    """ Route to view the leaderboard.
    """

    # Get arguments from url
    stat_name = request.args.get('stat_name', "Games", type=str)
    stat_period = request.args.get('stat_period', "Season", type=str)
    page = request.args.get('page', 1, type=int)

    # Set array of stat names to choose from
    stat_names = ["Games"] + STAT_CATEGORY_NAMES
    displayed_stat_names = STAT_CATEGORY_NAMES

    # Abort if the stat or period is not in list
    if stat_name not in stat_names or stat_period not in board_stats:
        abort(404)

    board_stat = board_stats[stat_period]

    # Check if current stat is games and period does not make sense 
    # with games ... if remove games stat from list
    remove_game_stat = (stat_period == "Game" 
                        or board_stat.get("div_by_games", False))
    
    if remove_game_stat is False:
        displayed_stat_names = ["Games"] + displayed_stat_names
    elif stat_name == "Games":
        stat_name = stat_names[1]

    # Convert the selected stat name to the stat name in our database
    # Pretty much just lowercase of name ex. Games -> games
    stat_var_names = ["game_count"] + STAT_CATEGORY_KEYS
    stat_var_name = stat_var_names[stat_names.index(stat_name)]

    # Make an array of parameters for the User.indv_stat query from board_stat
    query_params = [
        stat_var_name, 
        board_stat["period_1"], 
        board_stat.get("period_2"),
        board_stat.get("combine_max", False),
        board_stat.get("div_by_games", False),
    ]

    # Variable to filter minimum amount of games
    min_games = board_stat.get("min_games", 1)

    # Query users, first filter to make sure not root user or guest player 
    # and games played is greater than minumum, then order users by the 
    # target stat and period by using User.indv_stat function, finally 
    # paginate to keep the list small
    users = User.query.filter(
            User.id != 1, User.name != "Guest Player", 
            User.indv_stat("game_count", *query_params[1:3]) >= min_games
        ).order_by(User.indv_stat(*query_params).desc()) \
        .paginate(page=page, per_page=20)
    
    # Loop through all users and add the stat value to an array
    stat_vals = []
    for user in users.items:
        stat_vals.append(round(user.indv_stat(*query_params), 2))

    # If there is no current season remove period options that rely 
    # on a current season
    season = Season.query.first()
    rendered_periods = list(board_stats.keys())
    if season is None or season.is_before():
        rendered_periods.pop(1)
        rendered_periods.pop(3)
    
    return render_template(
        'leaderboard.html', title='Leaderboard', players=users, 
        stat_name=stat_name, stat_names=displayed_stat_names, 
        stat_period=stat_period, stat_periods=rendered_periods, 
        stat_desc=board_stat["description"], stat_vals=stat_vals
    )

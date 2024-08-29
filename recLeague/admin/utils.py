from recLeague.models import Team
from recLeague.config import NUM_TEAM_PLAYERS


def get_team_csv_text() -> str:
    """Returns a string in CSV format with all teams and players on the team.
    
    Returns:
        str: CSV formatted string with team data.
    """
    player_heading = ','.join([f'Player {i}' for i in range(NUM_TEAM_PLAYERS)])
    csv = f"Team,{player_heading}\n"

    csv = "Team,Player 1,Player 2\n"
    teams = Team.query.all()
    for team in teams:
        players = [p.name for p in team.players]
        csv += ",".join([team.name.replace(",", "")] + players) + "\n"

    return csv

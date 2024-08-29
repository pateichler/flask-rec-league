import sys
import os
sys.path[0] = os.path.join(sys.path[0], "..")
from datetime import datetime, timedelta

from cli.helper import create_app
from recLeague.models import User, Team, Division, Season
from recLeague import db, bcrypt
from recLeague.config import NUM_TEAM_PLAYERS

app = create_app()
app.app_context().push()


num_teams = 10
num_divisions = 2


def create_season():
    db.session.add(Season(
        name="Generated Season", date_start=datetime.today(), 
        date_end=(datetime.today() + timedelta(days=1))
    ))


def create_users():
    pw = bcrypt.generate_password_hash("pass").decode('utf-8')

    for i in range(num_teams * NUM_TEAM_PLAYERS):
        user = User(
            name=f"Robot {i+1}", email= f"robot{i+1}@gmail.com", password=pw
        )
        db.session.add(user)
    db.session.commit()


def create_teams():
    for i in range(num_teams):
        team = Team(name="Team " + str(i+1))
        team.division = Division.query.get(
            int((i / num_teams) * num_divisions) + 1
        )
        db.session.add(team)

        for p in range(NUM_TEAM_PLAYERS):
            User.query.get(p+2 + i * NUM_TEAM_PLAYERS).team = team

    db.session.commit()


def create_divisions():
    for i in range(num_divisions):
        db.session.add(Division(name=f"Division {i+1}"))    
    db.session.commit()


if User.query.count() > 1:
    print("Database already created users ... consider reinitializing database")
    print("aborting test database")
    sys.exit()

season = Season.query.first()
if season is None:
    print("Creating season")
    create_season()

print("Creating divisions")
create_divisions()

print("Creating users")
create_users()
print(User.query.all())

print("Creating teams")
create_teams()
# set_teams()
print(Team.query.all())

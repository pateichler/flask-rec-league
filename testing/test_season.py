from recLeague import db
from recLeague.models import User, Game, Team, Division, Season, Stats
from recLeague import create_app
from recLeague.config import TestConfig
from recLeague.games.routes import calculate_stats
import random
from datetime import datetime, timedelta

app = create_app(TestConfig)
app.app_context().push()

def create_users(num_users):
	pw = "$2b$12$5MlyOQ434ncCy3ny07Zl..Pr.xBTuxMf7ll6Q7DwCIog1bvqoznyS"
	admin_user = User(name="Patrick Eichler", email= "pateichler12@gmail.com", password=pw, is_admin=True)
	db.session.add(admin_user)
	current_user = admin_user

	for i in range(num_users):
		user = User(name="Robot " + str(i + 1), email= str(i+1) + "@gmail.com", password=pw)
		db.session.add(user)
	db.session.commit()
	print("Created users")

def create_teams(num_teams):
	if Team.query.count() > 0:
		print("Already teams ... not creating new teams")
		return

	num_users = User.query.count()
	if num_users * 2 < num_teams:
		print("Can't create teams ... not enough users")
		return
	for i in range(num_teams):
		team = Team(name= "Team " + str(i+1))
		team.players.append(User.query.get(num_users - (i+1)*2 + 1))
		team.players.append(User.query.get(num_users - (i+1)*2 + 2))
		db.session.add(team)
	db.session.commit()
	print("Created teams")

def create_divisions(num_divisions):
	if Division.query.count() > 0:
		print("Already divisions ... not creating new divisions")
		return

	num_teams = Team.query.count()
	for i in range(num_divisions):
		div = Division(name="Division " + str(i+1))
		db.session.add(div)
		
		for t in range(int(num_teams*float(i)/num_divisions), int(num_teams*float(i+1)/num_divisions)):
			Team.query.get(t+1).division = div
	db.session.commit()

def generate_rand_stat():
	s = Stats()
	stat_max = [25, 4, 6, 4, 5, 2]
	stat_arr = [random.randrange(st) for st in stat_max]
	s.set_stats(stat_arr, 1)
	return s

def generate_game(t1, t2):
	print("Creating game for " + t1.name + " : " + t2.name)

	score = random.randrange(6)
	game = Game(team_1_score=score, picture_file="Test")
	for s in range(4):
		game.player_stats.append(generate_rand_stat())

	print(t1.players)
	print(t2.players)
	game.players = [t1.players[0], t1.players[1], t2.players[0], t2.players[1]]
	game.is_sub = [False, False, False, False]
	if random.randrange(5) == 0:
		user = User.query.get(random.randrange(User.query.count())+1)
		if user.id not in [u.id for u in game.players]:
			i = random.randrange(4)
			game.players[i] = user
			game.is_sub[i] = True
	game.teams = [t1, t2]
	return game
	

def run_season(num_games):
	num_teams = Team.query.count()

	season = Season.query.first()
	if season is None:
		print("Creating season")
		db.session.add(Season(name="Generated Season", date_start=datetime.today(), date_end=(datetime.today() + timedelta(days=1))))
		db.session.commit()

	for i in range(num_games):
		t1 = Team.query.get(random.randrange(num_teams)+1)
		if random.randrange(3) < 2:
			ids = [div_t.id for div_t in t1.division.teams if div_t.id != t1.id]
			t2 = Team.query.get(ids[random.randrange(len(ids))])
		else:
			n = random.randrange(num_teams-1)+1
			t2 = Team.query.get(n if n < t1.id else n+1)

		g = generate_game(t1,t2)
		db.session.add(g)
		db.session.commit()

		g.verified = True
		calculate_stats(g.teams, g.players)
		db.session.commit()

	
	print("Created games")



import sys
if __name__ == '__main__':
	users = 80
	teams = 40
	divisions = 8
	games = 10
	if "init" in sys.argv:
		import init_test_database
		create_users(users)
	if "extend" not in sys.argv:
		create_teams(teams)
		create_divisions(divisions)
	run_season(games)



from datetime import datetime, timedelta

from flask import (
    render_template, request, Blueprint, redirect, url_for, abort, flash, 
    Response
)
from flask.typing import ResponseReturnValue
from flask_login import current_user

from recLeague import db, bcrypt
from recLeague.models import (
    User, Game, Team, Division, Season, Settings, Stats, player_game_table, 
    team_game_table, ArchivedSeason
)
from recLeague.admin.forms import (
    UserForm, UsersListForm, TeamsListForm, CreateSeasonForm, 
    SeasonForm, SettingsForm, ArchiveSeasonForm
)
from recLeague.admin.utils import get_team_csv_text
from recLeague.config import (
    DIVISION_NAMES, SCORECARD_PICS_PATH, STAT_CATEGORY_KEYS
)


admin = Blueprint('admin', __name__)


@admin.route("/admin/users", methods=['GET', 'POST'])
def users() -> ResponseReturnValue:
    if current_user.is_admin is False:
        abort(403)

    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.name) \
        .filter(User.id != 1, User.name != "Guest Player") \
        .paginate(page=page, per_page=20)

    form = UsersListForm()
    if form.validate_on_submit():
        if form.submit.data is False:
            return

        for i, user in enumerate(form.users):
            u = users.items[i]
            u.is_banned = user.status.data == 1
            u.is_admin = user.status.data == 2
        db.session.commit()
        flash('Users have been updated!', 'success')
        return redirect(url_for('admin.users'))
    
    if request.method == 'GET':
        for user in users.items:
            u = UserForm()
            if user.is_banned:
                u.status = 1
            elif user.is_admin:
                u.status = 2
            form.users.append_entry(u)

    return render_template(
        'admin_users.html', title='Users', form=form, users=users
    )


@admin.route("/admin/games", methods=['GET', 'POST'])
def games() -> ResponseReturnValue:
    if current_user.is_admin is False:
        abort(403)

    page = request.args.get('page', 1, type=int)
    game_cat = request.args.get('cat', "Unverified", type=str)
    games = Game.query.filter(game_cat == 'All' or Game.verified == False) \
        .order_by(Game.date_posted.desc()).paginate(page=page, per_page=20)

    # TODO: Remove sqlalchemy legacy code with new way of querying
    # if game_cat == 'All':
    #     game_select = db.select(Game)
    # else:
    #     game_select = db.select(Game).filter_by(verified=False)

    # games = db.paginate(
    #     game_select.order_by(Game.date_posted.desc()), page=page, per_page=20
    # )

    return render_template(
        'admin_games.html', title='Games', games=games, cat=game_cat
    )


@admin.route("/admin/teams", methods=['GET', 'POST'])
def teams() -> ResponseReturnValue:
    if current_user.is_admin is False:
        abort(403)

    all_teams = Team.query.all()
    form = TeamsListForm(all_teams)

    if form.validate_on_submit():
        if form.submit.data is False:
            return

        for i, team in enumerate(form.teams):
            db_team = all_teams[i]
            
            db_team.players.clear()
            for player in team.players:
                if player.data > 0:
                    db_team.players.append(User.query.get(player.data))

            db_team.division = (Division.query.get(team.division.data) 
                                if team.division.data > 0 else None)

        db.session.commit()
        flash('Teams have been updated!', 'success')
        return redirect(url_for('admin.teams'))

    return render_template(
        'admin_teams.html', title='Teams', form=form, teams=all_teams
    )


@admin.route("/admin/season/new", methods=['GET', 'POST'])
def create_season() -> ResponseReturnValue:
    if current_user.is_admin is False:
        abort(403)

    season = Season.query.first()
    if season is not None:
        flash('Season has already been created', 'warning')
        return redirect(url_for('main.home'))

    form = CreateSeasonForm()
    if form.validate_on_submit():
        s = Season(
            name=form.season_name.data, date_start=form.date_start.data,
            date_end=form.date_end.data)
        db.session.add(s)

        for i in range(form.divisions.data):
            d = Division(name=DIVISION_NAMES[i])
            db.session.add(d)

        db.session.commit()
        flash('Season has been created!', 'success')
        return redirect(url_for('main.home'))

    # Init season form with current day
    if request.method == 'GET': 
        yr = datetime.today().year
        period = "Spring" if datetime.today().month < 6 else "Fall"
        def_name = period + " " + str(yr)[-2:] + " season"
        default_start_date = datetime.today() + timedelta(days=7)

        form.season_name.data = def_name
        form.date_start.data = default_start_date

    return render_template(
        'admin_create_season.html', title='Create Season', form=form
    )


@admin.route("/admin/season", methods=['GET', 'POST'])
def season() -> ResponseReturnValue:
    if current_user.is_admin is False:
        abort(403)

    season = Season.query.first()
    if season is None:
        return redirect(url_for('admin.create_season'))
    
    form = SeasonForm()
    archive_form = ArchiveSeasonForm()
    team_choices = [
        (t.id, t.name) 
        for t in Team.query.order_by('name') if len(t.players) >= 2
    ]
    archive_form.champion_team.choices = team_choices
    archive_form.runner_up_team.choices = team_choices

    if datetime.now() > season.date_start:
        form.date_start.data = season.date_start

    empty_season = Game.query.count() == 0

    if form.validate_on_submit():
        if form.submit.data is False:
            return

        season.name = form.season_name.data
        season.date_start = form.date_start.data
        season.date_end = form.date_end.data
        db.session.commit()
        flash('Season has been updated!', 'success')
        return redirect(url_for('admin.season'))

    if request.method == 'GET':
        form.season_name.data = season.name
        form.date_start.data = season.date_start
        form.date_end.data = season.date_end
    
    return render_template(
        'admin_season.html', title='Season', form=form, 
        archive_form=archive_form, empty_season=empty_season
    )


def create_archived_season(s, form):
    # Long way of counting teams with 2 players ... possibly in 
    # future try to make this a query
    teams = Team.query.all()
    team_count = 0
    for t in teams:
        if len(t.players) >= 2:
            team_count += 1

    arch_season = ArchivedSeason(
        name=s.name, date_start=s.date_start, date_end=s.date_end, 
        num_games=Game.query.count(), num_teams=team_count, 
        num_divisions=Division.query.count()
    )

    if form.summary.data is not None:
        arch_season.summary = form.summary.data

    champion_team = Team.query.get(form.champion_team.data)
    arch_season.champion_team_name = champion_team.name
    for p in champion_team.players:
        arch_season.champions.append(p)

    runner_up_team = Team.query.get(form.runner_up_team.data)
    arch_season.runner_up_team_name = runner_up_team.name
    for p in runner_up_team.players:
        arch_season.runner_ups.append(p)

    db.session.add(arch_season)


@admin.route("/admin/season/delete", methods=['POST'])
def delete_season() -> ResponseReturnValue:
    season = Season.query.first_or_404()
    if season.is_active():
        abort(403)

    # Only create archived season if we have games in the season
    if Game.query.count() > 0:
        form = ArchiveSeasonForm()
        team_choices = [
            (t.id, t.name) 
            for t in Team.query.order_by('name') if len(t.players) >= 2
        ]
        form.champion_team.choices = team_choices
        form.runner_up_team.choices = team_choices

        create_archived_season(season, form)

    users = User.query.all()
    for u in users:
        # Setting team to None might not be the best, 
        # also might need to do this on games also
        u.team = None
        num_stats = len(STAT_CATEGORY_KEYS)
        if u.season_stats is not None:
            if u.prev_season_stats is None:
                u.prev_season_stats = Stats()
                u.prev_season_stats.set_stats([0]*num_stats, 0)
            u.prev_season_stats.add_stats(u.season_stats)

            if u.prev_season_best_stats is None:
                u.prev_season_best_stats = Stats()
                u.prev_season_best_stats.set_stats([0]*num_stats, 0)
            u.prev_season_best_stats.max_stats(u.season_stats)

            if u.prev_season_high_stats is None:
                u.prev_season_high_stats = Stats()
                u.prev_season_high_stats.set_stats([0]*num_stats, 0)
            u.prev_season_high_stats.max_stats(u.season_high_stats)
            
            db.session.delete(u.season_stats)
    
    # Game stat deletion could possibly be changed with a relationship 
    # cascade instead of this
    for game in Game.query.all():
        for stat in game.player_stats:
            db.session.delete(stat)

    # TODO: Do we need this commit here? It might cause issues if we run into an 
    # error midway through
    db.session.commit()

    Game.__table__.drop(db.engine)
    Team.__table__.drop(db.engine)
    Division.__table__.drop(db.engine)
    Season.__table__.drop(db.engine)

    player_game_table.drop(db.engine)
    team_game_table.drop(db.engine)

    db.session.commit()
    db.create_all()

    # Delete scorecard photos
    import os
    d = SCORECARD_PICS_PATH
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))

    flash('Season has been archived!', 'success')
    return redirect(url_for('main.home'))


@admin.route("/admin/settings", methods=['GET', 'POST'])
def settings() -> ResponseReturnValue:
    s = Settings.query.first()
    form = SettingsForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data) \
            .decode('utf-8')
        s.password = hashed_password
        db.session.commit()
        flash('Updated settings!', 'success')
        return redirect(url_for('admin.settings'))

    if request.method == 'GET':
        pass  # Future settings initialized in form here

    return render_template('admin_settings.html', title='Settings', form=form)


@admin.route("/admin/stats")
def stats() -> ResponseReturnValue:
    return render_template('admin_stats.html', title='Stats')


@admin.route("/admin/teamsCSV")
def downloadTeamsCSV() -> ResponseReturnValue:
    csv = get_team_csv_text()
    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition":
                 "attachment; filename=LeagueTeams.csv"})

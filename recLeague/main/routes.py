from flask import (
    render_template, request, Blueprint, redirect, url_for, flash, abort
)
from flask.typing import ResponseReturnValue
from flask_login import current_user, logout_user

from recLeague.config import (
    BRANDING, APPEARANCE, STAT_HIGHLIGHT
)
from recLeague.models import Game, Season, User, Team

main = Blueprint('main', __name__)


@main.route("/")
@main.route("/home")
def home() -> ResponseReturnValue:
    """ Home page route - displays all games by date descending """
    page = request.args.get('page', 1, type=int)
    
    games = Game.query.order_by(Game.date_posted.desc()) \
        .paginate(page=page, per_page=20)
    # current_user.last_active = datetime.utcnow()

    return render_template(
        'home.html', title=current_user.name, games=games, 
        highlight_stat=STAT_HIGHLIGHT
    )


@main.route("/search", methods=['GET', 'POST'])
def search() -> ResponseReturnValue:
    """ Search page route - search users or games """
    users = None
    teams = None

    find = request.args.get('f', type=str)
    if find is not None:
        users = User.query.filter(
            User.id != 1, User.name != "Guest Player", User.name.contains(find)
        )
        teams = Team.query.filter(Team.name.contains(find))

    return render_template(
        'search.html', title='Search', users=users, teams=teams
    )


# Flask routes that non-athenticated users can go to
public_routes = [
    "users.login", "users.register", "users.reset_request", "users.reset_token"
]


@main.route("/auth")
def is_authenticated() -> ResponseReturnValue:
    """Indicates whether the user is currently logged in.
    
    Method is used by NGINX for authorized static routes.
    """
    if current_user.is_authenticated:
        return "", 200

    abort(401)


@main.before_app_request
def before_request() -> ResponseReturnValue:
    """ Flask method that gets called before every HTTP request """

    # Check if user is current user is banned ... if so log them out
    if current_user.is_authenticated and current_user.is_banned:
        logout_user()
        flash('You have been banned', 'warning')
        return redirect(url_for('users.login'))

    # If user is logged in or request route is in one of the public 
    # rotues ... return and let user go to route
    if (current_user.is_authenticated 
            or (request.endpoint 
                and (request.endpoint in public_routes 
                     or request.path.startswith("/static/public")))):
        return

    # Non-athenticated user is trying to go into private section 
    # of website ... redirect them to login
    return redirect(url_for('users.login', next=request.path))


@main.app_context_processor
def inject_data():
    """ Injects data for jinja to use """
    if current_user.is_authenticated is False:
        return dict(branding=BRANDING, appearance=APPEARANCE)

    # User is authenticated so pass in season data to be used in the 
    # navbar in layout.html
    season = Season.query.first()
    return dict(season=season, branding=BRANDING, appearance=APPEARANCE)

    

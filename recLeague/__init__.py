import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail

from recLeague.config import (
    FlaskConfig,
    SQLALCHEMY_DATABASE_URI,
)

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'
csrf = CSRFProtect()
mail = Mail()


# Create the Flask application ... initialize all modules & blueprints
def create_app() -> Flask:
    """Creates Flask application object.
    
    This method sets the app configuration and imports app the blueprints.

    Returns:
        Flask: application object
    """
    app = Flask(__name__)

    app.config.from_object(FlaskConfig)

    # Set SQLAlchemy URI from configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
    
    # If we set Flask config path environment variable, use the file to fill 
    # in our app config
    if os.environ.get("FLASK_CONFIG_PATH") is not None:
        print(f"Using Flask config at {os.environ.get('FLASK_CONFIG_PATH')}")
        app.config.from_envvar("FLASK_CONFIG_PATH")

    if (app.config["DEBUG"] is False 
       and app.config["SECRET_KEY"] == FlaskConfig().SECRET_KEY):
        raise SystemExit("SECRET_KEY is not set! If you in production mode "
                         "set the Flask SECRET_KEY before continuing. "
                         "Otherwise if you are testing locally, set DEBUG "
                         "to true.")

    print(f"Using database: {SQLALCHEMY_DATABASE_URI}")

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    
    from recLeague.users.routes import users
    from recLeague.games.routes import games
    from recLeague.teams.routes import teams
    from recLeague.main.routes import main
    from recLeague.admin.routes import admin
    from recLeague.stats.routes import stats
    # from recLeague.errors.handlers import errors

    app.register_blueprint(users)
    app.register_blueprint(games)
    app.register_blueprint(teams)
    app.register_blueprint(main)
    app.register_blueprint(admin)
    app.register_blueprint(stats)
    # app.register_blueprint(errors)

    return app

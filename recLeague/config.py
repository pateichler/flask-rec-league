import os
import shutil
import json
import base64
import hashlib
from urllib.parse import urlparse


class FlaskConfig:
    """Default Flask configuration.
    
    See :doc:`Flask configuration <flask_config>` for overriding these values.
    """
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_DEBUG = False

    SECRET_KEY = "DEFAULT_SECRET_KEY"

    DEBUG = True


def copy_default_config_file():
    shutil.copyfile(
        get_config_path("default.json", "config"),
        get_config_path("my_config.json", "config")
    )


def get_config_path(path: str, base_path: str) -> str:
    extension = os.path.splitext(path)[1]

    if extension == '':
        path += '.json'
    elif extension != '.json':
        raise Exception(f"Unable to use config with {extension}. Config must \
        be .json file")

    if os.path.isabs(path) is False:
        abs_path = os.path.join(os.path.dirname(__file__), "..")
        path = os.path.join(abs_path, base_path, path)

    return path


def load_config_file(path: str) -> dict:
    if os.path.isfile(path) is False:
        raise Exception("ERROR: Could not find configuration file: "
                        + path)

    with open(path) as f:
        try:
            return json.load(f)
        except json.decoder.JSONDecodeError as e:
            print(f"Problem with configuration file at: {path}\n\
                See the following app config decoding error:\n")
            raise SystemExit(e)


_config_path = os.environ.get("LEAGUE_CONFIG_PATH")

# Check if empty config name ... is so change to default config name and copy 
# file if doesn't already exist
if _config_path is None:
    _config_path = "my_config.json"
    if os.path.isfile(get_config_path(_config_path, "config")) is False:
        copy_default_config_file()

CONFIG_PATH: str = get_config_path(_config_path, "config")
""" Path for loading the initial configuration ``.json`` file relative to 
    config folder or as absolute path.
    
    Variable is set from environment variable named 
    :ref:`LEAGUE_CONFIG_PATH <LEAGUE_CONFIG_PATH>`. If no environment variable 
    is set, the default value is ``my_config.json``.
    
    :meta hide-value:
"""

config_dict = load_config_file(CONFIG_PATH)

SQLALCHEMY_DATABASE_URI: str = config_dict["SQLALCHEMY_DATABASE_URI"]
""" Database URI for Flask SQLAlchemy.
    
    **JSON Path:** ``/SQLALCHEMY_DATABASE_URI``

    :meta hide-value:
"""

LEAGUE_NAME: str = config_dict["LEAGUE_INFO"].get("leage_name", "Rec League")
""" Name of the league.
    
    **JSON Path:** ``/LEAGUE_INFO/league_name``

    :meta hide-value:
"""

NUM_TEAM_PLAYERS: int = int(config_dict["NUM_TEAM_PLAYERS"])  # Test comment 4
""" Number of players on each team.
    
    **JSON Path:** ``/NUM_TEAM_PLAYERS``
    
    .. warning::

        This property is unable to change after initialization.
    
    :meta hide-value:
"""

# Game settings
score = config_dict["GAME"].get("score")
MIN_GAME_SCORE: int = int(score.get("min", 0) if score is not None else 0)
""" Minimum required score in a game.
    
    **JSON Path:** ``/GAME/score/min``

    :meta hide-value:
"""
MAX_GAME_SCORE: int = score.get("max", None) if score is not None else None
""" Maximum required score in a game.
    
    **JSON Path:** ``/GAME/score/max``

    :meta hide-value:
"""

SCORECARD_REQUIRED: bool = config_dict["GAME"].get("require_scorecard", False)
""" Boolean if scorecard is required with Game form.
    
    **JSON Path:** ``/GAME/require_scorecard``

    :meta hide-value:
"""

# Stat settings
# TODO: Validate stat settings to make sure they didn't change
STAT_CATEGORIES: list[dict] = list(config_dict["STATS"]["categories"])
""" Categories of game statistics.
    
    **JSON Path:** ``/STATS/categories``

    .. warning::

        This property is unable to change after initialization.

    :meta hide-value:
"""
STAT_HIGHLIGHT: str = config_dict["STATS"]["highlight"]
""" Statistic to highlight in quick game summary.
    
    **JSON Path:** ``/STATS/highlight``

    :meta hide-value:
"""

STAT_CATEGORY_KEYS: list[str] = [c["key"] for c in STAT_CATEGORIES]
STAT_CATEGORY_NAMES: list[str] = [c["name"] for c in STAT_CATEGORIES]


# Divisions
DIVISION_NAMES: list[str] = list(
    config_dict["DIVISION"].get("names", ["East", "West", "South", "North"])
)
""" Names of divisions.
    
    **JSON Path:** ``/DIVISION/names``

    :meta hide-value:
"""

MAX_DIVISIONS: int = (
    config_dict["DIVISION"].get("max_num", len(DIVISION_NAMES))
)
""" Maximum number of divisions when creating a season.
    
    **JSON Path:** ``/DIVISION/max_num``

    :meta hide-value:
"""
DEFUALT_NUM_DIVISIONS: int = config_dict["DIVISION"].get(
    "default_num", len(DIVISION_NAMES)
) 
""" Default number of divisions when creating a season.
    
    **JSON Path:** ``/DIVISION/max_num``

    :meta hide-value:
"""

assert MAX_DIVISIONS <= len(DIVISION_NAMES)
assert DEFUALT_NUM_DIVISIONS <= len(DIVISION_NAMES)


# Leaderboard
MIN_SEASON_AVERAGE_GAMES: int = int(
    config_dict["LEADERBOARD"].get("min_season_average_games", 3)
)
""" Minimum number of seasonal games for a user to be displayed on the season 
    average leaderboard.
    
    **JSON Path:** ``/LEADERBOARD/min_season_average_games``

    :meta hide-value:
"""
MIN_LIFETIME_AVERAGE_GAMES: int = int(
    config_dict["LEADERBOARD"].get("min_lifetime_average_games", 5)
)
""" Minimum number of lifetime games for a user to be displayed on the lifetime 
    average leaderboard.
    
    **JSON Path:** ``/LEADERBOARD/min_lifetime_average_games``

    :meta hide-value:
"""


# Scorecard pics
def get_scorecard_pics_static_path():
    # TODO: Comment on method

    uri = SQLALCHEMY_DATABASE_URI
    file_name = os.path.splitext(os.path.basename(urlparse(uri).path))[0]
    
    hasher = hashlib.sha1(uri.encode('utf-8'))
    hashed_name = base64.urlsafe_b64encode(
        hasher.digest()[:10]
    ).decode('utf-8')[:-2]

    directory = "_".join([file_name, hashed_name])
    
    return os.path.join("scorecard_pics", directory)


SCORECARD_PICS_STATIC_PATH: str = get_scorecard_pics_static_path()
""" Path to scorecard pics relative to the static folder.
    
    This is dynamically created from :py:data:`SQLALCHEMY_DATABASE_URI` by
    using the basename of the URI in combination with the full URI hashed to a 
    10 character hash. The two names are combined with a "`_`" as shown below.

    .. code-block::
        
        {uri_basename}_{hashed_uri}
    
    This naming scheme is beneficial when using multiple database URIs in order 
    to avoid overwriting other databases images. The basename is to make the 
    folder easily found by a human, and the hash is to make sure the path is 
    unique for URI. Without the hash a collision could occur for example:

    .. code-block::
        
        site:///test.db
        - vs. -
        site:///folder/test.db

    :meta hide-value:
"""


SCORECARD_PICS_PATH: str = os.path.join(
    "recLeague", "static", SCORECARD_PICS_STATIC_PATH
)
""" Path to scorecard pics relative to the recLeague module path.

    :meta hide-value:
"""

# Appearance
branding_dict = config_dict["LEAGUE_INFO"]["branding"]

BRANDING = {}

BRANDING["primary_logo"] = branding_dict.get(
    "primary_logo", "public/examples/default/Logo.png"
)
""" Path to primary logo.
    
    **JSON Path:** ``/LEAGUE_INFOG/branding/primary_logo``

    :meta hide-value:
"""
BRANDING["alternate_logo"] = branding_dict.get(
    "alternate_logo", "public/examples/default/AlternateLogo.png"
)
""" Path to alternate logo.
    
    **JSON Path:** ``/LEAGUE_INFOG/branding/alternate_logo``

    :meta hide-value:
"""
BRANDING["fav_icon"] = branding_dict.get(
    "fav_icon", "public/examples/default/icons/favicon.ico"
)
""" Path to fav icon ``.ico`` file.
    
    **JSON Path:** ``/LEAGUE_INFOG/branding/fav_icon``

    :meta hide-value:
"""
BRANDING["fav_icon_svg"] = branding_dict.get(
    "fav_icon_svg", "public/examples/default/icons/favicon.svg"
)
""" Path to fav icon ``.svg`` format.
    
    **JSON Path:** ``/LEAGUE_INFOG/branding/fav_icon_svg``

    :meta hide-value:
"""

APPEARANCE_PATH: str = get_config_path(
    config_dict["APPEARANCE"].get("path", "default"), 
    os.path.join("config", "appearance")
)
""" Path to appearance ``.json`` file relative to config/appearance folder or 
    as absolute path.
    
    **JSON Path:** ``/primary_color``

    :meta hide-value:
"""
appearance_dict = load_config_file(APPEARANCE_PATH)
APPEARANCE: dict = {}
""" Dictionary for website appearance.
    
    Values are loaded from JSON file at :py:data:`APPEARANCE_PATH`. Default 
    appearance is located at ``config/appearance/default.json`` with the 
    values included below.
    
    .. include:: ../../config/appearance/default.json
        :code: json

    **Entries**:

        **primary_color**: Primary color of the website.

            *json path*: /primary_color

        **secondary_color**: Secondary color of the website.

            *json path*: /secondary_color

        **primary_font_color**: Font color for when text is on the primary 
            color.

            *json path*: /primary_font_color

        **secondary_font_color**: Font color for when text is on the secondary 
            color.

            *json path*: /secondary_font_color

        **background_color**: Background color of the website.
            color.

            *json path*: /background_color

        **background_accent_color**: Background accent color of the website.
            color.

            *json path*: /background_accent_color

        **background_accent_overlap_color**: Background accent color when 
            color overlaps itself.

            *json path*: /background_accent_overlap_color

        **background_font_color**: Font color for when text is on the 
            background color.

            *json path*: /background_font_color

        **background_font_color_alternate**: Alternate font color for when 
            text is on the background color.

            *json path*: /background_font_color_alternate
    
    :meta hide-value:
"""

APPEARANCE["primary_color"] = appearance_dict.get(
    "primary_color", "#ef3d3d"
)
""" Primary color of the website.
    
    **Appearance JSON Path:** ``/primary_color``

    :meta hide-value:
"""
APPEARANCE["secondary_color"] = appearance_dict.get(
    "secondary_color", "#6c757d"
)
""" Secondary color of the website.
    
    **Appearance JSON Path:** ``/secondary_color``

    :meta hide-value:
"""
APPEARANCE["primary_font_color"] = appearance_dict.get(
    "primary_font_color", "white"
)
""" Font color for when text is on the primary color.
    
    **Appearance JSON Path:** ``/primary_font_color``

    :meta hide-value:
"""
APPEARANCE["secondary_font_color"] = appearance_dict.get(
    "secondary_font_color", "white"
)
""" Font color for when text is on the secondary color.
    
    **Appearance JSON Path:** ``/secondary_font_color``

    :meta hide-value:
"""
APPEARANCE["background_color"] = appearance_dict.get(
    "background_color", "white"
)
""" Background color of the website.
    
    **Appearance JSON Path:** ``/background_color``

    :meta hide-value:
"""
APPEARANCE["background_accent_color"] = appearance_dict.get(
    "background_accent_color", "#E5E5E5"
)
""" Background accent color of the website.
    
    **Appearance JSON Path:** ``/background_accent_color``

    :meta hide-value:
"""
APPEARANCE["background_accent_overlap_color"] = appearance_dict.get(
    "background_accent_overlap_color", "#CECECE"
)
""" Background accent overlap color of the website.
    
    **Appearance JSON Path:** ``/background_accent_overlap_color``

    :meta hide-value:
"""
APPEARANCE["background_font_color"] = appearance_dict.get(
    "background_font_color", "#212529"
)
""" Font color for when text is on the background color.
    
    **Appearance JSON Path:** ``/background_font_color``

    :meta hide-value:
"""
APPEARANCE["background_font_color_alternate"] = appearance_dict.get(
    "background_font_color_alternate", "lightgray"
)
""" Alternate font color for when text is on the background color.
    
    **Appearance JSON Path:** ``/background_font_color_alternate``

    :meta hide-value:
"""

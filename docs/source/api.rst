API
===

The following is the API documentation.

.. automodule:: recLeague
	:members:

Routes
------

Below are the API routes. Flask template routes for the application are not listed .

.. autoflask:: run:app
	:endpoints: main.is_authenticated, teams._get_team_players, teams._get_teams_latest_game_score, admin.downloadTeamsCSV


Environment Variables
---------------------

.. _FLASK_CONFIG_PATH:

Flask Config Path
^^^^^^^^^^^^^^^^^

``FLASK_CONFIG_PATH``

Path to a configuration file used to set Flask ``app.config``. Path should be absolute. See `flask.Config.from_envvar <https://flask.palletsprojects.com/en/3.0.x/api/#flask.Config.from_envvar>`_ for details about the config file.

.. _LEAGUE_CONFIG_PATH:

League Config Path
^^^^^^^^^^^^^^^^^^

``LEAGUE_CONFIG_PATH``

Path to a JSON configuration for league settings. See :ref:`config <config>` for details about the JSON file. Supports either relative or absolute paths. Relative paths are from the directory ``flask-rec-league/config``.

.. _config:

Configuration
-------------

Configuration is handled by JSON files. Default configuration is located at ``config/default.json`` with the values shown below.

.. include:: ../../config/default.json
	:code: json

.. automodule:: recLeague.config
	:members:
	:exclude-members: APPEARANCE

Appearance
^^^^^^^^^^

.. autodata:: recLeague.config.APPEARANCE


Database
--------

Database built with SQLAlchemy. 

.. automodule:: recLeague.models
	:members:
	:exclude-members: query


Utils
-----

.. automodule:: recLeague.games.utils
	:members:

.. automodule:: recLeague.users.utils
	:members:

.. automodule:: recLeague.admin.utils
	:members:


Forms
-----

.. automodule:: recLeague.games.forms
	:members:

.. automodule:: recLeague.users.forms
	:members:

.. automodule:: recLeague.teams.forms
	:members:

.. automodule:: recLeague.admin.forms
	:members:
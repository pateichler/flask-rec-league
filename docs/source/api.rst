API
===

The following is the API documentation.

.. automodule:: recLeague
	:members:

Environment Variables
---------------------

TODO: List environment variables

Command Line Interface
----------------------

TODO?

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

Games
^^^^^
.. automodule:: recLeague.games.utils
	:members:

Users
^^^^^
.. automodule:: recLeague.users.utils
	:members:

Admin
^^^^^
.. automodule:: recLeague.admin.utils
	:members:


Forms
-----

Games
^^^^^
.. automodule:: recLeague.games.forms
	:members:

Users
^^^^^
.. automodule:: recLeague.users.forms
	:members:

Teams
^^^^^
.. automodule:: recLeague.teams.forms
	:members:

Admin
^^^^^
.. automodule:: recLeague.admin.forms
	:members:
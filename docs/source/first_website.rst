Creating your first website
===========================

After :ref:`installation <installation>` you are ready to start to build your own custom rec league and deploy it on the internet.


Creating your configuration
---------------------------

Navigate to the config folder and duplicate the ``default.json`` config file to your custom name. 

.. code-block::
	
	cp config/default.json config/<your_config_path>.json

.. tip::
	
	For easier configuration, you may choose ``my_config`` as ``<your_config_path>`` since it is the default config path.

Next, open the new config file in the editor of your choice. Change the league configuration to suit the needs of your rec league. 

Here is a quick summary of the most important configuration parameters:

* **SQLALCHMEY_DATBASE_URI**: URI of the database to be created. Leave unchanged for the default path.
* **NUM_TEAM_PLAYERS**: Number of players on each team.
* **STATS/categories**: Array of statistics to be tracked by the application. Each stat must contain a ``name`` and ``key`` field. ``name`` is the stat name displayed to users. ``key`` is the database key for internal use.

.. important::

	Currently the parameters listed above can not be changed without causing issues after initializing the application. This may be fixed in the future.


See :ref:`config API <config>` for more details on other configuration parameters.


Setting config path
-------------------

If you choose ``my_config`` as your name, you may skip the step of setting the config path because the default config path is ``my_config``.

Set the project to use your newly created configuration by setting the config path. You can set the config path by the environment variable ``LEAGUE_CONFIG_PATH``:

.. code-block::

	export LEAGUE_CONFIG_PATH='<your_config_path>.json'

.. note::
	
	Environment variables set in the command line are not permanently set. For more information on what environment variables are and how to manage them check out `Ubuntu's community wiki <https://help.ubuntu.com/community/EnvironmentVariables>`_.

Running
-------

Initialize the web app by running ``initalize.py``.

.. code-block::

	python initialize.py

After initialized, run the web app by running ``run.py``.

.. code-block::
	
	python run.py

The website is then viewable at ``localhost:8000``.

.. tip::

	If you want to quickly switch out configurations, instead of changing the environment variable, you may also run the python scripts as follows:

	.. code-block::

		python initialize.py <your_config_path>
		python run.py <your_config_path>


The website should be all functional except the password reset form. For setting up the email for password reset continue on.
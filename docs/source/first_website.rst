Creating your first website
===========================

After :ref:`installation <installation>` you are ready to start to build your own custom rec league and deploy it on the internet.


Creating your configuration
---------------------------

Navigate to the config folder and duplicate the ``default.json`` config file to your custom name. 

.. code-block::
	
	cp config/default.json config/<your_config_path>.json

.. tip::
	
	For easier configuration, you may choose ``my_config`` as the config name since it is the default config path.

See TODO: Link config for settings the variables in the config file.


Setting config path
-------------------

If you choose ``my_config`` as your name, you may skip the step of setting the config path because the default config path is ``my_config``

Set the project to use your newly created configuration by setting the config path. You can set the config path by the environment variable ``LEAGUE_CONFIG_PATH``:

.. code-block::

	export LEAGUE_CONFIG_PATH='<your_config_path>.json'

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
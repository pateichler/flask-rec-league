Getting Started
===============

Requirements
------------

The web application is ran with Python. Rec Leagues is developed specifically with Python version 3.11.6. Other versions of Python 3 are not tested and not guaranteed to work. See the website for `Python <https://www.python.org>`_ for directions on installing Python.

A Python virtual environment is recommended for this application to maintain a clean separated workspace. There are many ways of setting up Python virtual environments. For a specific option check out `Python venv <https://docs.python.org/3/library/venv.html>`_.

.. _installation:

Installation
------------

The code is hosted on the `GitHub repository <https://github.com/pateichler/flask-rec-league>`_. Clone the repository to download the source code in your desired path.

.. code-block::

	git clone https://github.com/pateichler/flask-rec-league.git


Once installed, navigate to the repository. 

.. code-block::
	
	cd RecLeague


If you plan to use a Python virtual environment, create and activate the virtual environment.

Next, install the required Python packages via `pip <https://pip.pypa.io>`_.

.. code-block::
	
	pip install -r requirements.txt


Running website
---------------

After the repository and packages are installed, run an example.

.. code-block::

	python initialize.py
	python run.py

The output from the ``initialize.py`` will give the league password for creating new users, as well as the root user username and password. View the website by going to: ``localhost:8000``.
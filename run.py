""" Script runs the server.

Use command line arguments for testing.
"""

import os
from cli.helper import create_app, database_exists

app = create_app()

if __name__ == '__main__':
    if database_exists(app) is False:
        print("ERROR: Database not initialized! \
            Initialize app to create database.")
    else:
        port = os.environ.get('FLASK_PORT')
        app.run(port=(8000 if port is None else port))

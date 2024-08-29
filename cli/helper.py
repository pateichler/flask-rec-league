import sys

from sqlalchemy import inspect

from recLeague import create_app as create
from recLeague import db


def create_app():
    return create()


def get_answer(prompt):
    # Skip prompt if forced
    if "--forced" in sys.argv:
        return True

    print(prompt + " [Y]es or [N]o")
    
    yes = {'yes', 'y', 'ye', ''}
    no = {'no', 'n'}

    for i in range(3):
        try:
            choice = input().lower()
        except KeyboardInterrupt:
            return False

        if choice in yes:
            return True
        elif choice in no:
            return False
        else:
            print("Please respond with Y or N")

    print("Unable to parse response")
    return False


def database_exists(app):
    with app.app_context():
        inspector = inspect(db.engine)
        return inspector.has_table('user')
    return False

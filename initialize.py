import sys
import os
import secrets

from cli.helper import (
    create_app, database_exists, get_answer
)
from recLeague import db, bcrypt
from recLeague.config import SCORECARD_PICS_PATH
from recLeague.models import Settings, User


# Clear any existing database and create a new database
app = create_app()
app.app_context().push()

if database_exists(app):
    prompt = ("Database already exists. Do you wish to overwrite it with a "
              "new database?")

    if get_answer(prompt) is False:
        print("Canceling initialization")
        sys.exit()

db.drop_all()
db.create_all()


# Create initial settings data object
default_league_pass = "ChangeMe"
hashed_password = (
    bcrypt.generate_password_hash(default_league_pass).decode('utf-8')
)
s = Settings(password=hashed_password)
db.session.add(s)

print("=======================================")
print(f"League password: {default_league_pass}")
print("Make sure to change the league password")
print("=======================================")

# Create root user
random_hex = secrets.token_hex(8)
admin_pass = bcrypt.generate_password_hash(random_hex).decode('utf-8')
admin_user = User(
    name="League Admin", email="admin", password=admin_pass, is_admin=True
)
db.session.add(admin_user)
print("Created root user")
print("Email: admin")
print("Password: " + random_hex)
print("=======================================")

for i in range(2):
    guest_user = User(
        name="Guest Player", email=f"guest_{i+1}", password=admin_pass, 
        is_admin=False
    )
    db.session.add(guest_user)

db.session.commit()

# Clear photos
path = SCORECARD_PICS_PATH
if os.path.isdir(path):
    for f in os.listdir(path):
        os.remove(os.path.join(path, f))
else:
    os.makedirs(path)

print("App initialized")

import sys
import os
sys.path[0] = os.path.join(sys.path[0], "..")
from typing import Optional
import secrets

from cli.helper import create_app
from recLeague import db, bcrypt
from recLeague.models import User


def set_new_password(pw: Optional[str]):
    app = create_app()
    app.app_context().push()

    root_user = User.query.get(1)
    
    if pw is None:
        pw = secrets.token_hex(8)
    
    pw_encypted = bcrypt.generate_password_hash(pw).decode('utf-8')

    root_user.password = pw_encypted
    db.session.commit()
    print(f"Set new password to {pw}")


if __name__ == "__main__":
    set_new_password(None)

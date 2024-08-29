from util.cli import create_app
from recLeague import db
from recLeague.config import DIVISION_NAMES

if __name__ == "__main__":
    app = create_app()
    app.app_context().push()

    from recLeague.models import Division

    divs = Division.query.all()

    for i in range(len(divs)):
        divs[i].name = DIVISION_NAMES[i]

    db.session.commit()

    print("Set division names")

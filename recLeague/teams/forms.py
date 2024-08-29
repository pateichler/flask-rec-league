from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import ValidationError, Length

from recLeague.models import Team


class TeamCreateForm(FlaskForm):
    """Form for creating a new team.
    
    Attributes:
        team_name: 
        submit: 
    """
    team_name = StringField("Team Name", validators=[Length(min=2, max=40)])

    submit = SubmitField('Create team')

    def validate_team_name(self, t):
        t_query = Team.query.filter_by(name=t.data).first()
        if t_query:
            raise ValidationError('Team name already choosen. \
                Choose a different team name.')


class TeamJoinForm(FlaskForm):
    """Form for joining a team.
    
    Attributes:
        team: Select field to select joinable teams.
        submit: 
    """
    team = SelectField('Team', coerce=int)

    submit = SubmitField('Join team')

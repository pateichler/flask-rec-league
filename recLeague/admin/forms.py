from flask_wtf import FlaskForm
from wtforms import (
    SubmitField, SelectField, FieldList, FormField, StringField, 
    PasswordField, TextAreaField
)
from wtforms.validators import (
    ValidationError, Length, InputRequired, Optional, NumberRange
)
from wtforms.fields.html5 import IntegerField, DateTimeLocalField

from recLeague.models import User, Division
from recLeague.config import (
    NUM_TEAM_PLAYERS, DEFUALT_NUM_DIVISIONS, MAX_DIVISIONS
)


class UserForm(FlaskForm):
    """Form for User data editable by admin.
    
    Attributes:
        status: 
    """
    # TODO: Store status types in enum in config
    status = SelectField(
        'Banned', choices=[(0, 'Normal'), (1, 'Banned'), (2, 'Admin')], 
        coerce=int
    )


class UsersListForm(FlaskForm):
    """Form for all users for admin to edit.
    
    Attributes:
        users: 
        submit: 
    """
    users = FieldList(FormField(UserForm, label="Users"))
    submit = SubmitField('Update Users')
            

class TeamForm(FlaskForm):
    """Form for Team data editable by admin.
    
    Attributes:
        players: 
        division: 
    """
    players = FieldList(
        SelectField('Player', coerce=int), 
        max_entries=NUM_TEAM_PLAYERS
    )

    division = SelectField('Division', coerce=int)


class TeamsListForm(FlaskForm):
    """Form for all teams for admin to edit.
    
    Attributes:
        teams: 
        submit: 
    """
    teams = FieldList(FormField(TeamForm, label="Teams"))
    submit = SubmitField('Update Teams')

    def __init__(self, teams, *args, **kwargs):
        super(TeamsListForm, self).__init__(*args, **kwargs)

        # TODO: Maybe check if passed in teams length doesn't match current 
        # teams length, or maybe just check if request method is GET
        if len(self.teams) == 0:
            self._init_teams(teams)

        self._set_choices()

    def _init_teams(self, teams):
        for team in teams:
            team_form = self.teams.append_entry(TeamForm())

            for i in range(NUM_TEAM_PLAYERS):
                player = team.players[i] if i < len(team.players) else -1
                team_form.players.append_entry(player.id)

            team_form.division.data = (
                team.division.id if team.division is not None else -1
            )

    def _set_choices(self):
        player_choices = (
            [(-1, "---")] 
            + [(p.id, p.name) for p in User.query.order_by(User.name)
               .filter(User.id != 1, User.name != "Guest Player")]
        )
        division_choices = (
            [(-1, "---")] + [(d.id, d.name) for d in Division.query.all()]
        )
        
        for team in self.teams:
            # Set player choices
            for player_form in team.players:
                player_form.choices = player_choices

            # Set division choices
            team.division.choices = division_choices

    def validate_teams(self, teams):
        # Check to make sure player is not on any other teams
        selected_players = []
        for t in teams:
            for player in t.players:
                # Throw validation error if player already selected 
                # on different team
                if player.data in selected_players:
                    p_name = dict(player.choices).get(player.data)
                    raise ValidationError(
                        f"{p_name} can't be on multiple teams")

                # If player is selected for team ... add player
                # to selected players
                if player.data > 0:
                    selected_players.append(player.data)


class CreateSeasonForm(FlaskForm):
    """Form for creating a new season.
    
    Attributes:
        season_name: 
        date_end: 
        divisions: 
    """

    season_name = StringField(
        "Season name", validators=[Length(min=2, max=25)])

    date_start = DateTimeLocalField(
        "Start date", validators=[InputRequired()], format="%Y-%m-%dT%H:%M"
    )
    date_end = DateTimeLocalField(
        "End date", validators=[InputRequired()], format="%Y-%m-%dT%H:%M"
    )

    divisions = IntegerField(
        "Number of divisions", 
        validators=[InputRequired(), NumberRange(1, MAX_DIVISIONS)], 
        default=DEFUALT_NUM_DIVISIONS)

    submit = SubmitField('Create Season')

    def validate_date_end(self, end_date):
        if end_date.data < self.date_start.data:
            raise ValidationError("End date must be after start date")


class SeasonForm(FlaskForm):
    """Form for editing a current season.
    
    Attributes:
        season_name: 
        date_end: 
        submit: 
    """
    season_name = StringField(
        "Season name", validators=[Length(min=2, max=25)])

    date_start = DateTimeLocalField(
        "Start date", validators=[Optional()], format="%Y-%m-%dT%H:%M"
    )
    date_end = DateTimeLocalField(
        "End date", validators=[InputRequired()], format="%Y-%m-%dT%H:%M"
    )

    submit = SubmitField('Update season')

    def validate_date_end(self, end_date):
        if end_date.data < self.date_start.data:
            raise ValidationError("End date must be after start date")


class ArchiveSeasonForm(FlaskForm):
    """Form for archiving a season.
    
    Attributes:
        summary: 
        champion_team: 
        runner_up_team: 
        submit: 
    """
    summary = TextAreaField("Season summary")

    champion_team = SelectField('Champions', coerce=int)
    runner_up_team = SelectField('Runner-ups', coerce=int)

    submit = SubmitField('Archive')


class SettingsForm(FlaskForm):
    """Form for league settings.
    
    Attributes:
        password: 
    """

    password = PasswordField(
        "Registration password", validators=[Length(min=1, max=25)])

    submit = SubmitField('Update settings')

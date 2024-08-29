from typing import Optional, Sequence

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import (
    SubmitField, TextAreaField, SelectField, FieldList, FormField
)
from wtforms.validators import (
    InputRequired, ValidationError, Length, NumberRange
)
from wtforms.fields.html5 import IntegerField

from recLeague.models import User, Team, Stats, Game
from recLeague.config import (
    STAT_CATEGORIES, NUM_TEAM_PLAYERS, MIN_GAME_SCORE, MAX_GAME_SCORE, 
    STAT_CATEGORY_KEYS
)


class TeamCountValdiator(object):
    """ Custom wtform validator for validating stats between teams """
    def __init__(self, max_amount, team_id):
        self.max = max_amount
        self.team_id = team_id

    # Called when validating
    def __call__(self, form, field):
        """ Check if team stat is greater than maximum amount """
        total = 0
        player_range = (
            range(int(len(field)/2)) 
            if self.team_id == 0 else range(int(len(field)/2), len(field))
        )

        for i in player_range:
            total += field[i].data
        
        if total > self.max:
            raise ValidationError(
                f"Team {self.team_id + 1} total of {total} is greater than"
                f"max amount of {self.max}"
            )


def _get_stat_field_validators(stat_form_settings):
    validators = [InputRequired()]
    if stat_form_settings is not None:
        min_val = stat_form_settings.get("min", 0)
        max_val = stat_form_settings.get("max")

        validators.append(NumberRange(min_val, max_val))

    return validators


def _get_stat_list_validators(stat_form_settings):
    validators = []
    if stat_form_settings is not None:
        if "team_max" in stat_form_settings:
            validators.append(
                TeamCountValdiator(stat_form_settings["team_max"], 0)
            )
            validators.append(
                TeamCountValdiator(stat_form_settings["team_max"], 1)
            )
        if ("team_match_score" in stat_form_settings 
                and stat_form_settings["team_match_score"]):
            # TODO: calculate team total to match the score of the team
            pass

    return validators


def _init_stat_form_class(cls):
    max_entries = NUM_TEAM_PLAYERS * 2

    for cat in STAT_CATEGORIES:
        field_validators = _get_stat_field_validators(cat.get("form_settings"))
        list_validators = _get_stat_list_validators(cat.get("form_settings"))

        setattr(
            cls, cat["key"], 
            FieldList(IntegerField(
                validators=field_validators), validators=list_validators, 
                max_entries=max_entries, label=cat["name"]
            )
        )


# TODO: Possibly wrap StatForm in a constructor function to include all 
# dynamic code
class StatForm(FlaskForm):
    """Form for entering in game stats.
    
    Stats are set dynamically to this class using config stat names.
    """

    def set_stats(self, player_stats: Optional[Sequence[Stats]]) -> None:
        """Helper method sets stats in game form.
        
        Args:
            form (GameFrom): form to set
            player_stats (Optional[Sequence[Stats]]): stat values
        """

        for i in range(NUM_TEAM_PLAYERS * 2):
            for s in STAT_CATEGORY_KEYS:
                if player_stats is None:
                    val = 0
                else:
                    val = getattr(player_stats[i], s)

                getattr(self, s).append_entry(val)


_init_stat_form_class(StatForm)


class GameForm(FlaskForm):
    """Form for game data.
    
    Attributes:
        team_1: 
        team_2: 
        team_1_players: 
        team_2_players: 
        team_1_score: 
        team_2_score: 
        stats: 
        picture: 
        comment: 
        submit: 
    """
    team_1 = SelectField('Team 1', coerce=int)
    team_2 = SelectField('Team 2', coerce=int)

    team_1_players = FieldList(
        SelectField('Player', coerce=int), min_entries=NUM_TEAM_PLAYERS
    )
    team_2_players = FieldList(
        SelectField('Player', coerce=int), min_entries=NUM_TEAM_PLAYERS
    )

    _score_range = NumberRange(MIN_GAME_SCORE, MAX_GAME_SCORE)
    
    team_1_score = IntegerField(
        "Team 1 score", validators=[InputRequired(), _score_range]
    )
    team_2_score = IntegerField(
        "Team 2 score", validators=[InputRequired(), _score_range]
    )

    stats = FormField(StatForm, label="Stats")

    picture = FileField('Scorecard Picture')

    comment = TextAreaField('Comment', validators=[Length(max=100)])
    submit = SubmitField('Submit game')

    def __init__(self, is_updating: bool, *args, **kwargs):
        super(GameForm, self).__init__(*args, **kwargs)
        
        self._set_choices()
        self._set_picture_required(not is_updating)

    def _set_choices(self) -> None:
        """Sets the choices for team and player fields.
        
        Team choices are set to all teams in database with at least a full 
        team. Player choices are set to all players that have a team.
        """

        # Set team choices ... only have teams with 2 players
        # TODO: get query filter working
        # team_choices = [
        #     (t.id, t.name) 
        #     for t in Team.query.filter(
        #         func.length(Team.players) == 1
        #     ).order_by(Team.name)
        # ]

        team_choices = [
            (t.id, t.name) 
            for t in Team.query.order_by('name') 
            if len(t.players) >= NUM_TEAM_PLAYERS
        ] 
        self.team_1.choices = team_choices
        self.team_2.choices = [(-1, "---")] + team_choices

        # Possibly decide to let any user play in games?
        guest_players = [
            (u.id, "*Guest " + str(i+1)) 
            for i, u in enumerate(User.query.filter_by(name='Guest Player').all())
        ]
        player_choices = (
            guest_players + [
                (p.id, p.name) 
                for p in User.query.order_by(User.name)
                .filter(User.team != None)  # noqa: E711
            ]
        )
        
        add_players = len(self.team_1_players.data) == 0
        for i in range(NUM_TEAM_PLAYERS):
            if add_players:
                self.team_1_players.append_entry().choices = player_choices
                self.team_2_players.append_entry().choices = player_choices
            else:
                self.team_1_players[i].choices = player_choices
                self.team_2_players[i].choices = player_choices

    def _set_picture_required(self, required: bool) -> None:
        """Sets FileRequired attribute on picture field.
        
        Args:
            required (bool): If set True, FileRequired validator is added on 
            the picture field, otherwise FileRequired is removed.
        """

        if required:
            self.picture.validators = [
                FileAllowed(['jpg', 'png', 'jpeg']), FileRequired()
            ]
        else:
            self.picture.validators = [FileAllowed(['jpg', 'png', 'jpeg'])]    

    def set_form(self, game: Optional[Game]) -> None:
        """Sets the form with game data.
        
        Form is set with all data from the game object. If game is None, the 
        stat field will be initialized to an empty array of stats, and all 
        other fields will remain unset.

        Args:
            game (Optional[Game]): If given, sets form with data, otherwise 
                sets an empty form.
        """

        if game is None:
            self.stats.set_stats(None)
        else:
            self.stats.set_stats(game.player_stats)

            self.team_1_score.data = game.team_1_score
            self.team_2_score.data = game.team_2_score

            # Set team data
            self.team_1.data = game.teams[0].id
            self.team_2.data = game.teams[1].id

            # Set player data
            num_players = NUM_TEAM_PLAYERS
            for i in range(num_players):
                self.team_1_players[i].data = game.players[i].id
                self.team_2_players[i].data = game.players[i+num_players].id
            
            # Set game comment
            self.comment.data = game.comment

    def validate_team_2(self, team):
        if team.data < 0:
            raise ValidationError("Select a team")

        if team.data == self.team_1.data:
            raise ValidationError("Can't play yourself")

    def _validate_team_players(self, players):
        for i in range(len(players) - 1):
            for j in range(i+1, len(players)):
                if players[i].data == players[j].data:
                    players[i].errors.append("Player already choosen")
                    raise ValidationError("Invalid players")

    def validate_team_1_players(self, players):
        self._validate_team_players(players)

    def validate_team_2_players(self, players):
        self._validate_team_players(players)

        # Check with players from other team
        for i in range(len(players)):
            for j in range(len(players)):
                if players[i].data == self.team_1_players[j].data:
                    players[i].errors.append("Player already choosen")
                    raise ValidationError("Invalid players")

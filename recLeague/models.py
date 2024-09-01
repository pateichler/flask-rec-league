""" Script holds all sqlalchemy data models.
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Sequence, Optional

from itsdangerous import URLSafeTimedSerializer as Serializer
from itsdangerous.exc import BadSignature
from flask import current_app
from flask_login import UserMixin
from sqlalchemy.sql.expression import func, cast
from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy import or_
from sqlalchemy.ext.declarative import DeclarativeMeta

from recLeague import db, login_manager
from recLeague.config import (
    STAT_CATEGORY_KEYS, NUM_TEAM_PLAYERS
)

# Temp fix for mypy Model name error found here: 
# https://stackoverflow.com/questions/75774283/flask-sql-alchemy-and-mypy-error-with-db-model-incompatible-types-in-assignmen
# if TYPE_CHECKING:
#     from flask_sqlalchemy.model import Model
# else:
#     Model = db.Model

# Temp fix for mypy Model name error found here:
# https://github.com/dropbox/sqlalchemy-stubs/issues/76
BaseModel: DeclarativeMeta = db.Model


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


player_game_table = db.Table(
    'player_game_table',
    db.Column(
        'game_id', db.Integer, db.ForeignKey('game.id', ondelete="CASCADE")
    ),
    db.Column(
        'player_id', db.Integer, db.ForeignKey('user.id', ondelete="CASCADE")
    )
)

team_game_table = db.Table(
    'team_game_table',
    db.Column(
        'game_id', db.Integer, db.ForeignKey('game.id', ondelete="CASCADE")
    ),
    db.Column(
        'team_id', db.Integer, db.ForeignKey('team.id', ondelete="CASCADE")
    )
)


# Ideal statistics format would be array of integers stored as a single
# variable. Arrays are not supported with the database type. Need to switch to 
# Postgress if want arrays.
def init_stats(cls):
    for stat in STAT_CATEGORY_KEYS:
        setattr(
            cls, stat, db.Column(stat, db.Integer, nullable=False, default=0)
        )


class Stats(BaseModel):
    id = db.Column(db.Integer, primary_key=True)

    # _stat_keys: Sequence[str]
    game_count = db.Column(db.Integer, nullable=False, default=0)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))

    def get_stats(self) -> list[int]:
        return [getattr(self, stat) for stat in STAT_CATEGORY_KEYS]

    def set_stats(self, stats_arr: Sequence[int], game_count: int) -> None:
        for i in range(len(stats_arr)):
            setattr(self, STAT_CATEGORY_KEYS[i], stats_arr[i])
        
        self.game_count = game_count

    def add_stats(self, other_stats: Stats) -> None:
        for stat in STAT_CATEGORY_KEYS:
            setattr(
                self, stat, getattr(self, stat) + getattr(other_stats, stat)
            )
        
        self.game_count += other_stats.game_count

    def max_stats(self, other_stats: Stats) -> None:
        if other_stats is None:
            return

        for stat in STAT_CATEGORY_KEYS:
            setattr(
                self, stat, 
                max(getattr(self, stat), getattr(other_stats, stat))
            )

        self.game_count = max(self.game_count, other_stats.game_count)


init_stats(Stats)


class User(BaseModel, UserMixin):
    # Makes sure id's are never reused
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean(), default=False)
    is_banned = db.Column(db.Boolean(), default=False)
    date_joined = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow
    )
    # last_active = db.Column(db.DateTime)

    team_id = db.Column(
        db.Integer, db.ForeignKey('team.id', ondelete="CASCADE")
    )
    team = db.relationship("Team", backref="players", lazy=True)

    # Stats
    season_stats_id = db.Column(db.Integer, db.ForeignKey("stats.id"))
    season_stats = db.relationship(
        "Stats", foreign_keys=[season_stats_id], cascade="all, delete"
    )
    
    # Used for lifetime stats
    prev_season_stats_id = db.Column(db.Integer, db.ForeignKey("stats.id"))
    prev_season_stats = db.relationship(
        "Stats", foreign_keys=[prev_season_stats_id], cascade="all, delete"
    )

    # Used for single season best stats
    prev_season_best_stats_id = db.Column(
        db.Integer, db.ForeignKey("stats.id")
    )
    prev_season_best_stats = db.relationship(
        "Stats", 
        foreign_keys=[prev_season_best_stats_id], cascade="all, delete"
    )

    # Used for single game best
    season_high_stats_id = db.Column(db.Integer, db.ForeignKey("stats.id"))
    season_high_stats = db.relationship(
        "Stats", foreign_keys=[season_high_stats_id], cascade="all, delete"
    )

    # Used for single game best
    prev_season_high_stats_id = db.Column(
        db.Integer, db.ForeignKey("stats.id")
    )
    prev_season_high_stats = db.relationship(
        "Stats", foreign_keys=[prev_season_high_stats_id], cascade="all, delete"
    )

    def get_disp_name(self) -> str:
        s = ""
        if hasattr(self, "championships") and self.championships is not None:
            for c in self.championships:
                s += "🥇 "

        if hasattr(self, "second_places") and self.second_places is not None:
            for c in self.second_places:
                s += "🥈 "

        return s + self.name

    @hybrid_method
    def indv_stat(self, stat_type: str, stat_period: str, 
                  stat_period_2: Optional[str] = None, 
                  combine_max: bool = False, 
                  div_by_games: bool = False) -> int:
        mult = 1
        if div_by_games:
            mult = 1/self.indv_stat(
                "game_count", stat_period, stat_period_2, combine_max, False
            )

        per_1 = getattr(self, stat_period)
        if stat_period_2 is None:
            return (0 if per_1 is None else getattr(per_1, stat_type)) * mult

        per_2 = getattr(self, stat_period_2)
        
        if combine_max is False:
            return (((0 if per_1 is None else getattr(per_1, stat_type)) 
                    + (0 if per_2 is None else getattr(per_2, stat_type))) 
                    * mult)

        return mult * max(
            (0 if per_1 is None else getattr(per_1, stat_type)), 
            (0 if per_2 is None else getattr(per_2, stat_type))
        )

    @indv_stat.expression
    def indv_stat(cls, stat_type: str, stat_period: str, 
                  stat_period_2: Optional[str] = None, 
                  combine_max: bool = False, 
                  div_by_games: bool = False) -> int:
        # return None
        if stat_period_2 is None:
            if div_by_games:
                stat_per_game = (
                    cast(func.sum(getattr(Stats, stat_type)), db.Float) 
                    / cast(func.sum(getattr(Stats, "game_count")), db.Float)
                )

                return db.select(stat_per_game).\
                    where(Stats.id == getattr(cls, stat_period + "_id")).\
                    label('indv_stat')

            return db.select(func.sum(getattr(Stats, stat_type))).\
                where(Stats.id == getattr(cls, stat_period + "_id")).\
                label('indv_stat')

        comb_func = func.sum if combine_max is False else func.max
        if div_by_games:
            stat_per_game = (
                cast(comb_func(getattr(Stats, stat_type)), db.Float) 
                / cast(func.sum(getattr(Stats, "game_count")), db.Float)
            )

            return db.select(stat_per_game).\
                where(or_(
                    Stats.id == getattr(cls, stat_period + "_id"), 
                    Stats.id == getattr(cls, stat_period_2 + "_id")
                )).label('indv_stat')            

        return db.select(comb_func(getattr(Stats, stat_type))).\
            where(or_(
                Stats.id == getattr(cls, stat_period + "_id"), 
                Stats.id == getattr(cls, stat_period_2 + "_id")
            )).label('indv_stat')

    def get_reset_token(self) -> str:
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token: str) -> Optional[User]:
        s = Serializer(current_app.config['SECRET_KEY'])
        
        try:
            user_id = s.loads(token)['user_id']
        except BadSignature:
            return None

        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.name}', '{self.email}')"


class Game(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    
    team_1_score = db.Column(db.Integer, nullable=False)
    team_2_score = db.Column(db.Integer, nullable=False)
    
    player_stats = db.relationship("Stats", cascade="all, delete")

    picture_file = db.Column(db.String(20))
    comment = db.Column(db.String(120), unique=False, nullable=True)
    date_posted = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow
    )

    verified = db.Column(
        db.Boolean(), unique=False, nullable=False, default=False
    )
    
    players = db.relationship(
        "User", secondary=player_game_table, backref="games"
    )
    teams = db.relationship("Team", secondary=team_game_table, backref="games")
    is_sub = db.Column(
        db.PickleType, 
        default=[False] * (NUM_TEAM_PLAYERS * 2)
    )

    def did_team_1_win(self) -> bool:
        return self.team_1_score >= self.team_2_score

    def get_posted_timestamp(self) -> float:
        return self.date_posted.replace(tzinfo=timezone.utc).timestamp()

    def __repr__(self):
        return f"Game({self.id}, Teams: {self.teams}, Players: {self.players})"


class Team(BaseModel):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(40), unique=True, nullable=False)

    division_id = db.Column(
        db.Integer, db.ForeignKey('division.id', ondelete="CASCADE")
    )
    division = db.relationship("Division", backref="teams", lazy=True)

    # Team stats
    wins = db.Column(db.Integer, nullable=False, default=0)
    losses = db.Column(db.Integer, nullable=False, default=0)

    div_wins = db.Column(db.Integer, nullable=False, default=0)
    div_losses = db.Column(db.Integer, nullable=False, default=0)

    streak = db.Column(db.Integer, nullable=False, default=0)
    score_diff = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f"Team('{self.name}')"


class Division(BaseModel):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(20), unique=True, nullable=False)

    def __repr__(self):
        return f"Division: {self.name}"


class Season(BaseModel):
    """Database object representing seasons.
    
    Attributes:
        id (Mapped[int]): Unique ID of table.
        name (Mapped[str]): Name of the season.
        date_start (Mapped[DateTime]): Start date of the season. This date is 
            when users can start submitting games.
        date_end (Mapped[DateTime]): End date of the season. This date is when 
            seasons stop accepting new game submissions.
        is_archived (Mapped[bool]): True if the raw data from the season is 
            archived.
    """

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String, nullable=False)

    date_start = db.Column(db.DateTime, nullable=False)
    date_end = db.Column(db.DateTime, nullable=False)

    is_archived = db.Column(db.Boolean(), default=False)

    def is_active(self):
        now = datetime.now()
        return now > self.date_start and now < self.date_end

    def is_before(self):
        return datetime.now() < self.date_start

    def is_after(self):
        return datetime.now() > self.date_end


user_championship_table = db.Table(
    'user_championship_table',
    db.Column(
        'archived_season_id', db.Integer, 
        db.ForeignKey('archived_season.id', ondelete="CASCADE")
    ),
    db.Column(
        'player_id', db.Integer, db.ForeignKey('user.id', ondelete="CASCADE")
    )
)

user_runner_up_table = db.Table(
    'user_runner_up_table',
    db.Column(
        'archived_season_id', db.Integer, 
        db.ForeignKey('archived_season.id', ondelete="CASCADE")
    ),
    db.Column(
        'player_id', db.Integer, db.ForeignKey('user.id', ondelete="CASCADE")
    )
)


class ArchivedSeason(BaseModel):
    __tablename__ = 'archived_season'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String, nullable=False)
    summary = db.Column(db.Text)

    date_start = db.Column(db.DateTime, nullable=False)
    date_end = db.Column(db.DateTime, nullable=False)

    num_games = db.Column(db.Integer, nullable=False)
    num_teams = db.Column(db.Integer, nullable=False)
    num_divisions = db.Column(db.Integer, nullable=False)

    champion_team_name = db.Column(db.String(40), nullable=False)
    runner_up_team_name = db.Column(db.String(40), nullable=False)

    champions = db.relationship(
        "User", secondary=user_championship_table, backref="championships"
    )
    runner_ups = db.relationship(
        "User", secondary=user_runner_up_table, backref="second_places"
    )

    def __repr__(self):
        return "Season name: {}".format(self.name)


class Settings(BaseModel):
    id = db.Column(db.Integer, primary_key=True)

    password = db.Column(db.String(60), nullable=False)

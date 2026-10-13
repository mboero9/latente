"""Datos reales y demo usan namespaces separados en las claves compuestas."""

from datetime import datetime, date, timezone
from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    Date,
    JSON,
    ForeignKeyConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


def utcnow():
    return datetime.now(timezone.utc)


class League(Base):
    __tablename__ = "leagues"
    source: Mapped[str] = mapped_column(String(8), primary_key=True)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180))
    country: Mapped[str] = mapped_column(String(90))
    kind: Mapped[str] = mapped_column(String(20), default="League")
    season: Mapped[int] = mapped_column(Integer)
    seasons: Mapped[list] = mapped_column(JSON, default=list)
    coverage: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )


class Team(Base):
    __tablename__ = "teams"
    source: Mapped[str] = mapped_column(String(8), primary_key=True)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180))
    code: Mapped[str | None] = mapped_column(String(10))
    country: Mapped[str | None] = mapped_column(String(90))
    founded: Mapped[int | None] = mapped_column(Integer)
    venue: Mapped[str | None] = mapped_column(String(180))
    city: Mapped[str | None] = mapped_column(String(100))
    capacity: Mapped[int | None] = mapped_column(Integer)


class FixtureStatistics(Base):
    __tablename__ = "fixture_statistics"
    source: Mapped[str] = mapped_column(String(8), primary_key=True)
    fixture_id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[list] = mapped_column(JSON, default=list)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        ForeignKeyConstraint(["source", "fixture_id"], ["fixtures.source", "fixtures.id"]),
    )


class Membership(Base):
    __tablename__ = "memberships"
    source: Mapped[str] = mapped_column(String(8), primary_key=True)
    league_id: Mapped[int] = mapped_column(primary_key=True)
    season: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(primary_key=True)
    __table_args__ = (
        ForeignKeyConstraint(["source", "league_id"], ["leagues.source", "leagues.id"]),
        ForeignKeyConstraint(["source", "team_id"], ["teams.source", "teams.id"]),
    )


class Fixture(Base):
    __tablename__ = "fixtures"
    source: Mapped[str] = mapped_column(String(8), primary_key=True)
    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(Integer)
    season: Mapped[int] = mapped_column(Integer)
    round: Mapped[str | None] = mapped_column(String(180))
    kickoff: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    home_id: Mapped[int] = mapped_column(Integer)
    away_id: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(8))
    elapsed: Mapped[int | None] = mapped_column(Integer)
    extra: Mapped[int | None] = mapped_column(Integer)
    home_goals: Mapped[int | None] = mapped_column(Integer)
    away_goals: Mapped[int | None] = mapped_column(Integer)
    venue: Mapped[str | None] = mapped_column(String(180))
    referee: Mapped[str | None] = mapped_column(String(180))
    score: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    __table_args__ = (
        ForeignKeyConstraint(["source", "league_id"], ["leagues.source", "leagues.id"]),
        ForeignKeyConstraint(["source", "home_id"], ["teams.source", "teams.id"]),
        ForeignKeyConstraint(["source", "away_id"], ["teams.source", "teams.id"]),
        Index("ix_fixtures_source_kickoff", "source", "kickoff"),
        Index("ix_fixtures_league_season", "source", "league_id", "season"),
        Index("ix_fixtures_home", "source", "home_id", "kickoff"),
        Index("ix_fixtures_away", "source", "away_id", "kickoff"),
    )


class Standing(Base):
    __tablename__ = "standings"
    source: Mapped[str] = mapped_column(String(8), primary_key=True)
    league_id: Mapped[int] = mapped_column(primary_key=True)
    season: Mapped[int] = mapped_column(primary_key=True)
    group: Mapped[str] = mapped_column(String(180), primary_key=True)
    team_id: Mapped[int] = mapped_column(primary_key=True)
    rank: Mapped[int] = mapped_column(Integer)
    points: Mapped[int] = mapped_column(Integer)
    played: Mapped[int] = mapped_column(Integer)
    won: Mapped[int] = mapped_column(Integer)
    drawn: Mapped[int] = mapped_column(Integer)
    lost: Mapped[int] = mapped_column(Integer)
    goals_for: Mapped[int] = mapped_column(Integer)
    goals_against: Mapped[int] = mapped_column(Integer)
    difference: Mapped[int] = mapped_column(Integer)
    form: Mapped[str | None] = mapped_column(String(20))
    description: Mapped[str | None] = mapped_column(String(250))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    __table_args__ = (
        ForeignKeyConstraint(["source", "league_id"], ["leagues.source", "leagues.id"]),
        ForeignKeyConstraint(["source", "team_id"], ["teams.source", "teams.id"]),
    )


class Scorer(Base):
    __tablename__ = "scorers"
    source: Mapped[str] = mapped_column(String(8), primary_key=True)
    league_id: Mapped[int] = mapped_column(primary_key=True)
    season: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180))
    rank: Mapped[int] = mapped_column(Integer)
    goals: Mapped[int] = mapped_column(Integer)
    assists: Mapped[int | None] = mapped_column(Integer)
    appearances: Mapped[int | None] = mapped_column(Integer)
    penalties: Mapped[int | None] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    __table_args__ = (
        ForeignKeyConstraint(["source", "league_id"], ["leagues.source", "leagues.id"]),
        ForeignKeyConstraint(["source", "team_id"], ["teams.source", "teams.id"]),
    )


class SyncJob(Base):
    __tablename__ = "sync_jobs"
    key: Mapped[str] = mapped_column(String(140), primary_key=True)
    kind: Mapped[str] = mapped_column(String(30))
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    next_run: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
    last_success: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failures: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str | None] = mapped_column(String(200))


class ApiUsage(Base):
    __tablename__ = "api_usage"
    day: Mapped[date] = mapped_column(Date, primary_key=True)
    requests: Mapped[int] = mapped_column(Integer, default=0)
    provider_remaining: Mapped[int | None] = mapped_column(Integer)
    last_request: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    blocked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WorkerState(Base):
    __tablename__ = "worker_state"
    source: Mapped[str] = mapped_column(String(8), primary_key=True)
    heartbeat: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    message: Mapped[str] = mapped_column(String(200), default="Iniciando")

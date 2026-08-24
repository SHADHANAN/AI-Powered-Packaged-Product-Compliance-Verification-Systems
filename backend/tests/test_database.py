import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.config import get_settings
from app.database import Base, SessionLocal, check_db_connection, engine, get_db
from app.models.base import Base as ModelBase


def test_database_settings_loaded():
    """Verify that DATABASE_URL is properly configured in application settings."""
    settings = get_settings()
    assert hasattr(settings, "DATABASE_URL")
    assert settings.DATABASE_URL.startswith("postgresql")


def test_sqlalchemy_engine_initialization():
    """Verify that SQLAlchemy engine is created and is an instance of Engine."""
    assert isinstance(engine, Engine)
    assert engine.url.drivername.startswith("postgresql")


def test_declarative_base_model():
    """Verify that Base is a valid SQLAlchemy DeclarativeBase subclass."""
    assert issubclass(ModelBase, object)
    assert hasattr(ModelBase, "metadata")
    assert ModelBase is Base


def test_get_db_session_lifecycle():
    """Verify that get_db generator yields a valid session and closes it."""
    db_gen = get_db()
    session = next(db_gen)
    assert isinstance(session, Session)
    # Ensure closing without exception
    with pytest.raises(StopIteration):
        next(db_gen)


def test_check_db_connection_graceful_handling():
    """Verify that check_db_connection returns a boolean and does not raise unhandled exception."""
    result = check_db_connection()
    assert isinstance(result, bool)


def test_alembic_configuration_validity():
    """Verify that Alembic configuration and script directory can be loaded."""
    alembic_cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(alembic_cfg)
    revisions = list(script.walk_revisions())
    assert len(revisions) >= 3
    head_rev = script.get_current_head()
    assert head_rev == "0003_create_audit_logs"

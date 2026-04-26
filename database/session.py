from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base


def utcnow_str():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

engine = None
Base = declarative_base()
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False)
)


def init_engine(database_uri):
    global engine

    engine_options = {'echo': False}
    if database_uri.startswith('sqlite:'):
        engine_options['connect_args'] = {'check_same_thread': False}

    engine = create_engine(database_uri, **engine_options)
    db_session.configure(bind=engine)

    Base.query = db_session.query_property()

    return engine


def get_session():
    return db_session


def shutdown_session(exception=None):
    db_session.remove()

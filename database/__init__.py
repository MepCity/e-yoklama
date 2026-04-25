from database.session import Base, db_session as db, init_engine, get_session, shutdown_session


def init_db(app):
    engine = init_engine(app.config['SQLALCHEMY_DATABASE_URI'])

    app.teardown_appcontext(shutdown_session)

    import models  # noqa: F401 — modelleri import et ki Base.metadata tabloları görsün
    Base.metadata.create_all(bind=engine)

    return engine


def get_db():
    return get_session()

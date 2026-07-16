from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import Config

engine = create_engine(Config.DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def init_db():

    from db.models import (
        Room,
        Table,
        Recommendation
    )

    Base.metadata.create_all(bind=engine)

    print("✅ Tablas creadas/verificadas correctamente")


print("✅ Connected to DB OK")
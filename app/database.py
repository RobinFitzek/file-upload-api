from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Verbindung zur Postgres DB (gleiche Daten wie in docker-compose.yml)
DATABASE_URL = "postgresql+psycopg://geodata_user:geodata_pass@localhost:5432/geodata_db"

# Engine: Verbindung zur DB
engine = create_engine(DATABASE_URL)

# Session: eine "Unterhaltung" mit der DB (öffnen, queries, schließen)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Basisklasse für alle Modelle
Base = declarative_base()


def get_db():
    """Gibt eine DB-Session zurück, schließt sie nach Benutzung"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
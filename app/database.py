import os
from dotenv import load_dotenv
from sqlalchemy import create_engine # Für die Verbindung zur DB
from sqlalchemy.orm import sessionmaker, declarative_base

# .env Datei laden (für lokale Entwicklung)
load_dotenv()

# Verbindung aus ENV oder Fallback
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://geodata_user:geodata_pass@localhost:5432/geodata_db"
)

# Engine: Verbindung zur DB
engine = create_engine(DATABASE_URL)

# Engine erstellt Session: eine "Unterhaltung" mit der DB (öffnen, queries, schließen)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Elternklasse für alle Datenbankmodelle
Base = declarative_base()


def get_db():
    """Gibt eine DB-Session zurück, schließt sie nach Benutzung"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
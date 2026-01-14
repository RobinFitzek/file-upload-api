from sqlalchemy import Column, Integer, String, Float
from app.database import Base


class Geodata(Base):
    """
    Datenbank-Tabelle für Geodaten.
    Entspricht dem Schema aus den Example-Dateien.
    """
    __tablename__ = "geodata"

    # Spalten (basierend auf geodata_example_1.csv)
    id = Column(Integer, primary_key=True, index=True)
    flurstuecknummer = Column(String, nullable=True)
    longitude = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)  # In DB richtig geschrieben
    gemeinde = Column(String, nullable=True)
    bundesland = Column(String, nullable=True)
    groesse_ha = Column(Float, nullable=True)

    def __repr__(self):
        return f"<Geodata(id={self.id}, gemeinde={self.gemeinde})>"
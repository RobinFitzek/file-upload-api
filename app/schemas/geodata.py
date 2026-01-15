# db-validation - defines how data is validated and serialized before storing in the db 

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class GeodataBase(BaseModel):
    """Basis-Schema für Geodaten"""
    model_config = ConfigDict(populate_by_name=True)
    
    flurstuecknummer: Optional[str] = Field(None, alias="Flurstücknummer")
    longitude: Optional[float] = None
    latitude: Optional[float] = Field(None, alias="latidude")  # wegen Tippfehler in Quelldaten!
    gemeinde: Optional[str] = Field(None, alias="Gemeinde")
    bundesland: Optional[str] = Field(None, alias="Bundesland")
    groesse_ha: Optional[float] = Field(None, alias="Größe in ha")


class GeodataCreate(GeodataBase):
    """Für neue Einträge (ID wird automatisch generiert oder aus Datei)"""
    id: Optional[int] = Field(None, alias="ID")


class GeodataResponse(GeodataBase):
    """Für API-Responses"""
    id: int

from pydantic import BaseModel, Field
from typing import Optional


class GeodataBase(BaseModel):
    """Basis-Schema für Geodaten"""
    flurstuecknummer: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    gemeinde: Optional[str] = None
    bundesland: Optional[str] = None
    groesse_ha: Optional[float] = Field(None, alias="größe_in_ha")


class GeodataCreate(GeodataBase):
    """Für neue Einträge (ID wird automatisch generiert oder aus Datei)"""
    id: Optional[int] = None


class GeodataResponse(GeodataBase):
    """Für API-Responses"""
    id: int

    class Config:
        from_attributes = True
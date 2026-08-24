from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CenterPublic(BaseModel):
    id: str
    name: str
    description: str
    city: str
    region: str | None
    address: str
    specialties: list[str]
    services: list[str]
    served_needs: list[str]
    min_age_years: int | None
    max_age_years: int | None
    offers_in_person: bool
    offers_remote: bool
    phone: str
    email: str | None
    working_hours: str
    price_range: str | None
    latitude: float | None
    longitude: float | None
    is_favorite: bool
    created_at: datetime
    updated_at: datetime


class CenterFilterOptions(BaseModel):
    cities: list[str]
    specialties: list[str]
    services: list[str]

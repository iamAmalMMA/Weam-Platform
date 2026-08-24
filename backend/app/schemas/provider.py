from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


def _clean_list(values: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = " ".join(value.strip().split())
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            output.append(cleaned)
    return output


class CenterProfileCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    description: str = Field(min_length=10, max_length=3000)
    city: str = Field(min_length=2, max_length=100)
    region: str | None = Field(default=None, max_length=100)
    address: str = Field(min_length=3, max_length=300)
    specialties: list[str] = Field(default_factory=list, max_length=30)
    services: list[str] = Field(default_factory=list, max_length=50)
    served_needs: list[str] = Field(default_factory=list, max_length=50)
    min_age_years: int | None = Field(default=None, ge=0, le=100)
    max_age_years: int | None = Field(default=None, ge=0, le=100)
    offers_in_person: bool = True
    offers_remote: bool = False
    phone: str = Field(min_length=5, max_length=40)
    email: EmailStr | None = None
    working_hours: str = Field(min_length=2, max_length=240)
    price_range: str | None = Field(default=None, max_length=120)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @field_validator("specialties", "services", "served_needs")
    @classmethod
    def clean_lists(cls, values: list[str]) -> list[str]:
        return _clean_list(values)

    @model_validator(mode="after")
    def validate_profile(self):
        if self.min_age_years is not None and self.max_age_years is not None:
            if self.max_age_years < self.min_age_years:
                raise ValueError("max_age_years cannot be below min_age_years")
        if not self.offers_in_person and not self.offers_remote:
            raise ValueError("At least one delivery mode is required")
        return self


class CenterProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=180)
    description: str | None = Field(default=None, min_length=10, max_length=3000)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    region: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, min_length=3, max_length=300)
    specialties: list[str] | None = Field(default=None, max_length=30)
    services: list[str] | None = Field(default=None, max_length=50)
    served_needs: list[str] | None = Field(default=None, max_length=50)
    min_age_years: int | None = Field(default=None, ge=0, le=100)
    max_age_years: int | None = Field(default=None, ge=0, le=100)
    offers_in_person: bool | None = None
    offers_remote: bool | None = None
    phone: str | None = Field(default=None, min_length=5, max_length=40)
    email: EmailStr | None = None
    working_hours: str | None = Field(default=None, min_length=2, max_length=240)
    price_range: str | None = Field(default=None, max_length=120)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @field_validator("specialties", "services", "served_needs")
    @classmethod
    def clean_optional_lists(cls, values: list[str] | None) -> list[str] | None:
        return None if values is None else _clean_list(values)


class ManagedCenterPublic(BaseModel):
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
    is_active: bool
    verification_status: str
    verification_note: str | None
    created_at: datetime
    updated_at: datetime


class CenterSpecialistCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=180)
    professional_title: str = Field(min_length=2, max_length=140)
    specialty: str = Field(min_length=2, max_length=140)
    bio: str | None = Field(default=None, max_length=2000)


class CenterSpecialistUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=180)
    professional_title: str | None = Field(default=None, min_length=2, max_length=140)
    specialty: str | None = Field(default=None, min_length=2, max_length=140)
    bio: str | None = Field(default=None, max_length=2000)
    is_active: bool | None = None


class CenterSpecialistPublic(BaseModel):
    id: str
    center_id: str
    full_name: str
    professional_title: str
    specialty: str
    bio: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProviderDashboardPublic(BaseModel):
    center: ManagedCenterPublic | None
    specialists_count: int
    authorized_children_count: int
    account_kind: str

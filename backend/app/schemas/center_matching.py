from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.center import CenterPublic


class CenterMatchRequest(BaseModel):
    city: str | None = Field(default=None, max_length=100)
    delivery_mode: Literal["in_person", "remote", "both"] | None = None

    @field_validator("city")
    @classmethod
    def clean_city(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.strip().split())
        return cleaned or None


class CenterMatchSource(BaseModel):
    source_type: Literal["profile", "approved_report", "active_goal"]
    source_id: str
    title: str
    matched_signals: list[str]


class CenterMatchItem(BaseModel):
    rank: int
    match_level: Literal["strong", "good", "initial"]
    center: CenterPublic
    reasons: list[str]
    matched_signals: list[str]
    sources: list[CenterMatchSource]


class CenterMatchEvidence(BaseModel):
    profile_used: bool
    approved_reports_used: int
    active_goals_used: int


class CenterMatchResponse(BaseModel):
    id: str
    child_id: str
    child_name: str
    child_age_years: int | None
    preferred_city: str | None
    delivery_mode: Literal["in_person", "remote", "both"] | None
    summary: str
    profile_signals: list[str]
    evidence: CenterMatchEvidence
    insufficient_data: bool
    limitations: list[str]
    safety_note: str
    matches: list[CenterMatchItem]
    created_at: datetime

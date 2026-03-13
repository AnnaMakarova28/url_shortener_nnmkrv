from datetime import datetime

from pydantic import BaseModel, ConfigDict, HttpUrl


class LinkCreate(BaseModel):
    original_url: HttpUrl
    custom_alias: str | None = None
    expires_at: datetime | None = None
    project_name: str | None = None


class LinkCreateResponse(BaseModel):
    short_code: str
    short_url: str
    original_url: str
    project_name: str | None = None
    expires_at: datetime | None = None


class LinkStatsResponse(BaseModel):
    short_code: str
    original_url: str
    created_at: datetime
    clicks: int
    last_used_at: datetime | None = None
    expires_at: datetime | None = None
    project_name: str | None = None
    model_config = ConfigDict(from_attributes=True)

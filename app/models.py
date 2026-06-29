from pydantic import BaseModel, Field


class WeatherCreateRequest(BaseModel):
    location: str = Field(..., examples=["Tunis", "10001", "Paris, France"])
    start_date: str = Field(..., examples=["2026-06-01"])
    end_date: str = Field(..., examples=["2026-06-07"])


class WeatherUpdateRequest(BaseModel):
    start_date: str | None = None
    end_date: str | None = None
    notes: str | None = None

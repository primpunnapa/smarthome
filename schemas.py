from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Literal

class IndoorData(BaseModel):
    main: str
    description: str
    temperature: float
    humidity: float
    place: str
class OutdoorData(BaseModel):
    main: str
    description: str
    temperature: float
    humidity: float
    place: str

class WeatherResponse(BaseModel):
    temperature: float
    humidity: int
    weather_main: str
    weather_description: str
    recorded_at: datetime

class SuggestionResponse(BaseModel):
    place: str
    time: str
    temperature: dict
    humidity: dict
    weather: dict

class WeatherData(BaseModel):
    temperature: float
    humidity: float
    main: str
    description: str

class DressingRecommendationResponse(BaseModel):
    place: str
    weather: WeatherData
    recommendation: str
    emoji: str
    image: str

class HourlyDataPoint(BaseModel):
    hour: int
    temperature: float
    humidity: float
    min_temp: float
    max_temp: float

class HourlyStatsResponse(BaseModel):
    place: str
    source: str
    data: List[HourlyDataPoint]

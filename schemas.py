from pydantic import BaseModel
from datetime import datetime

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

# class RecommendationResponse(BaseModel):
#     status: str
#     indoor: IndoorData
#     outdoor: OutdoorData
#     recommendations: List[str]
#     time: datetime


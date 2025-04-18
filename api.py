from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from dbutils.pooled_db import PooledDB
import pymysql
from typing import List, Optional
from datetime import datetime
from config import DB_HOST, DB_USER, DB_PASSWD, DB_NAME
from schemas import (
    IndoorData, OutdoorData, WeatherResponse, SuggestionResponse,
    WeatherData, DressingRecommendationResponse, HourlyDataPoint,
    HourlyStatsResponse
)
from recommendations import *

app = FastAPI(title="Weather API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Database setup
pool = PooledDB(creator=pymysql,
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWD,
                database=DB_NAME,
                maxconnections=1,
                blocking=True
                )

# HTML endpoints remain the same
@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/statistics", response_class=HTMLResponse)
async def read_statistics(request: Request):
    return templates.TemplateResponse("statistic.html", {"request": request})

@app.get("/suggestion", response_class=HTMLResponse)
async def read_suggestion(request: Request):
    return templates.TemplateResponse("suggestion.html", {"request": request})

@app.get("/outfits", response_class=HTMLResponse)
async def read_outfits(request: Request):
    return templates.TemplateResponse("outfits.html", {"request": request})

@app.get("/analytics", response_class=HTMLResponse)
async def read_analytics(request: Request):
    return templates.TemplateResponse("analytics.html", {"request": request})

# API endpoints with proper schema validation
@app.get("/{place}/{source}/lastest", response_model=WeatherResponse)
async def get_weather_data(place: str, source: str):
    with pool.connection() as conn:
        with conn.cursor() as cs:
            cs.execute("""
                SELECT 
                    temperature,
                    humidity,
                    main as weather_main,
                    description as weather_description,
                    ts AS recorded_at
                FROM KULA
                WHERE place = %s AND source = %s
                ORDER BY ts DESC
                LIMIT 1
            """, [place, source])
            row = cs.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="No data found")
            
            return WeatherResponse(
                temperature=row[0],
                humidity=row[1],
                weather_main=row[2],
                weather_description=row[3],
                recorded_at=row[4]
            )

@app.get("/{place}/available-dates", response_model=List[str])
async def get_available_dates(place: str):
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT DATE(ts) as date_only
                FROM KULA
                WHERE place = %s
                ORDER BY date_only DESC
            """, (place,))
            return [row[0].strftime("%Y-%m-%d") for row in cursor.fetchall()]

@app.get("/{place}/temperature-humidity", response_model=List[HourlyDataPoint])
async def get_temp_and_humidity_by_date(place: str, date: str = Query(...)):
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    HOUR(ts) as hour,
                    ROUND(AVG(temperature), 2) as avg_temp,
                    ROUND(AVG(humidity), 2) as avg_humidity,
                    MIN(temperature) as min_temp,
                    MAX(temperature) as max_temp
                FROM KULA
                WHERE place = %s AND DATE(ts) = %s
                GROUP BY hour
                ORDER BY hour
            """, (place, date))
            return [
                HourlyDataPoint(
                    hour=row[0],
                    temperature=row[1],
                    humidity=row[2],
                    min_temp=row[3],
                    max_temp=row[4]
                ) for row in cursor.fetchall()
            ]

@app.get("/{place}/suggestion", response_model=SuggestionResponse)
async def compare_conditions(place: str, date: Optional[str] = None):
    try:
        with pool.connection() as conn:
            with conn.cursor() as cursor:
                query = """
                    SELECT 
                        i.temperature as indoor_temp,
                        i.humidity as indoor_humidity,
                        i.ts as indoor_time,
                        o.temperature as outdoor_temp,
                        o.humidity as outdoor_humidity,
                        o.main as weather_main,
                        o.description as weather_description,
                        o.ts as outdoor_time,
                        TIMESTAMPDIFF(MINUTE, i.ts, o.ts) as time_diff
                    FROM 
                        (SELECT temperature, humidity, ts 
                         FROM KULA 
                         WHERE place = %s AND source = 'indoor'
                         {date_filter}
                         ORDER BY ts DESC LIMIT 1) i,
                        (SELECT temperature, humidity, main, description, ts 
                         FROM KULA 
                         WHERE place = %s AND source = 'outdoor'
                         {date_filter}
                         ORDER BY ts DESC LIMIT 1) o
                    WHERE ABS(TIMESTAMPDIFF(MINUTE, i.ts, o.ts)) < 5
                """
                
                date_filter = ""
                params = (place, place)
                if date:
                    date_filter = "AND DATE(ts) = %s"
                    params = (place, date, place, date)
                
                cursor.execute(query.format(date_filter=date_filter), params)
                result = cursor.fetchone()

                if not result:
                    raise HTTPException(
                        status_code=404,
                        detail="No matching indoor/outdoor pairs within 5 minutes"
                    )

                temp_diff = result[0] - result[3]
                
                return SuggestionResponse(
                    place=place,
                    time=str(result[7]),
                    temperature={
                        "indoor": result[0],
                        "outdoor": result[3],
                        "suggestion": get_temp_suggestion(temp_diff)
                    },
                    humidity={
                        "indoor": {
                            "value": result[1],
                            "suggestion": get_humidity_suggestion(result[1], "indoor")
                        },
                        "outdoor": {
                            "value": result[4],
                            "suggestion": get_humidity_suggestion(result[4], "outdoor")
                        }
                    },
                    weather={
                        "weather_main": result[5],
                        "weather_description": result[6],
                        "suggestion": get_rain_suggestion(result[5], result[0])
                    }
                )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error comparing data: {str(e)}"
        )

@app.get("/indoor", response_model=List[IndoorData])
def get_indoor():
    with pool.connection() as conn, conn.cursor() as cs:
        cs.execute("""
            SELECT main, description, temperature, humidity, place 
            FROM KULA
            WHERE source='indoor'
        """)
        return [
            IndoorData(
                main=row[0],
                description=row[1],
                temperature=row[2],
                humidity=row[3],
                place=row[4]
            ) for row in cs.fetchall()
        ]

@app.get("/outdoor", response_model=List[OutdoorData])
def get_outdoor():
    with pool.connection() as conn, conn.cursor() as cs:
        cs.execute("""
            SELECT main, description, temperature, humidity, place 
            FROM KULA
            WHERE source='outdoor'
        """)
        return [
            OutdoorData(
                main=row[0],
                description=row[1],
                temperature=row[2],
                humidity=row[3],
                place=row[4]
            ) for row in cs.fetchall()
        ]

@app.get("/{place}/{source}/analytics/hourly", response_model=HourlyStatsResponse)
async def get_hourly_stats(
    place: str,
    source: str  # 'indoor' or 'outdoor'
):
    if source not in ["indoor", "outdoor"]:
        raise HTTPException(status_code=400, detail="Source must be 'indoor' or 'outdoor'")

    try:
        with pool.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        HOUR(ts) as hour,
                        ROUND(AVG(temperature), 2) as avg_temp,
                        ROUND(AVG(humidity), 2) as avg_humidity,
                        MIN(temperature) as min_temp,
                        MAX(temperature) as max_temp
                    FROM KULA
                    WHERE place = %s AND source = %s
                    GROUP BY hour
                    ORDER BY hour
                """, (place, source))
                
                results = cursor.fetchall()
                # print("Query results:", results)  # Debug print
                
                return HourlyStatsResponse(
                    place=place,
                    source=source,
                    data=[
                        HourlyDataPoint(
                            hour=row[0],
                            temperature=row[1],
                            humidity=row[2],
                            min_temp=row[3],
                            max_temp=row[4]
                        ) for row in results
                    ]
                )
    except Exception as e:
        print("Error in hourly stats endpoint:", str(e))  # Debug print
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/{place}/recommend/dressing", response_model=DressingRecommendationResponse)
async def get_dressing_recommendation(place: str):
    weather_data = await get_weather_data(place, "outdoor")
    
    suggestion, emoji, image = get_dressing_suggestion_with_visuals(
        temperature=weather_data.temperature,
        weather_main=weather_data.weather_main,
        description=weather_data.weather_description
    )

    return DressingRecommendationResponse(
        place=place,
        weather=WeatherData(
            temperature=weather_data.temperature,
            humidity=weather_data.humidity,
            main=weather_data.weather_main,
            description=weather_data.weather_description
        ),
        recommendation=suggestion,
        emoji=emoji,
        image=image
    )
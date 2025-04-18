from fastapi import FastAPI,HTTPException,Request,Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from dbutils.pooled_db import PooledDB
import pymysql
from typing import List
from config import DB_HOST, DB_USER, DB_PASSWD, DB_NAME
from schemas import *
from recommendations import *

app = FastAPI(title="Weather API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],  # Allowing requests from localhost
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
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


@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/statistics", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("statistic.html", {"request": request})
@app.get("/suggestion", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("suggestion.html", {"request": request})
@app.get("/outfits", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("outfits.html", {"request": request})
@app.get("/comparison", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("comparison.html", {"request": request})
@app.get("/analytics", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("analytics.html", {"request": request})
@app.get("/{place}/{source}/lastest", response_model=WeatherResponse)
async def get_weather_data(place, source):
    with pool.connection() as conn:
        with conn.cursor() as cs:
            cs.execute("""
                SELECT 
                    temperature,
                    humidity,
                    main as weather_main,
                    description weather_description,
                    ts AS recorded_at
                FROM KULA
                WHERE place = %s AND source = %s
                ORDER BY ts DESC
                LIMIT 1
            """, [place, source])
            row = cs.fetchone()
            if row:

                return WeatherResponse(
                    temperature=row[0],
                    humidity=row[1],
                    weather_main=row[2],
                    weather_description=row[3],
                    recorded_at=row[4]
                )

            return {"error": "No data found"}

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
            result = [row[0].strftime("%Y-%m-%d") for row in cursor.fetchall()]
    return result

@app.get("/{place}/temperature-humidity", response_model=dict)
async def get_temp_and_humidity_by_date(place: str, date: str = Query(...)):
    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    HOUR(ts) as hour,
                    ROUND(AVG(temperature), 2) as avg_temp,
                    ROUND(AVG(humidity), 2) as avg_humidity
                FROM KULA
                WHERE place = %s AND DATE(ts) = %s
                GROUP BY hour
                ORDER BY hour
            """, (place, date))
            rows = cursor.fetchall()
            return {
                "date": date,
                "data": [{
                    "hour": f"{row[0]:02d}:00",
                    "temperature": row[1],
                    "humidity": row[2]
                } for row in rows]
            }

@app.get("/{place}/suggestion", response_model=SuggestionResponse)
async def compare_conditions(place: str, date: str = None):
    try:
        with pool.connection() as conn:
            with conn.cursor() as cursor:
                # Base query
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
                
                # Add date filter if provided
                date_filter = ""
                params = (place, place)
                if date:
                    date_filter = "AND DATE(ts) = %s"
                    params = (place, date, place, date)
                
                # Format the final query
                final_query = query.format(date_filter=date_filter)
                
                cursor.execute(final_query, params)
                result = cursor.fetchone()

                if not result:
                    raise HTTPException(
                        status_code=404,
                        detail="No matching indoor/outdoor pairs within 5 minutes"
                    )

                # Extract tuple values
                indoor = {
                    'temperature': result[0],
                    'humidity': result[1],
                    'recorded_at': result[2]
                }

                outdoor = {
                    'temperature': result[3],
                    'humidity': result[4],
                    'weather_main': result[5],
                    'weather_description': result[6],
                    'recorded_at': result[7]
                }

                # Generate comparisons
                temp_diff = indoor['temperature'] - outdoor['temperature']

                return {
                    "place": place,
                    "time": str(outdoor['recorded_at']),
                    "temperature": {
                        "indoor": indoor['temperature'],
                        "outdoor": outdoor['temperature'],
                        "suggestion": get_temp_suggestion(temp_diff)
                    },
                    "humidity": {
                        "indoor": {
                            "value": indoor['humidity'],
                            "suggestion": get_humidity_suggestion(indoor['humidity'], "indoor")
                        },
                        "outdoor": {
                            "value": outdoor['humidity'],
                            "suggestion": get_humidity_suggestion(outdoor['humidity'], "outdoor")
                        }
                    },
                    "weather": {
                        "weather_main": outdoor['weather_main'],
                        "weather_description": outdoor['weather_description'],
                        "suggestion": get_rain_suggestion(outdoor['weather_main'], indoor['temperature'])
                    }
                }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error comparing data: {str(e)}"
        )
@app.get("/indoor")
def get_indoor() -> list[IndoorData]:
    with pool.connection() as conn, conn.cursor() as cs:
        cs.execute("""
                   SELECT main, description,temperature,humidity,place FROM KULA
                   WHERE source='indoor'
                   """)
        result = [
            IndoorData(main=main, description=description, temperature=temperature, humidity=humidity, place=place) for
            main, description, temperature, humidity, place in cs.fetchall()]
    return result


@app.get("/outdoor")
def get_outdoor() -> list[OutdoorData]:
    with pool.connection() as conn, conn.cursor() as cs:
        cs.execute("""
                   SELECT main, description,temperature,humidity,place FROM KULA
                   WHERE source='outdoor'
                   """)
        result = [
            OutdoorData(main=main, description=description, temperature=temperature, humidity=humidity, place=place) for
            main, description, temperature, humidity, place in cs.fetchall()]
    return result


@app.get("/{place}/{source}/analytics/hourly", response_model=dict)
async def get_hourly_stats(
        place: str,
        source: str,  # 'indoor' or 'outdoor'
):
    """Get hourly averages for temperature and humidity from specific source"""
    # Validate source
    if source not in ["indoor", "outdoor"]:
        return {"error": "Source must be 'indoor' or 'outdoor'"}

    with pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    DATE_FORMAT(ts, '%%Y-%%m-%%d %%H:00:00') AS hour,
                    ROUND(AVG(temperature), 2) as avg_temp,
                    ROUND(AVG(humidity), 2) as avg_humidity,
                    MAX(temperature) as max_temp,
                    MIN(temperature) as min_temp
                FROM KULA
                WHERE place = %s 
                  AND source = %s
                GROUP BY hour
                ORDER BY hour DESC
            """, [
                place,
                source,
            ])

            return {
                "place": place,
                "source": source,
                "data": [
                    {
                        "hour": row[0],
                        "temperature": row[1],
                        "humidity": row[2],
                        "min_temp": row[3],
                        "max_temp": row[4]
                    }
                    for row in cursor.fetchall()
                ]
            }

@app.get("/{place}/recommend/dressing", response_model=dict)
async def get_dressing_recommendation(place: str):
    weather_data = await get_weather_data(place, "outdoor")
    if "error" in weather_data:
        raise HTTPException(status_code=404, detail=weather_data["error"])

    suggestion, emoji, image = get_dressing_suggestion_with_visuals(
        temperature=weather_data.temperature,
        weather_main=weather_data.weather_main,
        description=weather_data.weather_description
    )

    return {
        "place": place,
        "recommendation": suggestion,
        "emoji": emoji,
        "image": image,
        "weather": {
            "temperature": weather_data.temperature,
            "main": weather_data.weather_main,
            "description": weather_data.weather_description
        }
    }


# python3 -m venv venv
# source venv/bin/activate  # For Mac/Linux
# uvicorn api:app --port 8000 --reload
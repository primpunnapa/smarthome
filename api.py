from fastapi import FastAPI,HTTPException,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from dbutils.pooled_db import PooledDB
import pymysql
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


@app.get("/{place}/suggestion", response_model=SuggestionResponse)
async def compare_conditions(place: str):
    try:
        with pool.connection() as conn:
            with conn.cursor() as cursor:
                # Get paired indoor/outdoor data within 10 minutes
                cursor.execute("""
                    SELECT 
                        i.temperature as indoor_temp,
                        i.humidity as indoor_humidity,
                        i.ts as indoor_time,
                        o.temperature as outdoor_temp,
                        o.humidity as outdoor_humidity,
                        o.main as weather_main,
                        o.ts as outdoor_time,
                        TIMESTAMPDIFF(MINUTE, i.ts, o.ts) as time_diff
                    FROM 
                        (SELECT temperature, humidity, ts 
                         FROM KULA 
                         WHERE place = %s AND source = 'indoor'
                         ORDER BY ts DESC
                         LIMIT 1) i,
                        (SELECT temperature, humidity, main, ts 
                         FROM KULA 
                         WHERE place = %s AND source = 'outdoor'
                         ORDER BY ts DESC
                         LIMIT 1) o
                    WHERE ABS(TIMESTAMPDIFF(MINUTE, i.ts, o.ts)) < 5
                """, (place, place))

                result = cursor.fetchone()

                if not result:
                    raise HTTPException(
                        status_code=404,
                        detail="No matching indoor/outdoor pairs within 10 minutes"
                    )

                # Extract tuple values (order matches SELECT)
                indoor = {
                    'temperature': result[0],  # indoor_temp
                    'humidity': result[1],  # indoor_humidity
                    'recorded_at': result[2]  # indoor_time
                }

                outdoor = {
                    'temperature': result[3],  # outdoor_temp
                    'humidity': result[4],  # outdoor_humidity
                    'weather_main': result[5],  # weather_main
                    'recorded_at': result[6]  # outdoor_time
                }

                # Generate comparisons
                temp_diff = indoor['temperature'] - outdoor['temperature']

                return {
                    "place": place,
                    # "time": datetime.now().isoformat(),
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


@app.get("/{place}/{source}/analytics/hourly", response_model=HourlyStatsResponse)
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
                    MIN(temperature) as min_temp,
                    MAX(humidity) as max_humid,
                    MIN(humidity) as min_humid
                FROM KULA
                WHERE place = %s 
                  AND source = %s
                GROUP BY hour
                ORDER BY hour DESC
            """, [
                place,
                source,
            ])

            data = cursor.fetchall()

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
                    )
                    for row in data
                ]
            )

@app.get("/{place}/recommend/dressing", response_model=DressingRecommendationResponse)
async def get_dressing_recommendation(place: str):
    weather_data = await get_weather_data(place, "outdoor")

    if "error" in weather_data:
        raise HTTPException(status_code=404, detail=weather_data["error"])

    suggestion, emoji, image = get_dressing_suggestion_with_visuals(
        temperature=weather_data.temperature,
        weather_main=weather_data.weather_main,
        description=weather_data.weather_description
    )

    return DressingRecommendationResponse(
        place=place, recommendation=suggestion, emoji=emoji, image=image,
        weather=WeatherData(temperature=weather_data.temperature, main=weather_data.weather_main,
                                              description=weather_data.weather_description))


# python3 -m venv venv
# source venv/bin/activate  # For Mac/Linux
# uvicorn api:app --port 8000 --reload

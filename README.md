# Project Overview

This project monitors indoor temperature and humidity using the KY-015 sensor connected to a KidBright board. 
The system integrates this data with outdoor weather data from a public API to provide real-time insights, alerts, 
and recommendations for maintaining a comfortable home environment.

# Members
Supidcha NILSARIKA  Software and Knowledge Engineering of Kasetsart University ID : 6610545545  
Punnapa PRAMOTEKUL  Software and Knowledge Engineering of Kasetsart University ID : 6610545863  

# Weather Dashboard

A web application that visualizes indoor/outdoor weather data with scatter plots, statistical summaries and recommendation actions.

## API Features

### Core Functionality

- **Weather Data**:
  - Get latest indoor/outdoor conditions
  - Temperature, humidity, and weather descriptions
  - Timestamped recordings
  - Place : **KU** (Computer building, Keff and OCS), **Ladprao** (Home)

- **Comparative Analysis**:
  - Indoor vs outdoor comparisons
  - Time-synchronized data pairing (±5 minutes)
  - Automatic suggestion generation

### Endpoint Overview

#### 1. Weather Data Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/{place}/{source}/lastest` | GET | Get latest weather data for a location |
| `/{place}/temperature-humidity` | GET | get all temperature and humidity by date |
| `/indoor` | GET | List all indoor sensor data |
| `/outdoor` | GET | List all outdoor sensor data |

#### 2. Recommendation Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/{place}/suggestion` | GET | Get comparative suggestions for a location |
| `/{place}/recommend/dressing` | GET | Get clothing recommendations with visuals |

#### 3. Analytics Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/{place}/available-dates` | GET | Get available date|
| `/{place}/{source}/analytics/hourly` | GET | Get hourly aggregated statistics |

* for {place}, select KU or Ladprao
* for {source}, select outdoor or indoor

### Key Technical Features

1. **Data Aggregation**:
   - Hourly averages for temperature/humidity
   - Min/max temperature tracking
   - Time-grouped data points

2. **Intelligent Recommendations**:
   - Weather-appropriate outfit suggestions
   - Comparative indoor/outdoor advice

3. **Visual Enhancements**:
   - Emoji integration for weather states
   - Outfit images for recommendations
   - Time-series data formatting

4. **Database Integration**:
   - Connection pooling for performance
   - MySQL compatible

# Installation

Python version >= 3.11

### Backend Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/primpunnapa/smarthome.git

2. Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    venv\Scripts\activate     # Windows
3. Install Python dependencies:
    ```bash
    pip install -r requirement.txt
   
4. Database setup:   
   * Create a MySQL database  
   * Update the connection settings in config.py  

### Frontend setup  
The frontend uses Chart.js via CDN for data visualization.  

### How to run :
```bash
uvicorn api:app --port 8000 --reload  
```

### our weather API
    http://localhost:8000/docs

### our weather dashboard
    http://localhost:8000

# NODE-RED FLOW

# OpenWeather API Access Guide
## Current Weather Data Integration  
https://openweathermap.org/current
### Prerequisites
1. OpenWeatherMap account
2. API key (obtained after registration)

### Getting Your API Key
1. Log in to your OpenWeatherMap account
2. Navigate to the "API Keys" tab
3. Copy your default key or generate a new one

### Making API Requests
Base Endpoint:  
https://api.openweathermap.org/data/2.5/weather

Required Parameters:  

| Parameter | Description   | Example Value      |
|-----------|---------------|--------------------|
| `lat`     | Latitude      | `13.847050`        |
| `lon`     | Longitude     | `100.571942`       |
| `appid`   | Your API key  | `your_api_key_here`|

KU : lat = 13.847050, lon = 100.571942  
Ladprao : lat = 13.7993271, lon = 100.6258821

### [openweather.json](node-red%2Fopenweather.json)
#### How to use
* replace YOUR_API_KEY with your Openweather API key
* replace YOUR_STD_ID with your student ID

### [sensor.json](node-red%2Fsensor.json)
#### How to use
* replace YOUR_STD_ID with your student ID
* 

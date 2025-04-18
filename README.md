# Project Overview

This project monitors indoor temperature and humidity using the KY-015 sensor connected to a KidBright board. 
The system integrates this data with outdoor weather data from a public API to provide real-time insights, alerts, 
and recommendations for maintaining a comfortable home environment.

# Weather Dashboard

A web application that visualizes indoor/outdoor weather data with scatter plots, statistical summaries and recommendation actions.

## API Features

### Core Functionality

- **Weather Data**:
  - Get latest indoor/outdoor conditions
  - Temperature, humidity, and weather descriptions
  - Timestamped recordings
  - Place : KU (Computer building, KU Gym and OCS), Home at Ladprao

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

### Backend Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/primpunnapa/smarthome.git
   cd weather-analytics

2. Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    venv\Scripts\activate     # Windows
3. Install Python dependencies:
    ```bash
    pip install -r requirements.txt
   
4. Database setup:   
   * Create a MySQL database  
   * Update the connection settings in config.py  

### Frontend Setup

uvicorn api:app --port 8000 --reload
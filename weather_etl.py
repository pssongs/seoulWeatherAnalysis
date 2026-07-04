import requests
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import text, create_engine
import os
from datetime import datetime, UTC

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
#Load API key from .env file
load_dotenv()

api_key = os.getenv("OPENWEATHER_API_KEY")

#Retrieves information from .env file to create engine
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
database = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
create_cities_table = """
CREATE TABLE IF NOT EXISTS cities(
    city_id SERIAL PRIMARY KEY,
    openweather_id INTEGER UNIQUE,
    city_name VARCHAR(50) NOT NULL,
    country CHAR(2) NOT NULL,
    latitude DECIMAL(8,5),
    longitude DECIMAL(8,5)
);
"""

insert_city_sql = """
INSERT INTO cities (
    openweather_id,
    city_name,
    country,
    latitude,
    longitude
)
VALUES (
    :openweather_id,
    :city_name,
    :country,
    :latitude,
    :longitude
)

RETURNING city_id
"""

get_city_id = """
SELECT city_id 
FROM cities
WHERE openweather_id = :openweather_id
"""

get_weather_id = """
SELECT openweather_id FROM cities
"""

create_observation_table = """
CREATE TABLE IF NOT EXISTS observations (
    observation_id SERIAL PRIMARY KEY,
    city_id INTEGER NOT NULL
        REFERENCES cities(city_id),
    observation_time TIMESTAMP NOT NULL,

    temperature DECIMAL(5,2),
    feels_like DECIMAL(5,2),
    temp_min DECIMAL(5,2),
    temp_max DECIMAL(5,2),

    humidity INTEGER,
    pressure INTEGER,

    wind_speed DECIMAL(5,2),
    wind_direction INTEGER,
    wind_gust DECIMAL(5,2),

    cloudiness INTEGER,

    weather_main VARCHAR(30),
    weather_description VARCHAR(100),
    visibility INTEGER
)
"""

insert_observation_sql = """
    INSERT INTO observations (
    city_id,
    observation_time,
    temperature,
    feels_like,
    temp_min,
    temp_max,
    humidity,
    pressure,
    wind_speed,
    wind_direction,
    wind_gust,
    cloudiness,
    weather_main,
    weather_description,
    visibility
    )
    VALUES (
    :city_id,
    :observation_time,
    :temperature,
    :feels_like,
    :temp_min,
    :temp_max,
    :humidity,
    :pressure,
    :wind_speed,
    :wind_direction,
    :wind_gust,
    :cloudiness,
    :weather_main,
    :weather_description,
    :visibility 
    )

    RETURNING observation_id
"""
def create_db_engine():
    return create_engine(
    f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}")
    

def get_weather(openweather_id: int) -> dict:
    """Get request to the API to receive the weather in specificed city"""
    params = {
    "id": openweather_id,
    "appid": api_key,
    "units": "metric"
    }

    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json()

def get_weather_by_city_name(city: str) -> dict:
    """Get request to the API to receive the weather in specificed city"""
    params = {
    "q": city,
    "appid": api_key,
    "units": "metric"
    }

    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json()

def build_city_param(weather: dict) -> dict:
    """Build a dictionary of city values from the weather response."""
    return {
    "openweather_id": weather["id"],
    "city_name": weather["name"],
    "country": weather["sys"]["country"],
    "latitude": weather["coord"]["lat"],
    "longitude": weather["coord"]["lon"]
    }


def get_or_create_city(engine, city_param: dict) -> int:
    """Retrieves city_id of the city. If city does not exist it creates it and returns the city_id"""
    with engine.begin() as conn:
        city_id = conn.execute(text(get_city_id),city_param).scalar()

        if city_id is None:
            city_id = conn.execute(
                text(insert_city_sql),
                city_param
            ).scalar()

    return city_id    


def build_observation_param(weather: dict, city_id:int) -> dict:
    """Build a dictionary of observation values from the weather response"""
    return {
        "city_id": city_id,
        "observation_time": datetime.fromtimestamp(weather["dt"],UTC),
        "temperature": weather["main"]["temp"],
        "feels_like": weather["main"]["feels_like"],
        "temp_min": weather["main"]["temp_min"],
        "temp_max": weather["main"]["temp_max"],
        "humidity": weather["main"]["humidity"],
        "pressure": weather["main"]["pressure"],
        "wind_speed": weather["wind"]["speed"],
        "wind_direction": weather["wind"]["deg"],
        "wind_gust": weather["wind"].get("gust"),
        "cloudiness": weather["clouds"]["all"],
        "weather_main": weather["weather"][0]["main"],
        "weather_description": weather["weather"][0]["description"],
        "visibility": weather["visibility"]
    }
    

def insert_observation(engine, observation_param: dict) -> int:
    """Inserts one weather observation into the database"""
    with engine.begin() as conn:
        observation_id = conn.execute(
            text(insert_observation_sql),
            observation_param
        ).scalar()
        
    
    return observation_id       

def create_tables(engine) -> None:
    with engine.begin() as conn:
        conn.execute(text(create_cities_table))
        conn.execute(text(create_observation_table))

def get_openweather_ids_sql(engine) -> list:
    with engine.connect() as conn:
        return conn.execute(text(get_weather_id)).scalars().all()
    
def main():
    engine = create_db_engine()

    openweather_ids = get_openweather_ids_sql(engine)
    create_tables(engine)

    for city in openweather_ids:
        try:
            weather = get_weather(city)

            city_param = build_city_param(weather)

            city_id = get_or_create_city(engine,city_param)

            observation_param = build_observation_param(weather, city_id)

            observation_id = insert_observation(engine,observation_param)

            print(f"{city}: inserted observation {observation_id}")
        except Exception as e:
            print(f"Failed to process {city}: {e}")

if __name__ == "__main__":
    main()
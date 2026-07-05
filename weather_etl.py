import requests, logging, time
from sqlalchemy import text, create_engine
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, UTC
from sql import create_cities_table, insert_city_sql, get_city_id, get_weather_id, create_observation_table, insert_observation_sql
from config import (
    OPENWEATHER_API_KEY,
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    BASE_URL,
)
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

def create_db_engine():
    return create_engine(
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    

def get_weather(openweather_id: int) -> dict:
    """Get request to the API to receive the weather in specificed city"""

    MAX_RETRIES = 3
    RETRY_DELAY = 2

    params = {
    "id": openweather_id,
    "appid": OPENWEATHER_API_KEY,
    "units": "metric"
    }

    for attempt in range(1,MAX_RETRIES+1):
        try: 
            response = requests.get(BASE_URL,params=params, timeout=10)
            response.raise_for_status()

            return response.json()
        
        except requests.exceptions.RequestException as e:
            logging.error(f"Attempt {attempt}/{MAX_RETRIES} failed for city {openweather_id}: {e}")
            if attempt < 3:
                time.sleep(RETRY_DELAY * attempt)
            else: 
                raise 

            



def get_weather_by_city_name(city: str) -> dict:
    """Get request to the API to receive the weather in specificed city"""
    params = {
    "q": city,
    "appid": OPENWEATHER_API_KEY,
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
        "visibility": weather["visibility"],
        "sunrise": datetime.fromtimestamp(weather["sys"]["sunrise"], UTC),
        "sunset": datetime.fromtimestamp(weather["sys"]["sunset"], UTC),
        "timezone": weather["timezone"],
        "rain_1h": weather.get("rain", {}).get("1h", 0.0),
        "snow_1h": weather.get("snow", {}).get("1h", 0.0)
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

def get_openweather_ids(engine) -> list:
    with engine.connect() as conn:
        return conn.execute(text(get_weather_id)).scalars().all()
    
def main():
    logging.info("Starting ETL...")
    engine = create_db_engine()

    create_tables(engine)

    openweather_ids = get_openweather_ids(engine)
    total_cities = len(openweather_ids)
    successful_inserts = 0
    failed_cities = 0
    duplicate_observations = 0

    for openweather_id in openweather_ids:
        try:
            weather = get_weather(openweather_id)

            city_param = build_city_param(weather)
            city_id = get_or_create_city(engine,city_param)
            city_name = weather["name"]
            observation_param = build_observation_param(weather, city_id)

            observation_id = insert_observation(engine,observation_param)
            if observation_id is None:
                logging.info(f"{city_name}: Observation already exists. Skipping.")
                duplicate_observations += 1
            else:    
                logging.info(f"{city_name}: inserted observation {observation_id}")
                successful_inserts += 1
        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed for {openweather_id}: {e}")
            failed_cities += 1
        except SQLAlchemyError as e:
            logging.error(f"Database error for {openweather_id}: {e}")
            failed_cities += 1
        except Exception:
            logging.exception(f"Unexpected error for {openweather_id}")
            failed_cities += 1
    logging.info(
        f"ETL finished. Processed: {total_cities},"
        f"Inserted: {successful_inserts}, "
        f"Duplicates: {duplicate_observations}, "
        f"Failures: {failed_cities}"
    )

if __name__ == "__main__":
    main()
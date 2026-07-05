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
    visibility DECIMAL(5,2),
    sunrise TIMESTAMP NOT NULL,
    sunset TIMESTAMP NOT NULL,
    timezone INTEGER,
    rain_1h DECIMAL(5,2),
    snow_1h DECIMAL(5,2)
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
    visibility,
    sunrise,
    sunset,
    timezone,
    rain_1h,
    snow_1h
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
    :visibility, 
    :sunrise,
    :sunset,
    :timezone,
    :rain_1h,
    :snow_1h
    )

    ON CONFLICT (city_id, observation_time)
    DO NOTHING
    RETURNING observation_id
"""
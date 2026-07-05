# Weather ETL pipeline: Ingests OpenWeatherMap data into PostgreSQL for analysis

---------

This project automates collection of weather data from OpenWeatherMap API and stores it in a structured PostgreSQL database for analytics and historical tracking.

Flow of the project:
OpenWeather API
        ↓
weather_etl.py (pipeline orchestration)
        ↓
sql.py (database operations)
        ↓
PostgreSQL (Aiven)

config.py (global configuration used by all modules)

## Tech Stack

- Python 3.10+
- requests (API ingestion from OpenWeatherMap)
- JSON parsing (Python standard library)
- SQLAlchemy (database engine and connection management)
- psycopg2 (PostgreSQL driver used for direct query execution)
- PostgreSQL (Aiven.io database)

## Set up Instructions

1. Clone the repository
    git clone <your-repo-url>
    cd <your-project-folder>
2. Create a virtual environment (recommended)
    python -m venv venv
    source venv/bin/activate   # Mac/Linux
    venv\Scripts\activate      # Windows
3. Install dependencies
    pip install -r requirements.txt
4. Set up environment variables
    Create a `.env` file in the root directory:

    OPENWEATHER_API_KEY=your_api_key_here
    DATABASE_URL=postgresql://user:password@host:port/dbname?sslmode=require

    Do not commit `.env` files to version control.
5. Database setup
    - Ensure your PostgreSQL database is running and accessible
6. Run the ETL pipeline
    - python weather_etl.py

## Project Structure

```text
weather-etl/
│
├── weather_etl.py        # Main ETL pipeline entry point + retry logic
├── config.py             # Central configuration (env vars, constants)
├── sql.py                # Database connection
├── seed_cities.py        # Loads initial city data into database
├── requirements.txt
├── example.env
├── README.md
│
├── .github/workflows/    # CI/CD pipeline (GitHub Actions)
│
└── weather.ipynb         # Development / experimentation notebook
```


## Module Overview

### weather_etl.py
Main entry point for the ETL pipeline.  
Handles:
- API calls to OpenWeatherMap
- Data transformation
- Pipeline orchestration

### sql.py
Handles database interactions:
- Connecting to PostgreSQL (Aiven.io)
- Inserting weather and city data
- Executing SQL queries

### config.py
Central configuration file:
- Loads environment variables
- Stores API keys and database connection settings

### seed_cities.py
Initializes the database with required city data for API ingestion.

## Database Layer Design

This project uses a hybrid database approach:

- SQLAlchemy is used for database engine initialization and connection management
- psycopg2 is used for executing raw SQL queries and direct database operations requiring fine-grained control

## Pipeline Behavior

When executed, the pipeline:

- Loads configuration from environment variables
- Retrieves or seeds city data
- Calls OpenWeatherMap API for each city
- Uses retry logic in API request function to handle transient failures
- Transforms JSON responses into structured records
- Inserts data into PostgreSQL (Aiven)

### Failure Handling
- API requests include retry logic within `get_weather()` to handle temporary network or rate-limit issues
- If a city fails after retries, it is skipped and logged
- Database-related errors are handled separately in `sql.py`
- Failures in individual cities do not stop the overall pipeline execution


## CI/CD (GitHub Actions)

This project includes GitHub Actions workflows to:

- Validate code structure on push
- Run basic checks 
- Ensure core ETL components do not break on commits

## Sample SQL Output

Example query to retrieve the latest weather data per city:

```sql
SELECT 
    c.city_name,
    o.temperature,
    o.humidity,
    o.weather_condition,
    o.timestamp
FROM observations o
JOIN cities c ON o.city_id = c.city_id
ORDER BY o.timestamp DESC
LIMIT 5;

Example result:
| city_name | temperature | humidity | weather_condition | timestamp           |
| --------- | ----------- | -------- | ----------------- | ------------------- |
| Seoul     | 28.3        | 72       | Clear Sky         | 2026-07-05 09:10:00 |
| Incheon   | 27.8        | 75       | Cloudy            | 2026-07-05 09:10:00 |
| Busan     | 29.1        | 70       | Sunny             | 2026-07-05 09:10:00 |
| Daegu     | 30.2        | 65       | Clear Sky         | 2026-07-05 09:10:00 |
| Jeju      | 26.4        | 78       | Rain              | 2026-07-05 09:10:00 |
```
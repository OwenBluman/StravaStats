from sqlalchemy import Table, Column, Integer, String, Float, DateTime, MetaData
from databases import Database

DATABASE_URL = "sqlite:///./strava_activities.db"

database = Database(DATABASE_URL)
metadata = MetaData()

activities = Table(
    "activities",
    metadata,
    Column("id", Integer, primary_key=True),              # Local DB ID
    Column("activity_id", Integer, unique=True),          # Strava activity ID
    Column("name", String),
    Column("distance", Float),
    Column("moving_time", Integer),
    Column("elapsed_time", Integer),
    Column("total_elevation_gain", Float),
    Column("type", String),
    Column("start_date", DateTime),
    Column("average_speed", Float),
    Column("max_speed", Float),
    Column("location_city", String, nullable=True),
    Column("location_state", String, nullable=True),
)

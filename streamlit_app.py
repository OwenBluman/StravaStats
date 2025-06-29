import streamlit as st
import databases
import sqlalchemy
import asyncio

DATABASE_URL = "sqlite:////Users/owenbluman/Projects/PycharmProjects/Projects/StravaStats/strava_activities.db"

database = databases.Database(DATABASE_URL)

metadata = sqlalchemy.MetaData()

activities = sqlalchemy.Table(
    "activities",
    metadata,
    sqlalchemy.Column("activity_id", sqlalchemy.BigInteger, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String),
    sqlalchemy.Column("average_speed", sqlalchemy.Float),
)

async def fetch_activities(min_speed):
    query = activities.select()
    if min_speed is not None:
        query = query.where(activities.c.average_speed >= min_speed)
    return await database.fetch_all(query)

def main():
    st.title("Strava Activities Filter")

    min_speed = st.slider("Minimum average speed (m/s)", 0.0, 15.0, 0.0)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    if not database.is_connected:
        loop.run_until_complete(database.connect())

    activities_list = loop.run_until_complete(fetch_activities(min_speed))

    st.write(f"Found {len(activities_list)} activities with average speed ≥ {min_speed:.2f} m/s")

    for act in activities_list[:10]:
        st.write(f"**{act['name']}** — Avg speed: {act['average_speed']:.2f} m/s")

if __name__ == "__main__":
    main()

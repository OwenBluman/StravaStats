import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import httpx
import databases
import sqlalchemy

DATABASE_FILENAME = "strava_activities.db"
print("Database absolute path:", os.path.abspath(DATABASE_FILENAME))

DATABASE_URL = f"sqlite:///{DATABASE_FILENAME}"
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

activities = sqlalchemy.Table(
    "activities",
    metadata,
    sqlalchemy.Column("activity_id", sqlalchemy.BigInteger, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String),
    sqlalchemy.Column("average_speed", sqlalchemy.Float),
)

engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine)

app = FastAPI()

import os

CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/callback"

access_token = None

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/auth")
async def auth():
    url = (
        f"https://www.strava.com/oauth/authorize?client_id={CLIENT_ID}"
        f"&response_type=code&redirect_uri={REDIRECT_URI}&approval_prompt=force&scope=read,activity:read_all"
    )
    return HTMLResponse(f'<a href="{url}">Authorize with Strava</a>')

@app.get("/callback")
async def callback(request: Request):
    global access_token
    code = request.query_params.get("code")

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://www.strava.com/oauth/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
            },
        )
        token_resp.raise_for_status()
        tokens = token_resp.json()
        access_token = tokens["access_token"]

    total_fetched = await fetch_and_store_activities()
    return HTMLResponse(f"Authorization complete! Fetched {total_fetched} activities.")

async def fetch_and_store_activities():
    if not access_token:
        return 0

    headers = {"Authorization": f"Bearer {access_token}"}
    page = 1
    per_page = 200
    total_activities = 0

    while True:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.strava.com/api/v3/athlete/activities",
                headers=headers,
                params={"page": page, "per_page": per_page},
            )
            resp.raise_for_status()
            activities_page = resp.json()

        if not activities_page:
            break

        await store_activities(activities_page)
        print(f"Page {page} fetched: {len(activities_page)} activities")
        total_activities += len(activities_page)
        page += 1

    print(f"Total activities fetched and stored: {total_activities}")
    return total_activities

async def store_activities(activity_list):
    inserted = 0
    for activity in activity_list:
        query = activities.insert().values(
            activity_id=activity["id"],
            name=activity["name"],
            average_speed=activity.get("average_speed", 0.0),
        )
        try:
            await database.execute(query)
            inserted += 1
        except Exception as e:
            print(f"Failed to insert activity {activity['id']}: {e}")
    print(f"Inserted {inserted} activities into database.")

@app.get("/activities")
async def get_activities(min_speed: float = 0.0):
    query = activities.select().where(activities.c.average_speed >= min_speed)
    results = await database.fetch_all(query)
    return results


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

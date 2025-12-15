from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Location APIs")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# -----------------------------------------
# Reference Location (BridgeLabz Bengaluru)
# -----------------------------------------
def get_reference_location():
    return {
        "name": "BridgeLabz Solutions Bengaluru",
        "latitude": 12.9145732,
        "longitude": 77.6385797
    }

# -----------------------------------------
# Match Logic
# -----------------------------------------
def is_match(loc, reference):
    return (
        round(loc["latitude"], 4) == round(reference["latitude"], 4)
        and round(loc["longitude"], 4) == round(reference["longitude"], 4)
    )

# -----------------------------------------
# GET API – Current Location
# -----------------------------------------
@app.get("/current-location")
def current_location():
    if not GOOGLE_API_KEY:
        raise HTTPException(status_code=500, detail="Missing Google API key")

    # Get live latitude & longitude (Google Geolocation API)
    geo_url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={GOOGLE_API_KEY}"
    geo_res = requests.post(geo_url).json()

    if "location" not in geo_res:
        raise HTTPException(status_code=500, detail="Error fetching current location")

    lat = geo_res["location"]["lat"]
    lng = geo_res["location"]["lng"]

    current = {"latitude": lat, "longitude": lng}
    reference = get_reference_location()

    # Check match
    if is_match(current, reference):
        return {"match": "YES", "reference": reference, "current": current}
    else:
        return {"match": "NO", "reference": reference, "current": current}

# -----------------------------------------
# Request Body Model for Search
# -----------------------------------------
class SearchPlace(BaseModel):
    place: str

# -----------------------------------------
# POST API – Search Location
# -----------------------------------------
@app.post("/search-location")
def search_location(data: SearchPlace):
    if not GOOGLE_API_KEY:
        raise HTTPException(status_code=500, detail="Missing Google API key")

    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={data.place}&key={GOOGLE_API_KEY}"
    res = requests.get(url).json()

    if res.get("status") != "OK" or not res.get("results"):
        return {"message": "No location found"}

    result = res["results"][0]
    searched = {
        "latitude": result["geometry"]["location"]["lat"],
        "longitude": result["geometry"]["location"]["lng"]
    }

    return {"searched_place": data.place, "latitude": searched["latitude"], "longitude": searched["longitude"]}

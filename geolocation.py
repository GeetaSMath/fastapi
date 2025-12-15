from fastapi import FastAPI
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Location APIs")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


# -----------------------------------------
# REFERENCE LOCATION (BRIDGELABZ)
# -----------------------------------------
def get_reference_location():
    return {
        "name": "BridgeLabz Solutions Bengaluru",
        "latitude": 12.9145732,
        "longitude": 77.6385797
    }


# -----------------------------------------
# MATCH LOGIC
# -----------------------------------------
def is_match(loc, reference):
    return (
        round(loc["latitude"], 4) == round(reference["latitude"], 4)
        and round(loc["longitude"], 4) == round(reference["longitude"], 4)
    )


# -----------------------------------------
# GET API – CURRENT LOCATION (NO MATCH CHECK)
# -----------------------------------------
@app.get("/current-location")
def get_current_location():

    # Get live latitude & longitude
    geo_url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={GOOGLE_API_KEY}"
    geo_res = requests.post(geo_url).json()

    lat = geo_res["location"]["lat"]
    lng = geo_res["location"]["lng"]

    # Reverse geocoding → full address
    rev_url = (
        f"https://maps.googleapis.com/maps/api/geocode/json?"
        f"latlng={lat},{lng}&key={GOOGLE_API_KEY}"
    )
    rev_res = requests.get(rev_url).json()

    address = rev_res["results"][0]["formatted_address"]

    return {
        "address": address,
        "latitude": lat,
        "longitude": lng
    }


# -----------------------------------------
# REQUEST BODY MODEL
# -----------------------------------------
class SearchPlace(BaseModel):
    place: str


# -----------------------------------------
# POST API – SEARCH LOCATION (WITH MATCH CHECK)
# -----------------------------------------
@app.post("/search-location")
def search_location(data: SearchPlace):

    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={data.place}&key={GOOGLE_API_KEY}"
    res = requests.get(url).json()

    result = res["results"][0]

    searched = {
        "latitude": result["geometry"]["location"]["lat"],
        "longitude": result["geometry"]["location"]["lng"]
    }

    reference = get_reference_location()

    status = "MATCH" if is_match(searched, reference) else "NOT MATCH"

    return {
        "status": status,
        "searched_place": data.place,
        "latitude": searched["latitude"],
        "longitude": searched["longitude"]
    }

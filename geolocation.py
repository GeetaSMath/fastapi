from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import requests
import json
import os
#geomap

load_dotenv()   # Load .env file

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

app = FastAPI()

# -----------------------------------------
# Reference Location
# -----------------------------------------
def save_reference_location():
    reference = {
        "name": "BridgeLabz Solutions Bengaluru",
        "latitude": 12.9145732,
        "longitude": 77.6385797,
        "address": "5, 14th A Main Rd, HSR Layout, Bengaluru, Karnataka 560102"
    }
    try:
        with open("reference_location.json", "w") as f:
            json.dump(reference, f, indent=4)
    except (PermissionError, IOError) as e:
        raise HTTPException(status_code=500, detail=f"File error: {str(e)}")
    return reference

# -----------------------------------------
# Current Location
# -----------------------------------------
def get_current_location():
    if not GOOGLE_API_KEY:
        raise HTTPException(status_code=500, detail="Missing Google API key")

    try:
        geo_url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={GOOGLE_API_KEY}"
        geo_res = requests.post(geo_url, timeout=5).json()

        if "location" not in geo_res:
            return {"error": geo_res}

        lat = geo_res["location"]["lat"]
        lng = geo_res["location"]["lng"]

        rev_url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={GOOGLE_API_KEY}"
        rev_res = requests.get(rev_url, timeout=5).json()

        address = "Unknown"
        if rev_res.get("status") == "OK" and rev_res.get("results"):
            address = rev_res["results"][0].get("formatted_address", "Unknown")

        return {"address": address, "latitude": lat, "longitude": lng}

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Network error: {str(e)}")
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=500, detail=f"Parsing error: {str(e)}")

# -----------------------------------------
# Search Location
# -----------------------------------------
def search_location(place: str):
    if not GOOGLE_API_KEY:
        raise HTTPException(status_code=500, detail="Missing Google API key")

    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={place}&key={GOOGLE_API_KEY}"
        r = requests.get(url, timeout=5).json()

        if r.get("status") != "OK" or not r.get("results"):
            return None

        result = r["results"][0]
        return {
            "address": result.get("formatted_address", "Unknown"),
            "latitude": result["geometry"]["location"]["lat"],
            "longitude": result["geometry"]["location"]["lng"]
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Network error: {str(e)}")
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=500, detail=f"Parsing error: {str(e)}")

# -----------------------------------------
# Check Match
# -----------------------------------------
def check_location_match(loc, ref):
    try:
        return (
            round(loc["latitude"], 4) == round(ref["latitude"], 4) and
            round(loc["longitude"], 4) == round(ref["longitude"], 4)
        )
    except (TypeError, KeyError) as e:
        raise HTTPException(status_code=500, detail=f"Logic error: {str(e)}")

# -----------------------------------------
# Request Model for POST
# -----------------------------------------
class LocationRequest(BaseModel):
    place: str

# -----------------------------------------
# FastAPI Endpoints
# -----------------------------------------
@app.get("/current-location")
def current_location():
    reference = save_reference_location()
    current = get_current_location()
    if "error" in current:
        return {"message": "Error fetching current location", "details": current["error"]}
    return {"reference": reference, "current": current}

@app.post("/search-location")
def search_location_post(request: LocationRequest):
    reference = save_reference_location()
    searched = search_location(request.place)
    if not searched:
        return {"message": "No location found"}

    if check_location_match(searched, reference):
        return {"message": "Search location matches reference", "location": searched}
    else:
        return {
            "message": "Search location does not match reference",
            "searched_latitude": searched["latitude"],
            "searched_longitude": searched["longitude"],
            "reference_latitude": reference["latitude"],
            "reference_longitude": reference["longitude"]
        }

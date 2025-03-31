from flask import Flask, request, jsonify
import requests
import json
import math
from geopy.distance import geodesic

app = Flask(__name__)

# URLs and API Keys
USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
OPENCAGE_API_URL = "https://api.opencagedata.com/geocode/v1/json"
OPENCAGE_API_KEY = "37cbba91b5474d4d972be3e4e1b987d1"  # Replace with your API key
FAULT_FILE = "fault_lines.geojson"  # Replace with your file

class EarthquakeAnalyzer:
    def __init__(self):
        self.earthquake_data = []
        self.fault_lines = self.load_fault_lines()

    def load_fault_lines(self):
        """Load fault lines from GeoJSON."""
        try:
            with open(FAULT_FILE, "r") as f:
                data = json.load(f)
                fault_points = []
                for feature in data["features"]:
                    geometry = feature["geometry"]
                    if geometry["type"] == "LineString":
                        fault_points.extend(geometry["coordinates"])
            return fault_points
        except Exception as e:
            print(f"❌ Error loading fault lines: {e}")
            return []

    def get_nearest_city(self, latitude, longitude):
        """Get nearest city using OpenCage API."""
        url = f"{OPENCAGE_API_URL}?q={latitude}+{longitude}&key={OPENCAGE_API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data["results"]:
                city = data["results"][0]["formatted"]
                return city
        return "Unknown"

    def get_nearest_fault_distance(self, latitude, longitude):
        """Calculate distance to the nearest fault line."""
        min_distance = float("inf")
        for coord in self.fault_lines:
            if isinstance(coord, list) and len(coord) == 2:
                fault_lon, fault_lat = coord
                distance = geodesic((latitude, longitude), (fault_lat, fault_lon)).km
                min_distance = min(min_distance, distance)
        return round(min_distance, 2)

    def fetch_earthquake_data(self):
        """Fetch live earthquake data from USGS."""
        response = requests.get(USGS_URL)
        if response.status_code == 200:
            data = response.json()
            features = data["features"]
            for feature in features:
                properties = feature["properties"]
                geometry = feature["geometry"]
                place = properties["place"]
                magnitude = properties["mag"]
                latitude, longitude = geometry["coordinates"][1], geometry["coordinates"][0]
                self.earthquake_data.append({
                    "Place": place,
                    "Latitude": latitude,
                    "Longitude": longitude,
                    "Magnitude": magnitude
                })
        else:
            print("❌ Failed to fetch earthquake data!")

    def get_nearest_earthquake(self, latitude, longitude):
        """Find the nearest earthquake to the given coordinates."""
        min_distance = float("inf")
        nearest_quake = None
        for quake in self.earthquake_data:
            distance = geodesic((latitude, longitude), (quake["Latitude"], quake["Longitude"])).km
            if distance < min_distance:
                min_distance = distance
                nearest_quake = quake
        return nearest_quake, round(min_distance, 2)

# Initialize analyzer and fetch earthquake data once
analyzer = EarthquakeAnalyzer()
analyzer.fetch_earthquake_data()

@app.route("/analyze", methods=["GET"])
def analyze():
    """API endpoint to analyze earthquake data."""
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))

        # Get nearest city and fault line distance
        nearest_city = analyzer.get_nearest_city(lat, lon)
        fault_distance = analyzer.get_nearest_fault_distance(lat, lon)

        # Get nearest earthquake and distance
        nearest_quake, quake_distance = analyzer.get_nearest_earthquake(lat, lon)

        if nearest_quake:
            response = {
                "Nearest City": nearest_city,
                "Distance to Fault Line (km)": fault_distance,
                "Nearest Earthquake": {
                    "Place": nearest_quake["Place"],
                    "Magnitude": nearest_quake["Magnitude"],
                    "Distance to User (km)": quake_distance
                }
            }
        else:
            response = {
                "Nearest City": nearest_city,
                "Distance to Fault Line (km)": fault_distance,
                "Nearest Earthquake": "No recent earthquake data available."
            }

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)

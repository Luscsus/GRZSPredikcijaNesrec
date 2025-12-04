import pandas as pd
import requests
import os
import time
from datetime import timedelta, datetime
import glob
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
INPUT_DIR = 'matched_results'
OUTPUT_DIR = 'matched_results_weather'  # Optional: save to a new directory to avoid overwriting immediately
GEOCODING_URL = "https://api.geoapify.com/v1/geocode/search"
WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")

# Cache for geocoding to avoid repeated calls
location_cache = {}

def get_coordinates(location_name):
    if not location_name or pd.isna(location_name):
        return None, None
    
    # Clean location name (sometimes it might have extra info)
    location_query = str(location_name).split(',')[0].strip()
    
    if location_query in location_cache:
        return location_cache[location_query]
    
    try:
        params = {
            "text": location_query,
            "format": "json",
            "filter": "countrycode:si",
            "apiKey": GEOAPIFY_API_KEY
        }
        response = requests.get(GEOCODING_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        if "results" in data and data["results"]:
            result = data["results"][0]
            lat = result["lat"]
            lon = result["lon"]
            location_cache[location_query] = (lat, lon)
            time.sleep(0.2) # Rate limiting
            return lat, lon
    except Exception as e:
        print(f"Error geocoding {location_name}: {e}")
    
    location_cache[location_query] = (None, None)
    return None, None

def get_weather_history(lat, lon, date_obj):
    if lat is None or lon is None:
        return {}
    
    start_date = date_obj - timedelta(days=2)
    end_date = date_obj
    
    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "daily": ["temperature_2m_mean", "rain_sum", "snowfall_sum"],
            "timezone": "auto"
        }
        
        response = requests.get(WEATHER_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        if "daily" not in data:
            return {}
            
        daily = data["daily"]

        if len(daily["time"]) != 3:
            pass

        # Map results by date string
        weather_map = {}
        for i, d_str in enumerate(daily["time"]):
            weather_map[d_str] = {
                "temp": daily["temperature_2m_mean"][i],
                "rain": daily["rain_sum"][i],
                "snow": daily["snowfall_sum"][i]
            }
            
        date_str = date_obj.strftime("%Y-%m-%d")
        date_minus_1_str = (date_obj - timedelta(days=1)).strftime("%Y-%m-%d")
        date_minus_2_str = (date_obj - timedelta(days=2)).strftime("%Y-%m-%d")
        
        result = {}
        
        # Helper to safely get value
        def get_val(d_str, key):
            if d_str in weather_map and weather_map[d_str][key] is not None:
                return weather_map[d_str][key]
            return None

        # Populate requested fields
        result["Temp_tisti_dan"] = get_val(date_str, "temp")
        result["Temp_prejsni_dan"] = get_val(date_minus_1_str, "temp")
        result["Temp_preprejsni_dan"] = get_val(date_minus_2_str, "temp")
        
        result["Kolicina_dezja_tisti_dan"] = get_val(date_str, "rain")
        result["Kolicina_dezja_prejsni_dan"] = get_val(date_minus_1_str, "rain")
        result["Kolicina_dezja_preprejsni_dan"] = get_val(date_minus_2_str, "rain")
        
        result["Snezenje_cm_tisti_dan"] = get_val(date_str, "snow")
        result["Snezenje_cm_prejsni_dan"] = get_val(date_minus_1_str, "snow")
        result["Snezenje_cm_preprejsni_dan"] = get_val(date_minus_2_str, "snow")
        
        return result

    except Exception as e:
        print(f"Error fetching weather for {lat}, {lon} on {date_obj}: {e}")
        return {}

def process_files():
    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    xlsx_files = glob.glob(os.path.join(INPUT_DIR, "*.xlsx"))
    
    for file_path in xlsx_files:
        print(f"Processing {file_path}...")
        try:
            df = pd.read_excel(file_path)
            
            # Check if required columns exist
            if "Datum" not in df.columns:
                print(f"Skipping {file_path}: 'Datum' column not found.")
                continue
            
            # Determine location column
            loc_col = "Lokacija"
            if "Lokacija" not in df.columns:
                if "location" in df.columns:
                    loc_col = "location"
                else:
                    print(f"Skipping {file_path}: Location column not found.")
                    continue
            
            print(f"Using '{loc_col}' for location data.")

            # Prepare new columns
            new_columns = [
                "Temp_tisti_dan", "Temp_prejsni_dan", "Temp_preprejsni_dan",
                "Kolicina_dezja_tisti_dan", "Kolicina_dezja_prejsni_dan", "Kolicina_dezja_preprejsni_dan",
                "Snezenje_cm_tisti_dan", "Snezenje_cm_prejsni_dan", "Snezenje_cm_preprejsni_dan"
            ]
            
            for col in new_columns:
                if col not in df.columns:
                    df[col] = None

            # Iterate and fetch data
            # Using iterrows is slow but simple. For API calls, the bottleneck is the network anyway.
            for index, row in df.iterrows():
                date_val = row["Datum"]
                location_val = row[loc_col]
                
                if pd.isna(date_val) or pd.isna(location_val):
                    continue
                
                # Ensure date is datetime object
                if not isinstance(date_val, datetime):
                    try:
                        date_val = pd.to_datetime(date_val)
                    except:
                        continue
                
                # Geocode
                lat, lon = get_coordinates(location_val)
                
                if lat is None:
                    print(f"Could not geocode: {location_val}")
                    continue
                
                # Fetch Weather
                weather_data = get_weather_history(lat, lon, date_val)
                
                # Update DataFrame
                for key, val in weather_data.items():
                    if key in df.columns:
                        df.at[index, key] = val
                
                time.sleep(1)
            
            # Save result
            filename = os.path.basename(file_path)
            output_path = os.path.join(OUTPUT_DIR, filename)
            df.to_excel(output_path, index=False)
            print(f"Saved processed file to {output_path}")

        except Exception as e:
            print(f"Failed to process {file_path}: {e}")

if __name__ == "__main__":
    process_files()

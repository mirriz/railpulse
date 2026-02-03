import requests
import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# --- CONFIGURATION ---
# Ensure this name matches what is in your .env file!
# We previously called it HUXLEY_TOKEN, but your code used OLDBWS_TOKEN.
TOKEN = os.getenv("HUXLEY_TOKEN") or os.getenv("OLDBWS_TOKEN")

BASE_URL = "https://huxley2.azurewebsites.net"

SPOKES = {
    "MAN": "Manchester Piccadilly",
    "YRK": "York",
    "WKF": "Wakefield Westgate",
    "HGT": "Harrogate"
}

def get_live_arrivals(hub_code="LDS"):
    """
    Fetches arrivals from Huxley and scans history for spoke stations.
    Includes logic to handle pass through trains (e.g. London -> Wakefield -> Leeds).
    """

    url = f"{BASE_URL}/arrivals/{hub_code}/20?accessToken={TOKEN}&expand=true"    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        trains = data.get("trainServices")
        if not trains:
            print(f"No trains found for {hub_code} (Station might be closed).")
            return []

        relevant_trains = []

        
        for train in trains:
            print(train)
            origin_list = train.get("origin", [])
            if not origin_list:
                continue
            origin_crs = origin_list[0].get("crs")
            
            # 2. Get Stopping History
            prev_points_data = train.get("previousCallingPoints", [])
            calling_points = prev_points_data[0].get("callingPoint", []) if prev_points_data else []
            
            matched_spoke = None
            
            # Direct Spoke (e.g. Manchester -> Leeds)
            if origin_crs in SPOKES:
                matched_spoke = origin_crs
            
            # Pass-Through Spoke (e.g. London -> Wakefield -> Leeds)
            else:
                for point in calling_points:
                    if point.get("crs") in SPOKES:
                        matched_spoke = point.get("crs")
                        # We don't break here; if it stops at multiple spokes
            
            # Process Valid Trains
            if matched_spoke:
                et = train.get("eta") 
                std = train.get("sta")
                
                status = "On Time"
                delay_minutes = 0
                
                if et == "Cancelled":
                    status = "Cancelled"
                    delay_minutes = 60
                elif et and et != "On time":
                    status = "Delayed"
                    delay_minutes = 10
                
                delay_reason = train.get("delayReason")
                
                relevant_trains.append({
                    "from_code": matched_spoke,         
                    "from_name": SPOKES[matched_spoke],
                    "origin_city": origin_list[0].get("locationName"), 
                    "scheduled": std,
                    "estimated": et,
                    "status": status,
                    "delay_weight": delay_minutes,
                    "platform": train.get("platform"),
                    "delay_reason": delay_reason
                })
                
        return relevant_trains

    except Exception as e:
        print(f"API ERROR: {e}. Using mock data.")
        return [
        {
            "from_code": "MAN",
            "from_name": "Manchester Piccadilly",
            "origin_city": "Manchester Piccadilly",
            "scheduled": "18:00",
            "estimated": "18:15", # Late!
            "status": "Delayed",
            "delay_weight": 15,
            "platform": "12"
        },
        {
            "from_code": "YRK",
            "from_name": "York",
            "origin_city": "York",
            "scheduled": "18:05",
            "estimated": "On time",
            "status": "On Time",
            "delay_weight": 0,
            "platform": "8"
        },
        {
            "from_code": "WKF",
            "from_name": "Wakefield Westgate",
            "origin_city": "London Kings Cross",
            "scheduled": "18:10",
            "estimated": "Cancelled", # Severe!
            "status": "Cancelled",
            "delay_weight": 60,
            "platform": "TBC"
        },
         {
            "from_code": "HGT",
            "from_name": "Harrogate",
            "origin_city": "Harrogate",
            "scheduled": "18:20",
            "estimated": "On time",
            "status": "On Time",
            "delay_weight": 0,
            "platform": "1"
        }
    ]

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: No Token found. Check your .env file.")
    else:
        print("Scanning for trains (Direct & Pass-Through)...\n")
        results = get_live_arrivals()
        
        print(f"Found {len(results)} relevant trains.")
        for t in results:
            print(f" -> [Line: {t['from_code']}] {t['scheduled']} Service from {t['origin_city']}: {t['status']}. {t['delay_reason'] if t['delay_reason'] else ''} ({t['estimated']}). Platform {t['platform'] if t['platform'] else 'TBC'}")
import requests
import platform
import json
import uuid
import os
from supabase import create_client
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

load_dotenv(resource_path('.env'))

def get_real_client_ip():
    """Fetches the real public IP address of the client in a desktop (.exe) environment."""
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=3)
        return response.json().get('ip')
    except Exception:
        return None

def get_location_data():
    """Fetches location data based on the real IP."""
    real_ip = get_real_client_ip()
    
    if not real_ip:
        return None 

    url = f"http://ip-api.com/json/{real_ip}?fields=status,country,regionName,city,lat,lon"
    try:
        response = requests.get(url, timeout=3)
        data = response.json()
        if data.get('status') == 'success':
            return {
                'country': data.get('country'),
                'region': data.get('regionName'),
                'city': data.get('city'),
                'lat': data.get('lat'),
                'lon': data.get('lon')
            }
    except Exception:
        pass
    return None

def get_supabase_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        return None
    
    return create_client(url, key)

def get_or_create_machine_id():
    """Retrieves or generates a unique machine ID and stores it locally."""
    id_file = os.path.join(os.path.expanduser("~"), ".magic_tracker_id.json")
    
    if os.path.exists(id_file):
        try:
            with open(id_file, "r") as f:
                return json.load(f).get("machine_id")
        except:
            pass
            
    new_id = uuid.uuid4().hex
    try:
        with open(id_file, "w") as f:
            json.dump({"machine_id": new_id}, f)
    except:
        pass
    return new_id

def log_app_usage(app_name="unknown_exe_app", action="app_executed", details=None):
    """Logs app usage to Supabase."""
    try:
        os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"
        user_agent = f"Desktop EXE / {os_info}"
    except Exception:
        user_agent = "Unknown Desktop"

    try:
        ip_address = requests.get('https://api.ipify.org', timeout=3).text
    except Exception:
        ip_address = "Offline or Blocked"

    loc_data = get_location_data()
    
    try:
        client = get_supabase_client()
        if not client:
            return False
            
        machine_id = get_or_create_machine_id()

        kst = timezone(timedelta(hours=9))
        korea_time = datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S")
        
        log_data = {
            "session_id": machine_id, 
            "app_name": app_name,
            "action": action,
            "timestamp": korea_time, 
            "country": loc_data['country'] if loc_data else "Unknown",
            "region": loc_data['region'] if loc_data else "Unknown",
            "city": loc_data['city'] if loc_data else "Unknown",
            "lat": loc_data['lat'] if loc_data else 0.0,
            "lon": loc_data['lon'] if loc_data else 0.0,
            "details" : details,
            "user_agent": user_agent,
            "ip_address": ip_address
        }
        
        client.table('usage_logs').insert(log_data, returning='minimal').execute()
        return True
    except Exception:
        return False
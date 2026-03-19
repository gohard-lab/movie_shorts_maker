import requests
from supabase import create_client
from datetime import datetime, timezone, timedelta

def get_real_client_ip():
    """데스크톱(.exe) 환경에서는 파이썬이 직접 공인 IP를 조회합니다."""
    try:
        # 프록시 서버가 없으므로 가장 단순하고 확실한 방법으로 내 공인 IP를 가져옵니다.
        response = requests.get('https://api.ipify.org?format=json', timeout=3)
        return response.json().get('ip')
    except Exception:
        return None

def get_location_data():
    """실제 IP를 기반으로 위치 정보를 가져옵니다."""
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
    # 사용하시는 Supabase URL과 Key를 그대로 넣으시면 됩니다.
    url = "https://gkzbiacodysnrzbpvavm.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdremJpYWNvZHlzbnJ6YnB2YXZtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM1NzE2MTgsImV4cCI6MjA4OTE0NzYxOH0.Lv5uVeNZOyo21tgyl2jjGcESoLl_iQTJYp4jdCwuYDU"

    return create_client(url, key)

def log_app_usage(app_name="unknown_exe_app", action="app_executed", details=None):
    """Supabase에 .exe 프로그램 실행 기록을 남깁니다."""
    loc_data = get_location_data()
    
    try:
        client = get_supabase_client()
        if not client:
            return False
            
        kst = timezone(timedelta(hours=9))
        korea_time = datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S")
        
        log_data = {
            "app_name": app_name,
            "action": action,
            "timestamp": korea_time, 
            "country": loc_data['country'] if loc_data else "Unknown",
            "region": loc_data['region'] if loc_data else "Unknown",
            "city": loc_data['city'] if loc_data else "Unknown",
            "lat": loc_data['lat'] if loc_data else 0.0,
            "lon": loc_data['lon'] if loc_data else 0.0,
            "details" : details
        }
        
        client.table('usage_logs').insert(log_data, returning='minimal').execute()
        return True
    except Exception:
        return False
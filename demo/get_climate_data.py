import requests

def fetch_climate_data(api_key, lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    
    response = requests.get(url)
    data = response.json()

    if response.status_code == 200:
        climate_temperature = data['main']['temp']
        climate_humidity = data['main']['humidity']
        return climate_temperature, climate_humidity
    else:
        print("Error fetching climate data:", data.get("message", "Unknown error"))
        return None, None

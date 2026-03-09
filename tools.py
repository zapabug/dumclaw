import requests

def get_weather():

    r = requests.get("https://wttr.in/?format=j1")
    data = r.json()

    current = data["current_condition"][0]

    temp = current["temp_C"]
    conditions = current["weatherDesc"][0]["value"]

    return f"{temp}°C and {conditions}"
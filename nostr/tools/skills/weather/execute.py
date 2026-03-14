import requests

def execute():
    """
    Fetch the current weather using wttr.in API.
    Returns a string with temperature and conditions.
    """
    try:
        r = requests.get("https://wttr.in/?format=j1", timeout=10)
        r.raise_for_status()
        data = r.json()
        current = data["current_condition"][0]
        temp = current["temp_C"]
        conditions = current["weatherDesc"][0]["value"]
        return f"{temp}°C and {conditions}"
    except (requests.RequestException, KeyError, IndexError) as e:
        return f"Weather service unavailable: {str(e)}"
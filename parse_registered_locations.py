import pandas as pd
from fetch_weather_data import Location


# PLEASE use csv and readlines()
def parse_registered_locations(source) -> list[Location]:
    df = pd.read_csv(source)
    if df.empty:
        return None

    _REGISTERED_LOCATIONS = []
    for idx in df.index:
        _REGISTERED_LOCATIONS.append([df.loc[idx, col] for col in df.columns])

    return [Location.form(item) for item in _REGISTERED_LOCATIONS]
import hashlib
import pandas as pd
import requests
from typing import Union
import csv
import os

coordinate_url = f'http://api.openweathermap.org/geo/1.0/direct?&appid={{key}}'
coordinate_url.format(
    key=BLANK # open weather map API key goes here
)

def _parse_coordinate_json(source: Union[dict, None]) -> Union[tuple[str, str], None]:
    if not source:
        return None
    
    source = source[0]

    lat = str(source.get('lat'))
    long = str(source.get('lon'))

    return (lat, long)

def retrieve(city: str, country: str) -> str:
    retries = 5
    params = {
        'q': [city, country],
    }
    for _ in range(retries):
        try:
            resp = requests.get(coordinate_url, timeout=10, params=params)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError):
            print(f'{_} of {retries} exhausted: {coordinate_url}.')

    return None

def create_id_for_registered_location(city: str, country: str) -> str:
    if not os.path.exists('config.csv'):
        print('Config file not found. Creating a new one.')

        with open('config.csv', 'w', newline='', encoding='utf-8') as config:
            writer = csv.writer(config)
            writer.writerows(
                ['id_sorter_stable_start'],
                [20]
            )

    config = pd.read_csv('config.csv')
    _sorter_stable_start = config.loc[0, 'id_sorter_stable_start']

    citycountry = city + ' ' + country
    hash = hashlib.sha256()
    hash.update(citycountry.encode())
    
    citycountry_id = f'{_sorter_stable_start}_' + hash.hexdigest()

    # update config data point
    config['id_sorter_stable_start'] = _sorter_stable_start + 1
    config.to_csv('config.csv', sep=',', index=False)

    return citycountry_id


def fetch_registered_location(city: str, country: str) -> Union[list[dict], None]:
    coordinate_json = retrieve(city, country)
    if not coordinate_json:
        return None

    return coordinate_json

def register_location_pipeline(city: str, country: str) -> bool:

    coordinate_json = fetch_registered_location(city, country)
    coordinates = _parse_coordinate_json(coordinate_json)
    if not coordinates:
        return False

    citycountry_id = create_id_for_registered_location(city, country)
    
    lat = coordinates[0]
    long = coordinates[1]

    with open('_registered_locations.csv', mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["loc_id","city","country","lat","long"])

        writer.writerow(
            {
                "loc_id": citycountry_id,
                "city": city,
                "country": country,
                "lat": lat,
                "long": long
            }
        )

    return True
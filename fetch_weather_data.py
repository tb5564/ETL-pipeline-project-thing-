from dataclasses import dataclass
import openmeteo_requests
from retry_requests import retry
import requests_cache
import pandas as pd
from typing import Union
import time

_STANDARD_VALUE_TRUNCATION = 14
CURRENT_VALUE_RANGE = range(15)

pd.set_option('display.max_colwidth', None)
pd.set_option('display.precision', _STANDARD_VALUE_TRUNCATION)

@dataclass(frozen=True)
class Location:
    loc_id: str
    city: str
    country: str
    lat: float
    long: float

    @staticmethod
    def form(source: list[str]) -> Location:
        return Location(
            loc_id= source[0],
            city=source[1],
            country=source[2],
            lat=source[3],
            long=source[4]
        )

def ingest(_registered_locations: Union[list[Location], list], timestamp: str) -> pd.DataFrame:
    _STANDARD_LOCATIONS = [
        Location("0_5acb56d47f383e98b8455b4da2aa0c1175541fae84bcb51984fd09709fc5e46f", 
                "New York", "United States", 40.7128, -74.0060),
        Location("1_b494d8a0198fd6e030172f327af4cda1f8579b1f1984589b16d2078668f6daca", 
                "London", "United Kingdom", 51.5072, -0.1276),
        Location("2_d753fbe5e86c12eae16e958faedd799e5d55dd376b7d44c1822df1cc8cc46473", 
                "Tokyo", "Japan", 35.6762, 139.6503),
        Location("3_07a6980da3f34493452f1a53449a9846acf22ea00995d893077a113da415de83", 
                "Sydney", "Australia", -33.8688, 151.2093),
        Location("4_1c5f84b8ae9be1f94d6c25aaed5fa711b09202de4c7a8e9fcb458392b1198f49", 
                "Paris", "France", 48.8566, 2.3522),
        Location("5_cb5b301910fc3ebadc66a3ea089c1ce71f30c4a51134f6b414fbd28dba372192", 
                "Cairo", "Egypt", 30.0444, 31.2357),
        Location("6_fc34bc6e72582cb55ec5e84246dc07c17ca5839060745fb014b3c461d5350ab1", 
                "Rio de Janeiro", "Brazil", -22.9068, -43.1729),
        Location("7_2a8ac2952e94106c8cb2c5edb6f082f28c76db85abb17507e43fccf7e5384b5d", 
                "Cape Town", "South Africa", -33.9249, 18.4241),
        Location("8_f302f81ce3edad75d2d49694b3e8f7c03b573ed61a062cd04d707f49d870907a", 
                "Mumbai", "India", 19.0760, 72.8777),
        Location("9_19909bc07450c32e94f1f916b511f7189cda2bea153e1bc6b486c17c1d615cd6", 
                "Beijing", "China", 39.9042, 116.4074),
        Location("10_02ed7d739a87a36df3c146dc204eb28c2f5ea4f66b129c5d33b9239ed1ee9c94",
                 "Singapore", "Singapore", 1.3521, 103.8198),
        Location("11_cca03a1bbfe051dfc19b496cc7cf9c87b13b3c49564b6d86140d961ccfdfc412",
                 "Mexico City", "Mexico", 19.4326, -99.1332),
        Location("12_3daaa494ac3d3c383d0589083f3e1b9e4b749657feca287cfc1da01a118511e7",
                 "Toronto", "Canada", 43.6532, -79.3832),
        Location("13_ac0b99519a089821648beca77eae62dfeb1309824d6f1ce43d0c914235a5f906",
                 "Moscow", "Russia", 55.7558, 37.6173),
        Location("14_1047f1345b75c8a24bf7092d6ee915eced031c3991921f444df22e1676c8242e",
                 "Istanbul", "Turkey", 41.0082, 28.9784),
        Location("15_bcd2d1ebb1100fcca6efc4f51601d45d0af34771edbad26cb42666dcfd0b8233",
                 "Buenos Aires", "Argentina", -34.6037, -58.3816),
        Location("16_b7d1ff3965ed1327ce7c26f8718e64733028c49a621ab40c6d07c5ef0942e54a",
                 "Nairobi", "Kenya", -1.2921, 36.8219),
        Location("17_25b2adf1a503bb090a661a85699ce54081e61004e2f875b0047d06b07ad71157",
                 "Seoul", "South Korea", 37.5665, 126.9780),
        Location("18_694db8af8942a73ccbf8a6eb306a863e9c16ab909bb72b278cdcb0a2b0ec6ea1",
                 "Reykjavik", "Iceland", 64.1466, -21.9426),
        Location("19_21a5b760d1e3ed82d6520f2334ba4b77409f39877413413d32b73b1032cd8f85",
                 "Auckland", "New Zealand", -36.8509, 174.7645),
        * (_registered_locations or [])
    ]

    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    url = "https://api.open-meteo.com/v1/forecast"

    data = []
    
    for loc in _STANDARD_LOCATIONS:
        data_obtained = False

        params = {
            "latitude": loc.lat,
            "longitude": loc.long,
            "models": "ncep_gfs_seamless",
            "current": [
                "temperature_2m", 
                "is_day", 
                "relative_humidity_2m", 
                "apparent_temperature", 
                "precipitation", 
                "showers", 
                "rain", 
                "snowfall", 
                "weather_code", 
                "cloud_cover", 
                "pressure_msl", 
                "surface_pressure", 
                "wind_speed_10m", 
                "wind_direction_10m", 
                "wind_gusts_10m"
            ],
            "forecast_days": 7,
        }

        while data_obtained == False:
            try:
                responses = openmeteo.weather_api(url, params=params)
        
                response = responses[0]
        
                current = response.Current()
                data.append([
                loc.loc_id,
                loc.city,
                loc.country,
                response.Elevation(),
                * [float(str(current.Variables(idx).Value())[:_STANDARD_VALUE_TRUNCATION]) for idx in CURRENT_VALUE_RANGE],
                'NULL',
                'No change.'
                ])
                data_obtained = True

            except: 
                # The simplest kind of resumable state for api IO. 
                # instead of doing this i suppose I could just quarantine the rows until new data is obtained. 
                # the sleeping option can remain as default behavior and "quarantine" can be configured in
                # the config file TODO

                print('Data extraction paused.')
                time.sleep(100) # usage limit? TODO


    ingestion_data = pd.DataFrame(
        data=data, 
        columns=[
            'loc_id',
            'city',
            'country',
            'elevation_m_asl',
            'temperature_2m',
            'is_day',
            'relative_humidity_2m',
            'apparent_temperature',
            'precipitation',
            'showers',
            'rain',
            'snowfall',
            'weather_code',
            'cloud_cover',
            'pressure_msl',
            'surface_pressure',
            'wind_speed_10m',
            'wind_direction_10m',
            'wind_gusts_10m',
            'obtained_at',
            'change_type'
        ])

    ingestion_data['obtained_at'] = [timestamp for _ in range(len(ingestion_data))]

    return ingestion_data
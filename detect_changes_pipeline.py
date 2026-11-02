import pandas as pd

_STANDARD_VALUE_TRUNCATION = 14

_EXCLUDE_ID_CITY_COUNTRY = 3
_EXCLUDE_TIMESTAMP_CHANGE = -2

pd.set_option('display.max_colwidth', None)
pd.set_option('display.precision', _STANDARD_VALUE_TRUNCATION)

_CHANGE_TYPES = {
    "elevation_m_asl": "Elevation",
    "temperature_2m": "Temperature",
    "is_day": "Day",
    "relative_humidity_2m": "Relative Humidity",
    "apparent_temperature": "Apparent Temp",
    "precipitation": "Precipitation",
    "showers": "Showers",
    "rain": "Rain",
    "snowfall": "Snowfall",
    "weather_code": "Weather code",
    "cloud_cover": "Cloud coverage",
    "pressure_msl": "Pressure",
    "surface_pressure": "Surface pressure",
    "wind_speed_10m": "Wind speed",
    "wind_direction_10m": "Wind direction",
    "wind_gusts_10m": "Wind gusts",
}

class DetectChanges:

    def __init__(self, old: pd.DataFrame, new: pd.DataFrame):

        # sort dataframe according to their ids so the data is perfectly mapped.
        # pandas sorts by the first char TODO
        self.old = old.sort_values(by='loc_id', axis='index', ignore_index=True)
        self.new = new.sort_values(by='loc_id', axis='index', ignore_index=True)


    # COULD BE MORE ELABORATE FOR CITIES TODO
    def _visualize(self) -> None:

        old = self.old[self.old.columns[
            _EXCLUDE_ID_CITY_COUNTRY:
            _EXCLUDE_TIMESTAMP_CHANGE
        ]]
        new = self.new[self.new.columns[
            _EXCLUDE_ID_CITY_COUNTRY:
            _EXCLUDE_TIMESTAMP_CHANGE
        ]]

        visual_comp = old.compare(new, result_names=('record', 'new'))
        print(visual_comp)


    def storage(self, quarantined_extraneous_record: pd.DataFrame) -> None:

        if not quarantined_extraneous_record.empty:
            self.new = pd.concat([self.new, quarantined_extraneous_record])

        with open('record.csv', 'w', newline='', encoding='utf-8') as record:

            self.new.to_csv(
                record,
                sep=',',
                quoting=1,
                quotechar='"',
                index=False
            )
            record.flush() # this is done because the python memory buffer waits to store the file. But it seems to
            # not do anything for the issue because its not about the buffer but about how the data gets to the 
            # record and is processed from it.

        with open('history.csv', 'w', newline='', encoding='utf-8') as history:
            self.new = pd.concat([self.old, self.new]).drop_duplicates()

            self.new.to_csv(
                history,
                sep=',',
                quoting=1,
                quotechar='"',
                index=False
            )
            history.flush()


    def map_timestamps(self, loc_id_objs: list, timestamp: str) -> None:

        id_obtained_at = dict([(loc_id, timestamp) for loc_id in loc_id_objs])
        
        self.new['obtained_at'] = (
            self.new['loc_id']
            .map(id_obtained_at)
            .fillna(self.new['obtained_at'])
        )


    def map_change_types(self, id_change_types: dict) -> None:

        self.new['change_type'] = (
            self.new['loc_id']
            .map(id_change_types)
            .fillna(self.new['change_type'])
        )


    def find_change_type(self, comp: pd.DataFrame) -> dict[str, str]:

        id_change_types = {}
        changed_ids = list(comp['loc_id'])

        # reduce load.
        comp = comp.drop(columns=['loc_id', 'obtained_at', 'change_type', 'city', 'country'])
        
        for _idx, row in comp.iterrows():
            changed = row[row.isna()].index.to_list()
            if not changed:
                id_change_types[changed_ids[_idx]] = 'No change.'
                continue

            change_types = [_CHANGE_TYPES.get(item) for item in changed]
            id_change_types[changed_ids[_idx]] = ' change, '.join(change_types) + ' change.'

        return id_change_types

        
    def run_pipeline(self, timestamp: str) -> None:
        _seen_extraneous_record = False
        _seen_changed_record = False
        quarantined_extraneous_record = pd.DataFrame([])

        record = len(self.old)

        if record != len(self.new):
            _seen_extraneous_record = True

        if _seen_extraneous_record == True:
            quarantined_extraneous_record = self.new[record:]
            self.new = self.new[:record]
                    

        # bypass pandas "Series truth ambiguous" ValueError
        comp = self.new[self.old != self.new].iloc[
            :, 
            _EXCLUDE_ID_CITY_COUNTRY:_EXCLUDE_TIMESTAMP_CHANGE
        ].dropna(how='all') 

        if not comp.empty:
            _seen_changed_record = True

        if True in (_seen_changed_record, _seen_extraneous_record):
            print('* Changes were detected.', flush=True)

            if _seen_changed_record == True:
                self._visualize()
                comp = self.new[self.old == self.new]
                
                id_change_types = self.find_change_type(comp)

                self.map_change_types(id_change_types)

                self.map_timestamps(id_change_types.keys(), timestamp)

            self.storage(quarantined_extraneous_record)
            print('* Record file successfully updated.')
            print('* History file successfully updated.')

            return None

        print('* No changes were detected.', flush=True)
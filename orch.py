from fetch_weather_data import ingest
from parse_registered_locations import parse_registered_locations
from detect_changes_pipeline import DetectChanges
from register_location import register_location_pipeline
import sys
import time
import pandas as pd
import os

_STANDARD_VALUE_TRUNCATION = 14

pd.set_option('display.max_colwidth', None)
pd.set_option('display.precision', _STANDARD_VALUE_TRUNCATION)

# stream data
# upserts, (check)
# checkpointing 
# structured logs
# config file, (check)
# cli, (check)
# scheduler
# idempotence
# transaction "Keep related database changes consistent if something fails."
# quaratine unexpected things for later, (check), sort of


_WEEKDAYS = {
    0: 'Sunday',
    1: 'Monday',
    2: 'Tuesday',
    3: 'Wednesday',
    4: 'Thursday',
    5: 'Friday',
    6: 'Saturday',
}
_TIMESTAMP = time.strftime(
    f'{{day}}, %m-%d-%Y, %I:%M%p',
    time.localtime()
).format(day=_WEEKDAYS.get(int(time.strftime('%w'))))


# COMMAND PRIMIITIVES
# Add a command to write to config file, disabling features like visualization of 
# after <-- before effect in the Detect change, perhaps a list of which cities
# to prioritize (if it is actually more meaningful beyond what i really want to do) 
# TODO

_COMMANDS = (
    'HELP',
    'REGISTER',
    'EXAMINE',
    'LOCATIONS',
)

_COMMANDS_NO_ARGS = (
    'HELP',
    'EXAMINE',
    'LOCATONS',
)

_COMMANDS_WITH_ARGS = (
    'REGISTER'
)

_COMMAND_DESCRIPTIONS = (
    '*\n'
    '-- REGISTER: Store a new location to file to retrieve its weather data in addition'
    'to that of \'standard locations\': e.g. \'REGISTER London UK\' (input country'
    'parameter must be the alpha-2 country code of a country of interest).\n'
    '-- EXAMINE: Run this command to detect changes.\n'
    '-- LOCATIONS: Run this command to display a pandas dataframe showing all locations'
    ' you\'ve registered.\n'
)

class CommandEngine():

    @staticmethod
    def _validate(source: list[str]) -> bool:

        keyw = source[0].upper()
        if keyw in _COMMANDS:
            if keyw in _COMMANDS_NO_ARGS and len(source) > 1:
                print('* Excessive arguments for given command.')
                return False
            
            elif keyw in _COMMANDS_WITH_ARGS and len(source) == 1:
                print('* Invalid format. No arguments provided for given command')
                return False

            return True
            
        print('* Not recognized command keyword.')
        return False
        
    def __init__(self, source: list[str]):
        self.input = source

    def _help(self):
        print(_COMMAND_DESCRIPTIONS)
        return

    def _register(self) -> None:
        reg = [None, None]
        for idx, item in enumerate(self.input[1:]):
            reg[idx] = item
        
        if reg[0] is None:
            print(f'* No city parameter provided: {reg}.')
            return None

        elif reg[1] is None:
            print(f'* No country parameter provided: {reg}.')
            return None

        elif reg[0] == reg[1]:
            print(f'* Arguments are equal.')
            return None

        elif len(reg[1]) > 2:
            print(f'* Input country arg too long to be a country code.')
            return None

        city = reg[0].title()
        country = reg[1].upper()

        if register_location_pipeline(city, country) == False:
            print(f'Failed to register input: {self.input}.')
            return None

        print('Sucessfully registered input.')

        return None


    def _examine(self) -> None:
        _registered_locations = parse_registered_locations('_registered_locations.csv')

        record_data = pd.read_csv('record.csv')
        # TODO: detect call by this function to replace generic structlog message.
        comp_data = ingest(_registered_locations, _TIMESTAMP)

        detect_change = DetectChanges(record_data, comp_data)
        detect_change.run_pipeline(_TIMESTAMP)

        return None

    # THE SIMPLEST KIND OF DISPLAY TODO
    def _locations(self) -> None:
        display = pd.read_csv('_registered_locations.csv')
        print('No locations registered.' if display.empty else display)


    def execute(self) -> None:
        keyw = self.input[0].upper()
        if keyw == _COMMANDS[0]:
            self._help()
        elif keyw == _COMMANDS[1]:
            self._register()
        elif keyw == _COMMANDS[2]:
            self._examine()
        elif keyw == _COMMANDS[3]:
            self._locations()

        return None

# TO WRITE NEW DATA TO CONFIG, JUST USE WRITEHEADER() AND WRITEROW() ITS NOT THAT HARD TODO

if __name__ == '__main__':
    
    if not os.path.exists('record.csv'):
        print('* Record not found. Inserting all data anew.')
        _registered_locations = parse_registered_locations('_registered_locations.csv')
        data = ingest(_registered_locations, _TIMESTAMP)

        with open('record.csv', 'w', newline='', encoding='utf-8') as r:
            data.to_csv(
                r,
                sep=',',
                index=False,
                quoting=1,
                quotechar='"'
            )

        # It would actually help to determine whether or not history.csv is a
        # valid record. This can be done by evaluating the fieldnames and if
        # every id is within a catalogue of registered and standard locations.
        with open('history.csv', 'w', newline='', encoding='utf-8') as h:
            data.to_csv(
                h,
                sep=',',
                index=False,
                quoting=1,
                quotechar='"'
            )

    print('* Weather thing. Empty line or \'q\' to quit.\n')
    while True:
        inp = input('USER.> ')
        inp = str(inp)
        inp = inp.strip()

        if inp.lower() in ['', 'q', 'quit', 'exit']:
            print('* Quitting.')
            sys.exit(0)

        inp = inp.split()
        if CommandEngine._validate(inp):
            engine = CommandEngine(inp)
            engine.execute()
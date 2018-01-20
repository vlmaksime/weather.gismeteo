# coding: utf-8
# Module: tests

import os
import sys
import unittest
import shutil

cwd = os.path.dirname(os.path.abspath(__file__))
cache_dir = os.path.join(cwd, 'cache')

plugin_name = 'weather.gismeteo'

# Import our module being tested
sys.path.append(os.path.join(cwd, plugin_name))
from resources.lib.gismeteo import Gismeteo

# Begin tests
params = {'cache_dir': cache_dir}
gismeteo = Gismeteo(params)

def tearDownModule():
    shutil.rmtree(cache_dir, True)

class GismeteoTestCase(unittest.TestCase):
    """
    Test Gismeteo class
    """

    def test_cities_ip(self):
        print('\n#cities_ip')

        location = gismeteo.cities_ip()

        if location is None:
            print('Current location not detected')
            self.assertIsNone(location)
        else:
            print('Current location is %s: %s (%s)' % (location['country'], location['name'], location['district']))
            self.assertTrue(location['name'])

    def test_cities_nearby(self):
        print('\n#cities_nearby')

        count = 0

        locations = gismeteo.cities_nearby('48.02', '37.8')

        print('Search results:')
        for location in locations:
            print('%s: %s (%s)' % (location['country'], location['name'], location['district']))
            count += 1

        self.assertTrue(count > 0)

    def test_cities_search(self):
        print('\n#cities_search')

        count = 0
        locations = gismeteo.cities_search('Donetsk')

        print('Search results:')
        for location in locations:
            print('%s: %s (%s)' % (location['country'], location['name'], location['district']))
            count += 1

        self.assertTrue(count > 0)

    def test_forecast(self):
        print('\n#forecast')

        has_forecast = False
        has_days = False
        has_hourly = False

        forecast = gismeteo.forecast('5080')

        if forecast is not None:
            print('%s: %s (%s)' % (forecast['country'], forecast['name'], forecast['district']))
            has_forecast = True

            current = forecast['current']
            print('Current weather: temperature - %i°C pressure - %imm humidity - %i%%' % (current['temperature']['air'], current['pressure'], current['humidity']))
            for day in forecast['days']:
                has_days = True
                print('Dayly weather for %s: temperature - %i..%i°C pressure - %imm humidity - %i%%' % (day['date']['local'][:10], day['temperature']['min'], day['temperature']['max'], day['pressure']['avg'], day['humidity']['avg']))
                if day.get('hourly') is not None:
                    for hour in day['hourly']:
                        has_hourly = True
                        print('Hourly wether for %s: temperature - %i°C, pressure - %imm, humidity - %i%%' % (hour['date']['local'][11:], hour['temperature']['air'], hour['pressure'], hour['humidity']))
                        break
                break

        self.assertTrue(has_forecast)
        self.assertTrue(has_days)
        self.assertTrue(has_hourly)

if __name__ == '__main__':
    unittest.main()
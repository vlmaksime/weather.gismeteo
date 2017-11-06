# -*- coding: utf-8 -*-
# Module: gismeteo
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import os
import sys
import urllib2
import time
from datetime import datetime

import xml.etree.cElementTree as etree
try:
    etree.fromstring('<?xml version="1.0"?><foo><bar/></foo>')
except TypeError:
    import xml.etree.ElementTree as etree

class Gismeteo:

    def __init__( self, params = {} ):

        self.lang = params.get('lang', 'en')

        base_url = 'https://services.gismeteo.ru/inform-service/inf_chrome'

        self._actions = {'cities_search': base_url + '/cities/?startsWith=#keyword&lang=#lang',
                         'cities_ip':     base_url + '/cities/?mode=ip&count=1&nocache=1&lang=#lang',
                         'cities_nearby': base_url + '/cities/?lat=#lat&lng=#lng&count=#count&nocache=1&lang=#lang',
                         'forecast':      base_url + '/forecast/?city=#city_id&lang=#lang',
                         }

    def _http_request( self, action, url_params={} ):

        url = self._actions.get(action)

        for key, val in url_params.iteritems():
            url = url.replace(key, val)

        try:
            req = urllib2.urlopen(url)
            response = req.read()
            req.close()
        except:
            response = ''

        return response

    def _get_locations_list( self, xml ):

        try:
            root = etree.fromstring(xml)
        except:
            root = None

        if root is not None:
            for item in root.iter('item'):

                location = {'name' : item.attrib['n'],
                            'id': item.attrib['id'],
                            'country': item.attrib['country_name'],
                            'district': item.attrib.get('district_name', ''),
                            'lat': item.attrib['lat'],
                            'lng': item.attrib['lng'],
                            'kind': item.attrib['kind'],
                            }

                yield location

    def _get_date(self, source, tzone):

        if isinstance(source, str):
            full_date = source if len(source) > 10 else source + 'T00:00:00'

            completed = False
            while not completed:
                try:
                    utc_sec = time.mktime(time.strptime(full_date, '%Y-%m-%dT%H:%M:%S'))
                    completed = True
                except:
                    pass

            result = {'local': full_date,
                      'unix': utc_sec,
                      'offset': tzone}
        elif isinstance(source, float):
            utc_sec = source - tzone * 60
            result = {'local': datetime.fromtimestamp(utc_sec).strftime('%Y-%m-%dT%H:%M:%S'),
                      'unix': utc_sec,
                      'offset': tzone}
        else:
            result = None

        return result

    def _get_forecast_info(self, xml):

        try:
            root = etree.fromstring(xml)
        except:
            root = None

        if root is not None:
                xml_location = root[0]

                return {'name' : xml_location.attrib['name'],
                        'id': xml_location.attrib['id'],
                        'country': xml_location.attrib['country_name'],
                        'district': xml_location.attrib.get('district_name', ''),
                        'lat': xml_location.attrib['lat'],
                        'lng': xml_location.attrib['lng'],
                        'cur_time': self._get_date(xml_location.attrib['cur_time'], int(xml_location.attrib['tzone'])),
                        'current': self._get_fact_forecast(xml_location),
                        'days': self._get_days_forecast(xml_location),
                        }

    def _get_item_forecast(self, xml_item, tzone):
        xml_values = xml_item[0]
        result = {}

        result['date'] = self._get_date(xml_item.attrib['valid'], tzone)
        if xml_item.attrib.get('sunrise') is not None:
            result['sunrise'] = self._get_date(float(xml_item.attrib['sunrise']), tzone)
        if xml_item.attrib.get('sunset') is not None:
            result['sunset'] = self._get_date(float(xml_item.attrib['sunset']), tzone)
        result['temperature'] = {'air': int(xml_values.attrib['t']),
                                 'comfort': int(xml_values.attrib['hi']),
                                 }
        if xml_values.attrib.get('water_t') is not None:
            result['temperature']['water'] = int(xml_values.attrib['water_t']),
        result['description'] = xml_values.attrib['descr']
        result['humidity'] = int(xml_values.attrib['hum'])
        result['pressure'] = int(xml_values.attrib['p'])
        result['cloudiness'] = xml_values.attrib['cl']
        result['storm'] = (xml_values.attrib['ts'] == '1')
        result['precipitation'] = {'type': xml_values.attrib['pt'],
                                   'amount': xml_values.attrib.get('prflt'),
                                   'intensity': xml_values.attrib['pr'],
                                   }
        if xml_values.attrib.get('ph') is not None:
            result['phenomenon'] = int(xml_values.attrib['ph']),
        if xml_item.attrib.get('tod') is not None:
            result['tod'] = int(xml_item.attrib['tod'])
        result['icon'] = xml_values.attrib['icon']
        result['gm'] = xml_values.attrib['grade']
        result['wind'] = {'speed': float(xml_values.attrib['ws']),
                          'direction': xml_values.attrib['wd'],
                          }

        return result

    def _get_fact_forecast(self, xml_location):
        fact = xml_location.find('fact')
        return self._get_item_forecast(fact, int(xml_location.attrib['tzone']))

    def _get_days_forecast(self, xml_location):
        tzone = int(xml_location.attrib['tzone'])
        for xml_day in xml_location.findall('day'):

            if xml_day.attrib.get('icon') is None:
                continue

            day = {'date': self._get_date(xml_day.attrib['date'], tzone),
                   'sunrise': self._get_date(float(xml_day.attrib['sunrise']), tzone),
                   'sunset': self._get_date(float(xml_day.attrib['sunset']), tzone),
                   'temperature': {'min': int(xml_day.attrib['tmin']),
                                   'max': int(xml_day.attrib['tmax']),
                                   },
                   'description': xml_day.attrib['descr'],
                   'humidity': {'min': int(xml_day.attrib['hummin']),
                                'max': int(xml_day.attrib['hummax']),
                                'avg': int(xml_day.attrib['hum']),
                                },
                   'pressure': {'min': int(xml_day.attrib['pmin']),
                                'max': int(xml_day.attrib['pmax']),
                                'avg': int(xml_day.attrib['p']),
                                },
                   'cloudiness': xml_day.attrib['cl'],
                   'storm': (xml_day.attrib['ts'] == '1'),
                   'precipitation': {'type': xml_day.attrib['pt'],
                                     'amount': xml_day.attrib['prflt'],
                                     'intensity': xml_day.attrib['pr'],
                                     },
                   'icon': xml_day.attrib['icon'],
                   'gm': xml_day.attrib['grademax'],
                   'wind': {'speed': {'min': float(xml_day.attrib['wsmin']),
                                      'max': float(xml_day.attrib['wsmax']),
                                      'avg': float(xml_day.attrib['ws']),
                                      },
                            'direction': xml_day.attrib['wd'],
                            },
                   }
            if len(xml_day):
                day['hourly'] = self._get_hourly_forecast(xml_day, tzone)

            yield day

    def _get_hourly_forecast(self, xml_day, tzone):
        for xml_forecast in xml_day.findall('forecast'):
            yield self._get_item_forecast(xml_forecast, tzone)

    def cities_search(self, keyword):

        url_params = {'#keyword': keyword,
                      '#lang': self.lang,
                      }

        response = self._http_request('cities_search', url_params)

        return self._get_locations_list(response)

    def cities_ip(self):
        locations = []

        url_params = {'#lang': self.lang,
                      }

        response = self._http_request('cities_ip', url_params)

        return self._get_locations_list(response)

    def cities_nearby(self, lat, lng, count = 5):
        url_params = {'#lat': lat,
                      '#lng': lng,
                      '#count': count,
                      '#lang': self.lang,
                      }

        response = self._http_request('cities_ip', url_params)

        return self._get_locations_list(response)

    def forecast(self, city_id):
        url_params = {'#city_id': city_id,
                      '#lang': self.lang,
                      }

        response = self._http_request('forecast', url_params)

        return self._get_forecast_info(response)

if __name__ == '__main__':
    gismeteo = Gismeteo()
    locations = gismeteo.cities_ip()
    for location in locations:
        print('%s (%s, %s)' % (location['name'], location['district'], location['country']))
        forecast = gismeteo.forecast(location['id'])
        current = forecast['current']
        print('\tCurrent weather: temperature - %i°C, pressure - %imm, humidity - %i%%' % (current['temperature']['air'], current['pressure'], current['humidity']))
        for day in forecast['days']:
            print('\t%s: temperature - %i..%i°C, pressure - %imm, humidity - %i%%' % (day['date']['local'], day['temperature']['min'], day['temperature']['max'], day['pressure']['avg'], day['humidity']['avg']))
            if day.get('hourly') is not None:
                for hour in day['hourly']:
                    print('\t\t%s: temperature - %i°C, pressure - %imm, humidity - %i%%' % (hour['date']['local'], hour['temperature']['air'], hour['pressure'], hour['humidity']))
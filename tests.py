# coding: utf-8
# Module: tests

from __future__ import print_function, unicode_literals
from future.utils import (PY26, PY27, python_2_unicode_compatible)
from builtins import range
from io import open
import os
import sys
import random
import unittest
import imp
from collections import defaultdict
import mock
import shutil
import re

plugin_name = 'weather.gismeteo'

cwd = os.path.dirname(os.path.abspath(__file__))
config_dir = os.path.join(cwd, 'config')
cache_dir = os.path.join(config_dir, 'cache')
addon_dir = os.path.join(cwd, plugin_name)

default_script = os.path.join(addon_dir,'default.py')

tempunit_list = [u'°F', u'K', u'°C', u'°Ré', u'°Ra', u'°Rø', u'°De', u'°N']
speedunit_list = ['km/h', 'm/min', 'm/s', 'ft/h', 'ft/min', 'ft/s', 'mph', 'kts', 'Beaufort', 'inch/s', 'yard/s', 'Furlong/Fortnight']
presunit_list   = ['mmHg','hPa', 'mbar', 'inHg']
precipunit_list = ['mm', 'inch']

dateshort_list = ['%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d']
meridiem_list = ['AM/PM', '/'] 

def get_version():
    with open(os.path.join(addon_dir, 'addon.xml'), 'r', encoding='utf-8') as addon_xml:
        return re.search(r'(?<!xml )version="(.+?)"', addon_xml.read()).group(1)
 
# Fake test objects

def fake_translate_path(path):
    return path

def fake_log(msg, level='DEBUG'):
    print('%s: %s' %(level, msg))

def fake_getRegion(id_):
    if id_ == 'tempunit':
        value = tempunit_list[0]
    elif id_ == 'speedunit':
        value = speedunit_list[0]
    elif id_ == 'dateshort':
        value = dateshort_list[0]
    elif id_ == 'meridiem':
        value = meridiem_list[0]

    return value

def fake_getInfoLabel(label_id):
    if label_id == 'System.BuildVersion':
        if PY26:
            return '15.2'
        elif PY27:
            return '17.6'
        else:
            return '19.0'
    
def fake_getLanguage():
    return 'English'

def fake_getLocalizedString(id_):
    return u''

@python_2_unicode_compatible
class FakeAddon(object):
    def __init__(self, id_='test.addon'):
        if id_:
            self._id = id_
        else:
            self._id = plugin_name

        self._settings = {'CurrentLocation': 'True',
                          'Location1': 'Donetsk',
                          'Location2': 'Makiivka',
                          'Location3': '',
                          'Location4': '',
                          'Location5': '',
                          'Location1ID': '5080',
                          'Location2ID': '',
                          'Location3ID': '',
                          'Location4ID': '',
                          'Location5ID': '',
                          'Language': '0',
                          'Weekend': '0',
                          'TimeZone': '0',
                          'PresUnit': '0',
                          'PrecipUnit': '0',
                          }        

    def getAddonInfo(self, info_id):
        value = None
        if info_id == 'path':
            value = addon_dir
        elif info_id == 'profile':
            value = config_dir
        elif info_id == 'id':
            value = self._id
        elif info_id == 'version':
            value = get_version()
        elif info_id == 'name':
            value = 'Addon name'
        
        #fake_log('Addon:getAddonInfo(%s) - %s' % (info_id, value))

        return value

    def getSetting(self, setting_id):
        value = self._settings.get(setting_id, '')
        return value
        

    def setSetting(self, setting_id, value):
        self._settings[setting_id] = value

        fake_log('Addon:setSetting(%s, %s)' % (setting_id, value))

    def getLocalizedString(self, id_):
        return u''

@python_2_unicode_compatible
class FakeWindow(object):
    def __init__(self, id_=-1):
        self._id = id_
        self._contents = defaultdict(str)

    def getProperty(self, key):
        return self._contents[key]

    def setProperty(self, key, value):
        self._contents[key] = value

    def clearProperty(self, key):
        del self._contents[key]

class FakeMonitor(object):
    def __init__(self):
        pass
    
    def abortRequested(self):
        return False
    
@python_2_unicode_compatible
class FakeKeyboard(object):
    def __init__(self, default='', heading='', hidden=False):
        self._text = ''
    
    def doModal(self, autoclose=None):
        pass
    
    def isConfirmed(self):
        return True
    
    def getText(self):
        if not self._text:
            list = ['Donetsk']
            self._text = list[random.randint(0, len(list)-1)]

            fake_log('Keyboard:getText - "%s"' % self._text)
        
        return self._text

@python_2_unicode_compatible
class FakeDialog(object):
    def __init__(self):
        pass

    def select(self, heading, list , autoclose=False, preselect=None, useDetails=False):
        fake_log('Dialog:select - list')
        for item in list:
            fake_log(item)
        
        return random.randint(0, len(list)-1)
    
    def ok(self, heading, line1 , line2='', line3=''):
        fake_log('Dialog:ok(%s, %s, %s, %s)' % (heading, line1, line2, line3))
    
# Mock Kodi Python API

mock_xbmcaddon = mock.MagicMock()
mock_xbmcaddon.Addon = FakeAddon

mock_xbmc = mock.MagicMock()
mock_xbmc.LOGDEBUG = 'DEBUG'
mock_xbmc.LOGNOTICE = 'NOTICE'
mock_xbmc.LOGWARNING = 'WARNING'
mock_xbmc.LOGERROR = 'ERROR'
mock_xbmc.translatePath.side_effect = fake_translate_path
mock_xbmc.getLocalizedString.side_effect = fake_getLocalizedString
mock_xbmc.log.side_effect = fake_log
mock_xbmc.getRegion.side_effect = fake_getRegion
mock_xbmc.getLanguage.side_effect = fake_getLanguage
mock_xbmc.getInfoLabel.side_effect = fake_getInfoLabel
mock_xbmc.Monitor = FakeMonitor
mock_xbmc.Keyboard = FakeKeyboard

mock_xbmcplugin = mock.MagicMock()

mock_xbmcgui = mock.MagicMock()
mock_xbmcgui.Window = FakeWindow
mock_xbmcgui.Dialog = FakeDialog

sys.modules['xbmcaddon'] = mock_xbmcaddon
sys.modules['xbmc'] = mock_xbmc
sys.modules['xbmcplugin'] = mock_xbmcplugin
sys.modules['xbmcgui'] = mock_xbmcgui

# Import our module being tested
sys.path.append(addon_dir)

def tearDownModule():
    shutil.rmtree(config_dir, True)
    
class PluginActionsTestCase(unittest.TestCase):

    def setUp(self):
        print('\n# Testing plugin actions')

    @mock.patch('resources.lib.simpleweather.sys.argv', [plugin_name, '1'])
    def test_forecast_1_current(self):
        print('# forecast_1_current')
        imp.load_source('__main__',  default_script)

    @mock.patch('resources.lib.simpleweather.sys.argv', [plugin_name, '2'])
    def test_forecast_2(self):
        print('# forecast_2')
        imp.load_source('__main__',  default_script)

    @mock.patch('resources.lib.simpleweather.sys.argv', [plugin_name, '3'])
    def test_forecast_3(self):
        print('# forecast_3')
        imp.load_source('__main__',  default_script)

    @mock.patch('resources.lib.simpleweather.sys.argv', [plugin_name, 'action=location&id=1'])
    def test_location(self):
        print('# location')
        imp.load_source('__main__',  default_script)

    @mock.patch('resources.lib.simpleweather.sys.argv', [plugin_name, 'action=clear_cache'])
    def test_clear_cache(self):
        print('# clear_cache')
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        open(os.path.join(cache_dir, 'test.tmp'), 'a').close() 

        imp.load_source('__main__',  default_script)

class APIExtendedTestCase(unittest.TestCase):

    def setUp(self):
        print('\n# API extended tests')
        from resources.lib.gismeteo import Gismeteo

        params = {'lang': 'en',
                  'cache_dir': cache_dir}
        self.gismeteo = Gismeteo(params)

    def test_cities_nearby(self):
        print('# cities_nearby')

        locations = self.gismeteo.cities_nearby('48.02', '37.8')

        print('Search results:')
        for location in locations:
            print('%s: %s (%s)' % (location['country'], location['name'], location['district']))

class UtilitiesModuleExtendedTestCase(unittest.TestCase):

    def setUp(self):
        print('\n# Module "resources.lib.utilities" extended tests')

    def test_speed_units(self):
        import resources.lib.utilities as utilities
        print('# speed_units')
        mps = 10

        for speedunit in speedunit_list:
            utilities.SPEEDUNIT = speedunit
            value = utilities.SPEED(mps)
            fake_log(u'{0} m/s is {1} {2}'.format(mps, value, utilities.SPEEDUNIT))

    def test_speed_beaufort(self):
        import resources.lib.utilities as utilities
        print('# speed_beaufort')
        utilities.SPEEDUNIT = 'Beaufort'

        for spd in [0.5, 3, 8, 15, 25, 33, 40, 57, 70, 83, 95, 110, 125]:
            value = utilities.KPHTOBFT(spd)
            fake_log(u'{0} km/h is {1} {2}'.format(spd, value, utilities.SPEEDUNIT))

    def test_temp_units(self):
        import resources.lib.utilities as utilities
        print('# temp_units')
        deg = 10
        
        for tempunit in tempunit_list:
            utilities.TEMPUNIT = tempunit
            value = utilities.TEMP(deg)
            fake_log(u'{0} °C is {1} {2}'.format(deg, value, utilities.TEMPUNIT))

    def test_pressure_units(self):
        import resources.lib.utilities as utilities
        print('# pressure_units')
        mm = 500

        for presunit in presunit_list:
            utilities.PRESUNIT = presunit
            value = utilities.PRESSURE(mm)
            fake_log(u'{0} mmHg is {1} {2}'.format(mm, value, utilities.PRESUNIT))

    def test_precipitation_units(self):
        import resources.lib.utilities as utilities
        print('# precipitation_units')
        mm = 1.2

        for precipunit in precipunit_list:
            utilities.PRECIPUNIT = precipunit
            value = utilities.PRECIPITATION(mm)
            fake_log(u'{0} mm is {1} {2}'.format(mm, value, utilities.PRECIPUNIT))

class DefaultModuleExtendedTestCase(unittest.TestCase):

    def setUp(self):
        print('\n# Module "default" extended tests')

    def test_clear(self):
        import default
        print('# clear')

        default.clear()

    def test_get_lang(self):
        import default
        print('# get_lang')

        for lang_id in range(0, 9):
            default.weather.set_setting('Language', str(lang_id))
            val = default.get_lang()
            fake_log('Language id {0} is "{1}"'.format(lang_id, val))

    def test_get_weekends(self):
        import default
        print('# get_weekends')

        for weekend_id in range(0, 3):
            default.weather.set_setting('Weekend', str(weekend_id))
            val = default.get_weekends()
            fake_log('Weekend id {0} is "{1}"'.format(weekend_id, val))

    def test_get_wind_direction(self):
        import default
        print('# get_wind_direction')

        for direct in [0, None]:
            val = default.get_wind_direction(direct)


if __name__ == '__main__':
    unittest.main()
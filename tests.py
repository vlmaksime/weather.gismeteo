# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
import os
import sys
import unittest
import imp
import mock
import shutil
import xbmc
import xbmcaddon

cwd = os.path.dirname(os.path.abspath(__file__))

addon_name = 'weather.gismeteo'

temp_dir = os.path.join(cwd, 'addon_data')

if not os.path.exists(temp_dir):
    os.mkdir(temp_dir)

addon_dir = os.path.join(cwd, addon_name)
addon_config_dir = os.path.join(temp_dir, addon_name)
xbmcaddon.init_addon(addon_dir, addon_config_dir, True)

default_script = os.path.join(addon_dir, 'default.py')
run_script = lambda : imp.load_source('__main__', default_script)

# Import our module being tested
sys.path.append(addon_dir)


def tearDownModule():

    print('Removing temporary directory: {0}'.format(temp_dir))
    shutil.rmtree(temp_dir, True)


class PluginActionsTestCase(unittest.TestCase):

    def setUp(self):

        print("Running test: {0}".format(self.id().split('.')[-1]))

    @staticmethod
    @mock.patch('resources.libs.simpleweather.sys.argv', ['plugin://{0}/'.format(addon_name), '0', '?action=location&id=1'])
    def test_01_location():

        xbmc.Keyboard.strings.append('London')

        run_script()


    @staticmethod
    def test_02_forecast():

        with mock.patch('resources.libs.simpleweather.sys') as mock_sys:
            mock_sys.argv = ['plugin://{0}/'.format(addon_name), '1', '1']

            run_script()

        with mock.patch('resources.libs.simpleweather.sys') as mock_sys:
            mock_sys.argv = ['plugin://{0}/'.format(addon_name), '1', '2']

            run_script()

if __name__ == '__main__':
    unittest.main()

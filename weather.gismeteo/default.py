# -*- coding: utf-8 -*-
import sys
import os
import time
from datetime import datetime

import math

import xbmc
import xbmcgui
import xbmcaddon

from resources.lib.gismeteo import Gismeteo
from resources.lib.provider import Provider

ADDON           = xbmcaddon.Addon()
ADDON_NAME      = ADDON.getAddonInfo('name')

LANGUAGE        = ADDON.getLocalizedString

provider = Provider()

def _get_lang():
    lang_id = int(ADDON.getSetting('Language'))

    return provider.get_languages()[lang_id]
    
def _forecast(loc_name, loc_id):
    retry = 0
    data = gismeteo.forecast(loc_id)
    while (retry < 10) and (not MONITOR.abortRequested()):
        data = gismeteo.forecast(loc_id)
        if data is not None:
            retry = 10
        else:
            retry += 1
            xbmc.sleep(1000)
    if data is not None:
        provider.set_location_props(data)
    else:
        provider.clear()

def _select_location(location):
    labels = []
    locations = []

    keyboard = xbmc.Keyboard('', xbmc.getLocalizedString(14024), False)
    keyboard.doModal()
    if (keyboard.isConfirmed() and keyboard.getText() != ''):
        text = keyboard.getText()
        dialog = xbmcgui.Dialog()
        
        for location in gismeteo.cities_search(text):
            if location['kind'] == 'A':
                location_name = '%s - %s' %(location['name'], LANGUAGE(32301))
            else:
                location_name = location['name']
                
            if location['district']:
                labels.append('%s (%s, %s)' % (location_name, location['district'], location['country']))
            else:
                labels.append('%s (%s)' % (location_name, location['country']))
            locations.append({'id':location['id'], 'name': location['name']})

        if len(locations) > 0:
            selected = dialog.select(xbmc.getLocalizedString(396), labels)
            if selected != -1:
                selected_location = locations[selected]
                ADDON.setSetting(sys.argv[1], selected_location['name'])
                ADDON.setSetting(sys.argv[1] + 'ID', selected_location['id'])
        else:
            dialog.ok(ADDON_NAME, xbmc.getLocalizedString(284))

def _get_location(id):
    location_name = ADDON.getSetting('Location%s' % id)
    location_id = ADDON.getSetting('Location%sID' % id)

    if (location_id == '') and (id != '1'):
        location_name = ADDON.getSetting('Location1')
        location_id = ADDON.getSetting('Location1ID')

    if location_id == '':
        for location in gismeteo.cities_ip():
            location_name = location['name']
            location_id = location['id']
            ADDON.setSetting('Location1', location_name)
            ADDON.setSetting('Location1ID', location_id)

            break

    return location_name, location_id
    
class MyMonitor(xbmc.Monitor):
    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)

MONITOR = MyMonitor()

if __name__ == '__main__':

    gismeteo = Gismeteo({'lang': _get_lang()})

    if sys.argv[1].startswith('Location'):
        _select_location(sys.argv[1])
    else:
        provider.clear()
        location_name, location_id = _get_location(sys.argv[1])
        if not location_id == '':
            _forecast(location_name, location_id)
        provider.refresh_locations()

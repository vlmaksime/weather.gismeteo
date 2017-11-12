# -*- coding: utf-8 -*-
import sys
import os
import time
from datetime import datetime

import math

import xbmc
import xbmcgui
import xbmcaddon

ADDON           = xbmcaddon.Addon()
ADDON_NAME      = ADDON.getAddonInfo('name')
ADDON_ID        = ADDON.getAddonInfo('id')
CWD             = ADDON.getAddonInfo('path').decode('utf-8')

LANGUAGE        = ADDON.getLocalizedString

TEMPUNIT       = unicode(xbmc.getRegion('tempunit'),encoding='utf-8')
SPEEDUNIT      = xbmc.getRegion('speedunit')

MAX_DAYS      = 16
MAX_DAILYS    = 16
MAX_LOCATIONS = 5
MAX_HOURLY    = 34
MAX_36HOUR    = 34
MAX_WEEKENDS  = 2

def SPEED(mps):
    if SPEEDUNIT == 'km/h':
        speed = mps * 3.6
    elif SPEEDUNIT == 'm/min':
        speed = mps * 60
    elif SPEEDUNIT == 'ft/h':
        speed = mps * 11810.88
    elif SPEEDUNIT == 'ft/min':
        speed = mps * 196.84
    elif SPEEDUNIT == 'ft/s':
        speed = mps * 3.281
    elif SPEEDUNIT == 'mph':
        speed = mps * 2.237
    elif SPEEDUNIT == 'knots':
        speed = mps * 1.944
    elif SPEEDUNIT == 'Beaufort':
        speed = KPHTOBFT(mps* 3.6)
    elif SPEEDUNIT == 'inch/s':
        speed = mps * 39.37
    elif SPEEDUNIT == 'yard/s':
        speed = mps * 1.094
    elif SPEEDUNIT == 'Furlong/Fortnight':
        speed = mps * 6012.886
    else:
        speed = mps
    return str(int(round(speed)))

def TEMP(deg):
    if TEMPUNIT == u'В°F':
        temp = deg * 1.8 + 32
    elif TEMPUNIT == u'K':
        temp = deg + 273.15
    elif TEMPUNIT == u'В°RГ©':
        temp = deg * 0.8
    elif TEMPUNIT == u'В°Ra':
        temp = deg * 1.8 + 491.67
    elif TEMPUNIT == u'В°RГё':
        temp = deg * 0.525 + 7.5
    elif TEMPUNIT == u'В°D':
        temp = deg / -0.667 + 150
    elif TEMPUNIT == u'В°N':
        temp = deg * 0.33
    else:
        temp = deg
    return str(int(round(temp)))

#### thanks to FrostBox @ http://forum.kodi.tv/showthread.php?tid=114637&pid=937168#pid937168
def DEW_POINT(self, Tc=0, RH=93, ext=True, minRH=( 0, 0.075 )[ 0 ]):
    Es = 6.11 * 10.0**( 7.5 * Tc / ( 237.7 + Tc ) )
    RH = RH or minRH
    E = ( RH * Es ) / 100
    try:
        DewPoint = ( -430.22 + 237.7 * math.log( E ) ) / ( -math.log( E ) + 19.08 )
    except ValueError:
        DewPoint = 0
    if ext:
        return TEMP( DewPoint )
    else:
        return str(int(round(DewPoint)))

class Provider:

    def __init__(self):

        self._define_constants()

        self.KODI_LANGUAGE = xbmc.getLanguage().lower()
        self.KODI_VERSION  = xbmc.getInfoLabel('System.BuildVersion')[:2]

        self.WEATHER_WINDOW  = xbmcgui.Window(12600)
        if self.KODI_VERSION < '16':
            self.WEATHER_ICON = xbmc.translatePath('special://temp/weather/%s.png').decode("utf-8")
        else:
            self.WEATHER_ICON = xbmc.translatePath('%s.png').decode("utf-8")

        self.DATE_FORMAT = xbmc.getRegion('dateshort')
        self.TIME_FORMAT = xbmc.getRegion('meridiem')

        self.CURRENT_TIME = {'unix': time.time()}
        self.WEEKENDS = self._get_weekends()

        self._set_property('Forecast.IsFetched', 'true')
        self._set_property('Current.IsFetched' , 'true')
        self._set_property('Today.IsFetched'   , 'true')
        self._set_property('Daily.IsFetched'   , 'true')
        self._set_property('Weekend.IsFetched' , 'true')
        self._set_property('36Hour.IsFetched'  , 'true')
        self._set_property('Hourly.IsFetched'  , 'true')
        self._set_property('Alerts.IsFetched'  , '')
        self._set_property('Map.IsFetched'     , '')

        # WeatherProvider
        # standard properties
        self._set_property('WeatherProvider'    , ADDON_NAME)
        self._set_property('WeatherProviderLogo', xbmc.translatePath(os.path.join(CWD, 'resources', 'media', 'banner.png')))

    def _define_constants(self):
        self.WIND_DIRECTIONS = {'1': 71,
                                '2': 73,
                                '3': 75,
                                '4': 77,
                                '5': 79,
                                '6': 81,
                                '7': 83,
                                '8': 85}

        self.MONTH_NAME_LONG = { '01' : 21,
                                 '02' : 22,
                                 '03' : 23,
                                 '04' : 24,
                                 '05' : 25,
                                 '06' : 26,
                                 '07' : 27,
                                 '08' : 28,
                                 '09' : 29,
                                 '10' : 30,
                                 '11' : 31,
                                 '12' : 32 }

        self.MONTH_NAME_SHORT = { '01' : 51,
                                  '02' : 52,
                                  '03' : 53,
                                  '04' : 54,
                                  '05' : 55,
                                  '06' : 56,
                                  '07' : 57,
                                  '08' : 58,
                                  '09' : 59,
                                  '10' : 60,
                                  '11' : 61,
                                  '12' : 62 }

        self.WEEK_DAY_LONG = { '0' : 17,
                               '1' : 11,
                               '2' : 12,
                               '3' : 13,
                               '4' : 14,
                               '5' : 15,
                               '6' : 16 }

        self.WEEK_DAY_SHORT = { '0' : 47,
                                '1' : 41,
                                '2' : 42,
                                '3' : 43,
                                '4' : 44,
                                '5' : 45,
                                '6' : 46 }

                     # xbmc lang name          # gismeteo code
        self.LANG = { 'afrikaans'             : '',
                      'albanian'              : '',
                      'amharic'               : '',
                      'arabic'                : '',
                      'armenian'              : '',
                      'azerbaijani'           : '',
                      'basque'                : '',
                      'belarusian'            : 'ru',
                      'bosnian'               : '',
                      'bulgarian'             : '',
                      'burmese'               : '',
                      'catalan'               : '',
                      'chinese (simple)'      : '',
                      'chinese (traditional)' : '',
                      'croatian'              : '',
                      'czech'                 : '',
                      'danish'                : '',
                      'dutch'                 : '',
                      'english'               : 'en',
                      'english (us)'          : 'en',
                      'english (australia)'   : 'en',
                      'english (new zealand)' : 'en',
                      'esperanto'             : '',
                      'estonian'              : '',
                      'faroese'               : '',
                      'finnish'               : '',
                      'french'                : '',
                      'galician'              : '',
                      'german'                : 'de',
                      'greek'                 : '',
                      'georgian'              : '',
                      'hebrew'                : '',
                      'hindi (devanagiri)'    : '',
                      'hungarian'             : '',
                      'icelandic'             : '',
                      'indonesian'            : '',
                      'italian'               : '',
                      'japanese'              : '',
                      'korean'                : '',
                      'latvian'               : 'lt',
                      'lithuanian'            : 'li',
                      'macedonian'            : '',
                      'malay'                 : '',
                      'malayalam'             : '',
                      'maltese'               : '',
                      'maori'                 : '',
                      'mongolian (mongolia)'  : '',
                      'norwegian'             : '',
                      'ossetic'               : '',
                      'persian'               : '',
                      'persian (iran)'        : '',
                      'polish'                : 'pl',
                      'portuguese'            : '',
                      'portuguese (brazil)'   : '',
                      'romanian'              : 'ro',
                      'russian'               : 'ru',
                      'serbian'               : '',
                      'serbian (cyrillic)'    : '',
                      'sinhala'               : '',
                      'slovak'                : '',
                      'slovenian'             : '',
                      'spanish'               : '',
                      'spanish (argentina)'   : '',
                      'spanish (mexico)'      : '',
                      'swedish'               : '',
                      'tajik'                 : '',
                      'tamil (india)'         : '',
                      'telugu'                : '',
                      'thai'                  : '',
                      'turkish'               : '',
                      'ukrainian'             : 'ua',
                      'uzbek'                 : '',
                      'vietnamese'            : '',
                      'welsh'                 : '' }

        self.WEATHER_CODES = {'c4':          '26',
                              'c4.st':       '26',
                              'c4.r1':       '11',
                              'c4.r1.st':    '4',
                              'c4.r2':       '11',
                              'c4.r2.st':    '4',
                              'c4.r3':       '12',
                              'c4.r3.st':    '4',
                              'c4.s1':       '16',
                              'c4.s1.st':    '16',
                              'c4.s2':       '16',
                              'c4.s2.st':    '16',
                              'c4.s3':       '16',
                              'c4.s3.st':    '16',
                              'c4.rs1':      '5',
                              'c4.rs1.st':   '5',
                              'c4.rs2':      '5',
                              'c4.rs2.st':   '5',
                              'c4.rs3':      '5',
                              'c4.rs3.st':   '5',
                              'd':           '32',
                              'd.st':        '32',
                              'd.c2':        '30',
                              'd.c2.r1':     '39',
                              'd.c2.r1.st':  '37',
                              'd.c2.r2':     '39',
                              'd.c2.r2.st':  '37',
                              'd.c2.r3':     '39',
                              'd.c2.r3.st':  '37',
                              'd.c2.rs1':    '42',
                              'd.c2.rs1.st': '42',
                              'd.c2.rs2':    '42',
                              'd.c2.rs2.st': '42',
                              'd.c2.rs3':    '42',
                              'd.c2.rs3.st': '42',
                              'd.c2.s1':     '41',
                              'd.c2.s1.st':  '41',
                              'd.c2.s2':     '41',
                              'd.c2.s2.st':  '41',
                              'd.c2.s3':     '41',
                              'd.c2.s3.st':  '41',
                              'd.c3':        '28',
                              'd.c3.r1':     '11',
                              'd.c3.r1.st':  '38',
                              'd.c3.r2':     '11',
                              'd.c3.r2.st':  '38',
                              'd.c3.r3':     '11',
                              'd.c3.r3.st':  '38',
                              'd.c3.s1':     '14',
                              'd.c3.s1.st':  '14',
                              'd.c3.s2':     '14',
                              'd.c3.s2.st':  '14',
                              'd.c3.s3':     '14',
                              'd.c3.s3.st':  '14',
                              'd.c3.rs1':    '42',
                              'd.c3.rs1.st': '42',
                              'd.c3.rs2':    '42',
                              'd.c3.rs2.st': '42',
                              'd.c3.rs3':    '42',
                              'd.c3.rs3.st': '42',
                              'n':           '31',
                              'n.st':        '31',
                              'n.c2':        '29',
                              'n.c2.r1':     '45',
                              'n.c2.r1.st':  '47',
                              'n.c2.r2':     '45',
                              'n.c2.r2.st':  '47',
                              'n.c2.r3':     '45',
                              'n.c2.r3.st':  '47',
                              'n.c2.rs1':    '42',
                              'n.c2.rs1.st': '42',
                              'n.c2.rs2':    '42',
                              'n.c2.rs2.st': '42',
                              'n.c2.rs3':    '42',
                              'n.c2.rs3.st': '42',
                              'n.c2.s1':     '46',
                              'n.c2.s1.st':  '46',
                              'n.c2.s2':     '46',
                              'n.c2.s2.st':  '46',
                              'n.c2.s3':     '46',
                              'n.c2.s3.st':  '46',
                              'n.c3':        '27',
                              'n.c3.r1':     '11',
                              'n.c3.r1.st':  '4',
                              'n.c3.r2':     '11',
                              'n.c3.r2.st':  '4',
                              'n.c3.r3':     '11',
                              'n.c3.r3.st':  '4',
                              'n.c3.rs1':    '42',
                              'n.c3.rs1.st': '42',
                              'n.c3.rs2':    '42',
                              'n.c3.rs2.st': '42',
                              'n.c3.rs3':    '42',
                              'n.c3.rs3.st': '42',
                              'n.c3.s1':     '14',
                              'n.c3.s1.st':  '14',
                              'n.c3.s2':     '14',
                              'n.c3.s2.st':  '14',
                              'n.c3.s3':     '14',
                              'n.c3.s3.st':  '14',
                              'mist':        '32',
                              'r1.mist':     '11',
                              'r1.st.mist':  '38',
                              'r2.mist':     '11',
                              'r2.st.mist':  '38',
                              'r3.mist':     '11',
                              'r3.st.mist':  '38',
                              's1.mist':     '14',
                              's1.st.mist':  '14',
                              's2.mist':     '14',
                              's2.st.mist':  '14',
                              's3.mist':     '14',
                              's3.st.mist':  '14',
                              'rs1.mist':    '42',
                              'rs1.st.mist': '42',
                              'rs2.mist':    '42',
                              'rs2.st.mist': '42',
                              'rs3.mist':    '42',
                              'rs3.st.mist': '42',
                              'nodata':      'na'}

    def _set_property(self, name, value):
        self.WEATHER_WINDOW.setProperty(name, value)

    def _is_weekend(self, day):
        return (self._get_weekday(day['date'], 'x') in self.WEEKENDS)

    def _get_time(self, date):
        if isinstance(date, float):
            date_time = time.localtime(date)
        else:
            date_time = time.localtime(date['unix'])

        if self.TIME_FORMAT != '/':
            local_time = time.strftime('%I:%M%p', date_time)
        else:
            local_time = time.strftime('%H:%M', date_time)
        return local_time

    def _convert_date(self, date):
        if isinstance(date, float):
            date_time = time.localtime(date)
        else:
            date_time = time.localtime(date['unix'])

        if self.DATE_FORMAT[1] == 'd' or self.DATE_FORMAT[0] == 'D':
            localdate = time.strftime('%d-%m-%Y', date_time)
        elif self.DATE_FORMAT[1] == 'm' or self.DATE_FORMAT[0] == 'M':
            localdate = time.strftime('%m-%d-%Y', date_time)
        else:
            localdate = time.strftime('%Y-%m-%d', date_time)
        if self.TIME_FORMAT != '/':
            localtime = time.strftime('%I:%M%p', date_time)
        else:
            localtime = time.strftime('%H:%M', date_time)
        return localtime + '  ' + localdate

    def _get_weekends(self):
        weekend = ADDON.getSetting('Weekend')

        if weekend == '2':
            weekends = [4,5]
        elif weekend == '1':
            weekends = [5,6]
        else:
            weekends = [6,0]

        return weekends

    def get_languages(self):

        languages = []
        if self.LANG[self.KODI_LANGUAGE] is not '': languages.append(self.LANG[self.KODI_LANGUAGE]) #0
        else: languages.append('en')

        languages.append('ru') #1
        languages.append('ua') #2
        languages.append('lt') #3
        languages.append('lv') #4
        languages.append('en') #5
        languages.append('ro') #6
        languages.append('de') #7
        languages.append('pl') #8

        return languages

    def _get_weekday(self, date, form):
        date_time = time.localtime(date['unix'])

        weekday = time.strftime('%w', date_time)
        if form == 's':
            return xbmc.getLocalizedString(self.WEEK_DAY_SHORT[weekday])
        elif form == 'l':
            return xbmc.getLocalizedString(self.WEEK_DAY_LONG[weekday])
        else:
            return int(weekday)

    def _get_month(self, date, form):
        date_time = time.localtime(date['unix'])

        month = time.strftime('%m', date_time)
        day = time.strftime('%d', date_time)
        if form == 'ds':
            label = day + ' ' + xbmc.getLocalizedString(self.MONTH_NAME_SHORT[month])
        elif form == 'dl':
            label = day + ' ' + xbmc.getLocalizedString(self.MONTH_NAME_LONG[month])
        elif form == 'ms':
            label = xbmc.getLocalizedString(self.MONTH_NAME_SHORT[month]) + ' ' + day
        elif form == 'ml':
            label = xbmc.getLocalizedString(self.MONTH_NAME_LONG[month]) + ' ' + day
        return label

    def _get_wind_direction(self, value):
        if self.WIND_DIRECTIONS.get(value) is not None:
            return xbmc.getLocalizedString(self.WIND_DIRECTIONS.get(value))
        else:
            return 'N/A'

    def _get_weather_icon(self, item, tod='d'):
        storm = item.get('storm', False)

        ph = item.get('ph')
        mist = (ph == 5 or (ph >= 10 and ph <= 12) \
                or ph == 28 or (ph >= 40 and ph <= 49) \
                or (ph >= 104 and ph <= 105) or ph == 110 \
                or ph == 120 or (ph >= 130 and ph <= 135))

        cl = item['cloudiness']
        pt = item['precipitation']['type']
        pr = item['precipitation']['intensity']

        icon_params = []

        if not (cl == '3' or mist):
            icon_params.append(tod)

        if cl != '0' and not mist:
            icon_params.append('c%d' % (int(cl) + 1 if cl != '101' else 2))

        if pr != '0' and pt != '0':
            icon_params.append('%s%s' % ('r' if pt == '1' else 's' if pt == '2' else 'rs', pr))

        if storm:
            icon_params.append('st')

        if mist:
            icon_params.append('mist')

        icon = '.'.join(icon_params)

        if icon == '':
            icon = 'nodata'

        return icon

    def _get_weather_code(self, item):

        #icon = self._get_weather_icon(item, tod)
        weather_code = self.WEATHER_CODES.get(item['icon'], 'na')

        return weather_code

    def clear(self):

        # Current
        # standart properties
        self._set_property('Current.Location'      , '')
        self._set_property('Current.Condition'     , '')
        self._set_property('Current.Temperature'   , '')
        self._set_property('Current.Wind'          , '')
        self._set_property('Current.WindDirection' , '')
        self._set_property('Current.Humidity'      , '')
        self._set_property('Current.FeelsLike'     , '')
        self._set_property('Current.UVIndex'       , '')
        self._set_property('Current.DewPoint'      , '')
        self._set_property('Current.OutlookIcon'   , '')
        self._set_property('Current.FanartCode'    , '')

        # extenden properties
        self._set_property('Current.LowTemperature'       , '')
        self._set_property('Current.HighTemperature'      , '')
        self._set_property('Current.Pressure'             , '')
        self._set_property('Current.SeaLevel'             , '')
        self._set_property('Current.GroundLevel'          , '')
        self._set_property('Current.WindGust'             , '')
        self._set_property('Current.Current.WindDirStart' , '')
        self._set_property('Current.WindDirEnd'           , '')
        self._set_property('Current.Rain'                 , '')
        self._set_property('Current.Snow'                 , '')
        self._set_property('Current.Precipitation'        , '')
        self._set_property('Current.Cloudiness'           , '')
        self._set_property('Current.ShortOutlook'         , '')

        # Today
        # extenden properties
        self._set_property('Today.Sunset'  , '')
        self._set_property('Today.Sunrise' , '')

        # Forecast
        # extenden properties
        self._set_property('Forecast.City'      , '')
        self._set_property('Forecast.Country'   , '')
        self._set_property('Forecast.Latitude'  , '')
        self._set_property('Forecast.Longitude' , '')
        self._set_property('Forecast.Updated'   , '')

        # Day
        # standart properties
        for count in range (0, MAX_DAYS + 1):
            self._set_property('Day%i.Title'       % count, '')
            self._set_property('Day%i.HighTemp'    % count, '')
            self._set_property('Day%i.LowTemp'     % count, '')
            self._set_property('Day%i.Outlook'     % count, '')
            self._set_property('Day%i.OutlookIcon' % count, '')
            self._set_property('Day%i.FanartCode'  % count, '')

        # Daily
        # extenden properties
        for count in range (1, MAX_DAILYS + 1):
            self._set_property('Daily.%i.LongDay'        % count, '')
            self._set_property('Daily.%i.ShortDay'       % count, '')
            self._set_property('Daily.%i.LongDate'       % count, '')
            self._set_property('Daily.%i.ShortDate'      % count, '')
            self._set_property('Daily%i.Outlook'         % count, '')
            self._set_property('Daily%i.ShortOutlook'    % count, '')
            self._set_property('Daily%i.OutlookIcon'     % count, '')
            self._set_property('Daily%i.FanartCode'      % count, '')
            self._set_property('Daily.%i.WindSpeed'      % count, '')
            self._set_property('Daily.%i.WindDirection'  % count, '')
            self._set_property('Daily%i.WindDegree'      % count, '')
            self._set_property('Daily%i.Humidity'        % count, '')
            self._set_property('Daily%i.TempMorn'        % count, '')
            self._set_property('Daily%i.TempDay'         % count, '')
            self._set_property('Daily%i.TempEve'         % count, '')
            self._set_property('Daily%i.TempNight'       % count, '')
            self._set_property('Daily%i.DewPoint'        % count, '')
            self._set_property('Daily%i.FeelsLike'       % count, '')
            self._set_property('Daily%i.WindGust'        % count, '')
            self._set_property('Daily%i.HighTemperature' % count, '')
            self._set_property('Daily%i.LowTemperature'  % count, '')
            self._set_property('Daily%i.Pressure'        % count, '')
            self._set_property('Daily%i.Cloudiness'      % count, '')
            self._set_property('Daily%i.Rain'            % count, '')
            self._set_property('Daily%i.Snow'            % count, '')
            self._set_property('Daily%i.Precipitation'   % count, '')

        # Hourly
        # extenden properties
        for count in range (1, MAX_HOURLY + 1):
            self._set_property('Hourly.%i.Time'             % count, '')
            self._set_property('Hourly.%i.LongDate'         % count, '')
            self._set_property('Hourly.%i.ShortDate'        % count, '')
            self._set_property('Hourly.%i.Outlook'          % count, '')
            self._set_property('Hourly.%i.ShortOutlook'     % count, '')
            self._set_property('Hourly.%i.OutlookIcon'      % count, '')
            self._set_property('Hourly.%i.FanartCode'       % count, '')
            self._set_property('Hourly.%i.WindSpeed'        % count, '')
            self._set_property('Hourly.%i.WindDirection'    % count, '')
            self._set_property('Hourly.%i.WindDegree'       % count, '')
            self._set_property('Hourly.%i.WindGust'         % count, '')
            self._set_property('Hourly.%i.Humidity'         % count, '')
            self._set_property('Hourly.%i.Temperature'      % count, '')
            self._set_property('Hourly.%i.HighTemperature'  % count, '')
            self._set_property('Hourly.%i.LowTemperature'   % count, '')
            self._set_property('Hourly.%i.DewPoint'         % count, '')
            self._set_property('Hourly.%i.FeelsLike'        % count, '')
            self._set_property('Hourly.%i.Pressure'         % count, '')
            self._set_property('Hourly.%i.SeaLevel '        % count, '')
            self._set_property('Hourly.%i.GroundLevel'      % count, '')
            self._set_property('Hourly.%i.Cloudiness'       % count, '')
            self._set_property('Hourly.%i.Rain'             % count, '')
            self._set_property('Hourly.%i.Snow'             % count, '')
            self._set_property('Hourly.%i.Precipitation'    % count, '')

    def refresh_locations(self):
        locations = 0
        for count in range(1, MAX_LOCATIONS + 1):
            loc_name = ADDON.getSetting('Location%s' % count)
            loc_id = ADDON.getSetting('Location%sID' % count)
            if loc_name != '':
                locations += 1
            elif loc_id != '':
                ADDON.setSetting('Location%sID' % count, '')
            self._set_property('Location%s' % count, loc_name)
        self._set_property('Locations', str(locations))

    def set_location_props(self, forecast_info):
        count_days = 0
        count_hourly = 0
        count_36hour = 0
        count_weekends = 0

        self._set_current_prop(forecast_info)
        self._set_forecast_prop(forecast_info)
        self._set_today_prop(forecast_info)

        for day in forecast_info['days']:

            if day.get('hourly') is not None:
                ext_temp = {}

                for hour in day['hourly']:

                    if hour['tod'] == 0:
                        ext_temp['night'] = hour['temperature']['air']
                    elif hour['tod'] == 1:
                        ext_temp['morn'] = hour['temperature']['air']
                    elif hour['tod'] == 2:
                        ext_temp['day'] = hour['temperature']['air']
                    elif hour['tod'] == 3:
                        ext_temp['eve'] = hour['temperature']['air']

                    if count_hourly < MAX_HOURLY \
                      and hour['date']['unix'] >= self.CURRENT_TIME['unix']:
                        self._set_hourly_prop(hour, count_hourly+1 )
                        count_hourly += 1

                    if count_36hour < MAX_36HOUR \
                      and hour['tod'] in [2, 3]:
                        if hour['tod'] == 2 \
                          and hour['date']['unix'] >= self.CURRENT_TIME['unix'] \
                          or hour['tod'] == 3:
                            self._set_36hour_prop(hour, count_days, hour['tod'], count_36hour+1 )
                            count_36hour += 1

                day['ext_temp'] = ext_temp

            if count_days <= MAX_DAYS:
                self._set_day_prop(day, count_days)
            if count_days <= MAX_DAILYS:
                self._set_daily_prop(day, count_days+1)
            if self._is_weekend(day) \
              and count_weekends <= MAX_WEEKENDS:
                self._set_weekend_prop(day, count_weekends+1)
                count_weekends += 1

            count_days += 1

    def _set_current_prop(self, forecast_info):
        current = forecast_info['current']
        weather_code = self._get_weather_code(current)

        # Current
        # standard properties
        self._set_property('Current.Location'     , forecast_info['name'])
        self._set_property('Current.Condition'    , current['description'])
        self._set_property('Current.Temperature'  , str(current['temperature']['air']))
        self._set_property('Current.Wind'         , str(int(round(current['wind']['speed'] * 3.6))))
        self._set_property('Current.WindDirection', self._get_wind_direction(current['wind']['direction']))
        self._set_property('Current.Humidity'     , str(current['humidity']))
        self._set_property('Current.FeelsLike'    , str(current['temperature']['comfort']))
        self._set_property('Current.DewPoint'     , DEW_POINT(current['temperature']['air'], current['humidity'], False))
        self._set_property('Current.OutlookIcon'  , '%s.png' % weather_code) # xbmc translates it to Current.ConditionIcon
        self._set_property('Current.FanartCode'   , weather_code)

        # extenden properties
        self._set_property('Current.Pressure'     , '%i mm Hg' % (current['pressure']))
        if current['precipitation']['amount'] is None:
            self._set_property('Current.Precipitation', '%s mm' % ('n/a'))
        else:
            self._set_property('Current.Precipitation', '%s mm' % (current['precipitation']['amount']))

    def _set_forecast_prop(self, forecast_info):
        # Forecast
        # extended properties

        self._set_property('Forecast.City'     , forecast_info['name'])
        self._set_property('Forecast.Country'  , forecast_info['country'])
        self._set_property('Forecast.State'    , forecast_info['district'])
        self._set_property('Forecast.Latitude' , forecast_info['lat'])
        self._set_property('Forecast.Longitude', forecast_info['lng'])
        self._set_property('Forecast.Updated'  , self._convert_date(forecast_info['cur_time']))

    def _set_today_prop(self, forecast_info):
        current = forecast_info['current']

        # Today
        # extended properties

        if current['sunrise']['unix'] == current['sunset']['unix']:
            self._set_property('Today.Sunrise', '')
            self._set_property('Today.Sunset' , '')
        else:
            self._set_property('Today.Sunrise', self._get_time(current['sunrise']))
            self._set_property('Today.Sunset' , self._get_time(current['sunset']))

    def _set_day_prop(self, day, count):

        weather_code = self._get_weather_code(day)

        #Day [0-6]
        # standard properties

        self._set_property('Day%i.Title'       % count, self._get_weekday(day['date'], 'l'))
        self._set_property('Day%i.HighTemp'    % count, str(day['temperature']['max']))
        self._set_property('Day%i.LowTemp'     % count, str(day['temperature']['min']))
        self._set_property('Day%i.Outlook'     % count, day['description'])
        self._set_property('Day%i.OutlookIcon' % count, '%s.png' % weather_code)
        self._set_property('Day%i.FanartCode'  % count, weather_code)

    def _set_daily_prop(self, day, count):
        weather_code = self._get_weather_code(day)

        # Daily [1-16]
        # extended properties

        self._set_property('Daily.%i.LongDay'         % count, self._get_weekday(day['date'], 'l'))
        self._set_property('Daily.%i.ShortDay'        % count, self._get_weekday(day['date'], 's'))
        if self.DATE_FORMAT[1] == 'd' or self.DATE_FORMAT[0] == 'D':
            self._set_property('Daily.%i.LongDate'    % count, self._get_month(day['date'], 'dl'))
            self._set_property('Daily.%i.ShortDate'   % count, self._get_month(day['date'], 'ds'))
        else:
            self._set_property('Daily.%i.LongDate'    % count, self._get_month(day['date'], 'ml'))
            self._set_property('Daily.%i.ShortDate'   % count, self._get_month(day['date'], 'ms'))
        self._set_property('Daily.%i.Outlook'         % count, day['description'])
        self._set_property('Daily.%i.OutlookIcon'     % count, self.WEATHER_ICON % weather_code)
        self._set_property('Daily.%i.FanartCode'      % count, weather_code)
        self._set_property('Daily.%i.WindSpeed'       % count, SPEED(day['wind']['speed']['avg']) + SPEEDUNIT)
        self._set_property('Daily.%i.WindDirection'   % count, self._get_wind_direction(day['wind']['direction']))
        self._set_property('Daily.%i.Humidity'        % count, '%i%%' % (day['humidity']['avg']))
        if day.get('ext_temp') is not None:
            self._set_property('Daily.%i.TempMorn'    % count, TEMP(day['ext_temp']['morn']) + TEMPUNIT)
            self._set_property('Daily.%i.TempDay'     % count, TEMP(day['ext_temp']['day']) + TEMPUNIT)
            self._set_property('Daily.%i.TempEve'     % count, TEMP(day['ext_temp']['eve']) + TEMPUNIT)
            self._set_property('Daily.%i.TempNight'   % count, TEMP(day['ext_temp']['night']) + TEMPUNIT)
        self._set_property('Daily.%i.DewPoint'        % count, DEW_POINT(day['temperature']['max'], day['humidity']['avg']) + TEMPUNIT)
        self._set_property('Daily.%i.HighTemperature' % count, TEMP(day['temperature']['max']) + TEMPUNIT)
        self._set_property('Daily.%i.LowTemperature'  % count, TEMP(day['temperature']['min']) + TEMPUNIT)
        if day['humidity']['avg']:
            self._set_property('Daily.%i.Pressure'    % count, '%i mm Hg' % (day['pressure']['avg']))
        else:
            self._set_property('Daily.%i.Pressure'    % count, '%i mm Hg' % (day['pressure']['max']))
        if day['precipitation']['amount'] is None:
            self._set_property('Daily.%i.Precipitation'   % count,  '%s mm' % ('n/a'))
        else:
            self._set_property('Daily.%i.Precipitation'   % count,  '%s mm' % (day['precipitation']['amount']))

    def _set_hourly_prop(self, hour, count):
        weather_code = self._get_weather_code(hour)

        #Hourly [1-34]
        self._set_property('Hourly.%i.Time'            % count, self._get_time(hour['date']))
        if self.DATE_FORMAT[1] == 'd' or self.DATE_FORMAT[0] == 'D':
            self._set_property('Hourly.%i.LongDate'    % count, self._get_month(hour['date'], 'dl'))
            self._set_property('Hourly.%i.ShortDate'   % count, self._get_month(hour['date'], 'ds'))
        else:
            self._set_property('Hourly.%i.LongDate'    % count, self._get_month(hour['date'], 'ml'))
            self._set_property('Hourly.%i.ShortDate'   % count, self._get_month(hour['date'], 'ms'))
        self._set_property('Hourly.%i.Outlook'         % count, hour['description'])
        self._set_property('Hourly.%i.OutlookIcon'     % count, self.WEATHER_ICON % weather_code)
        self._set_property('Hourly.%i.FanartCode'      % count, weather_code)
        self._set_property('Hourly.%i.WindSpeed'       % count, SPEED(hour['wind']['speed']) + SPEEDUNIT)
        self._set_property('Hourly.%i.WindDirection'   % count, self._get_wind_direction(hour['wind']['direction']))
        self._set_property('Hourly.%i.Humidity'        % count, '%i%%' % (hour['humidity']))
        self._set_property('Hourly.%i.Temperature'     % count, TEMP(hour['temperature']['air']) + TEMPUNIT)
        self._set_property('Hourly.%i.DewPoint'        % count, DEW_POINT(hour['temperature']['air'], hour['humidity']) + TEMPUNIT)
        self._set_property('Hourly.%i.FeelsLike'       % count, TEMP(hour['temperature']['comfort']) + TEMPUNIT)
        self._set_property('Hourly.%i.Pressure'        % count, '%i mm Hg' % (hour['pressure']))
        if hour['precipitation']['amount'] is None:
            self._set_property('Hourly.%i.Precipitation'   % count,  '%s mm' % ('n/a'))
        else:
            self._set_property('Hourly.%i.Precipitation'   % count,  '%s mm' % (hour['precipitation']['amount']))

    def _set_36hour_prop(self, hour, day_num, tod, count):
        weather_code = self._get_weather_code(hour)

        #36Hour [1-3]
        # extended properties
        self._set_property('36Hour.%i.LongDay'         % count, self._get_weekday(hour['date'], 'l'))
        self._set_property('36Hour.%i.ShortDay'        % count, self._get_weekday(hour['date'], 's'))
        if self.DATE_FORMAT[1] == 'd' or self.DATE_FORMAT[0] == 'D':
            self._set_property('36Hour.%i.LongDate'    % count, self._get_month(hour['date'], 'dl'))
            self._set_property('36Hour.%i.ShortDate'   % count, self._get_month(hour['date'], 'ds'))
        else:
            self._set_property('36Hour.%i.LongDate'    % count, self._get_month(hour['date'], 'ml'))
            self._set_property('36Hour.%i.ShortDate'   % count, self._get_month(hour['date'], 'ms'))
        self._set_property('36Hour.%i.Outlook'         % count, hour['description'])
        self._set_property('36Hour.%i.OutlookIcon'     % count, self.WEATHER_ICON % weather_code)
        self._set_property('36Hour.%i.FanartCode'      % count, weather_code)
        self._set_property('36Hour.%i.WindSpeed'       % count, SPEED(hour['wind']['speed']) + SPEEDUNIT)
        self._set_property('36Hour.%i.WindDirection'   % count, self._get_wind_direction(hour['wind']['direction']))
        self._set_property('36Hour.%i.Humidity'        % count, '%i%%' % (hour['humidity']))
        self._set_property('36Hour.%i.Temperature'     % count, TEMP(hour['temperature']['air']) + TEMPUNIT)
        self._set_property('36Hour.%i.DewPoint'        % count, DEW_POINT(hour['temperature']['air'], hour['humidity']) + TEMPUNIT)
        self._set_property('36Hour.%i.FeelsLike'       % count, TEMP(hour['temperature']['comfort']) + TEMPUNIT)
        self._set_property('36Hour.%i.Pressure'        % count, '%i mm Hg' % (hour['pressure']))
        if hour['precipitation']['amount'] is None:
            self._set_property('36Hour.%i.Precipitation'   % count,  '%s mm' % ('n/a'))
        else:
            self._set_property('36Hour.%i.Precipitation'   % count,  '%s mm' % (hour['precipitation']['amount']))

        if tod == 2:
            self._set_property('36Hour.%i.Heading'         % count, xbmc.getLocalizedString(33006+day_num))
            self._set_property('36Hour.%i.TemperatureHeading'  % count, xbmc.getLocalizedString(393))
        else:
            self._set_property('36Hour.%i.Heading'         % count, xbmc.getLocalizedString(33018+day_num))
            self._set_property('36Hour.%i.TemperatureHeading'  % count, xbmc.getLocalizedString(391))

    def _set_weekend_prop(self, day, count):
        weather_code = self._get_weather_code(day)

        # weekenda [1-2]
        # extended properties

        self._set_property('Weekend.%i.LongDay'         % count, self._get_weekday(day['date'], 'l'))
        self._set_property('Weekend.%i.ShortDay'        % count, self._get_weekday(day['date'], 's'))
        if self.DATE_FORMAT[1] == 'd' or self.DATE_FORMAT[0] == 'D':
            self._set_property('Weekend.%i.LongDate'    % count, self._get_month(day['date'], 'dl'))
            self._set_property('Weekend.%i.ShortDate'   % count, self._get_month(day['date'], 'ds'))
        else:
            self._set_property('Weekend.%i.LongDate'    % count, self._get_month(day['date'], 'ml'))
            self._set_property('Weekend.%i.ShortDate'   % count, self._get_month(day['date'], 'ms'))

        self._set_property('Weekend.%i.Outlook'         % count, day['description'])
        self._set_property('Weekend.%i.OutlookIcon'     % count, self.WEATHER_ICON % weather_code)
        self._set_property('Weekend.%i.FanartCode'      % count, weather_code)
        self._set_property('Weekend.%i.WindSpeed'       % count, SPEED(day['wind']['speed']['avg']) + SPEEDUNIT)
        self._set_property('Weekend.%i.WindDirection'   % count, self._get_wind_direction(day['wind']['direction']))
        self._set_property('Weekend.%i.Humidity'        % count, '%i%%' % (day['humidity']['avg']))
        if day.get('ext_temp') is not None:
            self._set_property('Weekend.%i.TempMorn'    % count, TEMP(day['ext_temp']['morn']) + TEMPUNIT)
            self._set_property('Weekend.%i.TempDay'     % count, TEMP(day['ext_temp']['day']) + TEMPUNIT)
            self._set_property('Weekend.%i.TempEve'     % count, TEMP(day['ext_temp']['eve']) + TEMPUNIT)
            self._set_property('Weekend.%i.TempNight'   % count, TEMP(day['ext_temp']['night']) + TEMPUNIT)
        self._set_property('Weekend.%i.DewPoint'        % count, DEW_POINT(day['temperature']['max'], day['humidity']['avg']) + TEMPUNIT)
        self._set_property('Weekend.%i.HighTemperature' % count, TEMP(day['temperature']['max']) + TEMPUNIT)
        self._set_property('Weekend.%i.LowTemperature'  % count, TEMP(day['temperature']['min']) + TEMPUNIT)
        if day['humidity']['avg']:
            self._set_property('Weekend.%i.Pressure'    % count, '%i mm Hg' % (day['pressure']['avg']))
        else:
            self._set_property('Weekend.%i.Pressure'    % count, '%i mm Hg' % (day['pressure']['max']))
        if day['precipitation']['amount'] is None:
            self._set_property('Weekend.%i.Precipitation'   % count,  '%s mm' % ('n/a'))
        else:
            self._set_property('Weekend.%i.Precipitation'   % count,  '%s mm' % (day['precipitation']['amount']))
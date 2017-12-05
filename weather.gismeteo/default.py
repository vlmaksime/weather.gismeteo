# -*- coding: utf-8 -*-
import sys
import os
import time

import xbmc
import xbmcgui

from resources.lib.gismeteo import Gismeteo
from resources.lib.utilities import *

_ = weather.initialize_gettext()

MAX_DAYS      = 7
MAX_DAILYS    = 7
MAX_LOCATIONS = 5
MAX_HOURLY    = 16
MAX_36HOUR    = 3
MAX_WEEKENDS  = 2

DATEFORMAT     = weather.date_format
TIMEFORMAT     = weather.time_format

WEATHER_ICON   = weather.weather_icon

KODILANGUAGE   = xbmc.getLanguage().lower()

CURRENT_TIME = {'unix': time.time()}

class MyMonitor(xbmc.Monitor):
    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)

def get_lang():
    lang_id = weather.Language
    if lang_id == 0: #System interface
        lang = LANG[KODILANGUAGE] if LANG[KODILANGUAGE] is not '' else 'en'
    elif lang_id == 1:
        lang = 'ru'
    elif lang_id == 2:
        lang = 'ua'
    elif lang_id == 3:
        lang = 'lt'
    elif lang_id == 4:
        lang = 'lv'
    elif lang_id == 5:
        lang = 'en'
    elif lang_id == 6:
        lang = 'ro'
    elif lang_id == 7:
        lang = 'de'
    elif lang_id == 8:
        lang = 'pl'

    return lang

def is_weekend(day):
    return (get_weekday(day['date'], 'x') in WEEKENDS)

def get_timestamp(date):
    if weather.TimeZone == 0:
        stamp = time.localtime(date['unix'])
    else:
        stamp = time.gmtime(date['unix'] + date['offset'] * 60)

    return stamp

def get_location_name(location):
    if location['kind'] == 'A':
        location_name = u'%s %s' %(_('a/p').decode('utf-8'), location['name'])
    else:
        location_name = location['name']
    return location_name

def get_time(date):
    date_time = get_timestamp(date)

    if TIMEFORMAT != '/':
        local_time = time.strftime('%I:%M%p', date_time)
    else:
        local_time = time.strftime('%H:%M', date_time)
    return local_time

def convert_date(date):
    date_time = get_timestamp(date)

    if DATEFORMAT[1] == 'd' or DATEFORMAT[0] == 'D':
        localdate = time.strftime('%d-%m-%Y', date_time)
    elif DATEFORMAT[1] == 'm' or DATEFORMAT[0] == 'M':
        localdate = time.strftime('%m-%d-%Y', date_time)
    else:
        localdate = time.strftime('%Y-%m-%d', date_time)
    if TIMEFORMAT != '/':
        localtime = time.strftime('%I:%M%p', date_time)
    else:
        localtime = time.strftime('%H:%M', date_time)
    return localtime + '  ' + localdate

def get_weekends():
    weekend = weather.Weekend

    if weekend == '2':
        weekends = [4,5]
    elif weekend == '1':
        weekends = [5,6]
    else:
        weekends = [6,0]

    return weekends

def get_weekday(date, form):
    date_time = get_timestamp(date)

    weekday = time.strftime('%w', date_time)
    if form == 's':
        return xbmc.getLocalizedString(WEEK_DAY_SHORT[weekday])
    elif form == 'l':
        return xbmc.getLocalizedString(WEEK_DAY_LONG[weekday])
    else:
        return int(weekday)

def get_month(date, form):
    date_time = get_timestamp(date)

    month = time.strftime('%m', date_time)
    day = time.strftime('%d', date_time)
    if form == 'ds':
        label = day + ' ' + xbmc.getLocalizedString(MONTH_NAME_SHORT[month])
    elif form == 'dl':
        label = day + ' ' + xbmc.getLocalizedString(MONTH_NAME_LONG[month])
    elif form == 'ms':
        label = xbmc.getLocalizedString(MONTH_NAME_SHORT[month]) + ' ' + day
    elif form == 'ml':
        label = xbmc.getLocalizedString(MONTH_NAME_LONG[month]) + ' ' + day
    return label

def get_wind_direction(value):
    if WIND_DIRECTIONS.get(value) is not None:
        return xbmc.getLocalizedString(WIND_DIRECTIONS.get(value))
    elif value == '0':
        return _('сalm')
    else:
        return _('n/a')

def get_weather_icon(item, tod='d'):
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

def get_weather_code(item):

    #icon = get_weather_icon(item, tod)
    weather_code = WEATHER_CODES.get(item['icon'], 'na')
    #weather_code = item['icon']
    return weather_code

def get_current_struct():
    struct = { # standart properties
              'Location':      '',
              'Condition':     '',
              'Temperature':   '',
              'Wind':          '',
              'WindDirection': '',
              'Humidity':      '',
              'FeelsLike':     '',
#              'UVIndex':       '',
              'DewPoint':      '',
              'OutlookIcon':   '',
              'FanartCode':    '',

               # extenden properties
#              'LowTemperature':  '',
#              'HighTemperature': '',
              'Pressure':        '',
#              'SeaLevel':        '',
#              'GroundLevel':     '',
#              'WindGust':        '',
#              'WindDirStart':    '',
#              'WindDirEnd':      '',
#              'Rain':            '',
#              'Snow':            '',
              'Precipitation':   '',
#              'Cloudiness':      '',
#              'ShortOutlook':    '',
              }

    return struct

def get_day_struct():
    struct = { # standart properties
              'Title': '',
              'HighTemp': '',
              'LowTemp': '',
              'Outlook': '',
              'OutlookIcon': '',
              'FanartCode':  '',
              }

    return struct

def get_daily_struct():

    struct = { # extenden properties
              'LongDay':            '',
              'ShortDay':           '',
              'LongDate':           '',
              'ShortDate':          '',
              'Outlook':            '',
#              'ShortOutlook':       '',
              'OutlookIcon':        '',
#              'LongOutlookDay':     '',
#              'LongOutlookNight':   '',
              'FanartCode':         '',
              'WindSpeed':          '',
              'MaxWind':            '',
              'WindDirection':      '',
#              'ShortWindDirection': '',
#              'WindDegree':         '',
#              'WindGust':           '',
              'Humidity':           '',
              'MinHumidity':        '',
              'MaxHumidity':        '',
              'HighTemperature':    '',
              'LowTemperature':     '',
              'DewPoint':           '',
              'TempMorn':           '',
              'TempDay':            '',
              'TempEve':            '',
              'TempNight':          '',
#              'FeelsLike':          '',
              'Pressure':           '',
#              'Cloudiness':         '',
#              'Rain':               '',
#              'Snow':               '',
              'Precipitation':      '',
              }

    return struct

def get_hourly_struct():
    struct = { # extenden properties
              'Time':             '',
              'LongDate':         '',
              'ShortDate':        '',
              'Outlook':          '',
#              'ShortOutlook':     '',
              'OutlookIcon':      '',
              'FanartCode':       '',
              'WindSpeed':        '',
              'WindDirection':    '',
#              'WindDegree':       '',
 #             'WindGust':         '',
              'Humidity':         '',
              'Temperature':      '',
#              'HighTemperature':  '',
#              'LowTemperature':   '',
              'DewPoint':         '',
              'FeelsLike':        '',
              'Pressure':         '',
#              'SeaLevel':         '',
#              'GroundLevel':      '',
#              'Cloudiness':       '',
#              'Rain':             '',
#              'Snow':             '',
              'Precipitation':    '',
              }

    return struct

def get_36hour_struct():
    struct = { # extenden properties
              'Heading':            '',
              'TemperatureHeading': '',
              'LongDay':            '',
              'ShortDay':           '',
              'LongDate':           '',
              'ShortDate':          '',
              'Outlook':            '',
#              'ShortOutlook':       '',
              'OutlookIcon':        '',
              'FanartCode':         '',
              'WindSpeed':          '',
              'WindDirection':      '',
#              'WindDegree':         '',
#              'WindGust':           '',
              'Humidity':           '',
              'Temperature':        '',
#              'HighTemperature':    '',
#              'LowTemperature':     '',
              'DewPoint':           '',
              'FeelsLike':          '',
              'Pressure':           '',
#              'Cloudiness':         '',
#              'Rain':               '',
#              'Snow':               '',
              'Precipitation':      '',
              }

    return struct

def clear():

    # Current
    weather.set_properties(get_current_struct(), 'Current')

    # Today
    # extenden properties
    weather.set_property('Today.Sunset'  , '')
    weather.set_property('Today.Sunrise' , '')

    # Forecast
    # extenden properties
    weather.set_property('Forecast.City'      , '')
    weather.set_property('Forecast.Country'   , '')
    weather.set_property('Forecast.Latitude'  , '')
    weather.set_property('Forecast.Longitude' , '')
    weather.set_property('Forecast.Updated'   , '')

    # Day
    day_props = get_day_struct()
    for count in range (0, MAX_DAYS + 1):
        weather.set_properties(day_props, 'Day', count, '')

    # Daily
    daily_props = get_daily_struct()
    for count in range (1, MAX_DAILYS + 1):
        weather.set_properties(daily_props, 'Daily', count)

    # Hourly
    hourly_props = get_hourly_struct()
    for count in range (1, MAX_HOURLY + 1):
        weather.set_properties(hourly_props, 'Hourly', count)

    # Weekend
    for count in range (1, MAX_WEEKENDS + 1):
        weather.set_properties(daily_props, 'Weekend', count)

    # 36Hour
    _36hour_props = get_36hour_struct()
    for count in range (1, MAX_36HOUR + 1):
        weather.set_properties(_36hour_props, '36Hour', count)

def refresh_locations():
    locations = 0
    if weather.CurrentLocation:
        location = gismeteo.cities_ip()
        loc_name = location['name']
        loc_id = location['id']

        if loc_name != '':
            locations += 1
            weather.set_property('Location%s' % locations, loc_name)

    for count in range(1, MAX_LOCATIONS + 1):
        loc_name = weather.get_setting('Location%s' % count)
        loc_id = weather.get_setting('Location%sID' % count)
        if loc_name != '':
            locations += 1
            weather.set_property('Location%s' % locations, loc_name)
        elif loc_id != '':
            weather.set_setting('Location%sID' % count, '')

    weather.set_property('Locations', str(locations))

def set_location_props(forecast_info):
    count_days = 0
    count_hourly = 0
    count_36hour = 0
    count_weekends = 0

    set_current_prop(forecast_info)
    set_forecast_prop(forecast_info)
    set_today_prop(forecast_info)

    for day in forecast_info['days']:
        day_temp = None
        if day.get('hourly') is not None:
            day_temp = {}

            for hour in day['hourly']:

                if hour['tod'] == 0:
                    day_temp['night'] = hour['temperature']['air']
                elif hour['tod'] == 1:
                    day_temp['morn'] = hour['temperature']['air']
                elif hour['tod'] == 2:
                    day_temp['day'] = hour['temperature']['air']
                elif hour['tod'] == 3:
                    day_temp['eve'] = hour['temperature']['air']

                if count_hourly < MAX_HOURLY \
                  and hour['date']['unix'] >= CURRENT_TIME['unix']:
                    set_hourly_prop(hour, count_hourly+1 )
                    count_hourly += 1

                if count_36hour < MAX_36HOUR \
                  and hour['tod'] in [2, 3]:
                    if hour['tod'] == 2 \
                      and hour['date']['unix'] >= CURRENT_TIME['unix'] \
                      or hour['tod'] == 3:
                        set_36hour_prop(hour, count_days, hour['tod'], count_36hour+1 )
                        count_36hour += 1

        if count_days <= MAX_DAYS:
            set_day_prop(day, count_days)
        if count_days <= MAX_DAILYS:
            set_daily_prop(day, count_days+1, day_temp)
        if is_weekend(day) \
          and count_weekends <= MAX_WEEKENDS:
            set_weekend_prop(day, count_weekends+1, day_temp)
            count_weekends += 1

        count_days += 1

def set_current_prop(forecast_info):
    current = forecast_info['current']
    weather_code = get_weather_code(current)

    location_name = get_location_name(forecast_info)

    # Current
    current_props = get_current_struct()
    current_props['Location']      = location_name

    set_outlook_info(current_props, current)
    set_wind_info(current_props, current['wind'])
    set_temperature_info(current_props, current, 'hour')
    set_other_info(current_props, current, 'cur')

    weather.set_properties(current_props, 'Current')

def set_forecast_prop(forecast_info):
    # Forecast
    forecast_props = { # extended properties
                      'City':      forecast_info['name'],
                      'Country':   forecast_info['country'],
                      'State':     forecast_info['district'],
                      'Latitude':  forecast_info['lat'],
                      'Longitude': forecast_info['lng'],
                      'Updated':   convert_date(forecast_info['cur_time']),
                      }

    weather.set_properties(forecast_props, 'Forecast')

def set_today_prop(forecast_info):
    current = forecast_info['current']

    if current['sunrise']['unix'] == current['sunset']['unix']:
        return

    # Today
    today_props = { # extended properties
                   'Sunrise': get_time(current['sunrise']),
                   'Sunset':  get_time(current['sunset']),
                   }

    weather.set_properties(today_props, 'Today')

def set_day_prop(day, count):

    #Day
    day_props = get_day_struct()
    set_date_info(day_props, day['date'])
    set_outlook_info(day_props, day)
    set_temperature_info(day_props, day, 'day')

    weather.set_properties(day_props, 'Day', count, '')

def set_date_info(props, date):
    keys = props.keys()

    if 'Title' in keys:
        props['Title'] = get_weekday(date, 'l')

    if 'Time' in keys:
        props['Time'] = get_time(date)

    if 'LongDay' in keys:
        props['LongDay'] = get_weekday(date, 'l')

    if 'ShortDay' in keys:
        props['ShortDay'] = get_weekday(date, 's')

    if 'LongDate' in keys:
        form = 'dl' if (DATEFORMAT[1] == 'd' or DATEFORMAT[0] == 'D') else 'ml'
        props['LongDate'] = get_month(date, form)

    if 'ShortDate' in keys:
        form = 'ds' if (DATEFORMAT[1] == 'd' or DATEFORMAT[0] == 'D') else 'ms'
        props['ShortDate'] = get_month(date, form)

def set_outlook_info(props, item, icon='%s.png'):
    weather_code = get_weather_code(item)

    keys = props.keys()

    if 'Outlook' in keys:
        props['Outlook'] = item['description']

    if 'Condition' in keys:
        props['Condition'] = item['description']

    if 'OutlookIcon' in keys:
        props['OutlookIcon'] = icon % weather_code

    if 'FanartCode' in keys:
        props['FanartCode']  = weather_code

def set_wind_info(props, wind):

    keys = props.keys()

    speed = 0
    if isinstance(wind['speed'], dict):
        speed = wind['speed']['avg']
    elif isinstance(wind['speed'], float):
        speed = wind['speed']

    if 'Wind' in keys:
        props['Wind'] = int(round(speed * 3.6))

    if 'WindSpeed' in keys:
        props['WindSpeed'] = '%s %s' % (SPEED(speed), _(SPEEDUNIT).decode('utf-8'))

    if 'WindDirection' in keys:
        props['WindDirection'] = get_wind_direction(wind['direction'])

    if 'MaxWind' in keys:
        props['MaxWind'] = '%s %s' % (SPEED(wind['speed']['max']), _(SPEEDUNIT).decode('utf-8'))


def set_temperature_info(props, item, type, day_temp=None):
    keys = props.keys()

    if 'DewPoint' in keys and type == 'day':
        props['DewPoint'] = DEW_POINT(item['temperature']['max'], item['humidity']['avg']) + TEMPUNIT
    elif 'DewPoint' in keys  and type == 'hour':
        props['DewPoint'] = DEW_POINT(item['temperature']['air'], item['humidity']) + TEMPUNIT

    if 'HighTemp' in keys:
        props['HighTemp'] = str(item['temperature']['max'])

    if 'LowTemp' in keys:
        props['LowTemp'] = str(item['temperature']['min'])

    if 'HighTemperature' in keys:
        props['HighTemperature'] = TEMP(item['temperature']['max']) + TEMPUNIT

    if 'HighTemperature' in keys:
        props['LowTemperature'] = TEMP(item['temperature']['min']) + TEMPUNIT

    if 'Temperature' in keys:
        props['Temperature'] = TEMP(item['temperature']['air']) + TEMPUNIT

    if 'FeelsLike' in keys:
        props['FeelsLike'] = TEMP(item['temperature']['comfort']) + TEMPUNIT

    if day_temp is not None:
        if 'TempMorn' in keys:
            props['TempMorn'] = TEMP(day_temp['morn']) + TEMPUNIT
        if 'TempDay' in keys:
            props['TempDay'] = TEMP(day_temp['day']) + TEMPUNIT
        if 'TempEve' in keys:
            props['TempEve'] = TEMP(day_temp['eve']) + TEMPUNIT
        if 'TempNight' in keys:
            props['TempNight'] = TEMP(day_temp['night']) + TEMPUNIT

def set_other_info(props, item, type):
    keys = props.keys()

    if 'Humidity' in keys:
        humidity =  item['humidity']['avg'] if type == 'day' else item['humidity']
        tpl = '%i%%' if type != 'cur' else '%i'
        props['Humidity'] = tpl % (humidity) if humidity is not None else _('n/a')

    if 'MinHumidity' in keys and type == 'day':
        humidity =  item['humidity']['min']
        props['MinHumidity'] = '%i%%' % (humidity) if humidity is not None else _('n/a')

    if 'MaxHumidity' in keys and type == 'day':
        humidity =  item['humidity']['max']
        props['MaxHumidity'] = '%i%%' % (humidity) if humidity is not None else _('n/a')

    if 'Pressure' in keys:
        pressure =  item['pressure']['avg'] if type == 'day' else item['pressure']
        props['Pressure'] = '%i %s' % (PRESSURE(pressure),  _(PRESUNIT)) if pressure is not None else _('n/a')

    if 'Precipitation' in keys:
        precip = item['precipitation']['amount']
        props['Precipitation'] = '%.1f %s' % (PRECIPITATION(precip), _(PRECIPUNIT)) if precip is not None else _('n/a')


def set_daily_prop(day, count, day_temp):

    # Daily
    daily_props = get_daily_struct()

    set_date_info(daily_props, day['date'])
    set_outlook_info(daily_props, day, WEATHER_ICON)
    set_wind_info(daily_props, day['wind'])
    set_temperature_info(daily_props, day, 'day', day_temp)
    set_other_info(daily_props, day, 'day')

    weather.set_properties(daily_props, 'Daily', count)

def set_hourly_prop(hour, count):

    #Hourly
    hourly_props = get_hourly_struct()

    set_date_info(hourly_props, hour['date'])
    set_outlook_info(hourly_props, hour, WEATHER_ICON)
    set_wind_info(hourly_props, hour['wind'])
    set_temperature_info(hourly_props, hour, 'hour')
    set_other_info(hourly_props, hour, 'hour')

    weather.set_properties(hourly_props, 'Hourly', count)

def set_36hour_prop(hour, day_num, tod, count):

    #36Hour
    _36hour_props = get_36hour_struct()

    set_date_info(_36hour_props, hour['date'])
    set_outlook_info(_36hour_props, hour, WEATHER_ICON)
    set_wind_info(_36hour_props, hour['wind'])
    set_temperature_info(_36hour_props, hour, 'hour')
    set_other_info(_36hour_props, hour, 'hour')

    if tod == 2:
        _36hour_props['Heading']            = xbmc.getLocalizedString(33006+day_num)
        _36hour_props['TemperatureHeading'] = xbmc.getLocalizedString(393)
    else:
        _36hour_props['Heading']            = xbmc.getLocalizedString(33018+day_num)
        _36hour_props['TemperatureHeading'] = xbmc.getLocalizedString(391)

    weather.set_properties(_36hour_props, '36Hour', count)

def set_weekend_prop(day, count, day_temp):

    # Weekend
    weekend_props = get_daily_struct()

    # extended properties
    set_date_info(weekend_props, day['date'])
    set_outlook_info(weekend_props, day, WEATHER_ICON)
    set_wind_info(weekend_props, day['wind'])
    set_temperature_info(weekend_props, day, 'day', day_temp)
    set_other_info(weekend_props, day, 'day')

    weather.set_properties(weekend_props, 'Weekend', count)

def forecast(loc_name, loc_id):
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
        set_location_props(data)
    else:
        clear()

def select_location(location):
    labels = []
    locations = []

    keyboard = xbmc.Keyboard('', xbmc.getLocalizedString(14024), False)
    keyboard.doModal()
    if (keyboard.isConfirmed() and keyboard.getText() != ''):
        text = keyboard.getText()
        dialog = xbmcgui.Dialog()

        for location in gismeteo.cities_search(text):
            location_name = get_location_name(location)

            if location['district']:
                labels.append('%s (%s, %s)' % (location_name, location['district'], location['country']))
            else:
                labels.append('%s (%s)' % (location_name, location['country']))
            locations.append({'id':location['id'], 'name': location_name})

        if len(locations) > 0:
            selected = dialog.select(xbmc.getLocalizedString(396), labels)
            if selected != -1:
                selected_location = locations[selected]
                weather.set_setting(sys.argv[1], selected_location['name'])
                weather.set_setting(sys.argv[1] + 'ID', selected_location['id'])
        else:
            dialog.ok(weather.name, xbmc.getLocalizedString(284))

def get_location(id):
    if id == '1' and weather.CurrentLocation:
        location = gismeteo.cities_ip()
        location_name = get_location_name(location)
        location_id = location['id']
    else:
        _id = id if not weather.CurrentLocation else str((int(id) - 1))
        location_name = weather.get_setting('Location%s' % _id, False)
        location_id = weather.get_setting('Location%sID' % _id, False)

        if (location_id == '') and (_id != '1'):
            location_name = weather.get_setting('Location1', False)
            location_id = weather.get_setting('Location1ID', False)

    return location_name, location_id

MONITOR = MyMonitor()

if __name__ == '__main__':

    WEEKENDS = get_weekends()

    weather.set_property('Forecast.IsFetched', 'true')
    weather.set_property('Current.IsFetched' , 'true')
    weather.set_property('Today.IsFetched'   , 'true')
    weather.set_property('Daily.IsFetched'   , 'true')
    weather.set_property('Weekend.IsFetched' , 'true')
    weather.set_property('36Hour.IsFetched'  , 'true')
    weather.set_property('Hourly.IsFetched'  , 'true')
    weather.set_property('Alerts.IsFetched'  , '')
    weather.set_property('Map.IsFetched'     , '')

    # WeatherProvider
    # standard properties
    weather.set_property('WeatherProvider'    , weather.name)
    weather.set_property('WeatherProviderLogo', xbmc.translatePath(os.path.join(weather.path, 'resources', 'media', 'banner.png')).decode("utf-8"))

    conf = {'lang': get_lang(),
            'cache_dir':  os.path.join(xbmc.translatePath('special://temp'), weather.id),
            'cache_time': 30, # time in minutes
            }
    gismeteo = Gismeteo(conf)

    if sys.argv[1].startswith('Location'):
        select_location(sys.argv[1])
    else:
        clear()
        location_name, location_id = get_location(sys.argv[1])
        if not location_id == '':
            forecast(location_name, location_id)
        refresh_locations()

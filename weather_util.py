#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : weather_util.py
# Author            : Yan <yanwong@126.com>
# Date              : 01.03.2024
# Last Modified Date: 06.03.2024
# Last Modified By  : Yan <yanwong@126.com>

import os
import json
import logging
import requests
from datetime import date

from map_util import GaodeGeo

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class GaodeWeather(object):
    def __init__(self, geo, weather_url):
        self.api_key = os.environ['GAODE_API_KEY']
        self.geo = geo
        self.weather_url = weather_url

    def get_forecast(self, address, city, forecast_type='all'):
        adcode = self.geo.get_adcode(address, city)
        if not adcode:
            logger.warning('Can not get adcode for address: {}'.format(address))
            return []

        top1_adcode = adcode[0]
        payload = {'city': top1_adcode, 'key': self.api_key, 'extensions': forecast_type}
        try:
            res = requests.get(self.weather_url, params=payload)
            res_content = json.loads(res.text)
        except Exception as e:
            logger.error('Request gaode weather api failed: {}'.format(e))
            return []

        if res_content['status'] == 0:
            logger.error('Gaode weather api error: {}'.format(res_content['info']))
            return []

        forecast = [{'date': date.fromisoformat(ca['date']),
                     'day_weather': ca['dayweather'],
                     'night_weather': ca['nightweather']}
                     for ca in res_content['forecasts'][0]['casts']]
        return forecast, top1_adcode

# if __name__ == '__main__':
#     geocode_url = "https://restapi.amap.com/v3/geocode/geo"
#     weather_url = "https://restapi.amap.com/v3/weather/weatherInfo"
#     staticmap_url = "https://restapi.amap.com/v3/staticmap"
# 
#     geo = GaodeGeo(geocode_url, staticmap_url)
# 
#     weather_cli = GaodeWeather(geo, weather_url)
#     r = weather_cli.get_forecast('安山古道', '绍兴')
#     print(r)



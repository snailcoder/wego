#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : weather_util.py
# Author            : Yan <yanwong@126.com>
# Date              : 01.03.2024
# Last Modified Date: 21.03.2024
# Last Modified By  : Yan <yanwong@126.com>

import os
import json
import logging
import requests
from datetime import date

from map_util import GaodeGeo

logger = logging.getLogger(__name__)

class GaodeWeather(object):
    def __init__(self, geo, weather_url):
        self.api_key = os.environ['GAODE_API_KEY']
        self.geo = geo
        self.weather_url = weather_url

    def get_forecast(self, geocode, forecast_type='all'):
        forecast = []
        payload = {
            'city': geocode['adcode'],
            'key': self.api_key,
            'extensions': forecast_type
        }
        try:
            res = requests.get(self.weather_url, params=payload)
            res_content = json.loads(res.text)
            if res_content['status'] == 0:
                logger.error('Gaode weather api error: {}'.format(res_content['info']))
            else:
                forecast = [{'date': date.fromisoformat(ca['date']),
                             'day_weather': ca['dayweather'],
                             'night_weather': ca['nightweather']}
                             for ca in res_content['forecasts'][0]['casts']]
        except Exception as e:
            logger.error('Request gaode weather api failed: {}'.format(e))

        return forecast


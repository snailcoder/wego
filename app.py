#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : app.py
# Author            : Yan <yanwong@126.com>
# Date              : 03.03.2024
# Last Modified Date: 03.03.2024
# Last Modified By  : Yan <yanwong@126.com>

import gradio as gr
import plotly.graph_objects as go

from map_util import GaodeGeo
from weather_util import GaodeWeather
from trip_advisor import QwenTripAdvisor

GAODE_GEOCODE_URL = 'https://restapi.amap.com/v3/geocode/geo'
GAODE_WEATHER_URL = 'https://restapi.amap.com/v3/weather/weatherInfo'
GAODE_STATICMAP_URL = 'https://restapi.amap.com/v3/staticmap'

QWEN_LLM_NAME = 'qwen-max'

geo_cli = GaodeGeo(GAODE_GEOCODE_URL, GAODE_STATICMAP_URL)
weather_cli = GaodeWeather(geo_cli, GAODE_WEATHER_URL)
trip_advisor = QwenTripAdvisor(QWEN_LLM_NAME)


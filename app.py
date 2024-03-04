#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : app.py
# Author            : Yan <yanwong@126.com>
# Date              : 03.03.2024
# Last Modified Date: 03.03.2024
# Last Modified By  : Yan <yanwong@126.com>

from datetime import date, timedelta
import logging

import gradio as gr
import plotly.graph_objects as go

from map_util import GaodeGeo, create_markers_figure
from weather_util import GaodeWeather
from trip_advisor import QwenTripAdvisor

GAODE_GEOCODE_URL = 'https://restapi.amap.com/v3/geocode/geo'
GAODE_WEATHER_URL = 'https://restapi.amap.com/v3/weather/weatherInfo'
GAODE_STATICMAP_URL = 'https://restapi.amap.com/v3/staticmap'

QWEN_LLM_NAME = 'qwen-max'

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

wg_geo = GaodeGeo(GAODE_GEOCODE_URL, GAODE_STATICMAP_URL)
wg_weather = GaodeWeather(wg_geo, GAODE_WEATHER_URL)
wg_trip_advisor = QwenTripAdvisor(QWEN_LLM_NAME)

def create_trip_brief(city, days, first_date):
    forecast = wg_weather.get_forecast(city, city)
    if not forecast:
        logger.warning('Can not get forecast of city: {}'.format(city))
        return None

    trip_dates = [first_date + timedelta(days=i) for i in range(days)]
    trip_brief = {'city': city, 'duration': f'{days}天', 'dates': trip_dates}

    weathers = []
    for td in trip_dates:
        i = 0
        while i < len(forecast):
            if forecast[i]['date'] == td:
                weathers.append(forecast[i])
                break
            i += 1
        if i == len(forecast):
            weathers.append({'day_weather': '未知', 'night_weather': '未知'})

    trip_brief['weathers'] = weathers
    return trip_brief

def get_trip_advise(trip_brief, max_retry=3):
    advise = {}
    for i in range(max_retry):
        advise = wg_trip_advisor.generate_advise(trip_brief)
        if advise:
            break
    return advise

def mark_advise_on_map(advise):
    city = advise['city']
    addresses = [
        sch['location'] for day in advise['days'] for sch in day['schedule']
    ]
    valid_locations, valid_addresses = [], []
    for addr in addresses:
        loclist = wg_geo.get_location(addr, city)
        if loclist:
            valid_locations.append(loclist[0])
            valid_addresses.append(addr)
    fig = create_markers_figure(valid_locations, valid_addresses)
    return fig

def create_highlighted_text(trip_brief, advise):
    highlighted = []

    days = advise['days']
    dates, weathers = trip_brief['dates'], trip_brief['weathers']

    for da, dt, we in zip(days, dates, weathers):
        dt_str = dt.isoformat()
        day_we, night_we = we['day_weather'], we['night_weather']
        label = f'{dt_str}, 白天{day_we}, 晚上{night_we}'

        label_texts = {'label': label, 'texts': []}
        for sch in da['schedule']:
            label_texts['texts'].extend([
                (sch['time'] + '\n', 'time'),
                (sch['location'], 'location'),
                (sch['description'] + '\n', 'tip')
            ])
        highlighted.append(label_texts)

    return highlighted

brief = create_trip_brief('长沙', 2, date(2024, 3, 5))
print('Demo brief: {}'.format(brief))

advise = get_trip_advise(brief)
print('Generated advise (in JSON): {}'.format(advise))

figure = mark_advise_on_map(advise)
highlighted = create_highlighted_text(brief, advise)

color_map = {'time': 'red', 'tip': 'green', 'location': 'blue'}

def showfig():
    return figure

with gr.Blocks() as demo:
    with gr.Column():
        plot = gr.Plot()
        with gr.Row():
            for ht in highlighted:
                gr.HighlightedText(
                    ht['texts'], label=ht['label'],
                    color_map=color_map, interactive=True
                )
    demo.load(showfig, outputs=[plot])

demo.launch(show_error=True)


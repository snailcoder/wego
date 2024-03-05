#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : app.py
# Author            : Yan <yanwong@126.com>
# Date              : 03.03.2024
# Last Modified Date: 05.03.2024
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
    first_date = date.fromisoformat(first_date)
    forecast = wg_weather.get_forecast(city, city)
    if not forecast:
        logger.warning('Can not get forecast of city: {}'.format(city))
        return None

    trip_dates = [first_date + timedelta(days=i) for i in range(days)]
    trip_brief = {'city': city, 'duration': f'{days}天'}

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

def generate_trip_advise(trip_brief, max_retry=3):
    advise = {}
    for i in range(max_retry):
        advise = wg_trip_advisor.generate_advise(trip_brief)
        if advise:
            break
        print(f'Retry to generate advise for the {i+1}th time...')
    return advise

def mark_advise_on_map(advise):
    city = advise['city']
    traces = []

    for day in advise['days']:
        date_trace = {'trace': day['date']}
        valid_locations, valid_addresses = [], []
        for sch in day['schedule']:
            addr = sch['location']
            loclist = wg_geo.get_location(addr, city)
            if loclist:
                valid_locations.append(loclist[0])
                valid_addresses.append(addr)
        date_trace.update({
            'locations': valid_locations, 'addresses': valid_addresses
        })
        traces.append(date_trace)

    fig = create_markers_figure(traces)

    return fig

def highlight_advise(brief, advise):
    highlighted = []

    days = advise['days']
    weathers = brief['weathers']
    dates = [w['date'] for w in weathers]

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

    highlighted_show = [
        gr.HighlightedText(h['texts'], label=h['label'], visible=True)
        for h in highlighted
    ]
    highlighted_hide = [
        gr.HighlightedText(visible=False)
        for _ in range(MAX_TRIP_DAYS - len(highlighted_show))
    ]
    return highlighted_show + highlighted_hide

def get_trip_brief_and_advise(city, days, first_date):
    brief = create_trip_brief(city, days, first_date)
    print('Trip brief: {}'.format(brief)) 
    advise = generate_trip_advise(brief)
    print('Generated advise (in JSON): {}'.format(advise))
    return brief, advise

MIN_TRIP_DAYS = 1
MAX_TRIP_DAYS = 7

with gr.Blocks() as demo:
    with gr.Column():
        with gr.Group():
            with gr.Row():
                city = gr.Textbox(
                    label='城市',
                    placeholder='择一城而往，例如新昌县, 杭州, 北京...'
                )
                days = gr.Number(
                    2, label='天数', minimum=MIN_TRIP_DAYS,
                    maximum=MAX_TRIP_DAYS, interactive=True
                )
                first_date = gr.Textbox(
                    label='开始日期',
                    placeholder='放飞自我的第一天，格式为yyyy-mm-dd'
                )
        go_btn = gr.Button('GO', size='sm')
        map_plot = gr.Plot(label='旅行地图')

        highlighted_texts = []
        with gr.Row():
            for i in range(MAX_TRIP_DAYS):
                ht = gr.HighlightedText(visible=False)
                highlighted_texts.append(ht)

    brief, advise = gr.State(), gr.State()

    go_btn.click(
        get_trip_brief_and_advise,
        inputs=[city, days, first_date],
        outputs=[brief, advise]
    ).then(
        mark_advise_on_map,
        inputs=[advise],
        outputs=[map_plot]
    ).then(
        highlight_advise,
        inputs=[brief, advise],
        outputs=highlighted_texts
    )

demo.launch(show_error=True)


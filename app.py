#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : app.py
# Author            : Yan <yanwong@126.com>
# Date              : 03.03.2024
# Last Modified Date: 08.03.2024
# Last Modified By  : Yan <yanwong@126.com>

from datetime import date, timedelta
import logging

import gradio as gr
import plotly.graph_objects as go

from map_util import GaodeGeo, plot_markers_map
from weather_util import GaodeWeather
from video_util import BilibiliVideo
from trip_advisor import QwenTripAdvisor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

GAODE_GEOCODE_URL = 'https://restapi.amap.com/v3/geocode/geo'
GAODE_WEATHER_URL = 'https://restapi.amap.com/v3/weather/weatherInfo'
GAODE_STATICMAP_URL = 'https://restapi.amap.com/v3/staticmap'
GAODE_POI_URL = 'https://restapi.amap.com/v3/place/text'

QWEN_LLM_NAME = 'qwen-max'

BILIBILI_SEARCH_URL = 'https://api.bilibili.com/x/web-interface/search/all/v2'
BILIBILI_EMBED_URL = '//player.bilibili.com/player.html'

DEFAULT_MARKER_LOCATION = '121.460351,31.163443'
DEFAULT_MARKER_ADDRESS = '上海人工智能实验室'
DEFAULT_BILIBILI_AID = '1351359862'
DEFAULT_BILIBILI_BVID = 'BV1Uz421D7Yk'

logger = logging.getLogger(__name__)

wg_geo = GaodeGeo(GAODE_GEOCODE_URL, GAODE_POI_URL, GAODE_STATICMAP_URL)
wg_weather = GaodeWeather(wg_geo, GAODE_WEATHER_URL)
wg_video = BilibiliVideo(BILIBILI_SEARCH_URL, BILIBILI_EMBED_URL)
wg_trip_advisor = QwenTripAdvisor(QWEN_LLM_NAME)

def create_trip_brief(city, days, first_date):
    first_date = date.fromisoformat(first_date)
    forecast, geocode = wg_weather.get_forecast(city, city)
    if not forecast:
        logger.warning('Can not get forecast of city: {}'.format(city))
        return None

    adcode, std_city = geocode['adcode'], geocode['formatted_address']
    trip_dates = [first_date + timedelta(days=i) for i in range(days)]
    trip_brief = {
        'city': city, 'adcode': adcode,
        'duration': f'{days}天', 'std_city': std_city
    }

    weathers = []
    for td in trip_dates:
        i = 0
        while i < len(forecast):
            if forecast[i]['date'] == td:
                weathers.append(forecast[i])
                break
            i += 1
        if i == len(forecast):
            weathers.append(
                {'date': td, 'day_weather': '未知', 'night_weather': '未知'}
            )

    trip_brief['weathers'] = weathers
    return trip_brief

def generate_trip_advise(trip_brief, max_retry=3):
    advise = {}
    i = 0
    while i < max_retry:
        advise = wg_trip_advisor.generate_advise(trip_brief)
        if advise:
            break
        i += 1
        logger.warning(f'Retry to generate advise for the {i}th time...')

    if i == max_retry:
        logger.error(f'Generate trip advise failed for {i} times.')
        return None
    advise['adcode'] = trip_brief['adcode']
    return advise

def mark_default_location_on_map():
    traces = [{
        'trace': DEFAULT_MARKER_ADDRESS,
        'locations': [DEFAULT_MARKER_LOCATION],
        'addresses': [DEFAULT_MARKER_ADDRESS]
    }]

    return plot_markers_map(traces)

def mark_city_on_map(city):
    if city:
        locations = wg_geo.get_location(city, city)
        if locations:
            traces = [
                {'trace': city, 'locations': locations[:1], 'addresses': [city]}
            ]
            return plot_markers_map(traces)

    return mark_default_location_on_map()

def mark_advise_on_map(advise):
    traces = []

    try:
        city = advise['adcode']

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
    except Exception as e:
        logger.error('Mark advise locations on map failed: {}'.format(e))
        raise gr.Error('Mark advise locations on map failed.')

    return plot_markers_map(traces)

def embed_default_video():
    return wg_video.get_embed_html_by_id(
            DEFAULT_BILIBILI_AID, DEFAULT_BILIBILI_BVID)

def embed_city_video(city):
    keyword = city + '宣传片'
    gr.Info('Searching videos.')
    videoinfo = wg_video.search_video(keyword)
    if not videoinfo:
        logger.warning(f'No video of {keyword} found.')
        gr.Warning(f'No video of {city} found.')
        return embed_default_video()

    return wg_video.get_embed_html(videoinfo[0])

def highlight_advise(brief, advise):
    highlighted = []

    try:
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
    except Exception as e:
        logger.error('Extract advise for highlighting failed: {}'.format(e))
        raise gr.Error('Extract advise for highlighting failed.')

    highlighted_show = [
        gr.HighlightedText(h['texts'], label=h['label'], visible=True)
        for h in highlighted
    ]
    highlighted_hide = [
        gr.HighlightedText(visible=False)
        for _ in range(MAX_TRIP_DAYS - len(highlighted_show))
    ]
    return highlighted_show + highlighted_hide

def get_trip_brief_and_video(city, days, first_date):
    brief = create_trip_brief(city, days, first_date)
    embed_html = embed_city_video(brief['std_city'])
    return brief, embed_html

def get_trip_advise(brief):
    logger.info(
        'Start to generate advise based on the trip brief: {}'.format(brief)
    )
    gr.Info('Start to generate advise...')
    advise = generate_trip_advise(brief)
    logger.info('Generated advise (in JSON): {}'.format(advise))
    gr.Info('Generation completed.')
    return advise

def get_trip_brief_and_advise(city, days, first_date):
    brief = create_trip_brief(city, days, first_date)
    logger.info(
        'Start to generate advise based on the trip brief: {}'.format(brief)
    )
    gr.Info('Start to generate advise.')
    advise = generate_trip_advise(brief)
    logger.info('Generated advise (in JSON): {}'.format(advise))
    gr.Info('Generation completed.')
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
                    label='天数', minimum=MIN_TRIP_DAYS,
                    maximum=MAX_TRIP_DAYS, interactive=True
                )
                first_date = gr.Textbox(
                    label='开始日期',
                    placeholder='放飞自我的第一天，格式为yyyy-mm-dd'
                )
        go_btn = gr.Button('GO', size='sm')
        video_html = gr.HTML(label='随便看看')
        map_plot = gr.Plot(label='旅行地图')

        highlighted_texts = []
        with gr.Row():
            for i in range(MAX_TRIP_DAYS):
                ht = gr.HighlightedText(visible=False)
                highlighted_texts.append(ht)

    brief, advise = gr.State(), gr.State()

    demo.load(mark_default_location_on_map, outputs=[map_plot])
    # demo.load(embed_default_video, outputs=[video_html])
    city.blur(mark_city_on_map, inputs=[city], outputs=[map_plot])
    # go_btn.click(
    #     get_trip_brief_and_advise,
    #     inputs=[city, days, first_date],
    #     outputs=[brief, advise],
    #     show_progress=True
    # ).then(
    #     mark_advise_on_map,
    #     inputs=[advise],
    #     outputs=[map_plot],
    #     show_progress=True
    # ).then(
    #     highlight_advise,
    #     inputs=[brief, advise],
    #     outputs=highlighted_texts,
    #     show_progress=True
    # )
    go_btn.click(
        get_trip_brief_and_video,
        inputs=[city, days, first_date],
        outputs=[brief, video_html],
        show_progress=True
    ).then(
        get_trip_advise,
        inputs=[brief],
        outputs=[advise],
        show_progress=True
    ).then(
        mark_advise_on_map,
        inputs=[advise],
        outputs=[map_plot],
        show_progress=True
    ).then(
        highlight_advise,
        inputs=[brief, advise],
        outputs=highlighted_texts,
        show_progress=True
    )

demo.launch(show_error=True)


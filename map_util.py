#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : map_util.py
# Author            : Yan <yanwong@126.com>
# Date              : 01.03.2024
# Last Modified Date: 06.03.2024
# Last Modified By  : Yan <yanwong@126.com>

import os
import json
import logging

import requests
import plotly.graph_objects as go

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def locations_center(locations):
    lon_lat = [loc.split(',') for loc in locations]
    center_lon = sum([float(ll[0]) for ll in lon_lat]) / len(lon_lat)
    center_lat = sum([float(ll[1]) for ll in lon_lat]) / len(lon_lat)
    return center_lon, center_lat

def create_markers_figure(location_traces, marker_size=10):
    fig = go.Figure()

    locations = []
    for tr in location_traces:
        locations.extend(tr['locations'])
        lon_lat = [loc.split(',') for loc in tr['locations']]

        fig.add_trace(go.Scattermapbox(
            name=tr['trace'],
            customdata=tr['addresses'],
            lat=[ll[1] for ll in lon_lat],
            lon=[ll[0] for ll in lon_lat],
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=marker_size
            ),
            hoverinfo='text',
            hovertemplate='<b>%{customdata}</b>'
        ))

    center_lon, center_lat = locations_center(locations)

    fig.update_layout(
        mapbox_style="open-street-map",
        hovermode='closest',
        mapbox=dict(
            bearing=0,
            center=go.layout.mapbox.Center(
                lat=center_lat,
                lon=center_lon
            ),
            pitch=0,
            zoom=9
        )
    )
    return fig

class GaodeGeo(object):
    def __init__(self, geocode_url, poi_url, staticmap_url,
                 staticmap_scale='2', staticmap_size='400*400'):
        self.api_key = os.environ['GAODE_API_KEY']
        self.geocode_url = geocode_url
        self.poi_url = poi_url
        self.staticmap_url = staticmap_url
        self.staticmap_scale = staticmap_scale  # 1: 普通 2: 高清
        self.staticmap_size = staticmap_size  # 最大支持1024*1024

    def get_adcode(self, address, city=None):
        payload = {'address': address, 'key': self.api_key}
        if city:
            payload['city'] = city
        try:
            res = requests.get(self.geocode_url, params=payload)
            res_content = json.loads(res.text)
        except Exception as e:
            logger.error('Request gaode geocode api failed: {}'.format(e))
            return []

        if res_content['status'] == 0:
            logger.error('Gaode geocode api error: {}'.format(res_content['info']))
            return []

        adcode = [g['adcode'] for g in res_content['geocodes']]
        return adcode

    def get_location(self, address, city=None):
        payload = {'address': address, 'key': self.api_key}
        if city:
            payload['city'] = city
        location = []
        try:
            res = requests.get(self.geocode_url, params=payload)
            res_content = json.loads(res.text)

            # logger.info('Response of gaode geocode api: {}'.format(res_content))

            if res_content['status'] == 0:
                logger.error('Gaode geocode api error: {}'.format(res_content['info']))
                return location

            if not city:
                location = [g['location'] for g in res_content['geocodes']]
                return location

            for g in res_content['geocodes']:
                if city == g['city'] or city == g['citycode'] or city == g['adcode']:
                    location.append(g['location'])
            if not location:
                logger.warning(f'No location of {address}:{city} found, searching POI.')
                payload['citylimit'] = True
                res = requests.get(self.poi_url, params=payload)
                res_content = json.loads(res.text)

                if res_content['status'] == 0:
                    logger.error('Gaode poi api error: {}'.format(res_content['info']))
                    return location

                location = [p['location'] for p in res_content['pois']]
        except Exception as e:
            logger.error('Get location failed: {}'.format(e))

        return location

    def get_staticmap(self, addresses, city, locations=None, marker=False, label=True):
        if not locations:
            locations = []
            for addr in addresses:
                coords = self.get_location(addr, city)
                locations.append(coords[0])

        payload = {'size': self.staticmap_size, 'scale': self.staticmap_scale,
                   'key': self.api_key}
        if marker:
            markers = []
            for addr, loc in zip(addresses, locations):
                marker_style = ','.join(['mid', '0xFF0000', addr[0]])
                markers.append(marker_style + ':' + loc)
            payload['markers'] = '|'.join(markers)
        if label:
            labels = []
            for addr, loc in zip(addresses, locations):
                label_style = ','.join([addr, '0', '1', '20', '0x000000', '0xFF0000'])
                labels.append(label_style + ':' + loc)
            payload['labels'] = '|'.join(labels)

        try:
            res = requests.get(self.staticmap_url, params=payload)
        except Exception as e:
            logger.error('Request gaode staticmap api failed: {}'.format(e))
            return ''
        return res.content

# if __name__ == '__main__':
#     geocode_url = "https://restapi.amap.com/v3/geocode/geo"
#     staticmap_url = "https://restapi.amap.com/v3/staticmap"
#     gaode = GaodeGeo(geocode_url, staticmap_url)
#     r = gaode.get_staticmap(['浙江大学', '西湖大学', '西湖', '西溪'], '杭州')
#     print(r)
#     img = Image.open(BytesIO(r))
#     print(img)
#     # with open('abc.png', 'wb') as f:
#     #     f.write(r)


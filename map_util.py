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
import re

import requests
import plotly.graph_objects as go

logger = logging.getLogger(__name__)

def locations_center(locations):
    lon_lat = [loc.split(',') for loc in locations]
    center_lon = sum([float(ll[0]) for ll in lon_lat]) / len(lon_lat)
    center_lat = sum([float(ll[1]) for ll in lon_lat]) / len(lon_lat)
    return center_lon, center_lat

def same_province(code1, code2):
    return int(code1) // 1000 == int(code2) // 1000

def same_city(code1, code2):
    return int(code1) // 100 == int(code2) // 100

def plot_markers_map(location_traces, marker_size=10):
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

    if not locations:
        logger.warning('No marker locations provided, can not plot.')
        return fig

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
        self.staticmap_scale = staticmap_scale  # 1: general 2: hd
        self.staticmap_size = staticmap_size  # largest: 1024*1024

    def get_geocode(self, address, city=None):
        payload = {'address': address, 'key': self.api_key}
        if city:
            payload['city'] = city
        geocode = []
        try:
            res = requests.get(self.geocode_url, params=payload)
            res_content = json.loads(res.text)
            if res_content['status'] == 0:
                logger.error('Gaode geocode api error: {}'.format(res_content['info']))
                return geocode

            geocode = [{
                'adcode': g['adcode'],
                'citycode': g['citycode'],
                'city': g['city'],
                'province': g['province'],
                'formatted_address': g['formatted_address']}
                for g in res_content['geocodes']]

        except Exception as e:
            logger.error('Get geocode failed: {}'.format(e))

        return geocode

    def get_location(self, address, city=None):
        payload = {'address': address, 'key': self.api_key}
        if city:
            payload['city'] = city
        location = []
        try:
            res = requests.get(self.geocode_url, params=payload)
            res_content = json.loads(res.text)

            if res_content['status'] == 0:
                logger.error('Gaode geocode api error: {}'.format(res_content['info']))
                return location

            geocodes = res_content.get('geocodes')
            if geocodes:
                if not city:
                    location = [g['location'] for g in res_content['geocodes']]
                else:
                    for g in geocodes:
                        lon_lat = g['location']

                        if re.match(r'(110|120|310|500)\d{3}', city) and \
                                same_province(city, g['adcode']):
                            location.append(lon_lat)
                        elif re.match(r'\d{6}', city) and same_city(city, g['adcode']):
                            location.append(lon_lat)
                        elif re.match(r'\d{3,4}', city) and city == g['citycode']:
                            location.append(lon_lat)
                        elif city in g['formatted_address']:
                            location.append(lon_lat)
            else:
                logger.warning(
                    f'Gaode does not provide geocodes of {address}:{city}'
                )

            if not location:
                logger.warning(f'Searching POI of {address}:{city}')

                payload.update({'keywords': address, 'citylimit': True})
                res = requests.get(self.poi_url, params=payload)
                res_content = json.loads(res.text)

                if res_content['status'] == 0:
                    logger.error('Gaode poi api error: {}'.format(res_content['info']))
                    return location

                pois = res_content.get('pois')
                if pois:
                    location = [p['location'] for p in pois]
                else:
                    logger.warning(
                        f'Gaode does not provide poi of {address}:{city}'
                    )
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
            logger.error('Get staticmap failed: {}'.format(e))
            return ''
        return res.content


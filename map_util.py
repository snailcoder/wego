#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : map_util.py
# Author            : Yan <yanwong@126.com>
# Date              : 01.03.2024
# Last Modified Date: 03.03.2024
# Last Modified By  : Yan <yanwong@126.com>

import os
import json
import logging
import requests

logger = logging.getLogger(__name__)

class Map(object):
    def sort_locations(self, locations):
        pass

    def plot_locations_circle(self, locations):
        pass

class GaodeGeo(object):
    def __init__(self, geocode_url, staticmap_url,
                 staticmap_scale='2', staticmap_size='400*400'):
        self.api_key = os.environ['GAODE_API_KEY']
        self.geocode_url = geocode_url
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
        try:
            res = requests.get(self.geocode_url, params=payload)
            res_content = json.loads(res.text)
        except Exception as e:
            logger.error('Request gaode geocode api failed: {}'.format(e))
            return []

        if res_content['status'] == 0:
            logger.error('Gaode geocode api error: {}'.format(res_content['info']))
            return []

        location = [g['location'] for g in res_content['geocodes']]
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
#     gaode = GaodeMap(geocode_url, staticmap_url)
#     r = gaode.get_staticmap(['北京大学', '人民大学', '天安门', '北海公园'], '北京')
#     with open('abc.png', 'wb') as f:
#         f.write(r)


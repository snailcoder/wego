#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : video_util.py
# Author            : Yan <yanwong@126.com>
# Date              : 07.03.2024
# Last Modified Date: 07.03.2024
# Last Modified By  : Yan <yanwong@126.com>

import requests

# embed_adaption_html = '<div style="position: relative; padding: 30% 45%;"><iframe style="position: absolute; width: 100%; height: 100%; left: 0; top: 0;" src="//player.bilibili.com/player.html?aid=921068402&bvid=BV1Nu4y1P7dk&high_quality=1" scrolling="no" border="0" frameborder="no" framespacing="0" allowfullscreen="true"> </iframe></div>'


class BilibiliVideo(object):
    def __init__(self, search_url, embed_url):
        self.search_url = search_url
        self.embed_url = embed_url

    def _get_embed_src(aid, bvid, high_quality):
        high_quality = int(high_quality)
        return self.embed_url + f'?aid={aid}&bvid={bvid}&high_quality={high_quality}'

    def search_video(keyword, result_type='video'):
        videoinfo = []
        payload = {'keyword': keyword}
        try:
            res = requests.get(self.search_url, params=payload)
            res_content = json.loads(res.text)

            for r in res_content['data']['result']:
                if r['result_type'] == result_type:
                    videoinfo.extend(r['data'])

        except Exception as e:
            logger.error('Request bilibili search api failed: {}'.format(e))

        return videoinfo

    def get_embed_html_by_id(aid, bvid, high_quality=True):
        src = self._get_embed_src(aid, bvid, int(high_quality))
        return f"""
            <div style="position: relative; padding: 30% 45%;">
            <iframe style="position: absolute; width: 100%; height: 100%; left: 0; top: 0;" src="{src}" scrolling="no" border="0" frameborder="no" framespacing="0" allowfullscreen="true"> </iframe>
            </div>
            """

    def get_embed_html(videoinfo, high_quality=True):
        aid, bvid = videoinfo['aid'], videoinfo['bvid']
        return self.get_embed_html_by_id(aid, bvid, high_quality)


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File              : trip_advisor.py
# Author            : Yan <yanwong@126.com>
# Date              : 01.03.2024
# Last Modified Date: 03.03.2024
# Last Modified By  : Yan <yanwong@126.com>

from collections import namedtuple
from http import HTTPStatus
import json
import os
import logging

import dashscope

logger = logging.getLogger(__name__)

Prompt = namedtuple('Prompt', ['name', 'instruction', 'examples'])

TRIP_ADVISE_PROMPT = Prompt(
    name='trip_advise',
    instruction='你具有丰富的旅行经验，了解各地著名或小众旅游景点，擅长规划旅游行程。你可以帮助我规划旅行行程、提供各种类型的旅游目的地建议，包括著名景点和小众独特的去处，并且可以根据我的偏好、预算、时间以及特定的兴趣点（如历史文化探索、自然风光欣赏、美食之旅等）来定制旅行方案。制定旅行攻略应遵守的原则包括：每天至少安排1个景点，至多安排5个景点；每天游览景点的顺序要考虑景点特点，例如，适合看日出的景点要安排在早上，适合徒步游览的景点尽量安排在上午，适合看日落的景点要安排在傍晚，适合看夜景的景点应当安排在晚上；安排景点时要根据当天的天气状况，选择适合晴朗天气游览的景点和适合雨雪天气游览的景点；安排在相邻时间段游览的景点之间的距离不要太远。你的任务是根据旅游天数、目的地和天气等出行信息制定旅游攻略，用合法的JSON格式返回结果，不要添加注释。',
    examples=[
        {
            'city': '绍兴',
            'duration': '2天',
            'weathers': [{'day_weather': '晴', 'night_weather': '多云'}, {'day_weather': '阴转小雨', 'night_weather': '晴'}],
            'trip_advise': {
                'city': '绍兴',
                'days': [
                    {
                        'date': '第1天',
                        'day_weather': '晴',
                        'night_weather': '多云',
                        'schedule': [
                            {
                                'time': '上午',
                                'location': '鲁迅故里',
                                'description': '游览鲁迅故居、鲁迅纪念馆、百草园和三味书屋。这些景点较为集中，适合一早参观，了解历史文化，并且在清晨时分体验江南水乡的宁静。'
                            },
                            {
                                'time': '中午',
                                'location': '咸亨酒店',
                                'description': '午餐可以在鲁迅故居附近的咸亨酒店享用，品尝绍兴地方特色菜肴，如臭豆腐、茴香豆和绍兴黄酒等。'
                            },
                            {
                                'time': '下午',
                                'location': '东湖景区',
                                'description': '午后阳光明媚，适宜在户外活动，东湖是理想的游览地点，可以乘乌篷船欣赏湖光山色。'
                            },
                            {
                                'time': '傍晚',
                                'location': '会稽山风景度假区',
                                'description': '若时间允许，可在傍晚前前往会稽山，虽然当天不适合看日落，但可以在多云的傍晚感受山间静谧氛围。'
                            },
                            {
                                'time': '晚上',
                                'location': '安昌古镇',
                                'description': '晚上入住安昌古镇内客栈，感受古镇夜景，体验当地生活气息，并为第二天早上游览古镇预留充足时间。'
                            }
                        ]
                    },
                    {
                        'date': '第2天',
                        'day_weather': '阴转小雨',
                        'night_weather': '晴',
                        'schedule': [
                            {
                                'time': '上午',
                                'location': '安昌古镇',
                                'description': '清晨游览古镇，欣赏雨后朦胧的江南水乡风貌，享受当地特色的早餐。'
                            },
                            {
                                'time': '中午',
                                'location': '兰亭景区',
                                'description': '由于预计白天有小雨，选择室内或半开放型的兰亭景区是个不错的选择，可以参观王羲之书法文化，避雨同时沉浸于艺术气息中。'
                            },
                            {
                                'time': '下午',
                                'location': '大禹陵',
                                'description': '如果雨势不大，可以考虑游览大禹陵，雨中的自然景观别有一番风味，带上雨具爬山或在景区内漫步，呼吸清新空气。'
                            },
                            {
                                'time': '傍晚',
                                'location': '书圣故里',
                                'description': '傍晚时分，若天气好转，可以去书圣故里，观赏文笔塔并登高远眺，体验绍兴城市风光。'
                            },
                            {
                                'time': '晚上',
                                'location': '绍兴古城',
                                'description': '鉴于晚上天气预报转晴，可以选择夜游绍兴古城，逛逛历史街区，体验古城墙、古桥及河两岸的夜景灯光秀。'
                            }
                        ]
                    }
                ]
            }
        },
        {
            'city': '北京',
            'duration': '2天',
            'weathers': [{'day_weather': '大雨', 'night_weather': '多云'}, {'day_weather': '小雨', 'night_weather': '晴'}],
            'trip_advise': {
                'city': '北京',
                'days': [
                    {
                        'date': '第1天',
                        'day_weather': '大雨',
                        'night_weather': '多云',
                        'schedule': [
                            {
                                'time': '上午',
                                'location': '国家博物馆',
                                'description': '鉴于全天大部分时间有雨，首日上午安排参观中国国家博物馆，这里丰富的馆藏和室内环境适合在雨天游览。'
                            },
                            {
                                'time': '中午',
                                'location': '王府井步行街',
                                'description': '在附近著名的王府井步行街享用午餐，并可在此购买一些北京特色小吃或纪念品。'
                            },
                            {
                                'time': '下午',
                                'location': '故宫博物院',
                                'description': '尽管当天有雨，但故宫内部游览不受影响。由于下雨可能减少室外游客数量，此时游览故宫可以避开部分人流，体验更佳。请提前通过网络预订门票，避免现场排队。'
                            },
                            {
                                'time': '傍晚',
                                'location': '南锣鼓巷',
                                'description': '若傍晚时分雨势减弱至多云，可以选择前往南锣鼓巷或后海地区，体验老北京胡同文化，同时可以在酒吧、茶馆或餐厅中稍作休息，等待夜幕降临。'
                            }
                        ]
                    },
                    {
                        'date': '第2天',
                        'day_weather': '小雨',
                        'night_weather': '晴',
                        'schedule': [
                            {
                                'time': '上午',
                                'location': '798艺术区',
                                'description': '上午安排去798艺术区，这里的室内艺术展览和创意店铺可以提供充足的避雨空间，且小雨天气下的艺术区别有一番韵味。'
                            },
                            {
                                'time': '中午',
                                'location': '三里屯商圈',
                                'description': '前往三里屯商圈，在那里找一家餐厅享用午餐，同时享受现代都市的繁华氛围。'
                            },
                            {
                                'time': '下午',
                                'location': '颐和园',
                                'description': '根据天气预报，下午可能会有小雨，可以选择在颐和园内乘坐游船观赏昆明湖及佛香阁等主要景观，即便下雨也能在长廊等遮蔽处欣赏园林美景。'
                            },
                            {
                                'time': '晚上',
                                'location': '奥林匹克公园',
                                'description': '考虑到晚上的天气会转晴，可在傍晚时分前往奥林匹克公园，参观鸟巢和水立方的夜景。如果时间允许，还可以在晴朗的夜晚观赏一场灯光秀表演。'
                            }
                        ]
                    }
                ]
            }
        }
    ]
)

class TripAdvisor(object):
    def get_trip_brief(self, trip):
        city = '目的地:' + trip['city']
        duration = '\n旅游天数:' + trip['duration']
        weather = '\n天气情况:'
        for i, w in enumerate(trip['weathers']):
            weather += f'第{i+1}天'
            day_weather, night_weather = w['day_weather'], w['night_weather']
            weather += f'白天{day_weather}, 晚上{night_weather}。'
        return city + duration + weather

    def create_prompt(self, trip):
        prompt = TRIP_ADVISE_PROMPT.instruction
        if TRIP_ADVISE_PROMPT.examples:
            prompt += '\n以下是根据出行信息制定旅游攻略的示例。'
            for i, example in enumerate(TRIP_ADVISE_PROMPT.examples):
                prompt += f'\n示例{i+1}:'
                example_brief = self.get_trip_brief(example)
                example_advise = json.dumps(
                    example['trip_advise'], ensure_ascii=False).encode('utf8').decode()
                prompt += f'\n出行信息如下:\n{example_brief}\n旅游攻略如下:\n{example_advise}'
        prompt += '\n请你根据以下出行信息制定旅游攻略:'
        prompt += '\n' + self.get_trip_brief(trip)
        return prompt

class QwenTripAdvisor(TripAdvisor):
    def __init__(self, model_name):
        self.model_name = model_name  # e.g. qwen-max, qwen-max-longcontext

    def generate_advise(self, trip):
        advise = ''
        prompt = self.create_prompt(trip)
        try:
            response = dashscope.Generation.call(
                model=self.model_name,
                prompt=prompt
            )
            if response.status_code == HTTPStatus.OK:
                logger.info(
                    'Qwen output: {}, usage info: {}'.format(
                        response.output, response.usage)
                )
                advise = json.loads(response.output['text'])
            else:
                logger.error(
                    'Qwen request failed. Request id: {}, status code: {},'
                    ' error code: {}, error message: {}'.format(
                        response.request_id, response.status_code,
                        response.code, response.message)
                )
        except Exception as e:
            logger.error('Qwen generation failed: {}'.format(e))

        return advise


# -*- coding: utf-8 -*-

import json
import scrapy
import re

class WeathernewsSpider(scrapy.Spider):
    name = 'WeatherNews'
    allowed_domains = ['weathernews.jp']
    obs_texts = ['', 'つぼみ', 'ピンクのつぼみ', '一輪開花', 'ちらほら咲いた', 'けっこう咲いた', '満開間近', '満開', '散り始め', '葉桜']

    def start_requests(self):
        areas = [
            {'name': '東京', 'url': 'https://weathernews.jp/s/sakura/area/tokyo.html'},
            {'name': '栃木', 'url': 'https://weathernews.jp/s/sakura/area/tochigi.html'},
            {'name': '山梨', 'url': 'https://weathernews.jp/s/sakura/area/yamanashi.html'},
            {'name': '埼玉', 'url': 'https://weathernews.jp/s/sakura/area/saitama.html'},
            {'name': '福島', 'url': 'https://weathernews.jp/s/sakura/area/fukushima.html'},
            {'name': '宮城', 'url': 'https://weathernews.jp/s/sakura/area/miyagi.html'}, # 仙台
            {'name': '長野', 'url': 'https://weathernews.jp/s/sakura/area/nagano.html'},
            {'name': '石川', 'url': 'https://weathernews.jp/s/sakura/area/ishikawa.html'}, # 金澤
            {'name': '富山', 'url': 'https://weathernews.jp/s/sakura/area/toyama.html'}
        ]

        for area in areas:
            request = scrapy.Request(url=area['url'], callback=self.parse_area)
            request.meta['area'] = area['name']

            yield request

    def parse_area(self, response):
        for spot in response.css('ul.result-list > li'):
            url = spot.css('a::attr(href)').extract_first()
            url = response.urljoin(url)

            request = scrapy.Request(url=url, callback=self.parse_spot)
            request.meta['area'] = response.meta['area']

            yield request

    def parse_spot(self, response):
        def extract_with_css(query):
            s = response.css(query).extract_first()
            if s:
                return s.strip()
            else:
                return ''

        m = re.search(r'sakura/spot/(\d+)/index.html', response.url)
        sid = m.group(1)
        url = 'https://weathernews.jp/ip/sakura/obs/meisyo.cgi?p=%s' % sid

        request = scrapy.Request(url=url, callback=self.parse_spot_date)
        request.meta['area'] = response.meta['area']
        request.meta['title'] = extract_with_css('div.titSpot > h3::text')
        request.meta['scale'] = extract_with_css('dd#honsuu::text')
        request.meta['kind'] = extract_with_css('dd#kind::text')
        request.meta['intro'] = extract_with_css('div#midokoro::text')
        request.meta['map'] = extract_with_css('a#map::attr(href)')
        request.meta['homepage'] = extract_with_css('a#homepage::attr(href)')
        request.meta['url'] = response.url

        yield request

    def parse_spot_date(self, response):
        resp = json.loads(response.body_as_unicode())

        data = {}
        data['區域'] = response.meta['area']
        data['地點'] = response.meta['title']
        data['規模'] = response.meta['scale']
        data['種類'] = response.meta['kind']
        data['介紹'] = response.meta['intro']
        data['地圖'] = response.meta['map']
        data['官網'] = response.meta['homepage']
        data['預測網址'] = response.meta['url']
        data['取材日'] = resp['obsday']
        data['開花'] = resp['kaika']
        data['五分咲き'] = resp['gobu']
        data['満開'] = resp['mankai']
        data['桜吹雪'] = resp['fubuki']
        data['狀態'] = self.obs_texts[int(resp['obsrank'])]

        yield data

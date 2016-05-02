#!/usr/bin/env python
# coding=utf-8

import scrapy
import demjson
from SpiderGanji.items import SpiderganjiItem
from SpiderGanji.spiders.startURL import startURL

class ershoufangGanji(scrapy.Spider):
    name = 'ershoufangGanji' 
    allowed_domains = ['ganji.com']
    start_urls = startURL.ershoufangURL

    def parse(self, response):
        house_page_query = '//body/div/div/div/ul/li/div/div/a[@class="list-info-title js-title"]'
        house_page_root = response.request.url.split('/')[2]
        for info in response.xpath(house_page_query):
            house_page_href = info.xpath('attribute::href').extract()[0]
            house_page_url = 'http://'+ house_page_root + house_page_href
            house_page_log = info.xpath('attribute::gjalog_fang').extract()[0]
            temp_time = house_page_log.split('@')[2]
            housePublishedTiem = temp_time.split('=')[1]
            yield scrapy.Request(house_page_url,callback=self.parse_house_page,meta={"time":housePublishedTiem})

    def parse_house_page(self,response):
        item = SpiderganjiItem()
        item['housePublishedTime'] = response.request.meta['time']
        item['houseTitle'] = response.xpath('//html/head/title/text()').extract()[0]
        item['houseCity'] = item['houseCity'] = response.xpath('//head/meta[@name="location"]/attribute::content').extract()[0].split(';')[1].split('=')[1]

        #此XPath节点可以获得房屋的所有基本信息
        house_info_query = '//body/div/div/div/div/div/div/ul[@class="basic-info-ul"]'

        price_query = 'li/b[@class="basic-info-price"]/text()'
        item['housePrice'] = response.xpath(house_info_query).xpath(price_query).extract()[0]

        area_query = 'li[3]/text()'
        temp_area = response.xpath(house_info_query).xpath(area_query).extract()[0]
        item['houseArea'] = temp_area.split('-')[1][:-1]

        #此处匹配房屋所在小区名
        #如果匹配不到就赋值为空，为什么呢？
        #因为有些页面的确没有显示对应的小区。
        #不要改变判断的顺序，如果html中有特殊符号插入就会导致匹配错误
        name_query_2 = 'li[6]/a/text()'
        name_query_3 = 'li[6]/text()'
        name_query = 'li[6]/span[2]/attribute::title'
        if response.xpath(house_info_query).xpath(name_query).extract_first():
            item['houseName'] = response.xpath(house_info_query).xpath(name_query).extract()[0]
        elif response.xpath(house_info_query).xpath(name_query_2).extract_first():
            item['houseName'] = response.xpath(house_info_query).xpath(name_query_2).extract()[0].strip().lstrip().rstrip()
        elif response.xpath(house_info_query).xpath(name_query_3).extract_first():
            item['houseName'] = response.xpath(house_info_query).xpath(name_query_3).extract()[0].strip().lstrip().rstrip()
        else:
            item['houseName'] = ''

        #此处匹配房屋地址
        #有些页面有地址，有些页面只有小区。
        #所以首先以地址为第一匹配，如果没有匹配成功则换为小区区域。
        address_query = 'li[8]/span[@title]/text()'
        if response.xpath(house_info_query).xpath(address_query).extract():
            item['houseAddress'] = response.xpath(house_info_query).xpath(address_query).extract()[0]
        else:
            district_query = 'li[7]/a/text()'
            temp_district = response.xpath(house_info_query).xpath(district_query).extract()
            houseDistrict = ''
            #注意此处可能也匹配不到小区区域
            if temp_district:
                for dist in temp_district:
                    houseDistrict = houseDistrict + '-' + dist
                item['houseAddress'] = houseDistrict.lstrip('-')
            else:
                item['houseAddress'] = ''

        #此XPath节点匹配经纬度信息
        position_query = '//body/div/div/div/div/div/div[@id="map_load"]'
        house_position = response.xpath(position_query)
        house_position_1 = house_position.xpath('attribute::data-ref').extract()
        if house_position_1:
            house_position_json = demjson.decode(house_position_1[0])
            house_position_split = house_position_json['lnglat'].split(',')

            item['houseBaiduLongitude'] = house_position_split[0][1:-1]
            item['houseBaiduLatitude'] = house_position_split[1]
        else:
            item['houseBaiduLongitude'] = ''
            item['houseBaiduLatitude'] = ''



        yield item
        

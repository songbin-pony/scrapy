from urllib import parse
import scrapy
from scrapy.loader.processors import MapCompose, Join
from scrapy.loader import ItemLoader
from scrapy.http import Request
from basic.items import PropertiesItem
from basic.functions import mysql


class BasicSpider(scrapy.Spider):
    name = "pony"
    allowed_domains = ["you.ctrip.com"]

    # Start on the first index page
    start_urls = (
        'https://you.ctrip.com/sitemap/spotdis/c0',
    )


    def parse(self, response):
        # Get the next index URLs and yield Requests
        next_selector = response.xpath('//*[@class="sitemap_block"]')
        if len(next_selector)!=0 :
            for item in next_selector:
                province=MapCompose(str.strip)(item.xpath('div/h2/text()').extract())[0]
                # self.log(province)
                second_selector=item.xpath('ul/li')
                for item_second in second_selector:
                    municipal_scenery_name=MapCompose(str.strip)(item_second.xpath('a/text()').extract())[0]
                    municipal_scenery_link=item_second.xpath('a/@href')[0].extract()
                    yield Request(parse.urljoin(response.url,municipal_scenery_link),callback=self.parse,meta={'province':province,'municipal_scenery_name':municipal_scenery_name})

        page_selector=response.xpath('//div[@class="list_mod2"]')
        if len(page_selector)!=0:
            province=response.meta['province']
            municipal_scenery_name=response.meta['municipal_scenery_name']
            for item_page in page_selector:
                # 风景的属性
                name=item_page.xpath('*//a[@title]/text()').extract()[0]
                rank=item_page.xpath('*//s/text()').extract()[0][1:-1]
                addr=MapCompose(str.strip)(item_page.xpath('*//*[@class="ellipsis"]/text()').extract())[0]
                score=item_page.xpath('*//a[@class="score"]/strong/text()').extract()[0]
                small_image_link=item_page.xpath('*//img/@src').extract()[0]
                detail_link=item_page.xpath('*[@class="leftimg"]/a/@href').extract()[0]
                # 现在将这些数据传过去，然后再另一个函数中写入数据库
                yield Request(parse.urljoin(response.url,detail_link),callback=self.parse_item,meta={'province':province,'municipal_scenery_name':municipal_scenery_name,'name':name,'rank':rank,'addr':addr,'score':score,'small_image_link':small_image_link,'detail_link':detail_link})

        # # 现在写跳转页面
        if len(response.xpath('//*[@class="nextpage"]/@href'))!=0:
            temp=response.xpath('//*[@class="rdetailbox"]')[-1]
            province=response.meta['province']
            municipal_scenery_name=response.meta['municipal_scenery_name']
            next_page_url=response.xpath('//a[@class="nextpage"]/@href').extract()[0]
            if len(temp.xpath('*//s/text()').extract())==1:
                yield Request(parse.urljoin(response.url,next_page_url),callback=self.parse,meta={'province':province,'municipal_scenery_name':municipal_scenery_name})




    def parse_item(self,response):
        province=response.meta['province']
        municipal_scenery_name=response.meta['municipal_scenery_name']
        name=response.meta['name']
        rank=int(response.meta['rank'])
        addr=response.meta['addr']
        score=response.meta['score']
        small_image_link=response.meta['small_image_link']
        detail_link=response.meta['detail_link']
        big_image_link=response.xpath('//img[@width="350"]/@src').extract()[0]
        self.log(province+municipal_scenery_name+name+str(rank)+addr+score+small_image_link+detail_link+big_image_link)
        temp=response.xpath('//div[contains(@class,"bright_spot")]//li/text()').extract()
        if len(temp)==0:
            bright_spot=''
        else:
            bright_spot=response.xpath('//div[contains(@class,"bright_spot")]//li/text()').extract()[0]
        sql="INSERT INTO table_2 (name,rank,addr,score,province,scenery_name,small_image_link,big_image_link,detail_link,bright_spot) VALUES ('{0}','{1}','{2}','{3}','{4}','{5}','{6}','{7}','{8}','{9}')".format(name,rank,addr,score,province,municipal_scenery_name,small_image_link,big_image_link,detail_link,bright_spot)
        mysql(sql)
        # self.log(big_image_link)
        # self.log(name+rank+addr+score+small_image_link)
        # self.log(float(score))

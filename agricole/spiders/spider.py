import re
import scrapy
from scrapy.loader import ItemLoader
from ..items import AgricoleItem
from itemloaders.processors import TakeFirst
import requests
import json
from scrapy import Selector
pattern = r'(\xa0)?'


url = "https://www.ca-cib.com/node/1333/ajax/news/getList?page={}&_wrapper_format=drupal_ajax"

payload="js=true&_drupal_ajax=1&ajax_page_state%5Btheme%5D=ca_cib&ajax_page_state%5Btheme_token%5D=&ajax_page_state%5Blibraries%5D=ca_cib%2Fglobal-assets%2Ccacib%2Ftwitter-widget%2Ccore%2Fdrupal.ajax%2Ccore%2Fhtml5shiv%2Ccore%2Fpicturefill%2Csystem%2Fbase%2Cviews%2Fviews.module"
headers = {
  'Connection': 'keep-alive',
  'Pragma': 'no-cache',
  'Cache-Control': 'no-cache',
  'sec-ch-ua': '"Chromium";v="88", "Google Chrome";v="88", ";Not A Brand";v="99"',
  'Accept': 'application/json, text/javascript, */*; q=0.01',
  'X-Requested-With': 'XMLHttpRequest',
  'sec-ch-ua-mobile': '?0',
  'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36',
  'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
  'Origin': 'https://www.ca-cib.com',
  'Sec-Fetch-Site': 'same-origin',
  'Sec-Fetch-Mode': 'cors',
  'Sec-Fetch-Dest': 'empty',
  'Referer': 'https://www.ca-cib.com/pressroom/news',
  'Accept-Language': 'en-US,en;q=0.9',
  'Cookie': '__utma=183314484.1796158292.1615794152.1615794152.1615794152.1; __utmc=183314484; __utmz=183314484.1615794152.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); cookieconsent_status=dismiss; __utmb=183314484.9.10.1615794152'
}


class AgricoleSpider(scrapy.Spider):
	name = 'agricole'
	page = 0
	start_urls = ['https://www.ca-cib.com/pressroom/news']

	def parse(self, response):
		data = requests.request("POST", url.format(self.page), headers=headers, data=payload)
		data = json.loads(data.text)
		container = data[0]['data']
		articles = Selector(text=container).xpath('//a[@class="news-tile"]')

		for article in articles:
			date = article.xpath('.//time//text()').get()
			link = article.xpath('.//@href').get()
			yield response.follow(link, self.parse_post, cb_kwargs=dict(date=date))

		if data[1]['command'] == "insert":
			self.page += 1
			yield response.follow(url.format(self.page),self.parse)

	def parse_post(self, response,date):
		title = response.xpath('//h1/text()').get()
		content = response.xpath('//div[@class="body-introduction"]//text()').getall() + response.xpath('//div[@class="body-description"]//text()').getall()
		content = [p.strip() for p in content if p.strip()]
		content = re.sub(pattern, "",' '.join(content))

		item = ItemLoader(item=AgricoleItem(), response=response)
		item.default_output_processor = TakeFirst()

		item.add_value('title', title)
		item.add_value('link', response.url)
		item.add_value('content', content)
		item.add_value('date', date)

		yield item.load_item()

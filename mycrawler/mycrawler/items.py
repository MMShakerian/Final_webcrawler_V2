# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class PageItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    status = scrapy.Field()
    parent_url = scrapy.Field()
    external = scrapy.Field()
    depth = scrapy.Field()

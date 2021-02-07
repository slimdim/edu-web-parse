# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class GbParseItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class HeadHunterVacancyItem(scrapy.Item):
    _id = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    salary = scrapy.Field()
    description = scrapy.Field()
    skills = scrapy.Field()
    author_url = scrapy.Field()


class HeadHunterAuthorItem(scrapy.Item):
    _id = scrapy.Field()
    url = scrapy.Field()
    name = scrapy.Field()
    area = scrapy.Field()
    description = scrapy.Field()
    author_url = scrapy.Field()


class InstagramItem(scrapy.Item):
    _id = scrapy.Field()
    data = scrapy.Field()
    date_parse = scrapy.Field()
    allow_following = scrapy.Field()
    image_urls = scrapy.Field()


class InstagramTagItem(InstagramItem):
    pass


class InstagramTagPostItem(InstagramItem):
    pass


class InstagramUser(InstagramItem):
    pass


class InstagramFollow(scrapy.Item):
    _id = scrapy.Field()
    date_parse = scrapy.Field()
    user_name = scrapy.Field()
    user_id = scrapy.Field()
    follow_type = scrapy.Field()
    follow_name = scrapy.Field()
    follow_id = scrapy.Field()

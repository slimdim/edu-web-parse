from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from gb_parse.spiders.autoyoula import AutoyoulaSpider
import dotenv
import pymongo as pm
import os

if __name__ == '__main__':
    pymongo_db = pm.MongoClient(os.getenv('MONGO_DB'))['gb_parse_01']
    crawler_settings = Settings()
    crawler_settings.setmodule('gb_parse.settings')
    crawler_process = CrawlerProcess(settings=crawler_settings)
    crawler_process.crawl(AutoyoulaSpider,
                          pymongo_db=pymongo_db)
    crawler_process.start()

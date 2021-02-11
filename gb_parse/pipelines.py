# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import os
import pymongo
from scrapy import Request
from scrapy.pipelines.images import ImagesPipeline


class MongoSavePipeline:
    def __init__(self):
        self.db_client = pymongo.MongoClient(os.getenv("MONGO_DB"))

    def process_item(self, item, spider):
        db = self.db_client["gb_parse_handshake"]
        collection = db[type(item).__name__]
        collection.insert_one(item)
        return item


class GbImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        for url in item.get('image_urls', []):
            try:
                yield Request(url)
            except Exception as e:
                print(e)

    def item_completed(self, results, item, info):
        if item.get('image_urls'):
            item['image_urls'] = [itm[1] for itm in results if itm[0]]
        return item

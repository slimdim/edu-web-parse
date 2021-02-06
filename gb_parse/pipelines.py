# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import os
import pymongo


class MongoSavePipeline:
    def __init__(self):
        self.db_client = pymongo.MongoClient(os.getenv("MONGO_DB"))

    def process_item(self, item, spider):
        db = self.db_client["gb_parse_hh"]
        collection = db[(type(item).__name__).split('Item')[0]]
        collection.insert_one(item)
        return item


class GbParsePipeline:
    def process_item(self, item, spider):
        return item

from urllib.parse import urljoin
from scrapy.loader import ItemLoader
from itemloaders.processors import Join, TakeFirst, MapCompose
from .items import HeadHunterVacancyItem, HeadHunterAuthorItem


def clean_string(item: str):
    return item.replace('\xa0', ' ').replace('\r\n', '')


def get_author_url(item):
    return urljoin('https://hh.ru/', item)


class HeadHunterVacancyLoader(ItemLoader):
    default_item_class = HeadHunterVacancyItem
    author_url_in = MapCompose(get_author_url)
    author_url_out = TakeFirst()
    title_out = TakeFirst()
    url_out = TakeFirst()
    description_out = Join(separator='')
    salary_in = MapCompose(clean_string)
    salary_out = Join(separator='')


class HeadHunterAuthorLoader(ItemLoader):
    default_item_class = HeadHunterAuthorItem
    author_url_out = TakeFirst()
    name_in = MapCompose(clean_string)
    name_out = Join(separator='')
    url_out = TakeFirst()
    description_in = MapCompose(clean_string)
    description_out = Join(separator='')

import requests
import bs4
import datetime
import pymongo
from urllib.parse import urljoin


class ParseMagnit:
    def __init__(self, start_url, pymongo_db):
        self.start_url = start_url
        self.pymongo_db = pymongo_db

    def __get_soup(self, url) -> bs4.BeautifulSoup:
        response = requests.get(url)
        return bs4.BeautifulSoup(response.text, "lxml")

    def run(self):
        for product in self.parse():
            self.save(product)

    def parse(self):
        soup = self.__get_soup(self.start_url)
        catalogue_main = soup.find('div', attrs={'class': 'сatalogue__main'})
        for product_tag in catalogue_main.find_all('a', recursive=False):
            try:
                yield self.product_parse(product_tag)
            except AttributeError:
                pass

    def product_parse(self, product: bs4.Tag) -> dict:
        product = {
            'url': urljoin(self.start_url, product.get('href')),
            'promo_name': self.find_or_skip_class_value(product, 'card-sale__header'),
            'product_name': self.find_or_skip_class_value(product, 'card-sale__title'),
            'old_price': self.magnit_price_to_float(self.find_or_skip_class_value(product, 'label__price_old')),
            'new_price': self.magnit_price_to_float(self.find_or_skip_class_value(product, 'label__price_new')),
            'image_url': urljoin(self.start_url, product.find("img").attrs.get("data-src")),
            'date_from': self.find_start_end_date(self.find_or_skip_class_value(product, 'card-sale__date')),
            'date_to': self.find_start_end_date(self.find_or_skip_class_value(product, 'card-sale__date'),
                                                start_date=False)
        }
        return {k: v for k, v in product.items() if v is not None}

    @staticmethod
    def find_or_skip_class_value(product: bs4.Tag, class_name: str):
        try:
            return product.find('div', attrs={'class': class_name}).text
        except AttributeError:
            return None

    @staticmethod
    def magnit_price_to_float(magnit_price):
        if magnit_price:
            try:
                return float((magnit_price.strip('\n')).replace('\n', '.'))
            except ValueError:
                return None
        else:
            return None

    @staticmethod
    def find_start_end_date(str_date, start_date=True) -> datetime.datetime:
        months = {"янв": 1, "фев": 2, "мар": 3, "апр": 4, "май": 5, "мая": 5, "июн": 6,
                  "июл": 7, "авг": 8, "сен": 9, "окт": 10, "ноя": 11, "дек": 12}
        result_date = []
        str_date_list = str_date.strip('\n').split('\n')
        for str_date in str_date_list:
            temp = str_date.split()
            result_date.append(datetime.datetime(year=datetime.datetime.now().year,
                                                 month=months[temp[2][:3]],
                                                 day=int(temp[1])))
        if start_date:
            return result_date[0]
        else:
            return result_date[1]

    def save(self, data):
        collection = self.pymongo_db['magnit']
        collection.insert_one(data)
        print(f'Object {data.get("product_name")} was saved')


if __name__ == "__main__":
    database = pymongo.MongoClient('mongodb://localhost:27017')['gb_parse_01']
    parser = ParseMagnit("https://magnit.ru/promo/?geo=moskva", database)
    parser.run()

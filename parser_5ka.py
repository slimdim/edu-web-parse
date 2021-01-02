import requests
import time
import json
from pathlib import Path


class StatusCodeError(Exception):
    def __init__(self, txt):
        self.txt = txt


class Parser:
    params = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
    }

    def __init__(self, start_url, category_url):
        self.start_url = start_url
        self.category_url = category_url

    def _get_response(self, url, **kwargs):
        while True:
            try:
                response = requests.get(url, **kwargs)
                if response.status_code != 200:
                    raise StatusCodeError(f'status {response.status_code}')
                return response
            except (requests.exceptions.ConnectTimeout, StatusCodeError):
                time.sleep(0.1)

    def run(self):
        for category in self.get_categories(self.category_url):
            file_path = Path(__file__).parent.joinpath(f'{category["parent_group_code"]}.json')
            data = {
                'parent_group_code': category['parent_group_code'],
                'parent_group_name': category['parent_group_name'],
                'products': [],
            }

            self.params['categories'] = category['parent_group_code']

            for products in self.parse(self.start_url):
                data['products'].extend(products)
            self.save_file(file_path, data)

    def parse(self, url):
        while url:
            response = self._get_response(url, params=self.params, headers=self.headers)
            data: dict = response.json()
            url = data['next']
            yield data.get('results', [])

    def get_categories(self, url):
        response = requests.get(url, headers=self.headers)
        return response.json()

    def save_file(self, file_path: Path, data: dict):
        with open(file_path, 'w', encoding='UTF-8') as file:
            json.dump(data, file, ensure_ascii=False)


if __name__ == '__main__':
    parser = Parser('https://5ka.ru/api/v2/special_offers/', 'https://5ka.ru/api/v2/categories/')
    parser.run()

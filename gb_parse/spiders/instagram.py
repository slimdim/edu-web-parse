import scrapy
import json
import datetime
from ..items import InstagramTagItem, InstagramTagPostItem


class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['www.instagram.com']
    start_urls = ['https://www.instagram.com/']
    login_url = 'https://www.instagram.com/accounts/login/ajax/'
    api_url = '/graphql/query/'
    query_hash = {
        'tag_posts': "9b498c08113f1e09617a1703c22b2f32",
    }

    def __init__(self, login, enc_password, tag_list, *args, **kwargs):
        self.tag_list = tag_list
        self.login = login
        self.enc_passwd = enc_password
        super().__init__(*args, **kwargs)

    def parse(self, response, **kwargs):
        try:
            js_data = self.js_data_extract(response)
            yield scrapy.FormRequest(
                self.login_url,
                method='POST',
                callback=self.parse,
                formdata={
                    'username': self.login,
                    'enc_password': self.enc_passwd,
                },
                headers={'x-CSRFToken': js_data['config']['csrf_token']}
            )
        except AttributeError:
            if response.json().get('authenticated'):
                for tag in self.tag_list:
                    tag_page = response.urljoin(f'/explore/tags/{tag}/')
                    yield scrapy.Request(tag_page, callback=self.tag_parse)

    def tag_parse(self, response):
        json_response = self.js_data_extract(response)
        tag = json_response['entry_data']['TagPage'][0]['graphql']['hashtag']
        item_tag = InstagramTagItem(
            date_parse=datetime.datetime.now(),
            data={
                'id': tag['id'],
                'name': tag['name'],
                'allow_following': tag['allow_following']
            },
            image_urls=[tag['profile_pic_url']]
        )
        yield item_tag
        yield from self.get_tag_posts(tag, response)

    def get_tag_posts(self, tag, response):
        if tag['edge_hashtag_to_media']['page_info']['has_next_page']:
            variables = {
                'tag_name': tag['name'],
                'first': 100,
                'after': tag['edge_hashtag_to_media']['page_info']['end_cursor'],
            }
            url = f'{self.api_url}?query_hash={self.query_hash["tag_posts"]}&variables={json.dumps(variables)}'
            yield response.follow(
                url,
                callback=self.tag_api_parse,
            )

        yield from self.get_post_item(tag['edge_hashtag_to_media']['edges'])

    def tag_api_parse(self, response):
        tag_api = self.js_data_extract(response)
        yield from self.get_tag_posts(tag_api['data']['hashtag'], response)

    @staticmethod
    def get_post_item(edges):
        for node in edges:
            yield InstagramTagPostItem(
                date_parse=datetime.datetime.utcnow(),
                data=node['node'],
                image_urls=[node['node']['thumbnail_src']]
            )

    @staticmethod
    def js_data_extract(response):
        script = response.xpath('//script[contains(text(), "window._sharedData =")]/text()').get()
        return json.loads(script.replace("window._sharedData =", '')[:-1])
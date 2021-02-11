import scrapy
import json
import datetime
from ..items import InstagramTagItem, InstagramTagPostItem, InstagramUser, InstagramFollow


class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['www.instagram.com']
    start_urls = ['https://www.instagram.com/']
    login_url = 'https://www.instagram.com/accounts/login/ajax/'
    api_url = '/graphql/query/'
    query_hash = {
        'tag_posts': "9b498c08113f1e09617a1703c22b2f32",
        'following': 'd04b0a864b4b54837c0d870b0e77e076',
        'followed': 'c76146de99bb02f6415203be841dd25a'
    }

    def __init__(self, login, enc_password, user_list=None, tag_list=None, *args, **kwargs):
        self.tag_list = tag_list
        self.user_list = user_list
        self.login = login
        self.enc_password = enc_password
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
                    'enc_password': self.enc_password,
                },
                headers={'x-CSRFToken': js_data['config']['csrf_token']}
            )
        except AttributeError:
            if response.json().get('authenticated'):
                if self.tag_list:
                    for tag in self.tag_list:
                        tag_page = response.urljoin(f'/explore/tags/{tag}/')
                        yield scrapy.Request(tag_page, callback=self.tag_parse)
                if self.user_list:
                    for user in self.user_list:
                        yield response.follow(f'/{user}', callback=self.user_parse)

    def user_parse(self, response):
        user_data = self.js_data_extract(response)['entry_data']['ProfilePage'][0]['graphql']['user']
        yield InstagramUser(
            date_parse=datetime.datetime.utcnow(),
            data=user_data
        )

        yield from self.get_follow_request(response, user_data)

    def get_follow_request(self, response, user_data, follow_query=None):
        if not follow_query:
            follow_query = {
                'id': user_data['id'],
                'first': 2,
            }

        url = f'/graphql/query/?query_hash={self.query_hash["followed"]}&variables={json.dumps(follow_query)}'
        yield response.follow(
            url,
            callback=self.get_api_followed,
            cb_kwargs={'user_data': user_data})

        url = f'/graphql/query/?query_hash={self.query_hash["following"]}&variables={json.dumps(follow_query)}'
        yield response.follow(
            url,
            callback=self.get_api_follow,
            cb_kwargs={'user_data': user_data})

    def get_api_follow(self, response, user_data):
        data = response.json()
        follow_type = 'following'
        yield from self.get_follow_item(user_data,
                                        data['data']['user']['edge_follow']['edges'],
                                        follow_type)
        if data['data']['user']['edge_follow']['page_info']['has_next_page']:
            follow_query = {
                'id': user_data['id'],
                'first': 100,
                'after': data['data']['user']['edge_follow']['page_info']['end_cursor'],
            }
            yield from self.get_follow_request(response, user_data, follow_query)

    def get_api_followed(self, response, user_data):
        data = response.json()
        follow_type = 'followed'
        yield from self.get_follow_item(user_data,
                                        data['data']['user']['edge_followed_by']['edges'],
                                        follow_type)
        if data['data']['user']['edge_followed_by']['page_info']['has_next_page']:
            follow_query = {
                'id': user_data['id'],
                'first': 100,
                'after': data['data']['user']['edge_followed_by']['page_info']['end_cursor'],
            }
            yield from self.get_follow_request(response, user_data, follow_query)

    def get_follow_item(self, user_data, follow_users_data, follow_type):
        for user in follow_users_data:
            if follow_type == 'followed':
                yield InstagramFollow(
                    user_id=user_data['id'],
                    user_name=user_data['username'],
                    follow_type='followed_by',
                    follow_id=user['node']['id'],
                    follow_name=user['node']['username']
                )
            else:
                yield InstagramFollow(
                    user_id=user_data['id'],
                    user_name=user_data['username'],
                    follow_type='following',
                    follow_id=user['node']['id'],
                    follow_name=user['node']['username']
                )
            yield InstagramUser(
                date_parse=datetime.datetime.utcnow(),
                data=user['node']
            )

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

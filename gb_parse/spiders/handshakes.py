import scrapy
import json
from scrapy.exceptions import CloseSpider
from ..items import InstagramFollow


class HandshakesSpider(scrapy.Spider):
    name = 'handshakes'
    allowed_domains = ['www.instagram.com']
    start_urls = ['http://www.instagram.com/']
    login_url = 'https://www.instagram.com/accounts/login/ajax/'
    query_hash = {
        'following': 'd04b0a864b4b54837c0d870b0e77e076',
        'followed': 'c76146de99bb02f6415203be841dd25a',
    }

    def __init__(self, login, enc_password, start_user, end_user, *args, **kwargs):
        self.login = login
        self.enc_password = enc_password
        self.start_user = start_user
        self.end_user = end_user
        self.mutual_friends_level_1 = []
        self.start_user_followed_by = []
        self.start_user_following = []
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
                yield response.follow(f'/{self.start_user}',
                                      callback=self.user_parse,
                                      meta={'level': 1, 'mutual': None})

    def user_parse(self, response):
        user_data = self.js_data_extract(response)['entry_data']['ProfilePage'][0]['graphql']['user']
        yield from self.get_follow_request(response, user_data)

    def get_follow_request(self, response, user_data):
        level = response.meta.get('level')
        mutual = response.meta.get('mutual')
        follow_query = response.meta.get('follow_query')
        if not follow_query:
            follow_query = {
                'id': user_data['id'],
                'first': 50,
            }

        url_followed = f'/graphql/query/?query_hash={self.query_hash["followed"]}&variables={json.dumps(follow_query)}'
        yield response.follow(
            url_followed,
            callback=self.get_api_followed,
            meta={'user_data': user_data, 'level': level, 'mutual_follower': mutual})

        url_following = f'/graphql/query/?query_hash={self.query_hash["following"]}&variables={json.dumps(follow_query)}'
        yield response.follow(
            url_following,
            callback=self.get_api_follow,
            meta={'user_data': user_data, 'level': level, 'mutual_follower': mutual})

    def get_api_followed(self, response):
        data = response.json()
        user_data = response.meta.get('user_data')
        follow_type = 'following'
        yield from self.get_follow_item(response,
                                        data['data']['user']['edge_followed_by']['edges'],
                                        follow_type)
        if data['data']['user']['edge_followed_by']['page_info']['has_next_page']:
            follow_query = {
                'id': user_data['id'],
                'first': 50,
                'after': data['data']['user']['edge_followed_by']['page_info']['end_cursor'],
            }
            response.meta['follow_query'] = follow_query
            yield from self.get_follow_request(response, user_data)

    def get_api_follow(self, response):
        data = response.json()
        user_data = response.meta.get('user_data')
        follow_type = 'followed'
        yield from self.get_follow_item(response,
                                        data['data']['user']['edge_follow']['edges'],
                                        follow_type)
        if data['data']['user']['edge_follow']['page_info']['has_next_page']:
            follow_query = {
                'id': user_data['id'],
                'first': 50,
                'after': data['data']['user']['edge_follow']['page_info']['end_cursor'],
            }
            response.meta['follow_query'] = follow_query
            yield from self.get_follow_request(response, user_data)

    def get_follow_item(self, response, follow_users_data, follow_type):
        user_data = response.meta.get('user_data')
        level = response.meta.get('level')
        mutual = response.meta.get('mutual')
        for user in follow_users_data:

            if follow_type == 'followed' and user['node']['is_private'] is False and user['node']['is_verified'] is False:
                yield InstagramFollow(
                    user_id=user_data['id'],
                    user_name=user_data['username'],
                    follow_type='followed_by',
                    follow_id=user['node']['id'],
                    follow_name=user['node']['username']
                )
                self.start_user_followed_by.append(user['node']['username'])
            elif follow_type == 'following' and user['node']['is_private'] is False and user['node']['is_verified'] is False:
                yield InstagramFollow(
                    user_id=user_data['id'],
                    user_name=user_data['username'],
                    follow_type='following',
                    follow_id=user['node']['id'],
                    follow_name=user['node']['username']
                )
                self.start_user_following.append(user['node']['username'])

        if len(self.start_user_followed_by) >= 1 and len(self.start_user_following) >= 1:
            self.mutual_friends_level_1 = list(set(self.start_user_followed_by) & set(self.start_user_following))
            if self.end_user in self.mutual_friends_level_1 and level == 1:
                print(f'Пользователь {self.start_user} и {self.end_user} подписаны друг на друга')
                raise CloseSpider('Matched!')

            elif self.end_user in self.mutual_friends_level_1 and level > 1:
                print(
                    f'Пользователь {self.start_user} и {self.end_user} знакомы друг с другом через пользователя '
                    f'{mutual}')
                raise CloseSpider('Matched')
            else:
                level = level + 1
                print(
                    f' Пользователи не подписаны друг на друга, анализ списка {self.mutual_friends_level_1}')
                for mutual_follower in self.mutual_friends_level_1:
                    mut_follower_url = 'http://www.instagram.com/' + mutual_follower
                    self.start_user_followed_by = []
                    self.start_user_following = []
                    yield response.follow(url=mut_follower_url,
                                          callback=self.user_parse,
                                          meta={'mutual_follower': mutual_follower, 'level': level})
        else:
            pass

    @staticmethod
    def js_data_extract(response):
        script = response.xpath('//script[contains(text(), "window._sharedData =")]/text()').get()
        return json.loads(script.replace("window._sharedData =", '')[:-1])

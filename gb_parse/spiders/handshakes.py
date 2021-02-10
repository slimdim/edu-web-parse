import scrapy
import json
import datetime


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
                yield response.follow(f'/{self.start_user}', callback=self.user_parse)

    def user_parse(self, response):
        pass

    @staticmethod
    def js_data_extract(response):
        script = response.xpath('//script[contains(text(), "window._sharedData =")]/text()').get()
        return json.loads(script.replace("window._sharedData =", '')[:-1])

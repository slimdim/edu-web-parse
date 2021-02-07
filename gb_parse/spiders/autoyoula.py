import scrapy
import re
from urllib.parse import urljoin
from urllib.parse import unquote


class AutoyoulaSpider(scrapy.Spider):
    name = 'autoyoula'
    allowed_domains = ['auto.youla.ru']
    start_urls = ['https://auto.youla.ru/']
    user_url = 'https://youla.ru/user/'

    css_query = {
        'brands': 'div.TransportMainFilters_block__3etab a.blackLink',
        'pagination': 'div.Paginator_block__2XAPy a.Paginator_button__u1e7D',
        'ads': 'div.SerpSnippet_titleWrapper__38bZM a.blackLink'
    }

    data_query = {
        'title': lambda resp: resp.css('div.AdvertCard_advertTitle__1S1Ak::text').get(),
        'price': lambda resp: float(resp.css('div.AdvertCard_price__3dDCr::text').get().replace('\u2009', '')),
        'description': lambda resp: resp.css('div.AdvertCard_descriptionInner__KnuRi::text').get(),
        'author_url': lambda resp: AutoyoulaSpider.get_author_url(resp),
        'images': lambda resp: resp.css('section.PhotoGallery_thumbnails__3-1Ob button::attr(style)').re(
            '(https?://[^\s]+)\)'),
        'specifications': lambda resp: AutoyoulaSpider.get_specifications(resp)
    }

    def __init__(self, pymongo_db, *args, **kwargs):
        self.pymongo_db = pymongo_db
        super().__init__(*args, **kwargs)

    def parse(self, response, **kwargs):
        brands_links = response.css(self.css_query['brands'])
        yield from self.gen_task(response, brands_links, self.brand_parse)

    def brand_parse(self, response):
        pagination_links = response.css(self.css_query['pagination'])
        yield from self.gen_task(response, pagination_links, self.brand_parse)
        ads_links = response.css(self.css_query['ads'])
        yield from self.gen_task(response, ads_links, self.ads_parse)

    def ads_parse(self, response):
        data = {}
        for key, selector in self.data_query.items():
            try:
                data[key] = selector(response)
            except (ValueError, AttributeError):
                continue
        self.save(data)

    def save(self, data):
        collection = self.pymongo_db['youla']
        collection.insert_one(data)
        print(f'Object {data.get("title")} was saved')

    @staticmethod
    def get_author_url(response):
        script = response.css('script') \
            .re_first(r'(?<=<script>window.transitState = decodeURIComponent\(").*(?="\);</script>)')
        encoded_script = unquote(script)
        user_id = re.search('youlaId","([0-9|a-zA-Z]+)","avatar', encoded_script)
        if user_id:
            return urljoin(AutoyoulaSpider.user_url, user_id.group(1))
        else:
            dealer_link = re.search('sellerLink","([\/a-zA-Z\-0-9]+)","type', encoded_script)
            if dealer_link:
                return urljoin(AutoyoulaSpider.start_urls[0], dealer_link.group(1))
            else:
                return None

    @staticmethod
    def get_specifications(response):
        data = {}
        spec_keys = response.css('div.AdvertCard_specs__2FEHc div.AdvertSpecs_data__xK2Qx::attr(data-target)')
        spec_values = response.css(
            'div.AdvertCard_specs__2FEHc div.AdvertSpecs_data__xK2Qx::text, div.AdvertCard_specs__2FEHc a::text')
        for key, value in zip(spec_keys, spec_values):
            data[key.get()] = value.get()
        return data

    @staticmethod
    def gen_task(response, link_list, callback):
        for link in link_list:
            yield response.follow(link.attrib['href'], callback=callback)

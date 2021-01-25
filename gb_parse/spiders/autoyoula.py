import scrapy
import re


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
        print(1)

    @staticmethod
    def get_author_url(response) -> str:
        script = response.css('script') \
            .re_first(r'(?<=<script>window.transitState = decodeURIComponent\(").*(?="\);</script>)')
        user_id = str(re.search('youlaId%22%2C%22([0-9|a-zA-Z]+)%22%2C%22avatar', script).group(1))
        return AutoyoulaSpider.user_url + user_id

    @staticmethod
    def get_specifications(response):
        data = {}
        spec_keys = response.css('div.AdvertCard_specs__2FEHc div.AdvertSpecs_label__2JHnS::text')
        spec_values = response.css('div.AdvertCard_specs__2FEHc div.AdvertSpecs_data__xK2Qx::text, div.AdvertCard_specs__2FEHc a::text')
        for key, value in zip(spec_keys, spec_values):
            data[key.get()] = value.get()
        return data

    @staticmethod
    def gen_task(response, link_list, callback):
        for link in link_list:
            yield response.follow(link.attrib['href'], callback=callback)

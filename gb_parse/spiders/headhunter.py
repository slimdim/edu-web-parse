import scrapy
from gb_parse.loaders import HeadHunterVacancyLoader, HeadHunterAuthorLoader


class HeadhunterSpider(scrapy.Spider):
    name = 'headhunter'
    allowed_domains = ['hh.ru']
    start_urls = ['https://hh.ru/search/vacancy?schedule=remote&L_profession_id=0&area=113']
    _xpath = {
        'pagination': '//div[@data-qa="pager-block"]//a[@data-qa="pager-page"]/@href',
        'vacancy_urls': '//a[@data-qa="vacancy-serp__vacancy-title"]/@href',
    }
    vacancy_xpath = {
        'title': '//h1[@data-qa="vacancy-title"]/text()',
        'salary': '//p[@class="vacancy-salary"]//text()',
        'description': '//div[@data-qa="vacancy-description"]//text()',
        'skills': '//div[@class="bloko-tag-list"]//span[@data-qa="bloko-tag__text"]/text()',
        'author_url': '//a[@data-qa="vacancy-company-name"]/@href',
    }

    author_xpath = {
        'name': '//div[@class="bloko-column bloko-column_xs-4 bloko-column_s-8 bloko-column_m-9 '
                'bloko-column_l-11"]//span[contains(@data-qa, "company-header-title-name")]/text()',
        'author_url': '//a[contains(@data-qa, "company-site")]/@href',
        'area': '//div[@class="employer-sidebar"]//div[contains(@data-qa, "sidebar-text-color")]//p/text()',
        'description': '//div[contains(@data-qa, "company-description")]//text()',
    }

    def parse(self, response, **kwargs):
        for pag_page in response.xpath(self._xpath["pagination"]):
            yield response.follow(pag_page, callback=self.parse)

        for vacancy_page in response.xpath(self._xpath["vacancy_urls"]):
            yield response.follow(vacancy_page, callback=self.vacancy_parse)

    def vacancy_parse(self, response, **kwargs):
        loader = HeadHunterVacancyLoader(response=response)
        loader.add_value("url", response.url)
        for key, value in self.vacancy_xpath.items():
            loader.add_xpath(key, value)

        yield loader.load_item()
        yield response.follow(
            response.xpath(self.vacancy_xpath["author_url"]).get(), callback=self.author_parse
        )

    def author_parse(self, response, **kwargs):
        loader = HeadHunterAuthorLoader(response=response)
        loader.add_value("url", response.url)
        for key, value in self.author_xpath.items():
            loader.add_xpath(key, value)
        yield loader.load_item()
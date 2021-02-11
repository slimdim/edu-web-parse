import os
from dotenv import load_dotenv
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from gb_parse.spiders.handshakes import HandshakesSpider

if __name__ == '__main__':
    load_dotenv(".env")
    crawler_settings = Settings()
    crawler_settings.setmodule('gb_parse.settings')
    crawler_process = CrawlerProcess(settings=crawler_settings)
    crawler_process.crawl(HandshakesSpider,
                          login=os.getenv('LOGIN'),
                          enc_password=os.getenv('ENC_PASSWORD'),
                          start_user='johngalt.94',
                          end_user='sl_voda')
    crawler_process.start()

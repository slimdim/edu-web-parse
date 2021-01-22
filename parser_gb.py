import requests
import bs4
from urllib.parse import urljoin, urlparse
from datetime import datetime
from database import Database
import json


class ParseGb:
    def __init__(self, start_url, database):
        self.start_url = start_url
        self.done_urls = set()
        self.tasks = [self.parse_task(self.start_url, self.pag_parse)]
        self.done_urls.add(self.start_url)
        self.database = database

    def _get_soup(self, *args, **kwargs):
        response = requests.get(*args, **kwargs)
        soup = bs4.BeautifulSoup(response.text, 'lxml')
        return soup

    def parse_task(self, url, callback):
        def wrap():
            soup = self._get_soup(url)
            return callback(url, soup)

        return wrap

    def run(self):
        for task in self.tasks:
            result = task()
            if result:
                self.database.create_post(result)

    def extract_post_comments(self, blog_id: int):
        url = urljoin('https://' + urlparse(self.start_url).hostname,
                      f'api/v2/comments?commentable_type=Post&commentable_id={blog_id}&order=desc')
        comments = requests.get(url).json()

        result = self.gb_comments_to_list(comments)
        return result

    @staticmethod
    def gb_comments_to_list(comments):
        result = []
        for comment in comments:
            result.append({'author': comment['comment']['user']['full_name'],
                           'body': comment['comment']['body'],
                           'gb_id': int(comment['comment']['id']),
                           'parent_id': int(comment['comment']['parent_id'])
                           if comment['comment']['parent_id'] else None,
                           'created_at': datetime.strptime(comment['comment']['created_at'],
                                                           '%Y-%m-%dT%H:%M:%S.%f%z')})
            result.extend(ParseGb.gb_comments_to_list(comment['comment']['children']))
        return result

    @staticmethod
    def find_image(soup: bs4.BeautifulSoup):
        try:
            image_div = soup.find('div', attrs={'class': 'blogpost-content'}).find_all('img')
            if not image_div:
                return None
            else:
                return image_div[0].get('src')
        except AttributeError:
            return None

    def post_parse(self, url, soup: bs4.BeautifulSoup) -> dict:
        author_name_tag = soup.find('div', attrs={'itemprop': 'author'})
        print(url)
        data = {
            'post_data': {
                'url': url,
                'title': soup.find('h1', attrs={'class': 'blogpost-title'}).text,
                'post_datetime': datetime.strptime(soup.find('time', attrs={'class': 'text-md'}).get('datetime'),
                                                   '%Y-%m-%dT%H:%M:%S%z'),
                'image': self.find_image(soup)
            },
            'author': {
                'url': urljoin(url, author_name_tag.parent.get('href')),
                'name': author_name_tag.text,
            },
            'tags': [{
                'name': tag.text,
                'url': urljoin(url, tag.get('href'))
            } for tag in soup.find_all('a', attrs={'class': 'small'})],
            'comments': self.extract_post_comments(int(soup.find('comments').get('commentable-id')))
        }
        return data

    def pag_parse(self, url, soup: bs4.BeautifulSoup):
        gb_pagination = soup.find('ul', attrs={'class': 'gb__pagination'})
        a_tags = gb_pagination.find_all('a')
        for a in a_tags:
            pag_url = urljoin(url, a.get('href'))
            if pag_url not in self.done_urls:
                task = self.parse_task(pag_url, self.pag_parse)
                self.tasks.append(task)
                self.done_urls.add(pag_url)
        posts_urls = soup.find_all('a', attrs={'class': 'post-item__title'})
        for post_url in posts_urls:
            post_href = urljoin(url, post_url.get('href'))
            if post_href not in self.done_urls:
                task = self.parse_task(post_href, self.post_parse)
                self.tasks.append(task)
                self.done_urls.add(post_href)


if __name__ == '__main__':
    parser = ParseGb('https://geekbrains.ru/posts/', Database('sqlite:///gb_blog.db'))
    parser.run()

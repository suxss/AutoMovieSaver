import random
import time
from typing import Tuple

from lxml import etree

from models.config import Config
from models.crawler import Crawler
from utils.web import WebRequests


class LeiJing(Crawler):
    def __init__(self, config: Config, parser, logger):
        self.web = WebRequests(logger=logger, timeout=5)
        self.config = config
        self.parser = parser(config, logger)

    def get_detail_page(self, page_start: int, page_end: int):
        url = f"https://www.leijing.xyz/?tagId=42204681950354"
        total_url = []
        i = page_start
        while i <= page_end:
            r = self.web.get(f"{url}&page={i}")
            html = etree.HTML(r.text)
            nodes = html.xpath('/html/body/div[2]/div/div[2]/div/div/div/div[2]/h2/a/@href')
            for node in nodes:
                total_url.append(f"https://www.leijing.xyz/{node}")
            i += 1
            time.sleep(random.random() * 2)
        return total_url

    def crawl(self, num: Tuple[int, int]):
        total_url = self.get_detail_page(num[0], num[1])
        for url in total_url:
            r = self.web.get(url)
            html = etree.HTML(r.text)
            info_html = '\n'.join([s.strip() for s in html.xpath('/html/body/div[2]/div/div/div[1]/div[1]/div[3]//text()')])
            try:
                movie_info, share_link = self.parser.parse(info_html)
                time.sleep(2)
            except TypeError:
                continue
            yield movie_info, share_link
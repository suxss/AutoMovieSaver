import random
import time
from typing import Tuple

from lxml import etree

from models.config import Config
from models.crawler import Crawler
from utils.web import WebRequests


class LeiJing(Crawler):
    prompt = '''你是一个从网页内容中提取指定信息的工具, 下面每次对话, 我将给你一段网页信息, 请你提取出三个信息并返回给我: 电影名, 上映年份, 以 https://cloud.189.cn 开头的天翼云盘分享链接. 三个信息请都使用文本格式给出, 用逗号隔开. 如果提取失败, 直接返回"失败", 不需要返回电影名与年份. 有时分享链接会带有访问码, 如果遇到这种情况, 请按照下面的例子将访问码与分享链接一并带上. 以下是两个正确回应的例子: 
        鬼滴语2, 2024, https://cloud.189.cn/t/2uiM7zb6nuyi（访问码：kp0m）
        You Only Live Once, 2025, http://cloud.189.cn/t/MRnMfemUvQ3u'''

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
                movie_info, share_link = self.parser.parse(info_html, self.prompt)
                time.sleep(2)
            except TypeError:
                continue
            yield movie_info, share_link
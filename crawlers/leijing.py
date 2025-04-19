import random
import time
from typing import Tuple

from lxml import etree

from models.config import Config
from models.crawler import Crawler
from utils.web import WebRequests


class LeiJing(Crawler):
    prompt = '''你是一个专业的电影信息提取工具。请从以下网页内容中精确提取三项关键信息：

1. 电影名称（中文或英文原名）
2. 上映年份（四位数字）
3. 天翼云盘分享链接（以https://cloud.189.cn或http://cloud.189.cn开头）

【输出格式要求】
* 三项信息必须以逗号分隔，不要有多余标点或文字
* 如果有访问码，请将其与链接一起提供，格式如：链接（访问码：xxxx）
* 如果提取失败，只返回一个词"失败"，无需解释

【提取规则】
* 电影名称：提取完整准确的电影标题，不包含副标题或其他描述
* 年份：仅提取4位数字年份，如2023、2024等
* 链接：必须是完整的天翼云盘链接，包含访问码（如有）

【输出示例】
正确格式示例：
鬼滴语2, 2024, https://cloud.189.cn/t/2uiM7zb6nuyi（访问码：kp0m）
You Only Live Once, 2025, http://cloud.189.cn/t/MRnMfemUvQ3u

请记住：只输出提取的三项信息，不要添加任何额外内容。'''

    def __init__(self, config: Config, parser, logger):
        self.web = WebRequests(logger=logger, timeout=5)
        self.config = config
        self.parser = parser(config, logger)
        self.logger = logger

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
        """从指定页码范围爬取电影信息
        
        Args:
            num: 起始和结束页码元组 (start_page, end_page)
            
        Yields:
            Tuple: 包含电影信息对象和分享链接的元组
        """
        try:
            # 获取所有详情页URL
            self.logger.info(f"开始爬取第{num[0]}页到第{num[1]}页的电影信息")
            total_urls = self.get_detail_page(num[0], num[1])
            self.logger.info(f"共获取到{len(total_urls)}个电影详情页链接")
            
            # 设置页面间隔时间范围（秒）
            min_sleep, max_sleep = 1.5, 3.0
            
            # 爬取每个详情页
            for index, url in enumerate(total_urls, 1):
                try:
                    self.logger.debug(f"开始处理第{index}/{len(total_urls)}个链接: {url}")
                    
                    # 请求详情页
                    response = self.web.get(url)
                    if response.status_code != 200:
                        self.logger.warning(f"获取页面失败: {url}, 状态码: {response.status_code}")
                        continue
                    
                    # 解析HTML内容
                    html = etree.HTML(response.text)
                    # 使用更稳健的XPath选择器提取电影信息部分
                    content_nodes = html.xpath('/html/body/div[2]/div/div/div[1]/div[1]/div[3]//text()')
                    if not content_nodes:
                        self.logger.warning(f"无法获取电影信息内容: {url}")
                        continue
                        
                    # 处理提取的文本内容
                    info_html = '\n'.join([s.strip() for s in content_nodes if s.strip()])
                    
                    # 调用解析器提取信息
                    movie_info, share_link = self.parser.parse(info_html, self.prompt)
                    if not movie_info or not share_link:
                        self.logger.warning(f"解析失败: {url}")
                        continue
                        
                    self.logger.debug(f"成功提取电影信息: {movie_info}")
                    
                    # 随机延时，防止请求过快
                    sleep_time = min_sleep + random.random() * (max_sleep - min_sleep)
                    time.sleep(sleep_time)
                    
                    yield movie_info, share_link
                    
                except TypeError as e:
                    self.logger.error(f"解析类型错误: {url}, 错误: {e}")
                    continue
                except Exception as e:
                    self.logger.error(f"处理详情页异常: {url}, 错误: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"爬取过程中发生错误: {e}")
            raise
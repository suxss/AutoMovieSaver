from typing import Tuple

from models.config import Config
from models.logger import Logger
from models.movie_info import MovieInfo
from models.parser import Parser
from utils.web import WebRequests


class OpenAIParser(Parser):
    def __init__(self, config: Config, logger: Logger):
        self.web = WebRequests(logger=logger)
        self.config = config

    def parse(self, html) -> Tuple[MovieInfo, str] | None:
        url = f"{self.config.api_url}/chat/completions"
        data = {"model": self.config.model,  # Qwen/Qwen2.5-32B-Instruct
                "messages": [
                    {"role": "user", "content": '''你是一个从网页内容中提取指定信息的工具, 下面每次对话, 我将给你一段网页信息, 请你提取出三个信息并返回给我: 电影名, 上映年份, 以 https://cloud.189.cn 开头的天翼云盘分享链接. 三个信息请都使用文本格式给出, 用逗号隔开. 如果提取失败, 直接返回"失败", 不需要返回电影名与年份. 有时分享链接会带有访问码, 如果遇到这种情况, 请按照下面的例子将访问码与分享链接一并带上. 以下是两个正确回应的例子: 
        鬼滴语2, 2024, https://cloud.189.cn/t/2uiM7zb6nuyi（访问码：kp0m）
        You Only Live Once, 2025, http://cloud.189.cn/t/MRnMfemUvQ3u'''},
                    {"role": "user", "content": html}
                ],
                "stream": False,
                "max_tokens": 4096}
        headers = {"Authorization": "Bearer " + self.config.token, "Content-Type": "application/json"}
        r = self.web.post(url, json=data, headers=headers)
        if r.status_code == 200:
            answer = r.json().get("choices", [{}])[0].get("message", {}).get("content")
            items = answer.split(",")
            if len(items) == 3:
                movie = MovieInfo(title=items[0].strip(), year=int(items[1].strip()), video_format="", edition="")
                return movie, items[2]
            return None
        raise BaseException("对话模型错误")


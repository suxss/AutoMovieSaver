from typing import Tuple

from models.config import Config
from models.logger import Logger
from models.movie_info import MovieInfo
from models.parser import Parser
from utils.web import WebRequests


class OpenAIParser(Parser):
    def __init__(self, config: Config, logger: Logger):
        self.web = WebRequests(logger=logger, timeout=5)
        self.config = config

    def parse(self, html, prompt) -> Tuple[MovieInfo, str] | None:
        url = f"{self.config.api_url}/chat/completions"
        data = {"model": self.config.model,  # Qwen/Qwen2.5-32B-Instruct
                "messages": [
                    {"role": "user", "content": prompt},
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


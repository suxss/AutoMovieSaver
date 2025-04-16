import logging
from typing import Optional, Dict, Any, Union
import time
import random

import requests
from requests.exceptions import RequestException


class WebRequests:
    """网络请求工具类，用于处理HTTP请求"""
    
    def __init__(self, logger=None, timeout: int = 3, max_retries: int = 3, retry_delay: float = 1.0):
        """初始化网络请求工具
        
        Args:
            logger: 日志记录器，默认为None
            timeout: 请求超时时间，单位为秒，默认3秒
            max_retries: 最大重试次数，默认3次
            retry_delay: 重试延迟时间，单位为秒，默认1秒
        """
        self.logger = logger or logging.getLogger(__name__)
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # 初始化会话
        self.session = requests.session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
            "Accept": "application/json;charset=UTF-8"
        })
    
    def _make_request(self, method: str, url: str, headers: Optional[Dict] = None, 
                     timeout: Optional[int] = None, encoding: str = 'utf-8', **kwargs) -> requests.Response:
        """执行HTTP请求
        
        Args:
            method: 请求方法，如 'get', 'post'
            url: 请求URL
            headers: 请求头
            timeout: 请求超时时间
            encoding: 响应编码
            **kwargs: 其他请求参数
            
        Returns:
            requests.Response: 响应对象
            
        Raises:
            RequestException: 请求异常
        """
        if timeout is None:
            timeout = self.timeout
            
        # 记录请求信息
        self.logger.debug(f"{method.upper()} {url}")
        
        # 准备请求参数
        request_kwargs = {'timeout': timeout, **kwargs}
        if headers:
            request_kwargs['headers'] = headers
            
        # 执行请求并重试
        for attempt in range(self.max_retries):
            try:
                response = getattr(self.session, method.lower())(url, **request_kwargs)
                response.encoding = encoding
                
                # 记录响应信息
                if response.status_code != 200:
                    self.logger.error(f"响应错误 [code={response.status_code}, url={url}]: {response.text}")
                else:
                    self.logger.debug(f"响应成功 [code={response.status_code}, url={url}]")
                    
                return response
                
            except RequestException as e:
                # 最后一次尝试失败时抛出异常
                if attempt == self.max_retries - 1:
                    self.logger.error(f"请求失败 [url={url}]: {str(e)}")
                    raise
                
                # 重试前等待一段时间
                retry_wait = self.retry_delay * (1 + random.random())
                self.logger.warning(f"请求失败，{retry_wait:.1f}秒后重试 ({attempt+1}/{self.max_retries}) [url={url}]: {str(e)}")
                time.sleep(retry_wait)

    def get(self, url: str, headers: Optional[Dict] = None, 
            timeout: Optional[int] = None, encoding: str = 'utf-8', **kwargs) -> requests.Response:
        """发送GET请求
        
        Args:
            url: 请求URL
            headers: 请求头
            timeout: 请求超时时间
            encoding: 响应编码
            **kwargs: 其他请求参数
            
        Returns:
            requests.Response: 响应对象
        """
        return self._make_request('get', url, headers, timeout, encoding, **kwargs)

    def post(self, url: str, data: Any = None, headers: Optional[Dict] = None,
             timeout: Optional[int] = None, encoding: str = 'utf-8', **kwargs) -> requests.Response:
        """发送POST请求
        
        Args:
            url: 请求URL
            data: 请求数据
            headers: 请求头
            timeout: 请求超时时间
            encoding: 响应编码
            **kwargs: 其他请求参数
            
        Returns:
            requests.Response: 响应对象
        """
        return self._make_request('post', url, headers, timeout, encoding, data=data, **kwargs)
        
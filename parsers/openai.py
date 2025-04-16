from typing import Tuple, Dict, Any, Optional

from models.config import Config
from models.movie_info import MovieInfo
from models.parser import Parser
from utils.web import WebRequests


class APIError(Exception):
    """API调用相关错误"""
    
    def __init__(self, message: str = "API调用错误", 
                 status_code: int = None, 
                 endpoint: str = None, 
                 response_data: Dict[str, Any] = None, 
                 request_data: Dict[str, Any] = None):
        """初始化API错误
        
        Args:
            message: 错误消息
            status_code: HTTP状态码
            endpoint: API端点
            response_data: API响应数据
            request_data: 请求数据（敏感信息会被过滤）
        """
        self.message = message
        self.status_code = status_code
        self.endpoint = endpoint
        self.response_data = response_data or {}
        self.request_data = self._filter_sensitive_data(request_data or {})
        super().__init__(self.message)
    
    def _filter_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """过滤请求数据中的敏感信息
        
        Args:
            data: 原始请求数据
            
        Returns:
            Dict: 过滤后的数据
        """
        filtered = data.copy()
        # 过滤令牌等敏感信息
        sensitive_keys = ['token', 'key', 'password', 'secret', 'auth', 'Bearer']
        for key in list(filtered.keys()):
            for sensitive in sensitive_keys:
                if sensitive.lower() in key.lower():
                    if isinstance(filtered[key], str) and filtered[key]:
                        filtered[key] = filtered[key][:4] + '****'
        
        # 递归处理嵌套字典
        for key, value in filtered.items():
            if isinstance(value, dict):
                filtered[key] = self._filter_sensitive_data(value)
        
        return filtered
    
    def __str__(self) -> str:
        """返回详细的错误信息字符串表示"""
        parts = [f"APIError: {self.message}"]
        
        if self.status_code:
            parts.append(f"Status Code: {self.status_code}")
        
        if self.endpoint:
            parts.append(f"Endpoint: {self.endpoint}")
            
        if self.response_data:
            error_msg = self.response_data.get('error', {}).get('message', '')
            if error_msg:
                parts.append(f"API Error: {error_msg}")
                
        return " | ".join(parts)
    
    @property
    def is_rate_limit_error(self) -> bool:
        """检查是否为速率限制错误"""
        if self.status_code == 429:
            return True
        
        if self.response_data:
            error_type = self.response_data.get('error', {}).get('type', '')
            error_msg = self.response_data.get('error', {}).get('message', '')
            return 'rate_limit' in error_type.lower() or 'rate limit' in error_msg.lower()
            
        return False
        
    @property
    def is_auth_error(self) -> bool:
        """检查是否为认证错误"""
        return self.status_code in (401, 403)
        
    @property
    def is_server_error(self) -> bool:
        """检查是否为服务器错误"""
        return self.status_code >= 500 if self.status_code else False


class OpenAIParser(Parser):
    def __init__(self, config: Config, logger):
        self.web = WebRequests(logger=logger, timeout=5)
        self.config = config
        self.logger = logger

    def parse(self, html, prompt) -> Tuple[MovieInfo, str] | None:
        url = f"{self.config.api_url}/chat/completions"
        data = {"model": self.config.model,
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "user", "content": html}
                ],
                "stream": False,
                "max_tokens": 4096}
        headers = {"Authorization": "Bearer " + self.config.token, "Content-Type": "application/json"}
        
        try:
            r = self.web.post(url, json=data, headers=headers)
            
            if r.status_code == 200:
                answer = r.json().get("choices", [{}])[0].get("message", {}).get("content")
                
                # 如果没有得到有效回答
                if not answer:
                    self.logger.warning("模型返回了空响应")
                    return None
                    
                items = answer.split(",")
                if len(items) == 3:
                    try:
                        year = int(items[1].strip())
                        movie = MovieInfo(title=items[0].strip(), year=year, video_format="", edition="")
                        return movie, items[2]
                    except ValueError as e:
                        self.logger.error(f"解析年份时出错: {items[1].strip()} - {e}")
                        return None
                else:
                    self.logger.warning(f"模型返回格式不正确: {answer}")
                    return None
            else:
                # 准备API错误的详细信息
                response_data = r.json() if r.text and r.headers.get('content-type', '').startswith('application/json') else {}
                
                error_msg = "对话模型错误"
                if r.status_code == 401 or r.status_code == 403:
                    error_msg = "API认证失败，请检查API密钥"
                elif r.status_code == 429:
                    error_msg = "API请求次数超限，请稍后再试"
                elif r.status_code >= 500:
                    error_msg = "API服务器错误，请稍后再试"
                
                self.logger.error(f"API请求失败: HTTP {r.status_code}")
                
                # 创建详细的APIError
                api_error = APIError(
                    message=error_msg,
                    status_code=r.status_code,
                    endpoint=url,
                    response_data=response_data,
                    request_data={"model": data["model"], "messages_count": len(data["messages"])}
                )
                
                # 根据错误类型记录不同级别的日志
                if api_error.is_rate_limit_error:
                    self.logger.warning(f"API速率限制: {str(api_error)}")
                elif api_error.is_auth_error:
                    self.logger.error(f"API认证错误: {str(api_error)}")
                elif api_error.is_server_error:
                    self.logger.error(f"API服务器错误: {str(api_error)}")
                else:
                    self.logger.error(f"API请求错误: {str(api_error)}")
                
                raise api_error
                
        except Exception as e:
            # 如果已经是APIError，直接抛出
            if isinstance(e, APIError):
                raise
                
            # 否则包装成APIError
            error_msg = f"调用对话模型时发生错误: {str(e)}"
            self.logger.error(error_msg)
            raise APIError(
                message=error_msg,
                endpoint=url,
                request_data={"model": data["model"], "messages_count": len(data["messages"])}
            ) from e


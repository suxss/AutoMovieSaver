import requests


class WebRequests:
    def __init__(self, logger=None, timeout=3):
        self.logger = logger
        self.timeout = timeout
        self.session = requests.session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
                                     "Accept": "application/json;charset=UTF-8"})

    def log(self, message: str, log_type="info"):
        if self.logger:
            self.logger.log(message, log_type)

    def get(self, url: str, headers=None, timeout=None, encoding='utf-8', **kwargs):
        self.log(f"GET {url}", log_type="debug")
        if timeout is None:
            timeout = self.timeout
        if headers is None:
            request = self.session.get(url, timeout=timeout, **kwargs)
        else:
            request = self.session.get(url, headers=headers, timeout=timeout, **kwargs)
        request.encoding = encoding
        if request.status_code != 200:
            self.log(f"Respond [code={request.status_code}, url={url}]:  {request.text}", log_type="error")
        else:
            self.log(f"Respond [code={request.status_code}, url={url}]", log_type="debug")
        return request

    def post(self, url: str, data=None, headers=None, timeout=None, encoding='utf-8', **kwargs):
        self.log(f"POST {url}", log_type="debug")
        if timeout is None:
            timeout = self.timeout
        if headers is None:
            request = self.session.post(url, data=data, timeout=timeout, **kwargs)
        else:
            request = self.session.post(url, data=data, headers=headers, timeout=timeout, **kwargs)
        request.encoding = encoding
        if request.status_code != 200:
            self.log(f"Respond [code={request.status_code}, url={url}]:  {request.text}", log_type="error")
        else:
            self.log(f"Respond [code={request.status_code}, url={url}]", log_type="debug")
        return request
        
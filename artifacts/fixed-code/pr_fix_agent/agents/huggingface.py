import requests

class CreateSSRFSafeSession:
    def __init__(self, timeout: float = 60.0):
        self.session = requests.Session()
        self.timeout = timeout

    def send(self, method, url, **kwargs):
        response = self.session.request(method=method, url=url, timeout=self.timeout, **kwargs)
        if response.status_code == 429:
            raise Exception("Rate limit exceeded")
        return response
import httpx

from washer.config import config


class BackendApi:
    def __init__(self):
        self.url = config.api_url

    def login(self, username: str, password: str) -> dict:
        response = httpx.post(
            f'{self.url}jwt/token',
            data={'username': username, 'password': password},
        )
        return response.json()

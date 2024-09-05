import httpx

from washer.config import config


class BackendApi:
    def __init__(self):
        self.url = config.api_url
        self.access_token = None
        self.refresh_token = None

    def register_user(self, data: dict) -> httpx.Response:
        api_url = self.url.rstrip('/')

        print(f'Отправка запроса на {api_url}/jwt/register с данными {data}')

        response = httpx.post(f'{api_url}/jwt/register', json=data)

        print(f'Ответ сервера: {response.status_code}, {response.text}')

        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens.get('access_token')
            self.refresh_token = tokens.get('refresh_token')

        return response

    def login(self, username: str, password: str) -> dict:
        response = httpx.post(
            f'{self.url}jwt/token',
            data={'username': username, 'password': password},
        )
        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens.get('access_token')
            self.refresh_token = tokens.get('refresh_token')
            return tokens
        else:
            return {'error': 'Ошибка авторизации'}

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
            f'{self.url.rstrip("/")}/jwt/token',
            data={'username': username, 'password': password},
        )
        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens.get('access_token')
            self.refresh_token = tokens.get('refresh_token')
            return tokens
        else:
            return {'error': 'Ошибка авторизации'}

    def get_logged_user(self) -> dict:
        if not self.access_token:
            return {'error': 'Access token not found'}

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
        }
        response = httpx.get(
            f'{self.url.rstrip("/")}/users/me', headers=headers
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {'error': 'Failed to fetch user information'}

    def create_user_car(self, car_data: dict) -> httpx.Response:
        if not self.access_token:
            print('Токен доступа отсутствует!')
            return None

        api_url = f'{self.url.rstrip("/")}/cars'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

        response = httpx.post(api_url, json=car_data, headers=headers)
        return response

    def get_user_cars(self) -> httpx.Response:
        headers = {'Authorization': f'Bearer {self.access_token}'}
        api_url = f'{self.url.rstrip("/")}/cars'
        response = httpx.get(api_url, headers=headers)
        return response

    def get_car_by_id(self, car_id: int) -> httpx.Response:
        headers = {'Authorization': f'Bearer {self.access_token}'}
        api_url = f'{self.url.rstrip("/")}/cars/{car_id}'
        response = httpx.get(api_url, headers=headers)
        return response

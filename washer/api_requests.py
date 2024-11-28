import json

import httpx

from washer.config import config


class BackendApi:
    def __init__(self):
        self.url = config.api_url
        self.access_token = None
        self.refresh_token = None

    def set_access_token(self, token: str):
        self.access_token = token

    def get_headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def create_box(self, box_data: dict) -> httpx.Response:
        api_url = f"{self.url.rstrip('/')}/car_washes/boxes"
        headers = self.get_headers()
        response = httpx.post(api_url, json=box_data, headers=headers)
        return response

    def create_schedule(self, schedule_data):
        url = f"{self.url.rstrip('/')}/car_washes/schedules"
        print(f'Отправляем запрос на URL: {url}')
        response = httpx.post(
            url, json=schedule_data, headers=self.get_headers()
        )
        return response

    def get_boxes(self, car_wash_id: int) -> httpx.Response:
        api_url = (
            f"{self.url.rstrip('/')}/car_washes/boxes"
            f"?car_wash_id={car_wash_id}"
        )
        headers = self.get_headers()
        response = httpx.get(api_url, headers=headers)

        print(f'Отправляем запрос на {api_url} с заголовками {headers}')
        print(f'Ответ сервера: {response.status_code}, {response.text}')

        return response

    def get_schedules(self, car_wash_id: int) -> httpx.Response:
        api_url = (
            f"{self.url.rstrip('/')}/car_washes/schedules"
            f"?car_wash_id={car_wash_id}&limit=1000"
        )
        headers = self.get_headers()
        response = httpx.get(api_url, headers=headers)
        return response

    def delete_schedule(self, schedule_id: int) -> httpx.Response:
        api_url = f"{self.url.rstrip('/')}/car_washes/schedules/{schedule_id}"
        headers = self.get_headers()
        response = httpx.delete(api_url, headers=headers)
        return response

    def register_user(self, data: dict, files: dict = None) -> httpx.Response:
        api_url = self.url.rstrip('/')

        form_data = {
            'new_user': (
                None,
                json.dumps(
                    {
                        'username': data['username'],
                        'password': data['password'],
                        'first_name': data['first_name'],
                        'last_name': data['last_name'],
                    }
                ),
                'application/json',
            )
        }

        if files:
            form_data.update(files)

        print(
            f'Отправка запроса на {api_url}/jwt/register с данными '
            f'{form_data} и файлами {files}'
        )

        response = httpx.post(f'{api_url}/jwt/register', files=form_data)

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

    def upload_car_wash_image(self, data: dict, files: dict) -> httpx.Response:
        api_url = f"{self.url.rstrip('/')}/car_washes/upload_image"

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
        }

        response = httpx.post(api_url, data=data, files=files, headers=headers)
        return response

    def update_box(self, box_id: int, new_name: str) -> httpx.Response:
        api_url = f"{self.url.rstrip('/')}/car_washes/boxes/{box_id}"
        headers = self.get_headers()
        data = {'name': new_name}
        response = httpx.patch(api_url, json=data, headers=headers)
        return response

    def delete_box(self, box_id: int) -> httpx.Response:
        api_url = f"{self.url.rstrip('/')}/car_washes/boxes/{box_id}"
        headers = self.get_headers()
        response = httpx.delete(api_url, headers=headers)
        return response

    def create_booking(self, booking_data: dict) -> httpx.Response:
        api_url = f"{self.url.rstrip('/')}/car_washes/bookings"
        headers = self.get_headers()
        response = httpx.post(api_url, json=booking_data, headers=headers)
        return response

    def get_bookings(self, car_wash_id: int) -> httpx.Response:
        api_url = (
            f"{self.url.rstrip('/')}/car_washes/bookings"
            f"?car_wash_id={car_wash_id}&limit=1000"
        )
        headers = self.get_headers()
        response = httpx.get(api_url, headers=headers)
        return response

    def get_available_times(
        self, car_wash_id: int, date: str
    ) -> httpx.Response:
        api_url = (
            f"{self.url.rstrip('/')}/car_washes/{car_wash_id}/available_times"
            f"?date={date}"
        )
        headers = self.get_headers()
        response = httpx.get(api_url, headers=headers)
        return response

    def get_locations(self) -> httpx.Response:
        api_url = (
            f"{self.url.rstrip('/')}/car_washes/locations?page=1&limit=10"
        )
        headers = self.get_headers()
        response = httpx.get(api_url, headers=headers)
        return response

    def create_price(self, price_data: dict) -> httpx.Response:
        api_url = f"{self.url.rstrip('/')}/car_washes/prices"
        headers = self.get_headers()
        response = httpx.post(api_url, json=price_data, headers=headers)
        return response

    def get_prices(self, car_wash_id: int) -> httpx.Response:
        api_url = (
            f"{self.url.rstrip('/')}/car_washes/prices"
            f"?car_wash_id={car_wash_id}"
        )
        headers = self.get_headers()
        response = httpx.get(api_url, headers=headers)
        return response

    def update_price(self, price_id: int, price_data: dict) -> httpx.Response:
        api_url = f"{self.url.rstrip('/')}/car_washes/prices/{price_id}"
        headers = self.get_headers()
        response = httpx.patch(api_url, json=price_data, headers=headers)
        return response

    def delete_price(self, price_id: int) -> httpx.Response:
        api_url = f"{self.url.rstrip('/')}/car_washes/prices/{price_id}"
        headers = self.get_headers()
        response = httpx.delete(api_url, headers=headers)
        return response

    def get_body_types(self, limit=100) -> httpx.Response:
        api_url = f"{self.url.rstrip('/')}/cars/body_types?limit={limit}"
        headers = self.get_headers()
        response = httpx.get(api_url, headers=headers)
        return response

    def get_car_price(self, car_wash_id: int) -> httpx.Response:
        api_url = (
            f"{self.url.rstrip('/')}/car_washes/prices"
            f"?page=1&limit=100&order_by=id&car_wash_id={car_wash_id}"
        )
        headers = self.get_headers()
        response = httpx.get(api_url, headers=headers)

        print(f'Отправляем запрос на {api_url}')
        print(f'Ответ сервера: {response.status_code}, {response.text}')

        return response

    def delete_booking(self, booking_id: int) -> httpx.Response:
        api_url = f"{self.url.rstrip('/')}/car_washes/bookings/{booking_id}"
        headers = self.get_headers()
        response = httpx.delete(api_url, headers=headers)
        return response

    def update_user(self, user_id: int, new_values: dict) -> httpx.Response:
        api_url = f"{self.url.rstrip('/')}/users/{user_id}"
        headers = self.get_headers()
        response = httpx.patch(api_url, json=new_values, headers=headers)
        return response

    def update_schedule(
        self, schedule_id: int, updated_data: dict
    ) -> httpx.Response:
        api_url = f"{self.url.rstrip('/')}/car_washes/schedules/{schedule_id}"
        headers = self.get_headers()
        response = httpx.patch(api_url, json=updated_data, headers=headers)
        return response

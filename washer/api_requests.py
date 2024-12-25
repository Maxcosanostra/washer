import io
import json
from concurrent.futures import ThreadPoolExecutor

import httpx

from washer.config import config
from washer.models.user import UserRegistration


class BackendApi:
    def __init__(self):
        self.url = config.api_url
        self.access_token = None
        self.refresh_token = None
        self.executor = ThreadPoolExecutor(
            max_workers=10
        )  # Добавлен ThreadPoolExecutor

    def set_access_token(self, token: str):
        self.access_token = token

    def get_headers(self):
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
        }
        return headers

    def create_box(self, box_data: dict) -> httpx.Response:
        api_url = f"{str(self.url).rstrip('/')}/car_washes/boxes"
        headers = self.get_headers()
        return httpx.post(api_url, json=box_data, headers=headers)

    def create_schedule(self, schedule_data):
        url = f"{str(self.url).rstrip('/')}/car_washes/schedules"
        print(f'Отправляем запрос на URL: {url}')
        response = httpx.post(
            url, json=schedule_data, headers=self.get_headers()
        )
        return response

    def get_boxes(self, car_wash_id: int) -> httpx.Response:
        api_url = (
            f"{str(self.url).rstrip('/')}/car_washes/boxes"
            f"?car_wash_id={car_wash_id}"
        )

        headers = self.get_headers()
        return httpx.get(api_url, headers=headers)

    def get_schedules(self, car_wash_id: int) -> httpx.Response:
        api_url = (
            f"{str(self.url).rstrip('/')}/car_washes/schedules"
            f"?car_wash_id={car_wash_id}&limit=1000"
        )

        headers = self.get_headers()
        return httpx.get(api_url, headers=headers)

    def delete_schedule(self, schedule_id: int) -> httpx.Response:
        api_url = (
            f"{str(self.url).rstrip('/')}/car_washes/schedules/{schedule_id}"
        )
        headers = self.get_headers()
        return httpx.delete(api_url, headers=headers)

    def register_user(self, user: UserRegistration) -> httpx.Response:
        api_url = f"{str(self.url).rstrip('/')}/jwt/register"

        user_data = user.model_dump(exclude={'image'}, exclude_unset=True)
        user_json = json.dumps(user_data)

        files = {'new_user': (None, user_json, 'application/json')}

        if user.image:
            files['image'] = (
                'avatar.png',
                io.BytesIO(user.image),
                'image/png',
            )

        print(f'Отправка запроса на {api_url} с данными {files}')
        response = httpx.post(api_url, files=files, headers=self.get_headers())
        print(f'Получен ответ: {response.status_code} - {response.text}')
        return response

    def login(self, username: str, password: str) -> dict:
        response = httpx.post(
            f'{str(self.url).rstrip("/")}/jwt/token',
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
            print('Access token not set!')
            return {'error': 'Access token not set!'}

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
        }
        api_url = f"{str(self.url).rstrip('/')}/users/me"
        try:
            response = httpx.get(api_url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(
                    f'Ошибка при получении данных пользователя: '
                    f'{response.status_code} - {response.text}'
                )
                return {
                    'error': f'Error {response.status_code}: {response.text}'
                }
        except httpx.RequestError as e:
            print(f'Ошибка запроса при получении данных пользователя: {e}')
            return {'error': 'Request failed'}

    def create_user_car(self, car_data: dict) -> httpx.Response:
        if not self.access_token:
            print('Токен доступа отсутствует!')
            return None

        api_url = f"{str(self.url).rstrip('/')}/cars"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

        response = httpx.post(api_url, json=car_data, headers=headers)
        return response

    def get_user_cars(self, user_id: int, limit: int = 100) -> httpx.Response:
        api_url = (
            f"{str(self.url).rstrip('/')}/cars?user_id={user_id}&limit={limit}"
        )
        headers = self.get_headers()
        response = httpx.get(api_url, headers=headers)
        return response

    def get_car_by_id(self, car_id: int) -> httpx.Response:
        headers = {'Authorization': f'Bearer {self.access_token}'}
        api_url = f'{str(self.url).rstrip('/')}/cars/{car_id}'
        response = httpx.get(api_url, headers=headers)
        return response

    def upload_car_wash_image(self, data: dict, files: dict) -> httpx.Response:
        api_url = f"{str(self.url).rstrip('/')}/car_washes/upload_image"

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
        }

        response = httpx.post(api_url, data=data, files=files, headers=headers)
        return response

    def update_box(self, box_id: int, new_name: str) -> httpx.Response:
        api_url = f"{str(self.url).rstrip('/')}/car_washes/boxes/{box_id}"
        headers = self.get_headers()
        return httpx.patch(api_url, json={'name': new_name}, headers=headers)

    def delete_box(self, box_id: int) -> httpx.Response:
        api_url = f"{str(self.url).rstrip('/')}/car_washes/boxes/{box_id}"
        headers = self.get_headers()
        return httpx.delete(api_url, headers=headers)

    def create_booking(self, booking_data: dict) -> httpx.Response:
        api_url = f"{str(self.url).rstrip('/')}/car_washes/bookings"
        headers = self.get_headers()
        response = httpx.post(api_url, json=booking_data, headers=headers)
        return response

    def get_bookings(self, car_wash_id: int) -> httpx.Response:
        api_url = (
            f"{str(self.url).rstrip('/')}/car_washes/bookings"
            f"?car_wash_id={car_wash_id}&limit=1000"
        )
        headers = self.get_headers()
        response = httpx.get(api_url, headers=headers)
        return response

    def get_available_times(
        self, car_wash_id: int, date: str
    ) -> httpx.Response:
        api_url = (
            f"{str(self.url).rstrip('/')}/car_washes/{car_wash_id}/"
            f"available_times?date={date}"
        )

        headers = self.get_headers()
        response = httpx.get(api_url, headers=headers)
        return response

    def get_available_times_async(
        self, car_wash_id: int, box_id: int, date: str, callback
    ) -> None:
        """
        Асинхронный метод для получения доступных временных слотов.
        Выполняет запрос в отдельном потоке и вызывает callback с ответом
        и box_id.
        """

        def task():
            response = self.get_available_times(car_wash_id, date)
            callback(response, box_id)

        self.executor.submit(task)

    def get_locations(self) -> httpx.Response:
        api_url = (
            f"{str(self.url).rstrip('/')}/car_washes/locations?page=1&limit=10"
        )
        headers = self.get_headers()
        response = httpx.get(api_url, headers=headers)
        return response

    def create_price(self, price_data: dict) -> httpx.Response:
        api_url = f"{str(self.url).rstrip('/')}/car_washes/prices"
        headers = self.get_headers()
        response = httpx.post(api_url, json=price_data, headers=headers)
        return response

    def get_prices(self, car_wash_id: int) -> httpx.Response:
        api_url = (
            f"{str(self.url).rstrip('/')}/car_washes/prices"
            f"?car_wash_id={car_wash_id}"
        )
        headers = self.get_headers()
        response = httpx.get(api_url, headers=headers)
        return response

    def update_price(self, price_id: int, price_data: dict) -> httpx.Response:
        api_url = f"{str(self.url).rstrip('/')}/car_washes/prices/{price_id}"
        headers = self.get_headers()
        response = httpx.patch(api_url, json=price_data, headers=headers)
        return response

    def delete_price(self, price_id: int) -> httpx.Response:
        api_url = f"{str(self.url).rstrip('/')}/car_washes/prices/{price_id}"
        headers = self.get_headers()
        response = httpx.delete(api_url, headers=headers)
        return response

    def get_body_types(self, limit=100) -> httpx.Response:
        api_url = f"{str(self.url).rstrip('/')}/cars/body_types?limit={limit}"
        headers = self.get_headers()
        response = httpx.get(api_url, headers=headers)
        return response

    def get_car_price(self, car_wash_id: int) -> httpx.Response:
        api_url = (
            f"{str(self.url).rstrip('/')}/car_washes/prices"
            f"?page=1&limit=100&order_by=id&car_wash_id={car_wash_id}"
        )
        headers = self.get_headers()
        response = httpx.get(api_url, headers=headers)

        print(f'Отправляем запрос на {api_url}')
        print(f'Ответ сервера: {response.status_code}, {response.text}')

        return response

    def delete_booking(self, booking_id: int) -> httpx.Response:
        api_url = (
            f"{str(self.url).rstrip('/')}/car_washes/bookings/{booking_id}"
        )
        headers = self.get_headers()
        response = httpx.delete(api_url, headers=headers)
        return response

    def update_user_data(self, user_id: int, new_values: dict) -> dict:
        """
        Обновление данных пользователя.

        :param user_id: Идентификатор пользователя.
        :param new_values: Словарь с обновляемыми полями пользователя.
        :return: Словарь с 'status_code' и 'data' при успехе
        или 'error' при ошибке.
        """
        url = f"{str(self.url).rstrip('/')}/users/{user_id}"
        headers = self.get_headers()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        try:
            response = httpx.patch(
                url,
                data={'new_values': json.dumps(new_values)},
                headers=headers,
            )
            if response.status_code == 200:
                return {
                    'status_code': response.status_code,
                    'data': response.json(),
                }
            else:
                return {'error': response.text}
        except httpx.RequestError as e:
            print(f'Ошибка запроса при обновлении пользователя: {e}')
            return {'error': str(e)}

    def update_schedule(
        self, schedule_id: int, updated_data: dict
    ) -> httpx.Response:
        api_url = (
            f"{str(self.url).rstrip('/')}/car_washes/schedules/{schedule_id}"
        )
        headers = self.get_headers()
        response = httpx.patch(api_url, json=updated_data, headers=headers)
        return response

    def get_brands(self, limit=1000) -> httpx.Response:
        api_url = f"{str(self.url).rstrip('/')}/cars/brands?limit={limit}"
        headers = self.get_headers()
        return httpx.get(api_url, headers=headers)

    def get_models(self, brand_id: int, limit=100) -> httpx.Response:
        api_url = (
            f"{str(self.url).rstrip('/')}/cars/models"
            f"?brand_id={brand_id}&limit={limit}"
        )

        headers = self.get_headers()
        return httpx.get(api_url, headers=headers)

    def get_generations(self, model_id: int, limit=100) -> httpx.Response:
        api_url = (
            f"{str(self.url).rstrip('/')}/cars/generations"
            f"?model_id={model_id}&limit={limit}"
        )

        headers = self.get_headers()
        return httpx.get(api_url, headers=headers)

    def get_configurations(
        self, generation_id: int, limit: int = 100
    ) -> httpx.Response:
        api_url = (
            f"{str(self.url).rstrip('/')}/cars/configurations"
            f"?generation_id={generation_id}&limit={limit}"
        )

        headers = self.get_headers()
        return httpx.get(api_url, headers=headers)

    def refresh_token(self, refresh_token: str) -> dict:
        response = httpx.post(
            f'{str(self.url).rstrip("/")}/jwt/refresh',
            json={'refresh_token': refresh_token},
        )
        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens.get('access_token')
            self.refresh_token = tokens.get('refresh_token')
            return tokens
        else:
            return {
                'error': 'Failed to refresh token',
                'details': response.text,
            }

    def delete_user_car(self, car_id: int) -> httpx.Response:
        api_url = f"{str(self.url).rstrip('/')}/cars/{car_id}"
        headers = self.get_headers()
        response = httpx.delete(api_url, headers=headers)
        return response

    def get_configuration_by_id(
        self, configuration_id: int, limit: int = 10000
    ) -> httpx.Response:
        api_url = f"{str(self.url).rstrip('/')}/cars/configurations"
        headers = self.get_headers()
        params = {'configuration_id': configuration_id, 'limit': limit}
        response = httpx.get(api_url, headers=headers, params=params)
        return response

    def get_user_avatar(self) -> httpx.Response:
        api_url = f"{str(self.url).rstrip('/')}/users/me"
        headers = self.get_headers()
        return httpx.get(api_url, headers=headers)

    def get_car_washes(self, page: int = 1) -> httpx.Response:
        api_url = f"{str(self.url).rstrip('/')}/car_washes"
        headers = self.get_headers()
        params = {'page': page}
        response = httpx.get(api_url, headers=headers, params=params)
        return response

    def get_location_data(self, location_id: int) -> httpx.Response:
        api_url = (
            f"{str(self.url).rstrip('/')}/car_washes/locations/{location_id}"
        )
        headers = self.get_headers()
        response = httpx.get(api_url, headers=headers)
        return response

    def get_box_by_id(self, box_id: int) -> httpx.Response:
        api_url = f"{str(self.url).rstrip('/')}/car_washes/boxes/{box_id}"
        headers = self.get_headers()
        response = httpx.get(api_url, headers=headers)
        return response

    def get_car_wash_by_id(self, car_wash_id: int) -> httpx.Response:
        api_url = f"{str(self.url).rstrip('/')}/car_washes/{car_wash_id}"
        headers = self.get_headers()
        response = httpx.get(api_url, headers=headers)
        return response

    def get_location_by_id(self, location_id: int) -> httpx.Response:
        api_url = (
            f"{str(self.url).rstrip('/')}/car_washes/locations/{location_id}"
        )
        headers = self.get_headers()
        response = httpx.get(api_url, headers=headers)
        return response

    def get_user_bookings(
        self, user_id: int, limit: int = 100
    ) -> httpx.Response:
        """
        Получение букингов пользователя по user_id.
        """
        api_url = f"{str(self.url).rstrip('/')}/car_washes/bookings"
        headers = self.get_headers()
        params = {'user_id': user_id, 'limit': limit}
        try:
            response = httpx.get(api_url, headers=headers, params=params)
            return response
        except httpx.RequestError as e:
            print(f'Ошибка запроса при получении букингов: {e}')
            return None

    def update_user_with_avatar(
        self, user_id: int, new_values: dict, image_bytes: bytes
    ) -> httpx.Response:
        """
        Обновление данных пользователя с загрузкой аватара.

        :param user_id: Идентификатор пользователя.
        :param new_values: Словарь с обновляемыми полями пользователя.
        :param image_bytes: Байтовые данные изображения аватара.
        :return: Объект httpx.Response или None в случае ошибки.
        """
        api_url = f"{str(self.url).rstrip('/')}/users/{user_id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
        }
        files = {'image': ('avatar.png', io.BytesIO(image_bytes))}
        data = {
            'new_values': json.dumps(new_values)
        }  # Добавлено поле 'new_values'
        try:
            response = httpx.patch(
                api_url, files=files, data=data, headers=headers
            )
            return response
        except httpx.RequestError as e:
            print(f'Ошибка запроса при обновлении пользователя: {e}')
            return None

    def update_car_wash(
        self, car_wash_id: int, new_values: dict, files: dict = None
    ) -> httpx.Response:
        """
        Обновление данных автомойки.

        :param car_wash_id: Идентификатор автомойки.
        :param new_values: Словарь с обновляемыми полями.
        :param files: Словарь с файлами для загрузки (например, изображение).
        :return: Объект httpx.Response.
        """
        api_url = f"{str(self.url).rstrip('/')}/car_washes/{car_wash_id}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
        }

        data = {'new_values': json.dumps(new_values)} if new_values else None

        try:
            response = httpx.patch(
                api_url,
                files=files,
                data=data,
                headers=headers,
            )
            return response
        except httpx.RequestError as e:
            print(f'Ошибка запроса при обновлении автомойки: {e}')
            return None

    def get_user_by_id(self, user_id: int) -> httpx.Response:
        api_url = f"{str(self.url).rstrip('/')}/users/{user_id}"
        headers = self.get_headers()
        try:
            response = httpx.get(api_url, headers=headers)
            return response
        except httpx.RequestError as e:
            print(
                f'Ошибка запроса при получении пользователя с ID '
                f'{user_id}: {e}'
            )
            return None

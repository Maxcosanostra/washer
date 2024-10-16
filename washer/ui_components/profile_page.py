import io
import json

import flet as ft
import httpx

from washer.config import config
from washer.ui_components.select_car_page import SelectCarPage


class ProfilePage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.api_url = config.api_url
        self.username = self.page.client_storage.get('username')

        self.avatar_url = self.page.client_storage.get('avatar_url')
        if not self.avatar_url:
            self.get_user_data()

        self.cars = []
        self.load_user_cars_from_server()

        self.bookings = []
        self.load_user_bookings_from_server()

        self.avatar_container = self.create_avatar_container()
        self.file_picker = self.create_file_picker()
        page.overlay.append(self.file_picker)

        page.clean()
        page.add(self.create_profile_page())

    def on_login_success(self):
        self.get_user_data()
        self.page.clean()
        self.page.add(self.create_profile_page())
        self.page.update()

    def load_user_cars_from_server(self):
        """Загрузка автомобилей пользователя с сервера"""
        try:
            access_token = self.page.client_storage.get('access_token')
            user_id = self.page.client_storage.get('user_id')

            if not user_id:
                print('User ID not found!')
                return

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
            }

            url = (
                f'{self.api_url.rstrip("/")}/cars?user_id={user_id}&limit=100'
            )

            response = httpx.get(url, headers=headers)

            if response.status_code == 200:
                cars = response.json().get('data', [])
                if cars:
                    print(f'Автомобили успешно загружены: {cars}')
                    self.cars = cars

                    self.page.client_storage.set(f'cars_{self.username}', cars)
                else:
                    print('Автомобили не найдены на сервере.')
                    self.cars = []
            else:
                print(
                    f'Ошибка при загрузке автомобилей с сервера: '
                    f'{response.status_code} - {response.text}'
                )
        except Exception as e:
            print(f'Ошибка при запросе автомобилей с сервера: {e}')

    def load_user_bookings_from_server(self):
        try:
            access_token = self.page.client_storage.get('access_token')
            user_id = self.page.client_storage.get('user_id')

            if not user_id:
                print('User ID not found!')
                return

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
            }

            url = (
                f'{self.api_url.rstrip("/")}/car_washes/bookings'
                f'?user_id={user_id}&limit=100'
            )

            response = httpx.get(url, headers=headers)

            if response.status_code == 200:
                bookings = response.json().get('data', [])
                if bookings:
                    print(f'Букинги успешно загружены: {bookings}')
                    self.bookings = bookings
                    self.page.client_storage.set(
                        f'bookings_{self.username}', bookings
                    )
                else:
                    print('Букинги не найдены на сервере.')
                    self.bookings = []
            else:
                print(
                    f'Ошибка при загрузке букингов: '
                    f'{response.status_code} - {response.text}'
                )
        except Exception as e:
            print(f'Ошибка при запросе букингов с сервера: {e}')

    def create_tabs(self):
        return ft.Tabs(
            tabs=[
                ft.Tab(
                    text='Мои автомобили',
                    content=ft.Container(
                        content=ft.Column(
                            controls=self.create_car_blocks()
                            + [
                                ft.ElevatedButton(
                                    text='Добавить автомобиль',
                                    on_click=self.on_add_car_click,
                                    bgcolor=ft.colors.PURPLE,
                                    color=ft.colors.WHITE,
                                )
                            ],
                            spacing=15,
                            scroll='adaptive',
                        ),
                        height=400,
                    ),
                ),
                ft.Tab(
                    text='Мои записи',
                    content=ft.Container(
                        content=ft.Column(
                            controls=self.create_booking_blocks()
                            or [
                                ft.Text(
                                    'Тут будут отображаться ваши записи...',
                                    size=14,
                                    color=ft.colors.GREY_500,
                                    weight=ft.FontWeight.NORMAL,
                                )
                            ],
                            spacing=15,
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            scroll='adaptive',
                        ),
                        height=400,
                    ),
                ),
            ],
            expand=True,
            animation_duration=300,
        )

    def create_profile_card(self):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.icons.ARROW_BACK,
                                on_click=self.on_back_click,
                            ),
                            ft.Container(expand=1),
                            ft.IconButton(
                                icon=ft.icons.LOGOUT,
                                on_click=self.on_logout_click,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(
                        content=self.avatar_container,
                        alignment=ft.alignment.center,
                        padding=ft.padding.only(top=-50),
                    ),
                    ft.Container(
                        content=ft.Text(
                            self.username, size=20, weight=ft.FontWeight.BOLD
                        ),
                        alignment=ft.alignment.center,
                        padding=ft.padding.only(top=-10),
                    ),
                    ft.Container(
                        content=ft.ElevatedButton(
                            icon=ft.icons.CAMERA_ALT,
                            text='Изменить фото профиля',
                            on_click=self.on_avatar_click,
                            width=300,
                        ),
                        alignment=ft.alignment.center,
                        padding=ft.padding.only(top=5),
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
            ),
            bgcolor=ft.colors.GREY_900,
            padding=ft.padding.all(10),
            border_radius=ft.border_radius.all(20),
            height=250,
        )

    def create_profile_page(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    self.create_profile_card(),
                    self.create_tabs(),
                ],
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
                expand=True,
            ),
            width=350,
            height=720,
            padding=ft.padding.all(20),
            border_radius=ft.border_radius.all(12),
        )

    def create_car_blocks(self):
        car_blocks = []

        print(f'Создаем карточки для автомобилей: {len(self.cars)}')

        for index, car in enumerate(self.cars):
            print(f'Отображаем автомобиль {index + 1}: {car}')

            car_name = car.get('name', 'Название не указано')

            car_block = ft.Card(
                content=ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Text(
                                            f'{car_name}',
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                    ],
                                    spacing=5,
                                ),
                                width=240,
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE,
                                on_click=lambda e, i=index: self.on_delete_car(
                                    i
                                ),
                                icon_color=ft.colors.RED,
                                padding=ft.padding.only(left=10, bottom=35),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    padding=ft.padding.all(10),
                    bgcolor=ft.colors.GREY_900,
                    border_radius=ft.border_radius.all(15),
                ),
                width=300,
                elevation=2,
            )
            car_blocks.append(car_block)

        if not car_blocks:
            print('Нет автомобилей для отображения')

        return car_blocks

    def create_booking_blocks(self):
        booking_blocks = []

        if not self.bookings:
            return [
                ft.Container(
                    content=ft.Text(
                        'Тут будут отображаться ваши записи...',
                        size=14,
                        color=ft.colors.GREY_500,
                        weight=ft.FontWeight.NORMAL,
                    ),
                    alignment=ft.alignment.center,
                    expand=True,
                    height=400,
                )
            ]

        for _index, booking in enumerate(self.bookings):
            booking_date = booking['start_datetime'].split('T')[0]
            booking_time = booking['start_datetime'].split('T')[1][:5]

            formatted_date = self.format_date(booking_date)

            booking_block = ft.Card(
                content=ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Text(
                                            f'Дата: {formatted_date}',
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        ft.Text(f'Время: {booking_time}'),
                                        ft.Text(
                                            f"Стоимость: {booking['price']} ₸"
                                        ),
                                    ],
                                    spacing=5,
                                ),
                                width=240,
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE,
                                on_click=lambda e,
                                booking_id=booking['id']: self.delete_booking(
                                    booking_id
                                ),
                                icon_color=ft.colors.RED,
                                padding=ft.padding.only(left=10, bottom=35),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    padding=ft.padding.all(10),
                    bgcolor=ft.colors.GREY_900,
                    border_radius=ft.border_radius.all(15),
                ),
                width=300,
                elevation=2,
            )
            booking_blocks.append(booking_block)

        return booking_blocks

    def format_date(self, booking_date):
        import datetime

        months = {
            1: 'января',
            2: 'февраля',
            3: 'марта',
            4: 'апреля',
            5: 'мая',
            6: 'июня',
            7: 'июля',
            8: 'августа',
            9: 'сентября',
            10: 'октября',
            11: 'ноября',
            12: 'декабря',
        }
        date_obj = datetime.datetime.strptime(booking_date, '%Y-%m-%d')
        return f'{date_obj.day} {months[date_obj.month]}'

    def load_location_by_id(self, location_id):
        try:
            access_token = self.page.client_storage.get('access_token')

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
            }

            url = f"{self.api_url.rstrip('/')}/locations/{location_id}"

            response = httpx.get(url, headers=headers)

            if response.status_code == 200:
                location = response.json().get('data', {})
                return location
            else:
                print(
                    f'Ошибка при загрузке данных автомойки: '
                    f'{response.status_code}'
                )
                return {}
        except Exception as e:
            print(f'Ошибка при запросе данных автомойки: {e}')
            return {}

    def delete_booking(self, booking_id):
        try:
            access_token = self.page.client_storage.get('access_token')
            if not access_token:
                print('Access token не найден.')
                return

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
            }

            url = (
                f'{self.api_url.rstrip("/")}/car_washes/bookings/{booking_id}'
            )

            response = httpx.delete(url, headers=headers)

            if response.status_code == 200:
                print(f'Букинг с ID {booking_id} успешно удален.')
                self.bookings = [
                    b for b in self.bookings if b['id'] != booking_id
                ]
                self.page.clean()
                self.page.add(self.create_profile_page())
                self.page.update()
            else:
                print(
                    f'Ошибка при удалении букинга: '
                    f'{response.status_code} - {response.text}'
                )
        except Exception as e:
            print(f'Ошибка при запросе удаления букинга: {e}')

    def create_avatar_container(self):
        avatar_url = self.avatar_url or None

        if avatar_url:
            print('Аватар загружен из локальной памяти:', avatar_url)
            avatar_content = ft.Image(
                src=avatar_url,
                width=100,
                height=100,
                fit=ft.ImageFit.COVER,
                border_radius=ft.border_radius.all(50),
            )
        else:
            print(
                'Аватар не найден в локальной памяти. '
                'Используем иконку по умолчанию.'
            )
            avatar_content = ft.Icon(
                ft.icons.PERSON,
                size=100,
                color=ft.colors.GREY,
            )

        self.avatar_image = avatar_content

        return ft.Container(
            content=self.avatar_image,
            alignment=ft.alignment.center,
            padding=20,
            on_click=self.on_avatar_click,
        )

    def create_file_picker(self):
        return ft.FilePicker(on_result=self.on_picture_select)

    def on_avatar_click(self, e):
        self.file_picker.pick_files(allow_multiple=False)

    def on_picture_select(self, e: ft.FilePickerResultEvent):
        if e.files:
            try:
                with open(e.files[0].path, 'rb') as image_file:
                    self.selected_image_bytes = image_file.read()

                avatar_url = e.files[0].path
                self.avatar_container.content = ft.Image(
                    src=avatar_url,
                    width=100,
                    height=100,
                    fit=ft.ImageFit.COVER,
                    border_radius=ft.border_radius.all(50),
                )
                self.page.update()

                self.upload_avatar_to_server()

            except Exception as ex:
                print(f'Ошибка при открытии файла: {ex}')

    def upload_avatar_to_server(self):
        try:
            user_id = self.page.client_storage.get('user_id')
            access_token = self.page.client_storage.get('access_token')
            if not user_id or not access_token:
                print('User ID или access_token не найдены')
                return

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
            }

            files = {
                'image': ('avatar.png', io.BytesIO(self.selected_image_bytes))
            }

            new_values = {'username': self.username}

            url = f"{self.api_url.rstrip('/')}/users/{user_id}"

            response = httpx.patch(
                url,
                files=files,
                data={'new_values': json.dumps(new_values)},
                headers=headers,
            )

            if response.status_code == 200:
                print('Аватар успешно загружен на сервер')
                self.get_user_data()

            else:
                print(
                    f'Ошибка загрузки аватара: '
                    f'{response.status_code} - {response.text}'
                )
        except Exception as e:
            print(f'Ошибка при загрузке аватара на сервер: {e}')

    def get_user_data(self):
        try:
            access_token = self.page.client_storage.get('access_token')
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
            }

            url = f"{self.api_url.rstrip('/')}/users/me"

            response = httpx.get(url, headers=headers)

            if response.status_code == 200:
                user_data = response.json()
                avatar_url = user_data.get('image_link')
                if avatar_url:
                    print('Аватар загружен с сервера:', avatar_url)
                    self.page.client_storage.set('avatar_url', avatar_url)
                    self.avatar_url = avatar_url

                    self.avatar_container.content = ft.Image(
                        src=avatar_url,
                        width=100,
                        height=100,
                        fit=ft.ImageFit.COVER,
                        border_radius=ft.border_radius.all(50),
                    )
                    self.page.update()
            else:
                print(
                    f'Ошибка при получении данных пользователя с сервера: '
                    f'{response.status_code} - {response.text}'
                )
        except Exception as e:
            print(f'Ошибка при запросе данных пользователя с сервера: {e}')

    def on_delete_avatar_click(self, e):
        self.page.client_storage.remove('avatar_url')

        self.avatar_container.content = ft.Icon(
            ft.icons.PERSON, size=100, color=ft.colors.GREY
        )
        self.page.update()

    def on_add_car_click(self, e):
        SelectCarPage(self.page, self.on_car_saved)

    def on_car_saved(self, car):
        user_key = f'cars_{self.username}'
        saved_cars = self.page.client_storage.get(user_key) or []

        saved_cars.append(car)
        self.page.client_storage.set(user_key, saved_cars)

        self.cars = saved_cars
        self.page.clean()
        self.page.add(self.create_profile_page())
        self.page.update()

    def on_delete_car(self, index):
        car_id = self.cars[index]['id']

        access_token = self.page.client_storage.get('access_token')

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

        url = f'{self.api_url.rstrip("/")}/cars/{car_id}'
        print(f'Отправка DELETE запроса на {url}')

        response = httpx.delete(url, headers=headers)

        if response.status_code == 200:
            del self.cars[index]
            self.page.client_storage.set(f'cars_{self.username}', self.cars)

            self.page.clean()
            self.page.add(self.create_profile_page())
            self.page.update()
            print(f'Автомобиль с ID {car_id} успешно удалён.')
        else:
            print(f'Ошибка при удалении автомобиля: {response.text}')

    def on_back_click(self, e):
        from washer.ui_components.wash_selection_page import WashSelectionPage

        WashSelectionPage(self.page)

    def on_logout_click(self, e):
        user_key = f'cars_{self.username}'
        self.page.client_storage.remove(user_key)

        self.page.client_storage.remove('access_token')
        self.page.client_storage.remove('refresh_token')
        self.page.client_storage.remove('username')
        self.page.client_storage.remove('avatar_url')

        from washer.ui_components.sign_in_page import SignInPage

        SignInPage(self.page)

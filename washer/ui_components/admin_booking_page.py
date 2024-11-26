import datetime
import locale

import flet as ft
import httpx

from washer.api_requests import BackendApi
from washer.config import config


class AdminSelectCarPage:
    def __init__(
        self,
        page: ft.Page,
        on_car_saved,
        car_wash,
        box_id,
        date,
        time,
        locations=None,
    ):
        self.page = page
        self.api_url = config.api_url
        self.on_car_saved = on_car_saved
        self.brands_dict = {}
        self.full_brands_list = []
        self.selected_brand = None
        self.selected_model_id = None
        self.selected_generation = None
        self.selected_generation_id = None
        self.generation_year_range = None
        self.generation_codes = None
        self.generations = []
        self.body_types_dict = {}
        self.selected_body_type = None
        self.brand_button_text = 'Выберите марку автомобиля'
        self.selected_car = {}
        self.car_wash = car_wash
        self.snack_bar = None
        self.box_id = box_id
        self.date = date
        self.time = time
        self.locations = locations
        self.api = BackendApi()
        self.api.set_access_token(self.page.client_storage.get('access_token'))

        self.car_price = 0
        self.price_text = ft.Text(
            'Стоимость: ₸0',
            size=32,
            weight=ft.FontWeight.BOLD,
        )

        self.save_button = self.create_next_button()
        self.save_button.disabled = True

        self.confirm_button = ft.ElevatedButton(
            text='Подтвердить букинг',
            on_click=self.on_confirm_booking,
            width=300,
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE,
            disabled=True,
        )

        self.search_dialog = self.create_search_dialog()
        self.brand_button = self.create_brand_button()
        self.model_dropdown = self.create_model_dropdown()
        self.generation_dropdown = self.create_generation_dropdown()
        self.body_type_dropdown = self.create_body_type_dropdown()

        page.clean()
        page.add(self.create_car_selection_page())
        page.add(self.price_text)
        page.add(self.confirm_button)

        self.load_brands()
        self.setup_snack_bar()

    def on_confirm_booking(self, e):
        if not (
            self.selected_car
            and self.selected_car.get('user_car_id')
            and self.car_price
            and self.box_id
            and self.date
            and self.time
        ):
            self.show_error_message(
                'Пожалуйста, выберите все необходимые данные.'
            )
            return

        start_datetime = f'{self.date}T{self.time}:00'
        end_datetime = (
            datetime.datetime.fromisoformat(start_datetime)
            + datetime.timedelta(hours=2)
        ).isoformat()

        user_car_id = self.selected_car.get('user_car_id')
        if user_car_id is None:
            self.show_error_message('ID выбранного автомобиля недоступен.')
            return

        booking_data = {
            'box_id': self.box_id,
            'user_car_id': user_car_id,
            'is_exception': False,
            'start_datetime': start_datetime,
            'end_datetime': end_datetime,
        }

        try:
            response = self.api.create_booking(booking_data)
            if response.status_code == 200:
                print('Букинг успешно создан!')
                self.show_success_message('Букинг успешно создан!')
                self.confirm_button.disabled = True
                self.page.update()

                from washer.ui_components.admin_booking_table import (
                    AdminBookingTable,
                )

                AdminBookingTable(
                    self.page,
                    self.car_wash,
                    self.api_url,
                    self.date,
                    selected_date=self.date,
                )

            else:
                print(f'Ошибка создания букинга: {response.text}')
                self.show_error_message(
                    f'Ошибка создания букинга: {response.text}'
                )
        except Exception as ex:
            print(f'Ошибка: {str(ex)}')
            self.show_error_message(f'Ошибка: {str(ex)}')

    def on_car_saved(self, car):
        self.selected_car = car
        print(f'Сохраненные данные автомобиля: {car}')

        if (
            self.selected_car
            and self.selected_car.get('user_car_id')
            and self.car_price
            and self.box_id
            and self.date
            and self.time
        ):
            self.confirm_button.disabled = False
        else:
            self.confirm_button.disabled = True

        self.page.update()

    def on_car_select(self, e):
        self.selected_car_id = e.control.value
        if (
            self.selected_car_id
            and self.car_price
            and self.box_id
            and self.date
            and self.time
        ):
            self.confirm_button.disabled = False
        else:
            self.confirm_button.disabled = True
        self.page.update()

    def create_car_selection_page(self):
        return ft.Container(
            content=ft.ListView(
                controls=[
                    ft.Container(height=20),
                    self.create_back_button(),
                    ft.Container(
                        content=ft.Text(
                            'Выберите автомобиль',
                            size=20,
                            weight=ft.FontWeight.BOLD,
                        ),
                        alignment=ft.alignment.center,
                        margin=ft.margin.only(bottom=20),
                    ),
                    ft.Container(
                        content=self.brand_button,
                        alignment=ft.alignment.center,
                        width=300,
                        margin=ft.margin.only(bottom=10),
                    ),
                    ft.Container(
                        content=self.model_dropdown,
                        alignment=ft.alignment.center,
                        width=300,
                        margin=ft.margin.only(bottom=10),
                    ),
                    ft.Container(
                        content=self.generation_dropdown,
                        alignment=ft.alignment.center,
                        width=300,
                        margin=ft.margin.only(bottom=10),
                    ),
                    ft.Container(
                        content=self.body_type_dropdown,
                        alignment=ft.alignment.center,
                        width=300,
                        margin=ft.margin.only(bottom=10),
                    ),
                    ft.Divider(),
                    ft.Container(
                        content=self.price_text,
                        alignment=ft.alignment.center,
                        margin=ft.margin.only(bottom=10),
                    ),
                    ft.Divider(),
                    ft.Container(
                        content=self.save_button,
                        alignment=ft.alignment.center,
                        width=300,
                        margin=ft.margin.only(bottom=20),
                    ),
                ],
                expand=True,
                padding=ft.padding.symmetric(horizontal=20, vertical=20),
            ),
            expand=True,
            border_radius=ft.border_radius.all(12),
        )

    def refresh_token(self):
        refresh_token = self.page.client_storage.get('refresh_token')
        if not refresh_token:
            print('Refresh token not found, redirecting to login.')
            return False

        response = httpx.post(
            f'{self.api_url}/jwt/refresh',
            json={'refresh_token': refresh_token},
        )

        if response.status_code == 200:
            tokens = response.json()
            self.page.client_storage.set(
                'access_token', tokens['access_token']
            )
            self.page.client_storage.set(
                'refresh_token', tokens['refresh_token']
            )
            return True
        else:
            print(f'Error refreshing token: {response.text}')
            return False

    def load_brands(self):
        access_token = self.page.client_storage.get('access_token')
        if not access_token:
            print('Access token not found, redirecting to login.')
            return

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

        url = f'{self.api_url.rstrip("/")}/cars/brands?limit=1000'

        response = httpx.get(url, headers=headers)

        if response.status_code == 401:
            if 'token has expired' in response.text.lower():
                if self.refresh_token():
                    self.load_brands()
                else:
                    self.page.add(
                        ft.Text(
                            'Session expired, please login again.',
                            color=ft.colors.RED,
                        )
                    )
        elif response.status_code == 200:
            brands = response.json().get('data', [])
            self.full_brands_list = brands
            self.brands_dict = {brand['name']: brand['id'] for brand in brands}
            self.update_brands_list(brands)

    def update_brands_list(self, brands):
        self.brands_list.controls.clear()
        self.brands_list.controls.extend(
            [
                ft.ListTile(
                    title=ft.Text(brand['name']),
                    on_click=self.on_brand_select,
                    data=brand['name'],
                )
                for brand in brands
            ]
        )
        self.page.update()

    def create_search_dialog(self):
        self.search_bar = ft.TextField(
            label='',
            hint_text='',
            on_change=self.on_search_change,
            width=300,
            height=30,
        )

        self.brands_list = ft.ListView(controls=[], height=300)

        return ft.AlertDialog(
            title=ft.Text('Выберите марку автомобиля'),
            content=ft.Container(
                content=ft.Column([self.search_bar, self.brands_list]),
                width=300,
            ),
            actions=[
                ft.TextButton('Закрыть', on_click=self.close_search_dialog)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def open_search_dialog(self, e):
        self.search_dialog.open = True
        self.page.dialog = self.search_dialog
        self.page.update()

    def close_search_dialog(self, e):
        self.search_dialog.open = False
        self.page.dialog = None
        self.page.update()

    def on_search_change(self, e):
        search_query = e.data.lower()

        if search_query == '':
            filtered_brands = self.full_brands_list
        else:
            filtered_brands = [
                {'name': name}
                for name in self.brands_dict
                if search_query in name.lower()
            ]

        self.update_brands_list(filtered_brands)

    def on_brand_select(self, e):
        selected_brand = e.control.data
        brand_id = self.brands_dict.get(selected_brand)

        if not brand_id:
            print('ID марки не найден.')
            return

        access_token = self.page.client_storage.get('access_token')
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

        clean_url = self.api_url.rstrip('/')
        url = f'{clean_url}/cars/models?brand_id={brand_id}&limit=100'

        response = httpx.get(url, headers=headers)

        if response.status_code == 200:
            models = response.json().get('data', [])
            self.models_dict = {model['name']: model['id'] for model in models}
            self.model_dropdown.options = [
                ft.dropdown.Option(model['name']) for model in models
            ]
            self.selected_brand = selected_brand

            self.brand_button_text = f'Марка: {selected_brand}'
            self.brand_button.content.controls[
                0
            ].value = self.brand_button_text

            self.model_dropdown.value = None
            self.generation_dropdown.options = []
            self.generation_dropdown.visible = False
            self.selected_generation = None
            self.body_type_dropdown.options = []
            self.body_type_dropdown.visible = False
            self.selected_model_id = None
            self.selected_generation_id = None
            self.save_button.disabled = True

            self.page.update()

        self.close_search_dialog(None)

    def on_model_select(self, e):
        selected_model = e.control.value
        self.selected_model_id = self.models_dict.get(selected_model)

        if not self.selected_model_id:
            print('ID модели не найден.')
            return

        access_token = self.page.client_storage.get('access_token')
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

        clean_url = self.api_url.rstrip('/')
        url = (
            f'{clean_url}/cars/generations'
            f'?model_id={self.selected_model_id}&limit=100'
        )

        response = httpx.get(url, headers=headers)

        if response.status_code == 200:
            generations = response.json().get('data', [])

            if not generations:
                print('Поколения для выбранной модели не найдены.')
                self.generation_dropdown.visible = False
                return

            self.generations = generations
            self.body_type_dropdown.options = []
            self.body_type_dropdown.value = None
            self.body_type_dropdown.visible = False
            self.save_button.disabled = True

            if len(generations) == 1:
                self.selected_generation = generations[0]['name']
                self.selected_generation_id = generations[0]['id']
                self.generation_year_range = generations[0].get(
                    'year_range', ''
                )
                self.generation_codes = generations[0].get('codes', '')

                self.show_snack_bar(
                    f'Поколение "{self.selected_generation}" '
                    f'выбрано автоматически',
                    bgcolor=ft.colors.BLUE,
                )

                print(
                    f'Автоматически выбрано поколение: '
                    f'{self.selected_generation} '
                    f'({self.generation_codes}) ({self.generation_year_range})'
                )
                self.generation_dropdown.visible = False
                self.get_body_type(self.selected_generation_id)
            else:
                self.generations_dict = {
                    f'{gen["name"]} ({gen["year_range"]})': gen['id']
                    for gen in generations
                }
                self.generation_dropdown.options = [
                    ft.dropdown.Option(f'{gen["name"]} ({gen["year_range"]})')
                    for gen in generations
                ]
                self.generation_dropdown.visible = True

                def on_generation_select(e):
                    if self.generation_dropdown.value:
                        self.selected_generation_id = (
                            self.generations_dict.get(
                                self.generation_dropdown.value
                            )
                        )
                        self.body_type_dropdown.options = []
                        self.body_type_dropdown.value = None
                        self.body_type_dropdown.visible = False
                        self.save_button.disabled = True
                        self.get_body_type(self.selected_generation_id)

                        selected_gen = next(
                            gen
                            for gen in self.generations
                            if gen['id'] == self.selected_generation_id
                        )
                        self.selected_generation = selected_gen['name']
                        self.generation_year_range = selected_gen.get(
                            'year_range', ''
                        )
                        self.generation_codes = selected_gen.get('codes', '')

                self.generation_dropdown.on_change = on_generation_select
                self.page.update()

        else:
            print(f'Ошибка при загрузке поколений: {response.text}')

    def on_generation_select(self, e):
        selected_generation = e.control.value
        self.selected_generation_id = self.generations_dict.get(
            selected_generation
        )

        print(
            f'Выбранное поколение: {selected_generation}, '
            f'ID поколения: {self.selected_generation_id}'
        )

        if not self.selected_generation_id:
            print('ID поколения не найден.')
            return

        self.selected_generation = selected_generation
        generation_info = next(
            (
                gen
                for gen in self.generations
                if gen['id'] == self.selected_generation_id
            ),
            None,
        )
        if generation_info:
            self.generation_year_range = generation_info.get('year_range', '')
            self.generation_codes = generation_info.get('codes', '')

        self.body_type_dropdown.options = []
        self.body_type_dropdown.value = None
        self.body_type_dropdown.visible = False
        self.page.update()
        print('Скрыт и сброшен dropdown с типом кузова')

        self.get_body_type(self.selected_generation_id)

    def get_body_type(self, generation_id):
        access_token = self.page.client_storage.get('access_token')
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

        clean_url = self.api_url.rstrip('/')
        url = (
            f'{clean_url}/cars/configurations'
            f'?generation_id={generation_id}&limit=100'
        )

        response = httpx.get(url, headers=headers)

        if response.status_code == 200:
            configurations = response.json().get('data', [])
            unique_body_types = {
                config['body_type_id'] for config in configurations
            }

            if len(unique_body_types) == 1:
                body_type_id = configurations[0]['body_type_id']
                body_type_name = self.get_body_type_name(body_type_id)
                self.selected_body_type = body_type_name
                print(f'Автоматически выбран тип кузова: {body_type_name}')

                self.show_snack_bar(
                    f'Тип кузова "{body_type_name}" выбран автоматически',
                    bgcolor=ft.colors.BLUE,
                )

                self.load_car_price(body_type_id)
                self.body_type_dropdown.visible = False
                self.save_button.disabled = False
                self.page.update()
            else:
                self.body_types_dict = self.fetch_body_type_names(
                    unique_body_types
                )
                self.body_type_dropdown.options = [
                    ft.dropdown.Option(self.body_types_dict[bt])
                    for bt in unique_body_types
                ]
                self.body_type_dropdown.value = None
                self.body_type_dropdown.visible = True
                self.save_button.disabled = True

                def on_body_type_select(e):
                    if self.body_type_dropdown.value:
                        selected_body_type_id = next(
                            (
                                bt_id
                                for bt_id, name in self.body_types_dict.items()
                                if name == self.body_type_dropdown.value
                            ),
                            None,
                        )
                        if selected_body_type_id:
                            self.selected_body_type = (
                                self.body_type_dropdown.value
                            )
                            self.load_car_price(selected_body_type_id)
                        self.save_button.disabled = False
                        self.page.update()

                self.body_type_dropdown.on_change = on_body_type_select
                self.page.update()
        else:
            print(f'Ошибка при загрузке конфигураций: {response.text}')

    def load_car_price(self, body_type_id):
        print(
            f"Загружаем цену для car_wash_id: "
            f"{self.car_wash['id']}, body_type_id: {body_type_id}"
        )

        response = self.api.get_prices(self.car_wash['id'])

        if response.status_code == 200:
            prices = response.json().get('data', [])
            print(f'Цены получены: {prices}')

            price = next(
                (
                    price
                    for price in prices
                    if price['body_type_id'] == body_type_id
                ),
                None,
            )

            if price:
                self.car_price = price['price']
                print(
                    f'Цена для body_type_id {body_type_id}: {self.car_price}'
                )
                self.show_price()
            else:
                print(
                    f'Цена для body_type_id '
                    f'{body_type_id} не найдена в списке.'
                )
        else:
            print(
                f'Ошибка загрузки цены: '
                f'{response.status_code} - {response.text}'
            )

    def show_price(self):
        self.price_text.value = f'Стоимость: ₸{int(self.car_price)}'
        self.page.update()

    def fetch_body_type_names(self, body_type_ids):
        access_token = self.page.client_storage.get('access_token')
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

        clean_url = self.api_url.rstrip('/')
        url = f'{clean_url}/cars/body_types?limit=100'

        response = httpx.get(url, headers=headers)

        if response.status_code == 200:
            body_types = response.json().get('data', [])
            return {
                bt['id']: bt['name']
                for bt in body_types
                if bt['id'] in body_type_ids
            }

    def get_body_type_name(self, body_type_id):
        return self.fetch_body_type_names([body_type_id]).get(body_type_id)

    def create_model_dropdown(self):
        return ft.Dropdown(
            label='Выберите модель',
            width=300,
            border_radius=ft.border_radius.all(25),
            options=[],
            on_change=self.on_model_select,
        )

    def create_generation_dropdown(self):
        return ft.Dropdown(
            label='Выберите поколение',
            width=300,
            border_radius=ft.border_radius.all(25),
            options=[],
            visible=False,
        )

    def create_body_type_dropdown(self):
        return ft.Dropdown(
            label='Выберите тип кузова',
            width=300,
            border_radius=ft.border_radius.all(25),
            options=[],
            visible=False,
        )

    def create_brand_button(self):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(self.brand_button_text, size=16),
                    ft.Icon(ft.icons.ARROW_DROP_DOWN),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            border=ft.border.all(1, ft.colors.GREY),
            border_radius=ft.border_radius.all(25),
            on_click=self.open_search_dialog,
            width=300,
            height=50,
        )

    def create_next_button(self):
        return ft.ElevatedButton(
            text='Далее',
            width=300,
            bgcolor=ft.colors.PURPLE,
            color=ft.colors.WHITE,
            on_click=self.on_save_click,
        )

    def setup_snack_bar(self):
        self.snack_bar = ft.SnackBar(
            content=ft.Text(''),
            bgcolor=ft.colors.GREEN,
            duration=3000,
        )
        self.page.overlay.append(self.snack_bar)
        self.page.update()

    def show_snack_bar(
        self,
        message: str,
        bgcolor: str = ft.colors.GREEN,
        text_color: str = ft.colors.WHITE,
    ):
        print(f'Показываем сообщение: {message}')

        self.snack_bar.content.value = message
        self.snack_bar.content.color = text_color

        self.snack_bar.bgcolor = bgcolor
        self.snack_bar.open = True

        self.page.update()

    def show_success_message(self, message: str):
        """Показать уведомление об успехе"""
        self.show_snack_bar(message, bgcolor=ft.colors.GREEN)

    def show_error_message(self, message: str):
        """Показать уведомление об ошибке"""
        self.show_snack_bar(message, bgcolor=ft.colors.RED)

    def on_save_click(self, e):
        access_token = self.page.client_storage.get('access_token')

        if not access_token:
            self.show_error_message('Токен доступа отсутствует!')
            return

        full_name = f'{self.selected_brand} {self.model_dropdown.value}'

        if self.selected_generation and self.selected_generation_id:
            generation_name = self.selected_generation
            generation_range = self.generation_year_range
            generation_codes = self.generation_codes

            if generation_codes and generation_range:
                full_name += (
                    f' {generation_name} ({generation_codes}) '
                    f'({generation_range})'
                )
            elif generation_codes:
                full_name += f' {generation_name} ({generation_codes})'
            elif generation_range:
                full_name += f' {generation_name} ({generation_range})'
            else:
                full_name += f' {generation_name}'

        if self.body_type_dropdown.value:
            full_name += f' {self.body_type_dropdown.value}'

        selected_car = {
            'brand': self.selected_brand,
            'model': self.model_dropdown.value,
            'generation': self.selected_generation or 'Не указано',
            'body_type': self.body_type_dropdown.value,
            'configuration_id': self.selected_generation_id,
            'name': full_name,
        }

        api_url = f"{self.api_url.rstrip('/')}/cars"

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

        try:
            response = httpx.post(api_url, json=selected_car, headers=headers)

            if response.status_code == 200:
                self.show_success_message(
                    f'Автомобиль "{full_name}" успешно сохранен!'
                )
                self.on_car_saved(response.json())

                self.selected_car = response.json()

                self.show_confirmation_page()

            else:
                error_message = response.text or 'Неизвестная ошибка'
                self.show_error_message(f'Ошибка: {error_message}')
        except Exception as e:
            self.show_error_message(f'Ошибка: {str(e)}')

    def show_confirmation_page(self):
        self.page.clean()

        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        date_obj = (
            self.date
            if isinstance(self.date, datetime.date)
            else datetime.datetime.strptime(self.date, '%Y-%m-%d').date()
        )
        formatted_date = date_obj.strftime('%d %B')
        day_of_week = date_obj.strftime('%a')
        day_of_week_translated = {
            'Mon': 'Пн',
            'Tue': 'Вт',
            'Wed': 'Ср',
            'Thu': 'Чт',
            'Fri': 'Пт',
            'Sat': 'Сб',
            'Sun': 'Вс',
        }.get(day_of_week, day_of_week)
        date_with_day = f'{formatted_date} ({day_of_week_translated})'

        generation_display = self.selected_generation
        if not generation_display and self.generation_year_range:
            generation_display = self.generation_year_range

        car_details = [
            ('Бренд', self.selected_brand),
            ('Модель', self.model_dropdown.value),
            ('Поколение', generation_display or 'Не указано'),
            (
                'Тип кузова',
                self.selected_body_type or self.body_type_dropdown.value,
            ),
        ]

        car_info_column = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(label, weight=ft.FontWeight.BOLD, size=16),
                        ft.Text(value, color=ft.colors.GREY_600, size=16),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
                for label, value in car_details
            ],
            spacing=10,
        )

        car_info_card = ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                'Информация об автомобиле',
                                size=18,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Divider(),
                            car_info_column,
                        ],
                        spacing=10,
                    ),
                    padding=ft.padding.all(20),
                ),
                elevation=3,
            ),
            width=370,
            margin=ft.margin.only(bottom=20),
        )

        booking_info_column = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text('Дата', weight=ft.FontWeight.BOLD, size=16),
                        ft.Text(
                            date_with_day, color=ft.colors.GREY_600, size=16
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Row(
                    [
                        ft.Text(
                            'Номер бокса', weight=ft.FontWeight.BOLD, size=16
                        ),
                        ft.Text(
                            str(self.box_id), color=ft.colors.GREY_600, size=16
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Row(
                    [
                        ft.Text('Время', weight=ft.FontWeight.BOLD, size=16),
                        ft.Text(
                            self.time[:5], color=ft.colors.GREY_600, size=16
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Row(
                    [
                        ft.Text(
                            'Стоимость', weight=ft.FontWeight.BOLD, size=16
                        ),
                        ft.Text(
                            f'₸{int(self.car_price)}',
                            color=ft.colors.GREY_600,
                            size=16,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=10,
        )

        booking_info_card = ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                'Информация о букинге',
                                size=18,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Divider(),
                            booking_info_column,
                        ],
                        spacing=10,
                    ),
                    padding=ft.padding.all(20),
                ),
                elevation=3,
            ),
            width=370,
            margin=ft.margin.only(bottom=20),
        )

        confirm_button = ft.ElevatedButton(
            text='Подтвердить букинг',
            on_click=self.on_confirm_booking,
            width=300,
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE,
        )

        back_button = ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        icon_size=30,
                        on_click=lambda e: self.on_back_to_car_selection(),
                    ),
                    ft.Text('Назад', size=16),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            margin=ft.margin.only(bottom=15),
        )

        self.page.add(
            ft.Container(
                content=ft.ListView(
                    controls=[
                        back_button,
                        car_info_card,
                        booking_info_card,
                        confirm_button,
                    ],
                    spacing=20,
                    padding=ft.padding.all(20),
                ),
                expand=True,
            )
        )

    def create_back_button(self):
        return ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        icon_size=30,
                        on_click=self.on_back_to_car_selection,
                    ),
                    ft.Text('Назад', size=16),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            margin=ft.margin.only(bottom=15),
        )

    def on_back_to_car_selection(self, e=None):
        self.page.clean()
        self.page.add(self.create_car_selection_page())

    def on_back_to_booking_page(self, e):
        from washer.ui_components.admin_booking_table import AdminBookingTable

        AdminBookingTable(self.page, self.car_wash, self.api_url, self.date)

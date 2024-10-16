import flet as ft
import httpx

from washer.config import config


class SelectCarPage:
    def __init__(self, page: ft.Page, on_car_saved):
        self.page = page
        self.api_url = config.api_url
        self.on_car_saved = on_car_saved
        self.brands_dict = {}
        self.full_brands_list = []
        self.selected_brand = None
        self.selected_model_id = None
        self.selected_generation = None
        self.selected_generation_id = None
        self.body_types_dict = {}
        self.brand_button_text = 'Выберите марку автомобиля'
        self.selected_car = {}

        self.search_dialog = self.create_search_dialog()
        self.brand_button = self.create_brand_button()

        self.model_dropdown = self.create_model_dropdown()
        self.generation_dropdown = self.create_generation_dropdown()
        self.body_type_dropdown = self.create_body_type_dropdown()
        self.save_button = self.create_save_button()

        page.clean()
        page.add(self.create_car_selection_page())

        self.load_brands()

    def create_car_selection_page(self):
        return ft.Container(
            content=ft.Container(
                content=ft.Column(
                    [
                        self.create_back_button(),
                        ft.Text(
                            'Выберите автомобиль',
                            size=20,
                            weight=ft.FontWeight.BOLD,
                        ),
                        self.brand_button,
                        self.model_dropdown,
                        self.generation_dropdown,
                        self.body_type_dropdown,
                        self.save_button,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                ),
                padding=ft.padding.all(20),
                width=400,
            ),
            alignment=ft.alignment.center,
            expand=True,
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
            print(f'New tokens received: {tokens}')
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
            self.redirect_to_sign_in_page()
            return

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

        url = f'{self.api_url.rstrip("/")}/cars/brands?limit=1000'
        print(f'Generated URL: {url}')

        response = httpx.get(url, headers=headers)

        if response.status_code == 401:
            if 'token has expired' in response.text.lower():
                print('Token has expired, attempting to refresh...')
                if self.refresh_token():
                    print('Token refreshed successfully, retrying request...')
                    self.load_brands()
                else:
                    print('Failed to refresh token, redirecting to login.')
                    self.page.add(
                        ft.Text(
                            'Session expired, please login again.',
                            color=ft.colors.RED,
                        )
                    )
                    self.redirect_to_sign_in_page()
        elif response.status_code == 200:
            brands = response.json().get('data', [])
            self.full_brands_list = brands
            self.brands_dict = {brand['name']: brand['id'] for brand in brands}
            self.update_brands_list(brands)
        else:
            print(
                f'Error loading brands: '
                f'{response.status_code} - {response.text}'
            )

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

        print(f'Выбранная марка: {selected_brand}, ID марки: {brand_id}')

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

        print(f'Запрашиваемый URL: {url}')

        response = httpx.get(url, headers=headers)

        if response.status_code == 401:
            if 'token has expired' in response.text.lower():
                print('Token has expired, attempting to refresh...')
                if self.refresh_token():
                    print('Token refreshed successfully, retrying request...')
                    self.on_brand_select(e)
                else:
                    print('Failed to refresh token, redirecting to login.')
                    self.page.add(
                        ft.Text(
                            'Session expired, please login again.',
                            color=ft.colors.RED,
                        )
                    )
                    self.redirect_to_sign_in_page()
        elif response.status_code == 200:
            models = response.json().get('data', [])
            if not models:
                print(f'Модели для марки {selected_brand} не найдены.')
            else:
                self.models_dict = {
                    model['name']: model['id'] for model in models
                }
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

                self.page.update()
        else:
            print(
                f'Ошибка при загрузке моделей автомобилей: '
                f'{response.status_code} - {response.text}'
            )

        self.close_search_dialog(None)

    def on_model_select(self, e):
        selected_model = e.control.value
        self.selected_model_id = self.models_dict.get(selected_model)

        print(
            f'Выбранная модель: '
            f'{selected_model}, ID модели: {self.selected_model_id}'
        )

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
            f'{clean_url}/cars/generations?'
            f'model_id={self.selected_model_id}&limit=100'
        )

        print(f'Запрашиваемый URL для поколений: {url}')

        response = httpx.get(url, headers=headers)

        if response.status_code == 401:
            if 'token has expired' in response.text.lower():
                print('Token has expired, attempting to refresh...')
                if self.refresh_token():
                    print('Token refreshed successfully, retrying request...')
                    self.on_model_select(e)
                else:
                    print('Failed to refresh token, redirecting to login.')
                    self.page.add(
                        ft.Text(
                            'Session expired, please login again.',
                            color=ft.colors.RED,
                        )
                    )
                    self.redirect_to_sign_in_page()
            else:
                print(
                    'Ошибка при загрузке поколений автомобилей: '
                    'Could not validate credentials'
                )
        elif response.status_code == 200:
            generations = response.json().get('data', [])

            if not generations:
                print('Поколения для выбранной модели не найдены.')
                self.generation_dropdown.visible = False
                return

            if len(generations) == 1:
                self.selected_generation = generations[0]['name']
                self.selected_generation_id = generations[0]['id']
                print(
                    f'Автоматически выбрано поколение: '
                    f'{self.selected_generation} '
                    f'({generations[0]["year_range"]})'
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
                self.generation_dropdown.on_change = self.on_generation_select

                print(f'Доступные поколения для модели {selected_model}:')
                for gen in generations:
                    print(
                        f'Поколение: '
                        f'{gen["name"]} ({gen["year_range"]}), ID: {gen["id"]}'
                    )

            self.page.update()
        else:
            print(
                f'Ошибка при загрузке поколений: '
                f'{response.status_code} - {response.text}'
            )

    def on_generation_select(self, e):
        """Обработчик выбора поколения"""
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
        self.body_type_dropdown.options = []
        self.body_type_dropdown.value = None
        self.body_type_dropdown.visible = False
        self.page.update()
        print('Скрыт и сброшен dropdown с типом кузова')

        self.get_body_type(self.selected_generation_id)

    def get_body_type(self, generation_id):
        """Запрос на получение типа кузова на основе поколения"""
        access_token = self.page.client_storage.get('access_token')
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

        clean_url = self.api_url.rstrip('/')
        url = (
            f'{clean_url}/cars/configurations?'
            f'generation_id={generation_id}&limit=100'
        )

        print(f'Запрашиваемый URL для конфигураций: {url}')

        response = httpx.get(url, headers=headers)

        if response.status_code == 401:
            if 'token has expired' in response.text.lower():
                print('Token has expired, attempting to refresh...')
                if self.refresh_token():
                    print('Token refreshed successfully, retrying request...')
                    self.get_body_type(generation_id)
                else:
                    print('Failed to refresh token, redirecting to login.')
                    self.page.add(
                        ft.Text(
                            'Session expired, please login again.',
                            color=ft.colors.RED,
                        )
                    )
                    self.redirect_to_sign_in_page()
            else:
                print(f'Ошибка при загрузке конфигураций: {response.text}')
        elif response.status_code == 200:
            configurations = response.json().get('data', [])
            if configurations:
                unique_body_types = {
                    config['body_type_id'] for config in configurations
                }

                if len(unique_body_types) > 1:
                    print(f'Доступные body_type_id: {unique_body_types}')

                    self.body_types_dict = self.fetch_body_type_names(
                        unique_body_types
                    )

                    self.body_type_dropdown.options = [
                        ft.dropdown.Option(self.body_types_dict[bt])
                        for bt in unique_body_types
                    ]
                    self.body_type_dropdown.value = None
                    self.body_type_dropdown.visible = True
                    self.page.update()

                    print(
                        'Выберите тип кузова: '
                        f'{[
                            self.body_types_dict[bt]
                            for bt in unique_body_types
                        ]}'
                    )

                else:
                    body_type_id = configurations[0]['body_type_id']
                    body_type_name = self.get_body_type_name(body_type_id)
                    print(f'Выбран тип кузова: {body_type_name}')
                    self.body_type_dropdown.value = body_type_name
                    self.body_type_dropdown.visible = True
                    self.page.update()

    def fetch_body_type_names(self, body_type_ids):
        """Запрос на получение имен типов кузова по их ID"""
        access_token = self.page.client_storage.get('access_token')
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

        clean_url = self.api_url.rstrip('/')
        url = f'{clean_url}/cars/body_types?limit=100'

        print(f'Запрашиваемый URL для типов кузова: {url}')

        response = httpx.get(url, headers=headers)

        if response.status_code == 401:
            if 'token has expired' in response.text.lower():
                print('Token has expired, attempting to refresh...')
                if self.refresh_token():
                    print('Token refreshed successfully, retrying request...')
                    self.fetch_body_type_names(body_type_ids)
                else:
                    print('Failed to refresh token, redirecting to login.')
                    self.page.add(
                        ft.Text(
                            'Session expired, please login again.',
                            color=ft.colors.RED,
                        )
                    )
                    self.redirect_to_sign_in_page()
            else:
                print(f'Ошибка при загрузке типов кузова: {response.text}')
        elif response.status_code == 200:
            body_types = response.json().get('data', [])
            return {
                bt['id']: bt['name']
                for bt in body_types
                if bt['id'] in body_type_ids
            }
        else:
            print(f'Ошибка при загрузке типов кузова: {response.text}')
            return {}

    def get_body_type_name(self, body_type_id):
        """Запрос на получение названия кузова на основе body_type_id"""
        body_type_name = self.fetch_body_type_names([body_type_id]).get(
            body_type_id, None
        )

        if body_type_name:
            print(f'Тип кузова: {body_type_name}')
        else:
            print('Тип кузова не найден.')

        return body_type_name

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
        """Кнопка для выбора марки автомобиля, стилизованная под dropdown"""
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

    def create_save_button(self):
        return ft.ElevatedButton(
            text='Сохранить',
            width=300,
            bgcolor=ft.colors.PURPLE,
            color=ft.colors.WHITE,
            on_click=self.on_save_click,
        )

    def on_save_click(self, e):
        access_token = self.page.client_storage.get('access_token')

        if not access_token:
            print('Токен доступа отсутствует!')
            self.page.add(
                ft.Text(
                    'Ошибка: Токен доступа отсутствует!', color=ft.colors.RED
                )
            )
            return

        selected_car = {
            'brand': self.selected_brand,
            'model': self.model_dropdown.value,
            'generation': self.selected_generation or 'Не указано',
            'body_type': self.body_type_dropdown.value,
            'configuration_id': self.selected_generation_id,
            'name': (
                f"{self.selected_brand} "
                f"{self.model_dropdown.value} "
                f"{self.selected_generation or ''}".strip()
            ),
        }

        api_url = f"{self.api_url.rstrip('/')}/cars"

        print(f'Отправка запроса на {api_url} с данными: {selected_car}')

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

        try:
            response = httpx.post(api_url, json=selected_car, headers=headers)

            if response.status_code == 200:
                print('Автомобиль успешно сохранен на сервере.')
                self.page.add(
                    ft.Text(
                        'Автомобиль успешно сохранен', color=ft.colors.GREEN
                    )
                )
                from washer.ui_components.profile_page import ProfilePage

                ProfilePage(self.page)
            else:
                error_message = response.text or 'Неизвестная ошибка'
                print(f'Ошибка при сохранении автомобиля: {error_message}')
                self.page.add(
                    ft.Text(f'Ошибка: {error_message}', color=ft.colors.RED)
                )
        except Exception as e:
            print(f'Ошибка при сохранении автомобиля: {e}')
            self.page.add(
                ft.Text(
                    f'Ошибка при сохранении автомобиля: {str(e)}',
                    color=ft.colors.RED,
                )
            )

    def update_profile_page(self):
        access_token = self.page.client_storage.get('access_token')
        user_id = self.page.client_storage.get('user_id')

        if not user_id:
            print('User ID not found!')
            return

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

        url = f'{self.api_url.rstrip("/")}/cars?user_id={user_id}'

        response = httpx.get(url, headers=headers)

        if response.status_code == 200:
            cars = response.json().get('data', [])
            print(f'Автомобили успешно загружены: {cars}')

            self.page.clean()
            self.page.add(self.create_profile_page(cars))
            self.page.update()
        else:
            print(f'Ошибка при загрузке автомобилей: {response.text}')

    def create_back_button(self):
        return ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        icon_size=30,
                        on_click=self.on_back_to_profile_click,
                    ),
                    ft.Text('Назад в профиль', size=16),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            margin=ft.margin.only(bottom=15),
        )

    def on_back_to_profile_click(self, _: ft.ControlEvent):
        from washer.ui_components.profile_page import ProfilePage

        ProfilePage(self.page)

import flet as ft
import httpx

from washer.config import config


class ProfilePage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.api_url = config.api_url
        self.brands_dict = {}
        self.full_brands_list = []
        self.selected_brand = None
        self.selected_model_id = None
        self.selected_generation = None
        self.selected_generation_id = None
        self.body_types_dict = {}
        self.brand_button_text = 'Выберите марку автомобиля'

        self.search_dialog = self.create_search_dialog()
        self.brand_button = self.create_brand_button()

        self.model_dropdown = self.create_model_dropdown()
        self.generation_dropdown = self.create_generation_dropdown()
        self.body_type_dropdown = self.create_body_type_dropdown()
        self.save_button = self.create_save_button()

        self.file_picker = self.create_file_picker()
        self.avatar_container = self.create_avatar_container()
        page.overlay.append(self.file_picker)

        page.clean()
        page.add(self.create_profile_container())

        self.load_brands()

    def create_file_picker(self):
        return ft.FilePicker(on_result=self.on_picture_select)

    def create_avatar_container(self):
        return ft.Container(
            content=ft.Image(
                src='https://via.placeholder.com/100',
                width=100,
                height=100,
                border_radius=ft.border_radius.all(50),
            ),
            on_click=self.on_picture_click,
        )

    def load_brands(self):
        clean_url = self.api_url.rstrip('/')

        access_token = self.page.client_storage.get('app.auth.access_token')
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

        response = httpx.get(
            f'{clean_url}/cars/brands?limit=1000', headers=headers
        )

        if response.status_code == 200:
            brands = response.json().get('data', [])
            self.full_brands_list = brands
            self.brands_dict = {brand['name']: brand['id'] for brand in brands}
            self.update_brands_list(brands)
        else:
            print(
                f'Ошибка при загрузке марок автомобилей: '
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

        access_token = self.page.client_storage.get('app.auth.access_token')
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

        clean_url = self.api_url.rstrip('/')
        url = f'{clean_url}/cars/models?brand_id={brand_id}&limit=100'

        print(f'Запрашиваемый URL: {url}')

        response = httpx.get(url, headers=headers)

        if response.status_code == 200:
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
            f'Выбранная модель: {selected_model}, '
            f'ID модели: {self.selected_model_id}'
        )

        if not self.selected_model_id:
            print('ID модели не найден.')
            return

        access_token = self.page.client_storage.get('app.auth.access_token')
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

        if response.status_code == 200:
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
                        f'Поколение: {gen["name"]}'
                        f' ({gen["year_range"]}), ID: {gen["id"]}'
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

        self.body_type_dropdown.options = []
        self.body_type_dropdown.value = None
        self.body_type_dropdown.visible = False
        self.page.update()
        print('Скрыт и сброшен dropdown с типом кузова')

        self.get_body_type(self.selected_generation_id)

    def get_body_type(self, generation_id):
        """Запрос на получение типа кузова на основе поколения"""
        access_token = self.page.client_storage.get('app.auth.access_token')
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

        if response.status_code == 200:
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
                        f'Выберите тип кузова: {
                        [self.body_types_dict[bt] for bt in unique_body_types]
                        }'
                    )
                else:
                    body_type_id = configurations[0]['body_type_id']
                    body_type_name = self.get_body_type_name(body_type_id)
                    print(f'Автоматически выбран тип кузова: {body_type_name}')
            else:
                print('Конфигурации не найдены.')
        else:
            print(
                f'Ошибка при загрузке конфигураций: '
                f'{response.status_code} - {response.text}'
            )

    def fetch_body_type_names(self, body_type_ids):
        """Получение названий типов кузова по id"""
        access_token = self.page.client_storage.get('app.auth.access_token')
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

        clean_url = self.api_url.rstrip('/')
        body_type_names = {}

        for bt_id in body_type_ids:
            url = f'{clean_url}/cars/body_types?limit=100'
            response = httpx.get(url, headers=headers)
            if response.status_code == 200:
                body_types = response.json().get('data', [])
                for bt in body_types:
                    if bt['id'] == bt_id:
                        body_type_names[bt_id] = bt['name']
            else:
                print(
                    f'Ошибка при загрузке типов кузова: '
                    f'{response.status_code} - {response.text}'
                )

        return body_type_names

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
        return ft.Container(
            content=ft.ElevatedButton(
                text='Сохранить',
                width=250,
                bgcolor=ft.colors.PURPLE,
                color=ft.colors.WHITE,
                on_click=self.save_car_selection,
            ),
            border_radius=ft.border_radius.all(25),
        )

    def create_profile_container(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.icons.ARROW_BACK,
                                on_click=lambda e: self.open_sign_in(),
                            ),
                            ft.Text('Создайте профиль', size=24),
                        ]
                    ),
                    self.avatar_container,
                    self.brand_button,
                    self.model_dropdown,
                    self.generation_dropdown,
                    self.body_type_dropdown,
                    self.save_button,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            ),
            padding=ft.padding.all(20),
            border_radius=ft.border_radius.all(25),
            width=350,
            alignment=ft.alignment.center,
        )

    def save_car_selection(self, e):
        selected_brand = self.selected_brand
        selected_model = self.model_dropdown.value
        selected_generation = (
            self.generation_dropdown.value
            if self.generation_dropdown.visible
            else self.selected_generation
        )
        selected_body_type = (
            self.body_type_dropdown.value
            if self.body_type_dropdown.visible
            else None
        )

        if selected_brand and selected_model:
            print(
                f'Сохранён автомобиль: {selected_brand}'
                f' - {selected_model} - {selected_generation} '
                f'- {selected_body_type}'
            )
        else:
            print('Выберите марку и модель автомобиля')

    def on_picture_click(self, _: ft.ControlEvent):
        self.file_picker.pick_files(allow_multiple=False)

    def on_picture_select(self, e: ft.FilePickerResultEvent):
        if e.files:
            img = ft.Image(
                src=e.files[0].path,
                width=100,
                height=100,
                border_radius=ft.border_radius.all(50),
            )
            self.avatar_container.content = img
            self.page.update()

    def open_sign_in(self):
        from washer.ui_components.sign_in_page import SignInPage

        SignInPage(self.page)

import flet as ft

from washer.api_requests import BackendApi
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
        self.selected_model = None
        self.selected_generation = None
        self.selected_generation_id = None
        self.generation_year_range = None
        self.generation_codes = None
        self.generations = []
        self.body_types_dict = {}
        self.selected_body_type = None
        self.selected_body_type_id = None
        self.brand_button_text = 'Выберите марку автомобиля'
        self.selected_car = {}
        self.snack_bar = None
        self.api = BackendApi()
        self.api.set_access_token(self.page.client_storage.get('access_token'))

        self.save_button = self.create_save_button()
        self.save_button.disabled = True

        self.search_dialog = self.create_search_dialog()
        self.brand_button = self.create_brand_button()
        self.model_dropdown = self.create_model_dropdown()
        self.generation_dropdown = self.create_generation_dropdown()
        self.body_type_dropdown = self.create_body_type_dropdown()

        self.page.appbar = self.create_add_car_appbar()
        self.page.clean()
        self.page.add(self.create_car_selection_page())

        self.load_brands()
        self.setup_snack_bar()

    def create_add_car_appbar(self):
        return ft.AppBar(
            leading=ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                on_click=self.return_to_cars_page,
                icon_color=ft.colors.WHITE,
                padding=ft.padding.only(left=10),
            ),
            title=ft.Text(
                'Добавить автомобиль', size=20, weight=ft.FontWeight.BOLD
            ),
            center_title=True,
            bgcolor=ft.colors.SURFACE_VARIANT,
            leading_width=40,
        )

    def create_car_selection_page(self):
        return ft.Container(
            content=ft.ListView(
                controls=[
                    ft.Container(height=20),
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

    def load_brands(self):
        response = self.api.get_brands()
        if response.status_code == 401:
            if 'token has expired' in response.text.lower():
                if self.refresh_token():
                    self.load_brands()
                else:
                    self.page.add(
                        ft.Text(
                            'Сессия истекла, пожалуйста, войдите снова.',
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
                brand
                for brand in self.full_brands_list
                if search_query in brand['name'].lower()
            ]

        self.update_brands_list(filtered_brands)

    def on_brand_select(self, e):
        selected_brand = e.control.data
        brand_id = self.brands_dict.get(selected_brand)

        if not brand_id:
            print('ID марки не найден.')
            return

        response = self.api.get_models(brand_id)
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
            self.selected_model = None
            self.selected_generation_id = None
            self.selected_body_type = None
            self.selected_body_type_id = None
            self.save_button.disabled = True

            self.page.update()

        self.close_search_dialog(None)

    def on_model_select(self, e):
        selected_model = e.control.value
        self.selected_model = selected_model
        self.selected_model_id = self.models_dict.get(selected_model)

        if not self.selected_model_id:
            print('ID модели не найден.')
            return

        response = self.api.get_generations(self.selected_model_id)
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
            self.selected_body_type = None
            self.selected_body_type_id = None
            self.save_button.disabled = True

            if len(generations) == 1:
                self.selected_generation = generations[0]['name']
                self.selected_generation_id = generations[0]['id']
                self.generation_year_range = generations[0].get(
                    'year_range', ''
                )
                self.generation_codes = generations[0].get('codes', '')

                if not self.selected_generation and self.generation_year_range:
                    self.selected_generation = self.generation_year_range

                self.show_snack_bar(
                    f'Поколение "{self.selected_generation}" '
                    f'выбрано автоматически',
                    bgcolor=ft.colors.BLUE,
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
            self.selected_generation = generation_info.get('name')
            self.generation_year_range = generation_info.get('year_range', '')
            self.generation_codes = generation_info.get('codes', '')

            if not self.selected_generation and self.generation_year_range:
                self.selected_generation = self.generation_year_range

        self.body_type_dropdown.options = []
        self.body_type_dropdown.value = None
        self.body_type_dropdown.visible = False
        self.selected_body_type = None
        self.selected_body_type_id = None
        self.save_button.disabled = True
        self.page.update()

        self.get_body_type(self.selected_generation_id)

    def get_body_type(self, generation_id):
        response = self.api.get_configurations(generation_id)
        if response.status_code == 200:
            configurations = response.json().get('data', [])
            unique_body_types = {
                config['body_type_id'] for config in configurations
            }

            if len(unique_body_types) == 1:
                body_type_id = configurations[0]['body_type_id']
                body_type_name = self.get_body_type_name(body_type_id)
                self.selected_body_type = body_type_name
                self.selected_body_type_id = body_type_id
                print(f'Автоматически выбран тип кузова: {body_type_name}')

                self.show_snack_bar(
                    f'Тип кузова "{body_type_name}" выбран автоматически',
                    bgcolor=ft.colors.BLUE,
                )

                self.body_type_dropdown.visible = False
                self.save_button.disabled = False
                self.page.update()
            else:
                self.body_types_dict = self.fetch_body_type_names(
                    unique_body_types
                )
                self.body_type_dropdown.options = [
                    ft.dropdown.Option(self.body_types_dict[bt_id])
                    for bt_id in unique_body_types
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
                            self.selected_body_type_id = selected_body_type_id
                        self.save_button.disabled = False
                        self.page.update()

                self.body_type_dropdown.on_change = on_body_type_select
                self.page.update()
        else:
            print(f'Ошибка при загрузке конфигураций: {response.text}')

    def fetch_body_type_names(self, body_type_ids):
        response = self.api.get_body_types()
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

    def create_save_button(self):
        return ft.ElevatedButton(
            text='Сохранить',
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
        self.show_snack_bar(message, bgcolor=ft.colors.GREEN)

    def show_error_message(self, message: str):
        self.show_snack_bar(message, bgcolor=ft.colors.RED)

    def on_save_click(self, e):
        access_token = self.page.client_storage.get('access_token')

        if not access_token:
            self.show_error_message('Токен доступа отсутствует!')
            return

        generation_display = self.selected_generation
        if not generation_display and self.generation_year_range:
            generation_display = self.generation_year_range

        full_name = f'{self.selected_brand} {self.selected_model}'
        if generation_display:
            full_name += f' {generation_display}'

        if self.selected_body_type:
            full_name += f' {self.selected_body_type}'

        selected_car = {
            'brand': self.selected_brand,
            'model': self.selected_model,
            'generation': generation_display or 'Не указано',
            'body_type': self.selected_body_type or 'Не указано',
            'configuration_id': self.selected_generation_id,
            'body_type_id': self.selected_body_type_id,
            'name': full_name,
        }

        try:
            response = self.api.create_user_car(selected_car)

            if response.status_code == 200:
                self.show_success_message(
                    f'Автомобиль "{full_name}" успешно сохранен!'
                )
                self.selected_car = response.json()
                self.selected_car.update(selected_car)
                print(f'Данные сохраненного автомобиля: {self.selected_car}')
                self.on_car_saved(self.selected_car)
            else:
                error_message = response.text or 'Неизвестная ошибка'
                self.show_error_message(f'Ошибка: {error_message}')
        except Exception as e:
            self.show_error_message(f'Ошибка: {str(e)}')

    def refresh_token(self):
        refresh_token = self.page.client_storage.get('refresh_token')
        if not refresh_token:
            print('Refresh token not found, redirecting to login.')
            return False

        response = self.api.refresh_token(refresh_token)

        if 'error' not in response:
            self.page.client_storage.set(
                'access_token', response['access_token']
            )
            self.page.client_storage.set(
                'refresh_token', response['refresh_token']
            )
            self.api.set_access_token(response['access_token'])
            return True
        else:
            print(f'Ошибка обновления токена: {response["details"]}')
            return False

    def return_to_cars_page(self, e=None):
        self.page.appbar = None
        from washer.ui_components.my_cars_page import MyCarsPage

        MyCarsPage(
            page=self.page,
            api_url=self.api_url,
            cars=[],
            on_car_saved_callback=self.on_car_saved,
        ).open()

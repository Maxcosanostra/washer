import re

import flet as ft

from washer.api_requests import BackendApi


class AdminCarSelectionPage:
    def __init__(
        self, page: ft.Page, on_car_selected, car_wash, box_id, date, time
    ):
        self.page = page
        self.on_car_selected = on_car_selected
        self.car_wash = car_wash
        self.box_id = box_id
        self.date = date
        self.time = time
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

        self.car_number = ''
        self.car_number_valid = False

        self.car_number_label = ft.Text(
            'Введите госномер автомобиля',
            size=16,
            weight=ft.FontWeight.BOLD,
            visible=False,
        )
        self.car_number_plate = self._create_license_plate_field()
        self.car_number_plate.visible = False

        self.brand_button_text = 'Выберите марку автомобиля'
        self.selected_car = {}
        self.snack_bar = None
        self.api = BackendApi()
        access_token = self.page.client_storage.get('access_token')
        if access_token:
            self.api.set_access_token(access_token)

        self.car_price = 0
        self.price_text = ft.Text(
            'Стоимость: ₸0',
            size=32,
            weight=ft.FontWeight.BOLD,
        )

        self.save_button = self.create_next_button()
        self.save_button.disabled = True

        self.search_dialog = self.create_search_dialog()
        self.brand_button = self.create_brand_button()
        self.model_dropdown = self.create_model_dropdown()
        self.generation_dropdown = self.create_generation_dropdown()
        self.body_type_dropdown = self.create_body_type_dropdown()

        page.clean()
        page.add(self.create_car_selection_page())
        page.add(self.price_text)

        self.load_brands()
        self.setup_snack_bar()

    def _create_license_plate_field(self):
        self.kz_flag = ft.Image(
            src='https://upload.wikimedia.org/wikipedia/commons/d/d3/Flag_of_Kazakhstan.svg',
            width=16,
            height=10,
            fit=ft.ImageFit.CONTAIN,
        )
        self.kz_text = ft.Text(
            'KZ',
            size=10,
            color=ft.colors.BLACK,
            weight=ft.FontWeight.BOLD,
        )
        self.kz_flag_container = ft.Column(
            controls=[self.kz_flag, self.kz_text],
            spacing=1,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            visible=False,
        )

        self.right_divider = ft.VerticalDivider(
            width=8,
            color=ft.colors.BLACK,
            visible=True,
        )

        self.last_two_field = ft.TextField(
            label='',
            hint_text='XY',
            text_style=ft.TextStyle(
                color=ft.colors.BLACK,
                weight=ft.FontWeight.BOLD,
                size=20,
            ),
            border=None,
            bgcolor=ft.colors.TRANSPARENT,
            width=22,
            visible=True,
            on_change=self.on_last_two_change,
        )
        last_two_container = ft.Container(
            content=self.last_two_field,
            width=40,
        )

        self.main_number_field = ft.TextField(
            label='',
            hint_text='505TCM',
            hint_style=ft.TextStyle(color=ft.colors.BLACK, size=16),
            text_style=ft.TextStyle(
                color=ft.colors.BLACK,
                weight=ft.FontWeight.BOLD,
                size=20,
            ),
            border=None,
            bgcolor=ft.colors.TRANSPARENT,
            width=100,
            visible=True,
            on_change=self.on_main_number_change,
            content_padding=ft.padding.all(0),
        )

        self.plate_container = ft.Container(
            width=180,
            height=40,
            bgcolor=ft.colors.WHITE,
            border_radius=ft.border_radius.all(6),
            border=ft.border.all(2, ft.colors.BLACK),
            padding=0,
            content=ft.Row(
                controls=[
                    self.kz_flag_container,
                    self.main_number_field,
                    self.right_divider,
                    last_two_container,
                ],
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=-1,
            ),
        )

        return self.plate_container

    def _hide_kz_and_right(self):
        self.kz_flag_container.visible = False
        self.right_divider.visible = False
        self.last_two_field.visible = False
        self.last_two_field.value = ''

    def on_main_number_change(self, e):
        main_value = e.control.value or ''
        raw_value = re.sub(r'\s+', '', main_value).upper()

        if not raw_value:
            self._hide_kz_and_right()
            self.main_number_field.width = 130
            self.plate_container.width = 180
            e.control.value = ''
        else:
            if raw_value[0].isdigit():
                self.kz_flag_container.visible = True
                self.right_divider.visible = True
                self.last_two_field.visible = True
                self.main_number_field.width = 100

                if len(raw_value) > 6:
                    overflow = raw_value[6:]
                    raw_value = raw_value[:6]
                    new_last = (self.last_two_field.value or '') + overflow
                    new_last = new_last[:2]
                    self.last_two_field.value = new_last

                e.control.value = raw_value
                self.plate_container.width = 180
            else:
                self._hide_kz_and_right()
                self.main_number_field.width = 180

                if len(raw_value) > 7:
                    raw_value = raw_value[:7]

                pattern = r'^([A-Z])(\d{3})([A-Z]{2,3})$'
                match = re.match(pattern, raw_value)
                if match:
                    part1, part2, part3 = match.groups()
                    spaced_value = f'{part1}  {part2}  {part3}'
                    e.control.value = spaced_value
                else:
                    e.control.value = raw_value

                num_chars = len(raw_value)
                calculated_width = 14 * num_chars + 20
                self.plate_container.width = max(140, calculated_width)

        e.page.update()
        self._validate_number()

    def on_last_two_change(self, e):
        last_val = e.control.value or ''
        last_val = re.sub(r'\s+', '', last_val).upper()
        if len(last_val) > 2:
            last_val = last_val[:2]
        e.control.value = last_val
        e.page.update()
        self._validate_number()

        if self.car_number.startswith(tuple(map(str, range(10)))):
            self.plate_container.width = 180
        else:
            main_val = (self.main_number_field.value or '').upper()
            main_val = re.sub(r'\s+', '', main_val)
            calculated_width = 14 * len(main_val) + 30
            self.plate_container.width = max(140, calculated_width)

        self.page.update()

    def _validate_number(self):
        main_val = (self.main_number_field.value or '').upper()
        main_val = re.sub(r'\s+', '', main_val)

        last_val = (self.last_two_field.value or '').upper()
        last_val = re.sub(r'\s+', '', last_val)

        full_raw = main_val + last_val

        pattern = r'^([A-Z]\d{3}[A-Z]{2,3}|\d{3}[A-Z]{2,3}\d{2})$'
        self.car_number_valid = bool(re.match(pattern, full_raw))

        self.car_number = full_raw
        self.check_if_save_button_should_be_enabled()

    def check_if_save_button_should_be_enabled(self):
        if (
            self.selected_brand
            and self.selected_model_id
            and self.selected_generation_id
            and self.selected_body_type_id
            and self.car_number_valid
        ):
            self.save_button.disabled = False
        else:
            self.save_button.disabled = True
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
                    ft.Container(
                        content=self.car_number_label,
                        alignment=ft.alignment.center,
                        width=300,
                        margin=ft.margin.only(bottom=5),
                    ),
                    ft.Container(
                        content=self.car_number_plate,
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

    def load_brands(self):
        response = self.api.get_brands()
        if response.status_code == 401:
            # Проверяем просроченность токена
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

            POPULAR_BRANDS = [
                'Audi',
                'BMW',
                'Mercedes-Benz',
                'Chevrolet',
                'Hyundai',
                'Kia',
                'Lada (ВАЗ)',
                'LiXiang',
                'Changan',
                'Nissan',
                'Renault',
                'Skoda',
                'Toyota',
                'Volkswagen',
                'Zeekr',
            ]

            def sort_key(brand_dict):
                brand_name = brand_dict['name']
                for i, popular_name in enumerate(POPULAR_BRANDS):
                    if brand_name.lower() == popular_name.lower():
                        return (0, i)
                return (1, brand_name.lower())

            brands.sort(key=sort_key)

            self.brands_dict = {brand['name']: brand['id'] for brand in brands}
            self.update_brands_list(brands)
        else:
            print(f'Ошибка загрузки брендов: {response.text}')

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
            hint_text='Поиск бренда',
            on_change=self.on_search_change,
            width=300,
            height=30,
        )

        self.brands_list = ft.ListView(controls=[], height=350)

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
            self.selected_generation_id = None
            self.body_type_dropdown.options = []
            self.body_type_dropdown.visible = False
            self.selected_body_type = None
            self.selected_body_type_id = None
            self.save_button.disabled = True

            self.car_number_label.visible = False
            self.car_number_plate.visible = False
            self.car_number = ''
            self.car_number_valid = False

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

            self.car_number_label.visible = False
            self.car_number_plate.visible = False
            self.car_number = ''
            self.car_number_valid = False

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

                        self.car_number_label.visible = False
                        self.car_number_plate.visible = False
                        self.car_number = ''
                        self.car_number_valid = False

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

                        self.get_body_type(self.selected_generation_id)

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
                g
                for g in self.generations
                if g['id'] == self.selected_generation_id
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

        self.car_number_label.visible = False
        self.car_number_plate.visible = False
        self.car_number = ''
        self.car_number_valid = False

        self.page.update()

        self.get_body_type(self.selected_generation_id)

    def get_body_type(self, generation_id):
        response = self.api.get_configurations(generation_id)
        if response.status_code == 200:
            configurations = response.json().get('data', [])
            unique_body_types = {c['body_type_id'] for c in configurations}

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
                self.load_car_price(body_type_id)
                self.body_type_dropdown.visible = False

                self.car_number_label.visible = True
                self.car_number_plate.visible = True
                self.save_button.disabled = False
                self.page.update()

                self.check_if_save_button_should_be_enabled()
            else:
                self.body_types_dict = {
                    bt_id: self.get_body_type_name(bt_id)
                    for bt_id in unique_body_types
                }
                self.body_type_dropdown.options = [
                    ft.dropdown.Option(self.body_types_dict[bt_id])
                    for bt_id in unique_body_types
                ]
                self.body_type_dropdown.value = None
                self.body_type_dropdown.visible = True
                self.save_button.disabled = True

                self.car_number_label.visible = False
                self.car_number_plate.visible = False
                self.car_number = ''
                self.car_number_valid = False

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
                            self.load_car_price(selected_body_type_id)
                        self.save_button.disabled = False
                        self.page.update()

                        self.car_number_label.visible = True
                        self.car_number_plate.visible = True
                        self.check_if_save_button_should_be_enabled()

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
        response = self.api.get_body_types()
        if response.status_code == 200:
            body_types = response.json().get('data', [])
            return {
                bt['id']: bt['name']
                for bt in body_types
                if bt['id'] in body_type_ids
            }
        else:
            print(
                f'Ошибка загрузки типов кузовов: '
                f'{response.status_code}, {response.text}'
            )
            return {}

    def get_body_type_name(self, body_type_id):
        names = self.fetch_body_type_names([body_type_id])
        return names.get(body_type_id, 'Неизвестно')

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
        self.show_snack_bar(message, bgcolor=ft.colors.GREEN)

    def show_error_message(self, message: str):
        self.show_snack_bar(message, bgcolor=ft.colors.RED)

    def on_save_click(self, e):
        access_token = self.page.client_storage.get('access_token')
        if not access_token:
            self.show_error_message('Токен доступа отсутствует!')
            return

        if not self.car_number_valid:
            self.show_error_message('Некорректный формат номера!')
            return

        generation_display = self.selected_generation
        if not generation_display and self.generation_year_range:
            generation_display = self.generation_year_range

        full_name = f'{self.selected_brand} {self.selected_model}'
        if generation_display:
            full_name += f' {generation_display}'
        if self.selected_body_type:
            full_name += f' {self.selected_body_type}'

        selected_car_for_request = {
            'name': full_name,
            'configuration_id': self.selected_generation_id,
            'license_plate': self.car_number,
        }

        try:
            response = self.api.create_user_car(selected_car_for_request)
            if response and response.status_code == 200:
                self.show_success_message(
                    f'Автомобиль "{full_name}" успешно сохранен!'
                )

                self.selected_car = response.json()

                if not self.selected_car.get('name'):
                    self.selected_car['name'] = full_name

                self.selected_car.update(
                    {
                        'brand': self.selected_brand,
                        'model': self.selected_model,
                        'generation': generation_display or 'Не указано',
                        'body_type': self.selected_body_type or 'Не указано',
                        'configuration_id': self.selected_generation_id,
                        'body_type_id': self.selected_body_type_id,
                        'car_number': self.car_number,
                    }
                )

                self.on_car_selected(self.selected_car, self.car_price)

            else:
                error_message = (
                    response.text if response else 'Неизвестная ошибка'
                )
                self.show_error_message(f'Ошибка: {error_message}')

        except Exception as ex:
            self.show_error_message(f'Ошибка: {str(ex)}')

    def create_back_button(self):
        return ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        icon_size=30,
                        on_click=lambda e: self.page.go_back(),
                    ),
                    ft.Text('Назад', size=16),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            margin=ft.margin.only(bottom=15),
        )

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

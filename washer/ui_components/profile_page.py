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
        self.brand_button_text = 'Выберите марку автомобиля'

        self.search_dialog = self.create_search_dialog()
        self.brand_button = self.create_brand_button()

        self.model_dropdown = self.create_model_dropdown()
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
        self.page.dialog = self.search_dialog
        self.search_dialog.open = True
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
                self.model_dropdown.options = [
                    ft.dropdown.Option(model['name']) for model in models
                ]
                self.selected_brand = selected_brand

                self.brand_button_text = f'Марка: {selected_brand}'
                self.brand_button.content.controls[
                    0
                ].value = self.brand_button_text
                self.page.update()
        else:
            print(
                f'Ошибка при загрузке моделей автомобилей: '
                f'{response.status_code} - {response.text}'
            )

        self.close_search_dialog(None)

    def create_model_dropdown(self):
        return ft.Dropdown(
            label='Выберите модель автомобиля',
            width=300,
            border_radius=ft.border_radius.all(25),
            options=[],
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

        if selected_brand and selected_model:
            print(f'Сохранён автомобиль: {selected_brand} - {selected_model}')
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

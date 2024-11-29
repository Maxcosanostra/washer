import io

import flet as ft
import httpx

from washer.config import config
from washer.ui_components.account_settings_page import AccountSettingsPage
from washer.ui_components.my_bookings_page import MyBookingsPage
from washer.ui_components.my_cars_page import MyCarsPage
from washer.ui_components.my_finance_page import MyFinancePage


class ProfilePage:
    def __init__(self, page: ft.Page, car_wash=None, location_data=None):
        self.page = page
        self.api_url = config.api_url
        self.username = self.page.client_storage.get('username')

        self.car_wash = car_wash or {}
        self.location_data = location_data or {}

        print(f'Инициализация ProfilePage - car_wash: {self.car_wash}')
        print(
            f'Инициализация ProfilePage - location_data: {self.location_data}'
        )

        self.cars = []
        self.bookings = []
        self.completed_visible = False

        self.completed_bookings_container = ft.Container(visible=False)

        self.avatar_container = self.create_avatar_container()
        self.file_picker = self.create_file_picker()
        page.overlay.append(self.file_picker)

        self.get_user_data()

        page.clean()
        page.add(self.create_profile_page())

    def on_login_success(self):
        self.get_user_data()
        self.page.clean()
        self.page.add(self.create_profile_page())
        self.page.update()

    def create_profile_card(self):
        return ft.Container(
            content=ft.Card(
                content=ft.Container(
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
                                    self.username,
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
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
                    padding=ft.padding.all(15),
                ),
                elevation=3,
            ),
            width=370,
            margin=ft.margin.only(bottom=20),
        )

    def create_profile_page(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(height=20),
                    self.create_profile_card(),
                    ft.Container(height=10),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.icons.DIRECTIONS_CAR,
                                    color=ft.colors.WHITE,
                                ),
                                ft.Text(
                                    'Мои автомобили', color=ft.colors.WHITE
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            spacing=5,
                        ),
                        on_click=self.open_cars_page,
                        width=300,
                        bgcolor=ft.colors.BLUE,
                        padding=ft.padding.symmetric(
                            vertical=10, horizontal=15
                        ),
                        border_radius=ft.border_radius.all(8),
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.icons.EVENT_NOTE, color=ft.colors.WHITE
                                ),
                                ft.Text('Мои записи', color=ft.colors.WHITE),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            spacing=5,
                        ),
                        on_click=self.open_bookings_page,
                        width=300,
                        bgcolor=ft.colors.BLUE,
                        padding=ft.padding.symmetric(
                            vertical=10, horizontal=15
                        ),
                        border_radius=ft.border_radius.all(8),
                    ),
                    ft.Divider(height=1, color=ft.colors.GREY_400),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.icons.ACCOUNT_CIRCLE,
                                    color=ft.colors.WHITE,
                                ),
                                ft.Text(
                                    'Учетная запись', color=ft.colors.WHITE
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            spacing=5,
                        ),
                        on_click=self.open_account_settings,
                        width=300,
                        bgcolor=ft.colors.BLUE,
                        padding=ft.padding.symmetric(
                            vertical=10, horizontal=15
                        ),
                        border_radius=ft.border_radius.all(8),
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.icons.ATTACH_MONEY,
                                    color=ft.colors.WHITE,
                                ),
                                ft.Text('Финансы', color=ft.colors.WHITE),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            spacing=5,
                        ),
                        on_click=self.open_finances_page,
                        width=300,
                        bgcolor=ft.colors.BLUE,
                        padding=ft.padding.symmetric(
                            vertical=10, horizontal=15
                        ),
                        border_radius=ft.border_radius.all(8),
                    ),
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

    def open_bookings_page(self, e):
        bookings_page = MyBookingsPage(
            page=self.page,
            api_url=self.api_url,
            car_wash=self.car_wash,
            location_data=self.location_data,
        )
        bookings_page.open()

    def open_cars_page(self, e):
        cars_page = MyCarsPage(
            page=self.page,
            api_url=self.api_url,
            cars=self.cars,
            on_car_saved_callback=lambda car: cars_page.open(),
        )
        cars_page.open()

    def open_account_settings(self, e):
        self.page.clean()
        AccountSettingsPage(self.page)
        self.page.update()

    def open_finances_page(self, e):
        finance_page = MyFinancePage(self.page)
        finance_page.open()

    def redirect_to_booking_page(self, e):
        self.page.appbar = None
        self.page.clean()

        from washer.ui_components.wash_selection_page import WashSelectionPage

        WashSelectionPage(self.page, username=self.username)

    def return_to_profile(self, e):
        self.page.appbar = None
        self.page.clean()
        self.page.add(self.create_profile_page())
        self.page.update()

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

    def create_avatar_container(self):
        return ft.Container(
            content=ft.Icon(ft.icons.PERSON, size=100, color=ft.colors.GREY),
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
            with open(e.files[0].path, 'rb') as image_file:
                self.selected_image_bytes = image_file.read()
            self.avatar_container.content = ft.Image(
                src=e.files[0].path,
                width=100,
                height=100,
                fit=ft.ImageFit.COVER,
                border_radius=ft.border_radius.all(50),
            )
            self.page.update()
            self.upload_avatar_to_server()

    def upload_avatar_to_server(self):
        user_id = self.page.client_storage.get('user_id')
        access_token = self.page.client_storage.get('access_token')
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }
        files = {
            'image': ('avatar.png', io.BytesIO(self.selected_image_bytes))
        }
        url = f"{self.api_url.rstrip('/')}/users/{user_id}"
        response = httpx.patch(
            url, files=files, data={'username': self.username}, headers=headers
        )
        if response.status_code == 200:
            self.get_user_data()

    def get_user_data(self):
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
                self.avatar_container.content = ft.Image(
                    src=avatar_url,
                    width=100,
                    height=100,
                    fit=ft.ImageFit.COVER,
                    border_radius=ft.border_radius.all(50),
                )
                self.page.update()

    def on_back_click(self, e):
        from washer.ui_components.wash_selection_page import WashSelectionPage

        WashSelectionPage(self.page)

    def on_logout_click(self, e):
        self.page.client_storage.remove('access_token')
        self.page.client_storage.remove('refresh_token')
        self.page.client_storage.remove('username')
        from washer.ui_components.sign_in_page import SignInPage

        SignInPage(self.page)

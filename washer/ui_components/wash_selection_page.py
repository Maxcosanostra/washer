import flet as ft
import httpx

from washer.config import config


class WashSelectionPage:
    car_washes_cache = None

    def __init__(self, page: ft.Page, username: str = None):
        self.page = page
        self.api_url = config.api_url
        self.username = username or self.page.client_storage.get('username')
        self.avatar_container = self.create_avatar_container()
        self.car_washes = []

        self.page.adaptive = True
        self.page.scroll = 'adaptive'

        access_token = self.page.client_storage.get('access_token')
        if not access_token:
            print('Access token not found, redirecting to login.')
            self.redirect_to_sign_in_page()
            return

        self.car_washes_list = ft.ListView(controls=[], padding=0, spacing=0)

        page.clean()
        page.add(self.create_main_container())
        self.load_car_washes()

    def create_avatar_container(self):
        avatar_url = self.get_avatar_from_server()

        if avatar_url:
            avatar_content = ft.Image(
                src=avatar_url,
                width=50,
                height=50,
                border_radius=ft.border_radius.all(25),
                fit=ft.ImageFit.COVER,
            )
        else:
            avatar_content = ft.Container(
                content=ft.Icon(
                    ft.icons.PERSON, size=50, color=ft.colors.GREY
                ),
                width=50,
                height=50,
                border_radius=ft.border_radius.all(25),
                bgcolor=ft.colors.GREY_200,
                alignment=ft.alignment.center,
            )

        return ft.Container(
            content=avatar_content,
            alignment=ft.alignment.center,
            padding=10,
            on_click=self.on_avatar_click,
        )

    def get_avatar_from_server(self):
        access_token = self.page.client_storage.get('access_token')
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

        url = f"{self.api_url.rstrip('/')}/users/me"

        response = httpx.get(url, headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            return user_data.get('image_link')
        else:
            print(f'Error fetching avatar: {response.status_code}')
            return None

    def on_avatar_click(self, e=None):
        from washer.ui_components.profile_page import ProfilePage

        selected_car_wash = self.car_washes[0]
        location_data = self.load_location_data(
            selected_car_wash.get('location_id')
        )

        ProfilePage(
            self.page, car_wash=selected_car_wash, location_data=location_data
        )

    def create_main_container(self):
        self.car_washes_list = ft.ListView(
            controls=self.create_wash_list(),
            padding=0,
            spacing=0,
        )

        return ft.Container(
            content=ft.ListView(
                controls=[
                    self.create_welcome_card(),
                    self.create_search_bar(),
                    self.car_washes_list,
                ],
                padding=ft.padding.symmetric(horizontal=20, vertical=10),
                spacing=10,
            ),
            margin=ft.margin.only(top=20),
            expand=True,
        )

    def create_welcome_card(self):
        return ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(
                                content=self.avatar_container,
                                alignment=ft.alignment.center,
                            ),
                            ft.Text(
                                f'Привет, {self.username}!',
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.LEFT,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.padding.all(10),
                    expand=True,
                ),
                elevation=3,
            ),
            alignment=ft.alignment.center,
            expand=True,
        )

    def create_search_bar(self):
        """Создает строку поиска для фильтрации автомоек по названию"""
        return ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.TextField(
                        prefix=ft.Icon(
                            ft.icons.SEARCH, size=20, color=ft.colors.GREY
                        ),
                        label='найти автомойку...',
                        label_style=ft.TextStyle(
                            size=14, color=ft.colors.GREY
                        ),
                        width=320,
                        height=50,
                        border=ft.InputBorder.NONE,
                        border_radius=ft.border_radius.all(15),
                        bgcolor=ft.colors.TRANSPARENT,
                        border_color=ft.colors.TRANSPARENT,
                        filled=False,
                        on_change=self.on_search_text_change,
                    ),
                    alignment=ft.alignment.center,
                    padding=ft.padding.all(0),
                ),
                elevation=0,
                width=320,
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.all(0),
        )

    def on_search_text_change(self, e):
        """Обработчик изменения текста поиска для фильтрации автомоек"""
        search_text = e.control.value.lower()
        filtered_washes = [
            wash
            for wash in self.car_washes
            if search_text in wash['name'].lower()
        ]
        self.update_wash_list(filtered_washes)

    def update_wash_list(self, washes):
        self.car_washes_list.controls = [
            self.create_car_wash_card(wash) for wash in washes
        ]
        self.car_washes_list.update()

    def create_wash_list(self):
        """Создает список карточек автомоек на основе загруженных данных"""
        return [self.create_car_wash_card(wash) for wash in self.car_washes]

    def create_car_wash_card(self, car_wash):
        """Создает карточку автомойки аналогично BookingPage"""
        image_link = car_wash.get('image_link', 'assets/spa_logo.png')
        location_id = car_wash.get('location_id')
        location_data = (
            self.load_location_data(location_id) if location_id else None
        )
        location_address = (
            f"{location_data['city']}, {location_data['address']}"
            if location_data
            else 'Адрес недоступен'
        )

        return ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Image(
                                src=image_link,
                                fit=ft.ImageFit.COVER,
                                expand=True,
                            ),
                            ft.Text(
                                f"{car_wash['name']}",
                                weight='bold',
                                size=20,
                                text_align=ft.TextAlign.LEFT,
                            ),
                            ft.Text(
                                location_address,
                                text_align=ft.TextAlign.LEFT,
                                color=ft.colors.GREY,
                            ),
                        ],
                        spacing=10,
                        expand=True,
                    ),
                    padding=ft.padding.all(10),
                    expand=True,
                    on_click=lambda e: self.on_booking_click(car_wash),
                ),
                elevation=3,
            ),
            alignment=ft.alignment.center,
            expand=True,
        )

    def on_booking_click(self, car_wash):
        from washer.ui_components.booking_page import BookingPage

        location_id = car_wash.get('location_id')
        location_data = (
            self.load_location_data(location_id) if location_id else None
        )

        cars = self.page.client_storage.get('cars') or []
        BookingPage(
            self.page,
            car_wash,
            self.username,
            cars,
            location_data=location_data,
        )
        self.page.update()

    def load_car_washes(self):
        """Загружает данные автомоек и обновляет список на странице"""
        if WashSelectionPage.car_washes_cache:
            print('Using cached car washes data')
            self.car_washes = WashSelectionPage.car_washes_cache
            self.update_wash_list(self.car_washes)
            return

        access_token = self.page.client_storage.get('access_token')
        if not access_token:
            print('Access token not found, redirecting to login.')
            self.redirect_to_sign_in_page()
            return

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }
        url = f'{self.api_url.rstrip("/")}/car_washes?page=1&limit=10'

        response = httpx.get(url, headers=headers)
        if response.status_code == 200:
            self.car_washes = response.json().get('data', [])
            WashSelectionPage.car_washes_cache = self.car_washes
            self.update_wash_list(self.car_washes)
        else:
            print(f'Error loading car washes: {response.text}')

    def load_location_data(self, location_id):
        """Загрузка данных о локации по её ID"""
        access_token = self.page.client_storage.get('access_token')
        url = f"{self.api_url.rstrip('/')}/car_washes/locations/{location_id}"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }
        response = httpx.get(url, headers=headers)

        if response.status_code == 200:
            location = response.json()
            print(f'Location data for location_id {location_id}: {location}')
            return location
        else:
            print(f'Failed to fetch location: {response.text}')
            return None

    def redirect_to_sign_in_page(self):
        from washer.ui_components.sign_in_page import SignInPage

        SignInPage(self.page)

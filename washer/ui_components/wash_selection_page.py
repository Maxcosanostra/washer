import flet as ft

from washer.api_requests import BackendApi


class WashSelectionPage:
    car_washes_cache = None

    def __init__(self, page: ft.Page, username: str = None):
        self.page = page
        self.api = BackendApi()
        self.api.set_access_token(self.page.client_storage.get('access_token'))
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

        self.search_bar = self.create_search_bar()
        self.search_bar.visible = False

        self.page.clean()
        self.main_container = self.create_main_container()
        self.page.add(self.main_container)
        self.load_car_washes()

        self.page.floating_action_button = ft.FloatingActionButton(
            icon=ft.icons.SEARCH,
            tooltip='Поиск автомойки',
            on_click=self.on_fab_click,
        )
        self.page.update()

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
        response = self.api.get_user_avatar()
        if response.status_code == 200:
            user_data = response.json()
            return user_data.get('image_link')
        else:
            print(
                f'Error fetching avatar: '
                f'{response.status_code}, {response.text}'
            )
            return None

    def on_avatar_click(self, e=None):
        from washer.ui_components.profile_page import ProfilePage

        if not self.car_washes:
            print('Car washes data is not loaded yet.')
            return

        selected_car_wash = self.car_washes[0]
        location_data = self.load_location_data(
            selected_car_wash.get('location_id')
        )

        ProfilePage(
            self.page, car_wash=selected_car_wash, location_data=location_data
        )

    def create_main_container(self):
        search_and_list_container = ft.Container(
            content=ft.Column(
                controls=[
                    self.search_bar,
                    self.car_washes_list,
                ],
                spacing=10,
            ),
            expand=True,
        )

        return ft.Container(
            content=ft.ListView(
                controls=[
                    self.create_welcome_card(),
                    ft.Container(
                        content=ft.Text(
                            'Автомойки',
                            weight=ft.FontWeight.BOLD,
                            size=24,
                            text_align=ft.TextAlign.LEFT,
                        ),
                        margin=ft.margin.only(top=20),
                    ),
                    search_and_list_container,
                ],
                padding=ft.padding.only(top=10, bottom=10),
                spacing=10,
            ),
            margin=ft.margin.only(top=20),
            expand=True,
            width=730,
            alignment=ft.alignment.center,
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
        return ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.TextField(
                        prefix=ft.Icon(
                            ft.icons.SEARCH, size=20, color=ft.colors.GREY
                        ),
                        label='Найти автомойку...',
                        label_style=ft.TextStyle(
                            size=14, color=ft.colors.GREY
                        ),
                        width=730,
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
                width=730,
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.all(0),
            width=730,
        )

    def on_fab_click(self, e):
        self.search_bar.visible = not self.search_bar.visible
        self.page.update()

    def on_search_text_change(self, e):
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
        return [self.create_car_wash_card(wash) for wash in self.car_washes]

    def create_car_wash_card(self, car_wash):
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
                            ft.Container(
                                content=ft.Image(
                                    src=image_link,
                                    fit=ft.ImageFit.COVER,
                                    width=float('inf'),
                                ),
                                height=170,
                                alignment=ft.alignment.center,
                            ),
                            ft.Text(
                                f"{car_wash['name']}",
                                weight=ft.FontWeight.BOLD,
                                size=24,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text(
                                location_address,
                                text_align=ft.TextAlign.CENTER,
                                color=ft.colors.GREY,
                                size=16,
                            ),
                        ],
                        spacing=0,
                    ),
                    padding=ft.padding.all(8),
                ),
                elevation=3,
            ),
            alignment=ft.alignment.center,
            width=400,
            on_click=lambda e, wash=car_wash: self.on_booking_click(wash),
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

        response = self.api.get_car_washes(page=1)  # Убрали параметр limit
        if response.status_code == 200:
            self.car_washes = response.json().get('data', [])
            WashSelectionPage.car_washes_cache = self.car_washes
            self.update_wash_list(self.car_washes)
        else:
            print(
                f'Error loading car washes: '
                f'{response.status_code}, {response.text}'
            )

    def load_location_data(self, location_id):
        """Загрузка данных о локации по её ID"""
        response = self.api.get_location_data(location_id)
        if response.status_code == 200:
            location = response.json()
            print(f'Location data for location_id {location_id}: {location}')
            return location
        else:
            print(
                f'Failed to fetch location: '
                f'{response.status_code}, {response.text}'
            )
            return None

    def redirect_to_sign_in_page(self):
        from washer.ui_components.sign_in_page import SignInPage

        SignInPage(self.page)

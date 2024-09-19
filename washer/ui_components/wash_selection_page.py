import flet as ft
import httpx

from washer.config import config


class WashSelectionPage:
    car_washes_cache = None

    def __init__(self, page: ft.Page, username: str = None):
        self.page = page
        self.api_url = config.api_url
        self.username = username or self.page.client_storage.get('username')
        self.car_washes = []

        stored_username = self.page.client_storage.get('username')
        if username and stored_username and stored_username != username:
            self.page.client_storage.remove('avatar_url')
            self.page.client_storage.remove('saved_cars')

        self.page.client_storage.set('username', self.username)

        access_token = self.page.client_storage.get('access_token')
        if not access_token:
            print('Access token not found, redirecting to login.')
            self.redirect_to_sign_in_page()
            return

        self.avatar_container = self.create_avatar_container()
        self.file_picker = self.create_file_picker()
        page.overlay.append(self.file_picker)

        page.clean()
        page.add(self.create_main_container())
        self.load_car_washes()

    def create_avatar_container(self):
        avatar_url = self.page.client_storage.get('avatar_url') or None

        if avatar_url:
            avatar_content = ft.Image(
                src=avatar_url,
                width=50,
                height=50,
                border_radius=ft.border_radius.all(25),
                fit=ft.ImageFit.COVER,
                key=f'avatar_{avatar_url}',
            )
        else:
            avatar_content = ft.Icon(
                ft.icons.PERSON, size=50, color=ft.colors.GREY
            )

        self.avatar_image = avatar_content

        return ft.Container(
            content=self.avatar_image,
            alignment=ft.alignment.center,
            padding=10,
            on_click=self.on_avatar_click,
        )

    def on_avatar_click(self, e):
        from washer.ui_components.profile_page import ProfilePage

        ProfilePage(self.page)

    def on_picture_select(self, e: ft.FilePickerResultEvent):
        if e.files:
            avatar_url = e.files[0].path
            self.page.client_storage.set('avatar_url', avatar_url)

            self.avatar_container.content = ft.Image(
                src=avatar_url,
                width=50,
                height=50,
                border_radius=ft.border_radius.all(25),
            )
            self.page.update()

    def create_file_picker(self):
        return ft.FilePicker(on_result=self.on_picture_select)

    def create_main_container(self):
        return ft.Column(
            controls=[
                ft.Container(
                    content=ft.Row(
                        [
                            self.avatar_container,
                            ft.Text(
                                f'Welcome, {self.username}!',
                                size=24,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Container(expand=1),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor=ft.colors.GREY_900,
                    padding=ft.padding.all(20),
                    width=350,
                ),
                self.create_search_bar(),
                ft.Column(
                    controls=[],
                    spacing=10,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            width=350,
            height=720,
            alignment=ft.MainAxisAlignment.START,
        )

    def create_wash_list(self):
        return [self.create_car_wash_card(wash) for wash in self.car_washes]

    def create_search_bar(self):
        return ft.Container(
            content=ft.TextField(
                prefix=ft.Icon(ft.icons.SEARCH, size=20),
                label='найти автомойку...',
                label_style=ft.TextStyle(size=14),
                width=320,
                border_radius=ft.border_radius.all(15),
                bgcolor=ft.colors.GREY_900,
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.symmetric(vertical=10),
        )

    def create_car_wash_card(self, car_wash):
        boxes_text = f"{car_wash.get('boxes', 'Unknown')} slots available"

        return ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Image(
                                src='assets/spa_logo.png',
                                width=100,
                                height=100,
                                fit=ft.ImageFit.COVER,
                                border_radius=ft.border_radius.all(50),
                            ),
                            ft.Text(f"{car_wash['name']}"),
                            ft.Text(boxes_text),
                        ],
                        spacing=10,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    on_click=lambda e: self.on_booking_click(car_wash),
                ),
                width=300,
                elevation=3,
            ),
            alignment=ft.alignment.center,
        )

    def on_booking_click(self, car_wash):
        from washer.ui_components.booking_page import BookingPage

        BookingPage(self.page, car_wash, self.username)
        self.page.update()

    def update_car_washes_list(self):
        car_wash_controls = [
            self.create_car_wash_card(wash) for wash in self.car_washes
        ]
        car_washes_column = self.page.controls[0].controls[2]
        car_washes_column.controls = car_wash_controls
        car_washes_column.alignment = ft.MainAxisAlignment.CENTER
        self.page.update()

    def load_car_washes(self):
        if WashSelectionPage.car_washes_cache:
            print('Using cached car washes data')
            self.car_washes = WashSelectionPage.car_washes_cache
            self.update_car_washes_list()
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
            self.update_car_washes_list()
        elif response.status_code == 401:
            if 'token has expired' in response.text.lower():
                print('Token has expired, attempting to refresh...')
                if self.refresh_access_token():
                    print('Token refreshed successfully, retrying request...')
                    self.load_car_washes()
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
                print('Could not validate credentials, redirecting to login.')
                error_message = (
                    'Error loading car washes: '
                    'Could not validate credentials'
                )

                self.page.add(
                    ft.Text(
                        error_message,
                        color=ft.colors.RED,
                    )
                )

                self.redirect_to_sign_in_page()
        else:
            error_message = (
                'Error loading car washes: ' 'Could not validate credentials'
            )

            self.page.add(
                ft.Text(
                    error_message,
                    color=ft.colors.RED,
                )
            )

    def refresh_access_token(self):
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

    def redirect_to_sign_in_page(self):
        from washer.ui_components.sign_in_page import SignInPage

        SignInPage(self.page)

    def on_search_change(self, e):
        query = e.data.lower()
        filtered_washes = [
            wash for wash in self.car_washes if query in wash['name'].lower()
        ]
        self.car_washes = filtered_washes
        self.update_car_washes_list()

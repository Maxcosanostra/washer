import flet as ft
import httpx

from washer.config import config


class WashSelectionPage:
    def __init__(self, page: ft.Page, username: str):
        self.page = page
        self.api_url = config.api_url
        self.username = username
        self.car_washes = []

        page.clean()
        page.add(self.create_main_container())
        self.load_car_washes()

    def create_main_container(self):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        f'Welcome, {self.username}',
                        size=24,
                        weight=ft.FontWeight.BOLD,
                    ),
                    self.create_search_bar(),
                    ft.Column(controls=[], width=350),
                ],
                spacing=20,
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=20,
        )

    def create_search_bar(self):
        return ft.TextField(
            label='Поиск автомоек',
            prefix_icon=ft.icons.SEARCH,
            on_change=self.on_search_change,
            width=300,
        )

    def create_car_wash_card(self, car_wash):
        return ft.Card(
            content=ft.Column(
                [
                    ft.Image(src='assets/spa_logo.png', width=100, height=100),
                    ft.Text(f"{car_wash['name']}"),
                    ft.Text(f"{car_wash['boxes']} slots available"),
                ],
                spacing=10,
            ),
            width=350,
        )

    def update_car_washes_list(self):
        car_wash_controls = [
            self.create_car_wash_card(wash) for wash in self.car_washes
        ]
        car_washes_column = self.page.controls[0].content.controls[2]
        car_washes_column.controls = car_wash_controls
        self.page.update()

    def load_car_washes(self):
        access_token = self.page.client_storage.get('access_token')
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

        url = f'{self.api_url.rstrip("/")}/car_washes?page=1&limit=10'

        response = httpx.get(url, headers=headers)

        if response.status_code == 200:
            self.car_washes = response.json().get('data', [])
            self.update_car_washes_list()
        elif (
            response.status_code == 401
            and 'token has expired' in response.text.lower()
        ):
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
            self.page.add(
                ft.Text(
                    f'Error loading car washes: {response.text}',
                    color=ft.colors.RED,
                )
            )

    def refresh_access_token(self):
        refresh_token = self.page.client_storage.get('refresh_token')
        if not refresh_token:
            print('Refresh token not found')
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

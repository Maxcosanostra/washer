import flet as ft

from washer.api_requests import BackendApi
from washer.config import config


class AdminPage:
    car_washes_cache = None

    def __init__(self, page: ft.Page):
        self.page = page
        self.api_url = config.api_url
        self.locations = {}
        self.selected_image = None
        self.current_car_wash_id = None

        self.api = BackendApi()
        access_token = self.page.client_storage.get('access_token')
        if access_token:
            self.api.set_access_token(access_token)

        self.page.adaptive = True

        self.page.appbar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.icons.LOGOUT,
                on_click=self.on_logout_click,
                icon_color='#ef7b00',
                padding=ft.padding.only(left=10),
            ),
            title=ft.Text(
                'Мои автомойки',
                size=20,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
            center_title=True,
            bgcolor=ft.colors.SURFACE_VARIANT,
            leading_width=60,
        )

        self.loading_overlay = ft.Container(
            content=ft.ProgressRing(),
            alignment=ft.alignment.center,
            visible=False,
            bgcolor='rgba(0, 0, 0, 0.8)',
            expand=True,
        )

        self.car_washes_list_view = ft.ListView(
            controls=[],
            spacing=10,
            expand=True,
            padding=ft.padding.all(10),
        )

        self.page.clean()
        self.page.add(self.create_admin_page())
        self.page.overlay.append(self.loading_overlay)
        self.page.navigation_bar = None
        self.load_car_washes()

    def create_admin_page(self):
        main_content = ft.ListView(
            controls=[
                ft.Container(height=10),
                self.car_washes_list_view,
            ],
            spacing=10,
            expand=True,
            padding=ft.padding.all(0),
        )

        return ft.Container(
            content=main_content,
            margin=ft.margin.only(top=-10),
            expand=True,
            width=730,
            alignment=ft.alignment.center,
        )

    def show_loading(self):
        self.loading_overlay.visible = True
        self.page.update()

    def hide_loading(self):
        self.loading_overlay.visible = False
        self.page.update()

    def load_car_washes(self):
        self.show_loading()
        self.load_locations()

        if AdminPage.car_washes_cache:
            print('Используем кэшированные данные')
            self.car_washes = AdminPage.car_washes_cache
            self.update_car_washes_list()
            self.hide_loading()
            return

        access_token = self.page.client_storage.get('access_token')
        if not access_token:
            print('Access token not found, redirecting to login.')
            self.hide_loading()
            return

        response = self.api.get_car_washes()
        if response.status_code == 200:
            self.car_washes = response.json().get('data', [])
            AdminPage.car_washes_cache = self.car_washes
            self.update_car_washes_list()
        else:
            print(f'Ошибка загрузки данных: {response.text}')

        self.hide_loading()

    def load_locations(self):
        access_token = self.page.client_storage.get('access_token')
        if not access_token:
            print('Access token not found, redirecting to login.')
            return

        response = self.api.get_locations()
        if response is not None and response.status_code == 200:
            self.locations = {
                loc['id']: loc for loc in response.json().get('data', [])
            }
            print(f'Загруженные локации: {self.locations}')
        else:
            print(
                f'Ошибка загрузки локаций: '
                f'{response.text if response else "No Response"}'
            )

    def update_car_washes_list(self):
        if self.car_washes_list_view:
            self.car_washes_list_view.controls = self.create_wash_list()
            self.page.update()

    def create_wash_list(self):
        return [self.create_car_wash_card(wash) for wash in self.car_washes]

    def create_car_wash_card(self, car_wash):
        image_link = car_wash.get('image_link', 'assets/spa_logo.png')
        location_id = car_wash.get('location_id')
        location = self.locations.get(location_id, {})
        city = location.get('city', 'Unknown City')
        address = location.get('address', 'Unknown Address')
        location_display = f'{city}, {address}'

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
                                height=200,
                                alignment=ft.alignment.center,
                            ),
                            ft.Text(
                                f"{car_wash['name']}",
                                weight=ft.FontWeight.BOLD,
                                size=24,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text(
                                location_display,
                                text_align=ft.TextAlign.CENTER,
                                color=ft.colors.GREY,
                                size=16,
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=ft.padding.all(10),
                    on_click=lambda e: self.open_car_wash_edit_page(car_wash),
                ),
                elevation=3,
            ),
            alignment=ft.alignment.center,
            width=400,
        )

    def open_car_wash_edit_page(self, car_wash):
        def load_edit_page(_):
            self.page.appbar = None
            self.page.update()

        from washer.ui_components.carwash_edit_page import CarWashEditPage

        CarWashEditPage(self.page, car_wash, self.locations)
        load_edit_page(None)

    def on_logout_click(self, _):
        def hide_appbar():
            self.page.appbar = None
            self.page.update()

        user_key = f'cars_{self.page.client_storage.get("username")}'
        self.page.client_storage.remove(user_key)
        self.page.client_storage.remove('access_token')
        self.page.client_storage.remove('refresh_token')
        self.page.client_storage.remove('username')

        from washer.ui_components.sign_in_page import SignInPage

        SignInPage(self.page)
        hide_appbar()

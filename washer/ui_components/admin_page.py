import json
import time
from datetime import date

import flet as ft
import httpx

from washer.config import config


class AdminPage:
    car_washes_cache = None

    def __init__(self, page: ft.Page):
        self.page = page
        self.api_url = config.api_url
        self.locations = {}
        self.selected_image = None
        self.current_car_wash_id = None

        self.page.adaptive = True

        self.page.appbar = ft.AppBar(
            title=ft.Text(
                'Управление автомойками',
                size=20,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
            center_title=True,
            bgcolor=ft.colors.SURFACE_VARIANT,
        )

        self.loading_overlay = ft.Container(
            content=ft.ProgressRing(),
            alignment=ft.alignment.center,
            visible=False,
            bgcolor='rgba(0, 0, 0, 0.8)',
            expand=True,
        )

        self.image_picker = ft.FilePicker(on_result=self.on_file_picked)
        self.page.overlay.append(self.image_picker)

        self.car_washes_list_view = ft.ListView(
            controls=[],
            spacing=10,
            expand=True,
            padding=ft.padding.all(10),
        )

        self.page.clean()
        self.page.add(self.create_main_container())
        self.page.overlay.append(self.loading_overlay)

        self.load_car_washes()

    def show_loading(self):
        self.loading_overlay.visible = True
        self.page.update()

    def hide_loading(self):
        self.loading_overlay.visible = False
        self.page.update()

    def create_main_container(self):
        return ft.Column(
            controls=[
                self.car_washes_list_view,
                ft.Container(
                    content=ft.TextButton(
                        text='Выйти',
                        on_click=self.on_logout_click,
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.RED,
                            color=ft.colors.WHITE,
                        ),
                    ),
                    alignment=ft.alignment.center,
                    padding=ft.padding.symmetric(vertical=20),
                ),
            ],
            expand=True,
            height=720,
            alignment=ft.MainAxisAlignment.START,
        )

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

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

        url = f'{self.api_url.rstrip("/")}/car_washes?page=1&limit=10'
        response = httpx.get(url, headers=headers)

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

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

        url = (
            f'{self.api_url.rstrip("/")}/car_washes/locations?page=1&limit=100'
        )
        response = httpx.get(url, headers=headers)

        if response.status_code == 200:
            self.locations = {
                loc['id']: loc for loc in response.json().get('data', [])
            }
            print(f'Загруженные локации: {self.locations}')
        else:
            print(f'Ошибка загрузки локаций: {response.text}')

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
                            ft.Image(
                                src=image_link,
                                width=300,
                                height=180,
                                fit=ft.ImageFit.COVER,
                            ),
                            ft.Text(
                                f"{car_wash['name']}",
                                weight=ft.FontWeight.BOLD,
                                size=20,
                                text_align=ft.TextAlign.LEFT,
                            ),
                            ft.Text(
                                f'{location_display}',
                                text_align=ft.TextAlign.LEFT,
                            ),
                            ft.TextButton(
                                'Изменить изображение',
                                on_click=lambda _: self.change_image(
                                    car_wash['id']
                                ),
                            ),
                            ft.TextButton(
                                'Посмотреть букинги',
                                on_click=lambda e,
                                cw=car_wash: self.open_booking_table_page(cw),
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=ft.padding.all(10),
                    on_click=lambda e: self.open_car_wash_edit_page(car_wash),
                ),
                width=300,
                elevation=3,
            ),
            alignment=ft.alignment.center,
        )

    def change_image(self, car_wash_id):
        self.current_car_wash_id = car_wash_id
        self.image_picker.pick_files(
            allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE
        )

    def on_file_picked(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.selected_image = e.files[0].path
            print(
                f'Выбрано изображение: {self.selected_image} '
                f'для автомойки {self.current_car_wash_id}'
            )
            self.update_car_wash_image(self.current_car_wash_id)

    def update_car_wash_image(self, car_wash_id):
        files = {'image': open(self.selected_image, 'rb')}
        new_values = {'name': 'Spa Detailing', 'location_id': 1}

        access_token = self.page.client_storage.get('access_token')
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

        api_url = f"{self.api_url.rstrip('/')}/car_washes/{car_wash_id}"
        response = httpx.patch(
            api_url,
            files=files,
            data={'new_values': json.dumps(new_values)},
            headers=headers,
        )

        if response.status_code == 200:
            print('Изображение успешно обновлено')
            self.refresh_cache(car_wash_id, files['image'].name)
        else:
            print(f'Ошибка при обновлении изображения: {response.text}')

    def refresh_cache(self, car_wash_id, new_image_link):
        for car_wash in AdminPage.car_washes_cache:
            if car_wash['id'] == car_wash_id:
                car_wash['image_link'] = new_image_link
                self.update_car_washes_list()

    def open_car_wash_edit_page(self, car_wash):
        def load_edit_page(_):
            self.page.appbar = None
            self.page.update()

        from washer.ui_components.carwash_edit_page import CarWashEditPage

        CarWashEditPage(self.page, car_wash, self.api_url, self.locations)
        load_edit_page(None)

    def on_logout_click(self, _):
        def delayed_hide_appbar():
            time.sleep(0.1)
            self.page.appbar = None
            self.page.update()

        user_key = f'cars_{self.page.client_storage.get("username")}'
        self.page.client_storage.remove(user_key)
        self.page.client_storage.remove('access_token')
        self.page.client_storage.remove('refresh_token')
        self.page.client_storage.remove('username')

        from washer.ui_components.sign_in_page import SignInPage

        SignInPage(self.page)

        delayed_hide_appbar()

    def open_booking_table_page(self, car_wash):
        def load_booking_table(_):
            self.page.appbar = None
            self.page.update()

        from washer.ui_components.admin_booking_table import AdminBookingTable

        if car_wash:
            print(
                f"Открываем страницу букингов для автомойки: "
                f"{car_wash['name']} (ID: {car_wash['id']})"
            )
        else:
            print('Ошибка: car_wash не передан!')

        current_date = str(date.today())

        if not car_wash.get('id'):
            print('Ошибка: ID автомойки не найден')
            return
        if not self.api_url:
            print('Ошибка: API URL не передан')
            return

        AdminBookingTable(self.page, car_wash, self.api_url, current_date)
        load_booking_table(None)

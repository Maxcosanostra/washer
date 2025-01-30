from collections import defaultdict

import flet as ft

from washer.api_requests import BackendApi
from washer.ui_components.carwash_edit_page import CarWashEditPage


class ClientsPage:
    def __init__(
        self,
        page: ft.Page,
        car_wash,
        locations,
        is_selection_mode=False,
        on_car_selected=None,
    ):
        self.page = page
        self.car_wash = car_wash
        self.locations = locations
        self.api = BackendApi()
        self.api.set_access_token(self.page.client_storage.get('access_token'))
        self.clients = defaultdict(lambda: {'user_info': {}, 'cars': []})

        self.is_selection_mode = is_selection_mode
        self.on_car_selected = on_car_selected

        self.page.clean()
        self.page.adaptive = True

        self.page.appbar = self.create_app_bar()

        self.page.floating_action_button = self.create_fab()

        self.search_bar = self.create_search_bar(visible=False)
        self.clients_list = ft.Column(expand=True, spacing=10)

        content_list_view = ft.ListView(
            controls=[
                ft.Container(height=10),
                ft.Container(
                    content=ft.Text(
                        'Наши клиенты',
                        weight=ft.FontWeight.BOLD,
                        size=24,
                        text_align=ft.TextAlign.LEFT,
                    ),
                    margin=ft.margin.only(top=20),
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            self.search_bar,
                            self.clients_list,
                        ],
                        spacing=10,
                    ),
                    expand=True,
                ),
            ],
            padding=ft.padding.only(top=10, bottom=10),
            spacing=10,
        )

        self.main_container = ft.Container(
            content=content_list_view,
            margin=ft.margin.only(top=-10),
            expand=True,
            width=730,
            alignment=ft.alignment.center,
        )

        self.loading_overlay = self.loading_overlay()
        self.page.overlay.append(self.loading_overlay)

        self.page.add(self.main_container)

        self.show_loading()
        self.load_clients()
        self.hide_loading()

        self.page.update()

    def create_app_bar(self):
        app_bar = ft.AppBar(
            leading=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        on_click=self.on_back_click,
                        icon_color='#ef7b00',
                        padding=ft.padding.only(left=10, right=5),
                    ),
                    ft.Text('Назад', size=16, color='#ef7b00'),
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            center_title=True,
            title=ft.Text('Наши клиенты', size=20, color=ft.colors.BLACK),
            bgcolor=ft.colors.SURFACE_VARIANT,
            leading_width=120,
        )
        return app_bar

    def create_fab(self):
        return ft.FloatingActionButton(
            icon=ft.icons.SEARCH,
            tooltip='Поиск клиентов',
            on_click=self.on_fab_click,
            bgcolor=ft.colors.BLUE,
        )

    def loading_overlay(self):
        return ft.Container(
            content=ft.ProgressRing(),
            alignment=ft.alignment.center,
            visible=False,
            bgcolor='rgba(0, 0, 0, 0.3)',
            expand=True,
        )

    def show_loading(self):
        if self.page.overlay:
            self.loading_overlay.visible = True
            self.page.update()

    def hide_loading(self):
        if self.page.overlay:
            self.loading_overlay.visible = False
            self.page.update()

    def on_back_click(self, e):
        self.page.clean()
        CarWashEditPage(self.page, self.car_wash, self.locations)

    def load_clients(self):
        car_wash_id = self.car_wash['id']
        response = self.api.get_bookings(car_wash_id)

        if response.status_code != 200:
            self.show_error_message('Не удалось загрузить букинги.')
            return

        bookings = response.json().get('data', [])
        user_ids = set()

        for booking in bookings:
            user = booking.get('user_car', {}).get('user', {})
            if user:
                user_id = user['id']
                user_ids.add(user_id)
                if not self.clients[user_id]['user_info']:
                    self.clients[user_id]['user_info'] = {
                        'id': user['id'],
                        'username': user.get('username', 'Неизвестный'),
                        'first_name': user.get('first_name', ''),
                        'last_name': user.get('last_name', ''),
                        'phone_number': user.get('phone_number') or '---',
                        'image_link': user.get('image_link', None),
                        'role_id': user.get('role_id', None),
                    }

        for user_id in user_ids:
            cars_response = self.api.get_user_cars(user_id=user_id)
            if cars_response and cars_response.status_code == 200:
                cars = cars_response.json().get('data', [])
                self.clients[user_id]['cars'] = cars
            else:
                print(
                    f"Ошибка загрузки автомобилей для пользователя {user_id}: "
                    f"{cars_response.text if cars_response else 'No response'}"
                )

                self.clients[user_id]['cars'] = []

        self.build_clients_ui()

    def build_clients_ui(self):
        self.update_clients_list(self.clients)

    def create_search_bar(self, visible: bool = False):
        search_field = ft.TextField(
            prefix=ft.Icon(ft.icons.SEARCH, size=20, color=ft.colors.GREY),
            label='Поиск клиентов...',
            label_style=ft.TextStyle(size=14, color=ft.colors.GREY),
            width=730,
            height=50,
            border=ft.InputBorder.NONE,
            border_radius=ft.border_radius.all(15),
            bgcolor=ft.colors.TRANSPARENT,
            border_color=ft.colors.TRANSPARENT,
            filled=False,
            on_change=self.on_search,
        )
        self.search_text_field = search_field

        return ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=search_field,
                    alignment=ft.alignment.center,
                    padding=ft.padding.all(0),
                ),
                elevation=0,
                width=730,
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.all(0),
            width=730,
            visible=visible,
        )

    def on_search(self, e):
        query = e.control.value.lower()
        filtered_clients = defaultdict(lambda: {'user_info': {}, 'cars': []})

        for user_id, data in self.clients.items():
            user_info = data['user_info']
            role_id = user_info.get('role_id')
            if role_id != 2:
                continue

            first_name = user_info.get('first_name', '').strip()
            last_name = user_info.get('last_name', '').strip()
            full_name = f'{first_name} {last_name}'.lower()

            phone_number = (user_info.get('phone_number') or '').lower()
            if query in full_name or query in phone_number:
                filtered_clients[user_id] = data

        self.update_clients_list(filtered_clients)

    def update_clients_list(self, clients_data):
        self.clients_list.controls.clear()

        has_clients = False

        for user_id, data in clients_data.items():
            user_info = data['user_info']
            role_id = user_info.get('role_id')

            print(f'Processing user_id={user_id}, role_id={role_id}')

            if role_id != 2:
                continue

            has_clients = True

            cars = data['cars']
            # first_name = user_info.get('first_name', '').strip()
            # last_name = user_info.get('last_name', '').strip()
            # full_name = f'{first_name} {last_name}'.strip() or user_info.get(
            #     'username', 'Неизвестный'
            # )

            user_card = self.create_client_card(
                {'user_info': user_info, 'cars': cars}
            )

            self.clients_list.controls.append(user_card)

        if not has_clients:
            no_results = ft.Container(
                content=ft.Text(
                    'Клиенты не найдены.',
                    size=16,
                    color=ft.colors.GREY,
                    text_align=ft.TextAlign.CENTER,
                ),
                alignment=ft.alignment.center,
                padding=ft.padding.all(20),
            )
            self.clients_list.controls.append(no_results)

        self.page.update()

    def create_client_card(self, client):
        user_info = client['user_info']
        cars = client['cars']

        first_name = user_info.get('first_name', '').strip()
        last_name = user_info.get('last_name', '').strip()
        full_name = f'{first_name} {last_name}'.strip() or user_info.get(
            'username', 'Неизвестный'
        )

        return ft.Card(
            elevation=2,
            content=ft.Container(
                padding=ft.padding.all(10),
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.CircleAvatar(
                                    content=ft.Icon(ft.icons.PERSON, size=24),
                                    radius=24,
                                    bgcolor=ft.colors.BLUE_100
                                    if not user_info.get('image_link')
                                    else None,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            full_name,
                                            size=18,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        ft.Text(
                                            user_info.get(
                                                'phone_number', '---'
                                            ),
                                            size=14,
                                            color=ft.colors.GREY,
                                        ),
                                        ft.Text(
                                            f"ID: "
                                            f"{user_info.get('id', '---')}",
                                            size=12,
                                            color=ft.colors.GREY,
                                        ),
                                    ],
                                    spacing=2,
                                    alignment=ft.MainAxisAlignment.START,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            spacing=10,
                        ),
                        ft.Divider(),
                        ft.Text(
                            'Автомобили:', size=16, weight=ft.FontWeight.BOLD
                        ),
                        ft.Column(
                            controls=[
                                ft.ListTile(
                                    leading=ft.Icon(ft.icons.DIRECTIONS_CAR),
                                    title=ft.Text(
                                        car.get(
                                            'name', 'Неизвестный автомобиль'
                                        )
                                    ),
                                    subtitle=ft.Text(
                                        f"Гос. номер: "
                                        f"{car.get('license_plate', '---')}"
                                    ),
                                    on_click=self.on_car_click
                                    if self.is_selection_mode
                                    else None,
                                    data=car['id']
                                    if self.is_selection_mode
                                    else None,
                                )
                                for car in cars
                            ],
                            spacing=5,
                            # padding=ft.padding.only(left=0),
                        ),
                    ],
                    spacing=10,
                ),
            ),
        )

    def on_car_click(self, e):
        if not self.is_selection_mode or not self.on_car_selected:
            return

        car_id = e.control.data
        if not car_id:
            self.show_error_message('Не удалось получить ID автомобиля.')
            return

        try:
            response = self.api.get_car_by_id(car_id)
            if response.status_code == 200:
                car_details = response.json()
                self.on_car_selected(car_details)
            else:
                error_message = (
                    response.text if response else 'Неизвестная ошибка'
                )
                self.show_error_message(
                    f'Ошибка при получении данных автомобиля: {error_message}'
                )
        except Exception as ex:
            self.show_error_message(
                f'Ошибка при получении данных автомобиля: {str(ex)}'
            )

    def show_error_message(self, message: str):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.colors.RED),
            open=True,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def on_fab_click(self, e):
        self.search_bar.visible = not self.search_bar.visible

        self.page.update()

        if self.search_bar.visible and hasattr(self, 'search_text_field'):
            self.search_text_field.focus()

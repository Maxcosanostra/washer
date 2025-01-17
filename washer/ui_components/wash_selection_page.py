import datetime

import flet as ft

from washer.api_requests import BackendApi
from washer.config import config
from washer.ui_components.account_settings_page import AccountSettingsPage
from washer.ui_components.my_finance_page import MyFinancePage


class WashSelectionPage:
    car_washes_cache = None

    def __init__(self, page: ft.Page, username: str = None):
        self.page = page
        self.api = BackendApi()
        self.api.set_access_token(self.page.client_storage.get('access_token'))
        self.username = username or self.page.client_storage.get('username')
        self.api_url = config.api_url
        self.avatar_container = self.create_avatar_container()
        self.car_washes = []

        self.page.adaptive = True
        self.page.scroll = 'adaptive'

        access_token = self.page.client_storage.get('access_token')
        if not access_token:
            print('Access token not found, redirecting to login.')
            self.redirect_to_sign_in_page()
            return

        self.page.clean()

        self.page.appbar = self.create_app_bar_with_drawer()
        self.page.drawer = self.create_navigation_drawer()

        self.progress_bar = ft.ProgressBar(width=400, visible=False)

        self.car_washes_list = ft.ListView(controls=[], padding=0, spacing=0)

        self.search_bar = self.create_search_bar()
        self.search_bar.visible = False

        self.main_container = self.create_main_container()
        self.page.add(
            self.main_container,
            ft.Container(self.progress_bar, alignment=ft.alignment.center),
        )

        self.progress_bar.visible = True
        self.page.update()

        self.load_car_washes()

        self.progress_bar.visible = False

        self.page.floating_action_button = ft.FloatingActionButton(
            icon=ft.icons.SEARCH,
            tooltip='Поиск автомойки',
            on_click=self.on_fab_click,
        )

        self.page.navigation_bar = ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.icons.EVENT_NOTE,
                    label='Записи',
                ),
                ft.NavigationBarDestination(
                    icon=ft.icons.HOME,
                    label='Главная',
                ),
                ft.NavigationBarDestination(
                    icon=ft.icons.CAR_REPAIR,
                    label='Мои автомобили',
                ),
            ],
            selected_index=1,
            on_change=self.on_navigation_change,
        )

        self.page.update()

    def reload_page(self):
        username = self.username
        self.page.clean()
        WashSelectionPage(self.page, username)

    def create_navigation_drawer(self):
        drawer = ft.NavigationDrawer(
            on_dismiss=self.on_drawer_dismiss,
            on_change=self.on_drawer_change,
            controls=[
                ft.Container(
                    padding=ft.padding.all(16),
                    bgcolor=ft.colors.BLUE_GREY_900,
                    content=ft.Row(
                        controls=[
                            self.avatar_container,
                            ft.Text(
                                f'Привет, {self.username}!',
                                color=ft.colors.WHITE,
                                size=18,
                                weight=ft.FontWeight.BOLD,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                ft.Divider(thickness=1, color=ft.colors.GREY_300),
                ft.NavigationDrawerDestination(
                    label='Главная',
                    icon=ft.icons.HOME_OUTLINED,
                    selected_icon=ft.icons.HOME,
                ),
                ft.NavigationDrawerDestination(
                    label='Мои финансы',
                    icon=ft.icons.ATTACH_MONEY_OUTLINED,
                    selected_icon=ft.icons.ATTACH_MONEY,
                ),
                ft.Divider(thickness=1, color=ft.colors.GREY_300),
                ft.NavigationDrawerDestination(
                    label='Настройки',
                    icon=ft.icons.SETTINGS_OUTLINED,
                    selected_icon=ft.icons.SETTINGS,
                ),
                ft.NavigationDrawerDestination(
                    label='Выйти',
                    icon=ft.icons.LOGOUT_OUTLINED,
                    selected_icon=ft.icons.LOGOUT,
                ),
            ],
        )
        return drawer

    def create_app_bar_with_drawer(self):
        return ft.AppBar(
            leading=ft.IconButton(
                icon=ft.icons.MENU,
                on_click=self.open_drawer,
            ),
            title=ft.Container(
                content=ft.Text(
                    'Wexy!',
                    font_family='LavishlyYours',
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=None,
                ),
                margin=ft.margin.only(top=-9),
                # Слегка поднимаем текст через отрицательный отступ
            ),
            center_title=True,
            bgcolor=None,
        )

    def open_drawer(self, e):
        self.page.drawer.open = True
        self.page.update()  # Обновляем страницу

    def on_drawer_dismiss(self, e):
        print('NavigationDrawer закрыт')

    def on_drawer_change(self, e):
        if not self.page.drawer:
            print('NavigationDrawer отсутствует на текущей странице.')
            return

        selected = e.control.selected_index
        print(f'Выбранный индекс в NavigationDrawer: {selected}')

        self.page.drawer.open = False
        self.page.update()
        print(f'NavigationDrawer закрыт: {self.page.drawer.open}')

        if selected == 0:
            self.reload_page()
        elif selected == 1:
            self.open_my_finances_page()
        elif selected == 2:
            self.open_settings_page()
        elif selected == 3:
            self.logout()

        if self.page.drawer:
            print(
                f'NavigationDrawer после обработки выбора: '
                f'{self.page.drawer.open}'
            )

    def open_settings_page(self):
        AccountSettingsPage(self.page)
        self.page.update()

    def open_my_finances_page(self):
        my_finance_page = MyFinancePage(self.page)
        my_finance_page.open()

        if hasattr(self.page, 'navigation_bar'):
            self.page.navigation_bar.selected_index = 3
        self.page.update()

    def logout(self):
        self.page.client_storage.clear()
        self.redirect_to_sign_in_page()

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

        ProfilePage(self.page)

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

        available_slots = self.get_available_slots(car_wash['id'])

        if available_slots > 0:
            slots_text = 'Есть свободные боксы'
        else:
            slots_text = 'Свободных боксов на сегодня нет'

        return ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Stack(
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
                            ft.Container(
                                content=ft.Text(
                                    slots_text,
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.colors.BLACK,
                                ),
                                border=ft.Border(
                                    left=ft.BorderSide(
                                        color=ft.colors.GREY, width=2
                                    ),
                                    right=ft.BorderSide(
                                        color=ft.colors.GREY, width=2
                                    ),
                                    top=ft.BorderSide(
                                        color=ft.colors.GREY, width=2
                                    ),
                                    bottom=ft.BorderSide(
                                        color=ft.colors.GREY, width=2
                                    ),
                                ),
                                border_radius=ft.border_radius.all(10),
                                padding=ft.padding.symmetric(
                                    horizontal=6, vertical=2
                                ),
                                right=10,
                                top=10,
                                bgcolor='#80E0E0E0',
                            ),
                            ft.Text(
                                f"{car_wash['name']}",
                                weight=ft.FontWeight.BOLD,
                                size=24,
                                text_align=ft.TextAlign.CENTER,
                                top=170,
                            ),
                            ft.Text(
                                location_address,
                                text_align=ft.TextAlign.CENTER,
                                color=ft.colors.GREY,
                                size=16,
                                top=203,
                            ),
                        ]
                    ),
                    height=240,
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
            self.update_wash_list_with_slots(self.car_washes)
            return

        response = self.api.get_car_washes(page=1)
        if response.status_code == 200:
            self.car_washes = response.json().get('data', [])
            WashSelectionPage.car_washes_cache = self.car_washes
            self.update_wash_list_with_slots(self.car_washes)
        else:
            print(
                f'Error loading car washes: '
                f'{response.status_code}, {response.text}'
            )

    def update_wash_list_with_slots(self, washes):
        self.car_washes_list.controls = [
            self.create_car_wash_card(wash) for wash in washes
        ]
        self.car_washes_list.update()

    def get_available_slots(self, car_wash_id, date=None):
        if date is None:
            date = datetime.datetime.today().date()
        total_available = 0

        try:
            response = self.api.get_available_times(
                car_wash_id, date.isoformat()
            )
            if response and response.status_code == 200:
                all_available_times = response.json().get(
                    'available_times', {}
                )
                for _box_id, time_ranges in all_available_times.items():
                    for time_range in time_ranges:
                        try:
                            start_time = datetime.datetime.fromisoformat(
                                time_range[0]
                            )
                            end_time = datetime.datetime.fromisoformat(
                                time_range[1]
                            )

                            while start_time < end_time:
                                potential_end_time = (
                                    start_time + datetime.timedelta(hours=2)
                                )

                                if (
                                    start_time.date() == date
                                    and start_time > datetime.datetime.now()
                                    and potential_end_time <= end_time
                                ):
                                    total_available += 1
                                start_time += datetime.timedelta(hours=1)
                        except ValueError:
                            continue
        except Exception as e:
            print(f'Ошибка при обновлении доступных мест: {str(e)}')

        return total_available

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

    def on_navigation_change(self, e):
        selected_index = e.control.selected_index
        print(f'NavigationBar selected index: {selected_index}')

        if selected_index == 0:
            self.open_my_bookings_page()
        elif selected_index == 1:
            self.reload_page()
        elif selected_index == 2:
            self.open_my_cars_page()

        self.page.update()

    def open_my_bookings_page(self):
        from washer.ui_components.my_bookings_page import MyBookingsPage

        if not self.car_washes:
            print('Car washes data is not loaded yet.')
            return

        selected_car_wash = self.car_washes[0]
        location_data = self.load_location_data(
            selected_car_wash.get('location_id')
        )

        my_bookings_page = MyBookingsPage(
            page=self.page,
            api_url=self.api_url,
            car_wash=selected_car_wash,
            location_data=location_data,
        )
        my_bookings_page.open()

        self.page.navigation_bar.selected_index = 0
        self.page.update()

    def open_my_cars_page(self):
        from washer.ui_components.my_cars_page import MyCarsPage

        cars = self.page.client_storage.get('cars') or []
        my_cars_page = MyCarsPage(
            page=self.page,
            api_url=self.api_url,
            cars=cars,
        )
        my_cars_page.open()

        self.page.navigation_bar.selected_index = 2
        self.page.update()

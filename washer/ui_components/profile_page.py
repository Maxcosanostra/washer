import io
from datetime import datetime

import flet as ft
import httpx

from washer.config import config
from washer.ui_components.account_settings_page import AccountSettingsPage
from washer.ui_components.select_car_page import SelectCarPage


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

    # def open_account_settings(self, e):
    #     self.page.clean()
    #     self.page.add(self.create_account_settings_page())
    #     self.page.update()

    def open_account_settings(self, e):
        """Открывает страницу,используя отдельный класс AccountSettingsPage."""
        self.page.clean()
        AccountSettingsPage(self.page)  # Создаем экземпляр отдельного класса
        self.page.update()

    def open_finances_page(self, e):
        self.page.clean()
        self.page.add(self.create_finances_page())
        self.page.update()

    def create_finances_page(self):
        self.page.appbar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                on_click=self.return_to_profile,
                icon_color=ft.colors.WHITE,
                padding=ft.padding.only(left=10),
            ),
            title=ft.Text(
                'Финансы',
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.WHITE,
            ),
            center_title=True,
            bgcolor=ft.colors.BLUE,
            leading_width=40,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        'Финансовая информация будет здесь',
                        size=20,
                        color=ft.colors.GREY_700,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
            ),
            padding=ft.padding.all(20),
        )

    # def open_account_settings(self, e):
    #     self.page.clean()
    #     self.page.add(self.create_account_settings_page())
    #     self.page.update()
    #
    # def create_account_settings_page(self):
    #     self.page.appbar = ft.AppBar(
    #         leading=ft.IconButton(
    #             icon=ft.icons.ARROW_BACK,
    #             on_click=self.return_to_profile,
    #             icon_color=ft.colors.WHITE,
    #             padding=ft.padding.only(left=10),
    #         ),
    #         title=ft.Text(
    #             'Учетная запись', size=20, weight=ft.FontWeight.BOLD
    #         ),
    #         center_title=True,
    #         bgcolor=ft.colors.SURFACE_VARIANT,
    #         leading_width=40,
    #     )
    #
    #     return ft.Container(
    #         content=ft.Column(
    #             controls=[
    #                 ft.Text(
    #                     'Настройки аккаунта будут здесь',
    #                     size=20,
    #                     color=ft.colors.GREY_700,
    #                 ),
    #             ],
    #             alignment=ft.MainAxisAlignment.CENTER,
    #             horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    #             spacing=15,
    #         ),
    #         padding=ft.padding.all(20),
    #     )

    def open_cars_page(self, e):
        self.load_user_cars_from_server()
        self.page.clean()
        self.page.add(self.create_cars_page())
        self.page.update()

    def create_cars_page(self):
        self.page.appbar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                on_click=self.return_to_profile,
                icon_color=ft.colors.WHITE,
                padding=ft.padding.only(left=10),
            ),
            title=ft.Text(
                'Мои автомобили',
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.WHITE,
            ),
            center_title=True,
            bgcolor=ft.colors.BLUE,
            leading_width=40,
        )

        car_blocks = [self.create_car_display(car) for car in self.cars]

        if not self.cars:
            empty_image = ft.Container(
                content=ft.Image(
                    src='https://drive.google.com/uc?id=122KNtdntfiTPaOB5eAA0b1N_IxCPMY3a',
                    width=300,
                    height=300,
                    fit=ft.ImageFit.COVER,
                ),
                padding=ft.padding.only(top=100),
            )
            empty_text = ft.Container(
                content=ft.Text(
                    'У вас пока нет добавленных автомобилей',
                    size=18,
                    color=ft.colors.GREY_500,
                    text_align=ft.TextAlign.CENTER,
                ),
                padding=ft.padding.only(top=20),
            )
            car_blocks = [
                empty_image,
                empty_text,
            ]

        return ft.Container(
            content=ft.Column(
                controls=[
                    *car_blocks,
                    ft.ElevatedButton(
                        text='Добавить автомобиль',
                        on_click=self.on_add_car_click,
                        bgcolor=ft.colors.BLUE,
                        color=ft.colors.WHITE,
                    ),
                ],
                spacing=15,
                scroll='adaptive',
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.all(20),
        )

    def create_car_display(self, car):
        car_name = car.get('name', 'Название не указано')
        parts = car_name.split(' ')
        brand = parts[0] if len(parts) > 0 else 'Бренд не указан'
        model = (
            ' '.join(parts[1:-1]) if len(parts) > 2 else 'Модель не указана'
        )
        generation = parts[-1] if len(parts) > 1 else 'Поколение не указано'

        car_details = [
            ('Модель', model),
            ('Поколение', generation),
        ]

        car_info_column = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(label, weight=ft.FontWeight.BOLD, size=16),
                        ft.Text(value, color=ft.colors.GREY_600, size=16),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
                for label, value in car_details
            ],
            spacing=10,
        )

        delete_button = ft.TextButton(
            'Удалить автомобиль',
            on_click=lambda e: self.on_delete_car(car['id']),
            style=ft.ButtonStyle(
                color=ft.colors.RED_400,
                padding=ft.padding.symmetric(vertical=5),
            ),
        )

        return ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Container(
                                content=ft.Text(
                                    brand,
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                alignment=ft.alignment.center,
                                padding=ft.padding.only(bottom=10),
                            ),
                            car_info_column,
                            ft.Divider(),
                            delete_button,
                        ],
                        spacing=15,
                    ),
                    padding=ft.padding.all(15),
                ),
                elevation=3,
            ),
            width=370,
            margin=ft.margin.only(bottom=20),
        )

    def open_bookings_page(self, e):
        self.load_user_bookings_from_server()
        self.page.clean()
        self.page.add(self.create_bookings_page())
        self.page.update()

    def create_bookings_page(self):
        self.page.appbar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                on_click=self.return_to_profile,
                icon_color=ft.colors.WHITE,
                padding=ft.padding.only(left=10),
            ),
            title=ft.Text(
                'Мои записи',
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.WHITE,
            ),
            center_title=True,
            bgcolor=ft.colors.PURPLE,
            leading_width=40,
        )

        active_bookings = [
            booking
            for booking in self.bookings
            if datetime.fromisoformat(booking['start_datetime'])
            > datetime.now()
        ]

        booking_content = [
            self.create_booking_display(booking, active=True)
            for booking in active_bookings
        ]

        completed_bookings = [
            self.create_booking_display(booking, active=False)
            for booking in self.bookings
            if datetime.fromisoformat(booking['start_datetime'])
            <= datetime.now()
        ]

        if not booking_content:
            empty_image = ft.Container(
                content=ft.Image(
                    src='https://drive.google.com/uc?id=11B4mRtzpx2TjtO6X4t-nc5gdf_fHHEoK',
                    width=300,
                    height=300,
                    fit=ft.ImageFit.COVER,
                ),
                padding=ft.padding.only(top=130),
            )
            empty_text = ft.Container(
                content=ft.Text(
                    'У вас пока нет активных записей',
                    size=18,
                    color=ft.colors.GREY_500,
                    text_align=ft.TextAlign.CENTER,
                ),
                padding=ft.padding.only(top=20),
                # Отступ между изображением и текстом
            )
            booking_content = [empty_image, empty_text]

        toggle_button = ft.ElevatedButton(
            text='Показать записи'
            if not self.completed_visible
            else 'Скрыть записи',
            on_click=self.toggle_completed_visibility,
            bgcolor=ft.colors.PURPLE,
            color=ft.colors.WHITE,
        )
        booking_content.append(toggle_button)

        self.completed_bookings_container.content = ft.Column(
            controls=completed_bookings,
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        booking_content.append(self.completed_bookings_container)

        return ft.Container(
            content=ft.Column(
                controls=booking_content,
                spacing=15,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll='adaptive',
            ),
            padding=ft.padding.all(10),
        )

    def return_to_profile(self, e):
        self.page.appbar = None
        self.page.clean()
        self.page.add(self.create_profile_page())
        self.page.update()

    def load_user_cars_from_server(self):
        """Загрузка автомобилей пользователя с сервера"""
        try:
            access_token = self.page.client_storage.get('access_token')
            user_id = self.page.client_storage.get('user_id')

            if not user_id:
                print('User ID not found!')
                return

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
            }

            url = (
                f'{self.api_url.rstrip("/")}/cars?user_id={user_id}&limit=100'
            )
            response = httpx.get(url, headers=headers)

            if response.status_code == 200:
                self.cars = response.json().get('data', [])
            else:
                print(
                    f'Ошибка при загрузке автомобилей с сервера: '
                    f'{response.status_code} - {response.text}'
                )
        except Exception as e:
            print(f'Ошибка при запросе автомобилей с сервера: {e}')

    def load_user_bookings_from_server(self):
        try:
            access_token = self.page.client_storage.get('access_token')
            user_id = self.page.client_storage.get('user_id')

            if not user_id:
                print('User ID not found!')
                return

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
            }

            url = (
                f'{self.api_url.rstrip("/")}/car_washes/bookings'
                f'?user_id={user_id}&limit=100'
            )
            response = httpx.get(url, headers=headers)

            if response.status_code == 200:
                self.bookings = response.json().get('data', [])
            else:
                print(
                    f'Ошибка при загрузке букингов: '
                    f'{response.status_code} - {response.text}'
                )
        except Exception as e:
            print(f'Ошибка при запросе букингов с сервера: {e}')

    def create_car_blocks(self):
        car_blocks = []
        for index, car in enumerate(self.cars):
            car_name = car.get('name', 'Название не указано')
            car_block = ft.Card(
                content=ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Text(
                                            f'{car_name}',
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                        )
                                    ],
                                    spacing=5,
                                ),
                                width=240,
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE,
                                on_click=lambda e, i=index: self.on_delete_car(
                                    i
                                ),
                                icon_color=ft.colors.RED,
                                padding=ft.padding.only(left=10, bottom=35),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    padding=ft.padding.all(10),
                    bgcolor=ft.colors.GREY_900,
                    border_radius=ft.border_radius.all(15),
                ),
                width=300,
                elevation=2,
            )
            car_blocks.append(car_block)
        return car_blocks

    def on_delete_car(self, car_id):
        def confirm_delete(e):
            self.page.close(dlg_modal)
            self.delete_car_from_server(car_id)

        def cancel_delete(e):
            self.page.close(dlg_modal)

        dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text('Подтверждение удаления'),
            content=ft.Text('Вы уверены, что хотите удалить этот автомобиль?'),
            actions=[
                ft.TextButton('Да', on_click=confirm_delete),
                ft.TextButton('Нет', on_click=cancel_delete),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.open(dlg_modal)

    def delete_car_from_server(self, car_id):
        access_token = self.page.client_storage.get('access_token')
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }
        url = f'{self.api_url.rstrip("/")}/cars/{car_id}'
        print(f'Отправка DELETE запроса на {url}')

        response = httpx.delete(url, headers=headers)

        if response.status_code == 200:
            self.cars = [car for car in self.cars if car['id'] != car_id]
            self.page.clean()
            self.page.add(
                self.create_cars_page()
            )  # Обновляем страницу автомобилей
            self.page.update()
            print(f'Автомобиль с ID {car_id} успешно удалён.')
        else:
            print(f'Ошибка при удалении автомобиля: {response.text}')

    def create_booking_blocks(self):
        current_datetime = datetime.now()
        active_bookings = []
        completed_bookings = []

        for booking in self.bookings:
            booking_datetime = datetime.fromisoformat(
                booking['start_datetime']
            )
            if booking_datetime > current_datetime:
                active_bookings.append(
                    self.create_booking_display(booking, active=True)
                )
            else:
                completed_bookings.append(
                    self.create_booking_display(booking, active=False)
                )

        blocks = []
        if active_bookings:
            blocks.append(
                ft.Text(
                    'Актуальные записи',
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.BLUE,
                )
            )
            blocks.extend(active_bookings)

        toggle_button = ft.TextButton(
            text='Показать завершенные записи'
            if not self.completed_visible
            else 'Скрыть завершенные записи',
            on_click=self.toggle_completed_visibility,
            style=ft.ButtonStyle(
                color=ft.colors.GREY, padding=ft.padding.symmetric(vertical=10)
            ),
        )
        blocks.append(toggle_button)

        self.completed_bookings_container = ft.Container(
            visible=self.completed_visible,
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            'Завершенные записи',
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.GREY,
                        ),
                        alignment=ft.alignment.center,
                    ),
                    *completed_bookings,
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.only(top=20),
            expand=True,
        )

        blocks.append(self.completed_bookings_container)

        return (
            blocks
            if blocks
            else [
                ft.Text('Записей пока нет', color=ft.colors.GREY_500, size=18)
            ]
        )

    def toggle_completed_visibility(self, e):
        self.completed_visible = not self.completed_visible

        e.control.text = (
            'Скрыть записи' if self.completed_visible else 'Показать записи'
        )

        self.completed_bookings_container.visible = self.completed_visible

        e.control.update()
        self.page.update()

    def create_booking_display(self, booking, active=True):
        car_wash_name = self.car_wash.get('name', 'Автомойка не указана')
        address = (
            f"{self.location_data.get('city', 'Город не указан')}, "
            f"{self.location_data.get('address', 'Адрес не указан')}"
        )

        booking_details = [
            (
                'Дата и время',
                f"{booking['start_datetime'].split('T')[0]} в "
                f"{booking['start_datetime'].split('T')[1][:5]}",
            ),
            ('Выбранный бокс', f"Бокс №{booking['box_id']}"),
            ('Автомойка', car_wash_name),
            ('Адрес', address),
            ('Цена', f"₸{booking['price']}"),
        ]

        booking_info_column = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(label, weight=ft.FontWeight.BOLD, size=16),
                        ft.Text(value, color=ft.colors.GREY_600, size=16),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
                for label, value in booking_details
            ],
            spacing=10,
        )

        additional_message = (
            ft.Text(
                'Мы ждем вас!' if active else '',
                size=18,
                color=ft.colors.GREY_500,
                text_align=ft.TextAlign.CENTER,
            )
            if active
            else None
        )

        cancel_button = (
            ft.TextButton(
                'Отменить букинг',
                on_click=lambda e: self.on_delete_booking(booking['id']),
                style=ft.ButtonStyle(
                    color=ft.colors.RED_400,
                    padding=ft.padding.symmetric(vertical=5),
                ),
            )
            if active
            else None
        )

        return ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [booking_info_column, ft.Divider()]
                        + ([additional_message] if additional_message else [])
                        + ([cancel_button] if cancel_button else []),
                        spacing=15,
                    ),
                    padding=ft.padding.all(15),
                ),
                elevation=3,
            ),
            width=400,
            padding=ft.padding.all(5),
            margin=ft.margin.only(bottom=20),
        )

    def on_delete_booking(self, booking_id):
        def confirm_delete(e):
            self.page.close(dlg_modal)
            self.delete_booking_from_server(booking_id)

        def cancel_delete(e):
            self.page.close(dlg_modal)

        dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text('Подтверждение отмены'),
            content=ft.Text('Вы уверены, что хотите отменить этот букинг?'),
            actions=[
                ft.TextButton('Да', on_click=confirm_delete),
                ft.TextButton('Нет', on_click=cancel_delete),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.open(dlg_modal)

    def delete_booking_from_server(self, booking_id):
        access_token = self.page.client_storage.get('access_token')
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }
        url = f'{self.api_url.rstrip("/")}/car_washes/bookings/{booking_id}'
        print(f'Отправка DELETE запроса на {url}')

        response = httpx.delete(url, headers=headers)

        if response.status_code == 200:
            self.bookings = [b for b in self.bookings if b['id'] != booking_id]
            self.page.clean()
            self.page.add(self.create_bookings_page())
            self.page.update()
            print(f'Букинг с ID {booking_id} успешно удален.')
        else:
            print(f'Ошибка при удалении букинга: {response.text}')

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

    def on_add_car_click(self, e):
        SelectCarPage(self.page, self.on_car_saved)

    def on_car_saved(self, car):
        self.cars.append(car)
        self.page.clean()
        self.page.add(self.create_cars_page())
        self.page.update()
